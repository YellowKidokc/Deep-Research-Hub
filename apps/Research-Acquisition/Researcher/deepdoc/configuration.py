import uuid
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "RESEARCH_PROFILE.env"), override=True)

LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o-mini", 
    "temperature": 0.5,
}

THREAD_CONFIG = {
    "configurable": {
        "thread_id": str(uuid.uuid4()),
        "max_queries": int(os.getenv("DEEPDOC_MAX_QUERIES", "6")),
        "search_depth": int(os.getenv("DEEPDOC_SEARCH_DEPTH", "4")),
        "num_reflections": int(os.getenv("DEEPDOC_REFLECTIONS", "3")),
        "n_points": int(os.getenv("DEEPDOC_RETRIEVAL_POINTS", "8")),
    }
}
