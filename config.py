import os
from dotenv import load_dotenv

load_dotenv(".env.local")

GROQ_MODEL_NAME = f"groq:{os.environ.get('GROQ_CHAT_MODEL')}" 

