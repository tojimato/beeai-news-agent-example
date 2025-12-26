import os
from dotenv import load_dotenv

load_dotenv(".env.local")

GROQ_STRATEGY_MODEL = "groq:openai/gpt-oss-120b" 
GROQ_TRANSLATOR_MODEL = "groq:openai/gpt-oss-20b" 
GROQ_COMPOUND_MODEL = "groq:groq/compound"
GROQ_LLAMA_8B_MODEL = "groq:llama-3.1-8b-instant"

OPENAI_STRATEGY_MODEL = "openai:gpt-5"  
OPENAI_TRANSLATOR_MODEL = "openai:gpt-5-mini"
OPENAI_CHEAPEST_MODEL = "openai:gpt-5-nano"
