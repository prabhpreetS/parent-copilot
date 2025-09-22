# Imports
import asyncio
import logging
import os
from functools import lru_cache

import openai
from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase.client import Client, create_client

# Local Imports
from src.v1.utils.text_chunking import chunk_text, update_metadata
from src.v1.config.config import (
    EMBEDDING_MODEL,
    SUPABASE_QUERY_NAME,
    SUPABASE_TABLE_NAME,
)

_ = load_dotenv(find_dotenv())

# Configure logging
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI()

class RetrievalMemory:
    def __init__(self):
        self.supabase_url = os.environ["SUPABASE_URL"]
        self.supabase_key = os.environ["SUPABASE_KEY"]
        self.openai_api_key = os.environ["OPENAI_API_KEY"]

        self.supabase_client = create_client(
            self.supabase_url, self.supabase_key
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
   
        )
        
        
        