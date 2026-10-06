; ----------------------------------------------------
; OpenRouter API Key
; ----------------------------------------------------

APIKey := "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"

; ----------------------------------------------------
; Prompts
; ----------------------------------------------------

prompts := [{
    promptName: "Multi-model custom prompt",
    menuText: "&1 - Gemini, GPT-4o, Claude",
    systemPrompt: "You are a helpful assistant. Follow the instructions that I will provide or answer any questions that I will ask. My first query is the following:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free,
    openai/gpt-4o,
    anthropic/claude-3.7-sonnet
    )",
    isCustomPrompt: true,
    customPromptInitialMessage: "How can I leverage the power of AI in my everyday tasks?",
    tags: ["&Custom prompts", "&Multi-models"]
}, {
    promptName: "Rephrase",
    menuText: "&1 - Rephrase",
    systemPrompt: "Your task is to rephrase the following text or paragraph in English to ensure clarity, conciseness, and a natural flow. If there are abbreviations present, expand it when it's used for the first time, like so: OCR (Optical Character Recognition). The revision should preserve the tone, style, and formatting of the original text. If possible, split it into paragraphs to improve readability. Additionally, correct any grammar and spelling errors you come across. You should also answer follow-up questions if asked. Respond with the rephrased text only:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )",
    tags: ["&Text manipulation"]
}, {
    promptName: "Summarize",
    menuText: "&2 - Summarize",
    systemPrompt: "Your task is to summarize the following article in English to ensure clarity, conciseness, and a natural flow. If there are abbreviations present, expand it when it's used for the first time, like so: OCR (Optical Character Recognition). The summary should preserve the tone, style, and formatting of the original text, and should be in its original language. If possible, split it into paragraphs to improve readability. Additionally, correct any grammar and spelling errors you come across. You should also answer follow-up questions if asked. Respond with the rephrased text only:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )",
    tags: ["&Text manipulation", "&Articles"]
}, {
    promptName: "Translate to English",
    menuText: "&3 - Translate to English",
    systemPrompt: "Generate an English translation for the following text or paragraph, ensuring the translation accurately conveys the intended meaning or idea without excessive deviation. If there are abbreviations present, expand it when it's used for the first time, like so: OCR (Optical Character Recognition). The translation should preserve the tone, style, and formatting of the original text. If possible, split it into paragraphs to improve readability. Additionally, correct any grammar and spelling errors you come across. You should also answer follow-up questions if asked. Respond with the rephrased text only:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )",
    tags: ["&Text manipulation", "Language"]
}, {
    promptName: "Define",
    menuText: "&4 - Define",
    systemPrompt: "Provide and explain the definition of the following, providing analogies if needed. In addition, answer follow-up questions if asked:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )",
    tags: ["&Text manipulation", "Learning"]
}, {
    promptName: "Lossless Meaning Packet",
    menuText: "&8 - Lossless Meaning Packet",
    systemPrompt: "
    (
    You are a semantic compression engine for multi-AI handoff.

    Convert the user's selected text into a compact LOSSLESS-MEANING PACKET.

    This is not a normal summary. Preserve the meaning map so another capable AI can reconstruct the original working context without cold-start flattening.

    Required output shape:

    # LMP v0.2

    ## Decode
    State that this is a compressed meaning map. Instruct the next AI to preserve ontology, claims, dependency order, terms, IDs, equations, relationship dynamic, and unresolved tensions. No rewrite unless asked.

    ## Seal
    Include title or inferred topic, source type if inferable, estimated compression intent, and any obvious date/version/status signals. Do not invent facts.

    ## Spine
    Give the structural outline in the order the source wants to be read.

    ## Terms
    List the load-bearing terms, symbols, names, file names, model names, axiom IDs, equations, tags, and domain labels.

    ## Claims
    List the claims that must survive transfer. Use compact bullets. Keep exact wording when a sentence is load-bearing.

    ## Edges
    Capture dependency relationships: requires, blocks, derives, anchors, verifies, contradicts, resolves, opens, or hands off to.

    ## Relationship Dynamic
    Capture the living collaboration layer: what David/user is trying to do, what pressure or uncertainty is active, how the AI should behave, what tone/posture matters, what should not be flattened into machinery, and what the next AI is responsible to preserve.

    ## Open Questions / Risks
    Name what is unresolved, brittle, uncertain, or needs a follow-up pass.

    ## Next Action
    Give the next practical action in one to five bullets.

    Rules:
    - Compress hard, but do not erase intent.
    - Prefer dense, readable bullets over prose.
    - Preserve exact IDs, equations, paths, names, and commands.
    - Keep theological, physics, math, HTML/API, and relationship layers distinct.
    - Mark overclaims instead of deleting them.
    - Do not add generic encouragement.
    - Return the packet only.
    )",
    APIModels: "
    (
    openai/gpt-4o
    )",
    tags: ["&Text manipulation", "&Custom prompts", "Theophysics"]
}, {
    promptName: "Auto-paste custom prompt",
    menuText: "&5 - Auto-paste custom prompt",
    systemPrompt: "You are a helpful assistant. Follow the instructions that I will provide or answer any questions that I will ask.",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )",
    isCustomPrompt: true,
    isAutoPaste: true,
    tags: ["&Custom prompts", "&Auto paste"]
}, {
    promptName: "Web search",
    menuText: "&6 - Web search",
    systemPrompt: "Provide the latest information and answer follow-up questions that I will ask. My first query is the following:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free:online
    )",
    tags: ["&Web search", "Learning"]
}, {
    promptName: "Web search custom prompt",
    menuText: "&7 - Web search custom prompt",
    systemPrompt: "Provide the latest information and answer follow-up questions that I will ask. My first query is the following:",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free:online
    )",
    isCustomPrompt: true,
    tags: ["&Web search", "&Custom prompts"]
}, {
    promptName: "Deep thinking multi-model custom prompt",
    menuText: "&1 - Deep thinking multi-model custom prompt",
    systemPrompt: "You are a helpful assistant. Follow the instructions that I will provide or answer any questions that I will ask. My first query is the following:",
    APIModels: "
    (
    perplexity/r1-1776,
    openai/o3-mini-high,
    anthropic/claude-3.7-sonnet:thinking,
    google/gemini-2.0-flash-thinking-exp:free
    )",
    isCustomPrompt: true,
    customPromptInitialMessage: "This is a message template."
}, {
    promptName: "Deep thinking multi-model web search custom prompt",
    menuText: "&2 - Deep thinking multi-model custom prompt web search",
    systemPrompt: "Provide information about the following. In addition, answer follow-up questions that I will ask or follow any instructions that I may provide:",
    APIModels: "
    (
    perplexity/r1-1776:online,
    openai/o3-mini-high:online,
    anthropic/claude-3.7-sonnet:thinking:online,
    google/gemini-2.0-flash-thinking-exp:free:online
    )",
    isCustomPrompt: true
}, {
    promptName: "Multi-line prompt example",
    menuText: "Multi-line prompt example",
    systemPrompt: "
    (
    This prompt is broken down into multiple lines.

    Here is the second sentence.

    And the third one.

    As long as the prompt is inside the quotes and the opening and closing parenthesis,

    it will be valid.
    )",
    APIModels: "
    (
    google/gemini-2.0-flash-thinking-exp:free
    )"
}]
