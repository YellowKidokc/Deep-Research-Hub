from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder
import operator

from langgraph.types import Command, Send

from deepresearch.prompts import *
from deepresearch.client_init import init_llm
from deepresearch.chunk_prep import create_chunks
from deepresearch.qdrant_setup import rag_pipeline_setup, retrieve_from_store
from deepresearch.schema import AgentState, ResearchState, Sections, Literal, Queries, SearchResult, Feedback

from configuration import LLM_CONFIG

llm = init_llm(
    provider=LLM_CONFIG["provider"],
    model=LLM_CONFIG["model"],
    temperature=LLM_CONFIG["temperature"]
)

def resource_setup_node(state: AgentState, config: RunnableConfig):
    thread_id = config.get("configurable").get("thread_id")
    directory_path = state.get("resource_path")
    # The user already selected the resource folder before the graph starts.
    # Do not ask a second ingestion question inside the graph.
    chunks = create_chunks(directory_path, auto_continue=True)
    if not chunks:
        raise ValueError(f"No supported document content was found in: {directory_path}")
    rag_pipeline_setup(thread_id, chunks)


def report_structure_planner_node(state: AgentState, config: RunnableConfig):
    report_structure_planner_system_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(REPORT_STRUCTURE_PLANNER_SYSTEM_PROMPT_TEMPLATE),
        HumanMessagePromptTemplate.from_template(
            template="""
            Topic: {topic}
            Outline: {outline}
            """
        ),
        MessagesPlaceholder(variable_name="messages")
    ])

    report_structure_planner_llm = report_structure_planner_system_prompt | llm
    result = report_structure_planner_llm.invoke(state)
    return {"messages": [result]}


def human_feedback_node(state: AgentState, config: RunnableConfig)->Command[Literal["section_formatter", "report_structure_planner"]]:
    human_message = input("Please provide feedback on the report structure (type 'continue' to continue): ")
    report_structure = state.get("messages")[-1].content
    if human_message == "continue":
        return Command(
            goto="section_formatter",
            update={"messages": [HumanMessage(content=human_message)], "report_structure": report_structure}
        )
    else:
        return Command(
            goto="report_structure_planner",
            update={"messages": [HumanMessage(content=human_message)]}
        )



def section_formatter_node(state: AgentState, config: RunnableConfig) -> Command[Literal["research_agent"]]:
    section_formatter_system_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SECTION_FORMATTER_SYSTEM_PROMPT_TEMPLATE),
        HumanMessagePromptTemplate.from_template(template="{report_structure}"),
    ])

    section_formatter_llm = section_formatter_system_prompt | llm.with_structured_output(Sections)
    result = section_formatter_llm.invoke(state)
    return Command(
        update={"sections": result.sections},
        goto=[
            Send(
                "research_agent",
                {
                    "section": s,
                }
            ) for s in result.sections
        ]
    )


def section_knowledge_node(state: ResearchState, config: RunnableConfig):
    section_knowledge_system_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SECTION_KNOWLEDGE_SYSTEM_PROMPT_TEMPLATE),
        HumanMessagePromptTemplate.from_template(template="{section}"),
    ])

    section_knowledge_llm = section_knowledge_system_prompt | llm
    result = section_knowledge_llm.invoke(state)
    return {"knowledge": result.content}


def query_generator_node(state: ResearchState, config: RunnableConfig):
    query_generator_system_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(QUERY_GENERATOR_SYSTEM_PROMPT_TEMPLATE),
        HumanMessagePromptTemplate.from_template(template="Section: {section}\nPrevious Queries: {searched_queries}\nReflection Feedback: {reflection_feedback}"),
    ])

    query_generator_llm = query_generator_system_prompt | llm.with_structured_output(Queries)
    state.setdefault("reflection_feedback", "")
    state.setdefault("searched_queries", [])
    configurable = config.get("configurable")

    input_data = {
        **state,
        **configurable  # includes max_queries, search_depth, etc.
    }

    result = query_generator_llm.invoke(input_data, configurable)
    return {"generated_queries": result.queries, "searched_queries": result.queries}


def rag_search_node(state: ResearchState, config: RunnableConfig):
    queries = state["generated_queries"]
    configurable = config.get("configurable")
    search_results = []
    for query in queries:
        raw_content = []
        response = retrieve_from_store(query.query, configurable.get("thread_id"), configurable.get("n_points"))
        for result in response:
            content = f"filename:{result.payload['document']['filename']}\nPage_number:{result.payload['document']['page_number']}\nPage_Content: {result.payload['document']["page_content"]}\n\n\n"
            raw_content.append(content)
        search_results.append(SearchResult(query=query, raw_content=raw_content))
    return {"search_results": search_results}


def result_accumulator_node(state: ResearchState, config: RunnableConfig):
    # Preserve retrieved evidence verbatim. An earlier LLM summarization stage
    # could manufacture facts before the report writer ever saw the sources.
    evidence_blocks = []
    for search_result in state.get("search_results", []):
        query = getattr(getattr(search_result, "query", None), "query", "")
        raw_items = getattr(search_result, "raw_content", []) or []
        evidence_blocks.append(f"QUERY: {query}")
        evidence_blocks.extend(str(item) for item in raw_items)
    accumulated = "\n\n".join(evidence_blocks).strip()
    if not accumulated:
        accumulated = "NOT FOUND IN RETRIEVED SOURCES"
    return {"accumulated_content": accumulated}


def reflection_feedback_node(state: ResearchState, config: RunnableConfig) -> Command[Literal["final_section_formatter", "query_generator"]]:
    reflection_feedback_system_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(REFLECTION_FEEDBACK_SYSTEM_PROMPT_TEMPLATE),
        HumanMessagePromptTemplate.from_template(template="Section: {section}\nAccumulated Content: {accumulated_content}"),
    ])

    reflection_feedback_llm = reflection_feedback_system_prompt | llm.with_structured_output(Feedback)
    reflection_count = state.get("reflection_count", 0)
    configurable = config.get("configurable")
    result = reflection_feedback_llm.invoke(state)
    feedback = result.feedback
    feedback_complete = feedback is True or (
        isinstance(feedback, str) and feedback.strip().lower() == "true"
    )
    max_reflections = int(configurable.get("num_reflections", 0))
    # Finish when the model says the section is complete or when the retry
    # budget is exhausted. The previous comparison was reversed and could loop.
    if feedback_complete or reflection_count >= max_reflections:
        return Command(
            update={"reflection_feedback": feedback},
            goto="final_section_formatter"
        )
    else:
        return Command(
            update={"reflection_feedback": feedback, "reflection_count": reflection_count + 1},
            goto="query_generator"
        )
    

def final_section_formatter_node(state: ResearchState, config: RunnableConfig):
    # Evidence-first mode: keep the actual retrieved passages. GPT Researcher
    # handles narrative synthesis; DeepDoc's reliable job is local evidence.
    section = state.get("section")
    section_name = getattr(section, "section_name", "Evidence section")
    evidence = state.get("accumulated_content") or "NOT FOUND IN RETRIEVED SOURCES"
    return {"final_section_content": [f"## {section_name}\n\n{evidence}"]}


def final_report_writer_node(state: AgentState, config: RunnableConfig):
    sections = state.get("final_section_content") or []
    report = "# DeepDoc Source Evidence Packet\n\n"
    report += "> Evidence-first output. Passages below are preserved from retrieved local files; no model-written factual synthesis was added.\n\n"
    report += "\n\n".join(str(section) for section in sections)
    return {"final_report_content": report}
