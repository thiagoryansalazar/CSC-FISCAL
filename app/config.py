import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///storage/database.sqlite')
LLM_ENABLED = os.getenv('LLM_ENABLED', 'true').lower() == 'true'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
STORAGE_INPUT = os.getenv('STORAGE_INPUT_PATH', 'storage/input')
STORAGE_XML = os.getenv('STORAGE_XML_PATH', 'storage/xml')
STORAGE_CHROMA = os.getenv('STORAGE_CHROMA_PATH', 'storage/chroma_db')
