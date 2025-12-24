import os
from dotenv import load_dotenv

load_dotenv(".env.local")

GROQ_MODEL_NAME = f"groq:{os.environ.get('GROQ_CHAT_MODEL')}" 
GROQ_BASIC_MODEL_NAME = f"groq:{os.environ.get('GROQ_BASIC_CHAT_MODEL')}" 

