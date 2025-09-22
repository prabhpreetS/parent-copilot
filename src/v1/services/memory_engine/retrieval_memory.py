# Imports
import asyncio
import logging
import os
from functools import lru_cache
import json
import time

import openai
from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from asyncio import Semaphore
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase.client import Client, create_client

# Local Imports
from src.v1.utils.text_chunking import (
    chunk_text,
    split_json_into_kv_chunks,
    update_metadata, 
    get_json_splitter)

from src.v1.config.config import (
    EMBEDDING_MODEL,
    SUPABASE_QUERY_NAME,
    SUPABASE_TABLE_NAME,
    CONTRACT_VECTORSTORE_LIMIT,
)
from src.v1.services.model import get_response
from src.v1.utils.prompts import DOCUMENT_TO_JSON_SYSTEM_PROMPT, DOCUMENT_TO_JSON_USER_PROMPT

_ = load_dotenv(find_dotenv())

# Configure logging
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI()
router = APIRouter()

# Initialize OpenAI and Supabase
openai.api_key = os.environ["OPENAI_API_KEY"]
supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_KEY"]


@lru_cache(maxsize=1)
def get_supabase_client():
    return create_client(supabase_url, supabase_key)
##########
CONCURRENCY_LIMIT = 2

semaphore = Semaphore(CONCURRENCY_LIMIT)

async def process_chunk(chunk: str, system_prompt: str):
    async with semaphore:
        prompt = DOCUMENT_TO_JSON_USER_PROMPT.format(text=chunk)
        try:
            tokens, json_response, model = await get_response(
                prompt, system_prompt, response_format='json_object',
                model='openai', temperature=0.7
            )
            parsed = json.loads(json_response)
            return parsed
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            return None

async def convert_contract_to_json1(contract_text: str, user_id: str):
    try:
        chunks = [contract_text[i:i+4000] for i in range(0, len(contract_text), 4000)]
        print(f"Split into {len(chunks)} chunks")

        start_time = time.time()
        tasks = [process_chunk(chunk, DOCUMENT_TO_JSON_SYSTEM_PROMPT) for chunk in chunks]
        results: List[dict] = await asyncio.gather(*tasks)

        # Filter out failed responses
        results = [r for r in results if r is not None]

        # Merge logic (depends on your specific JSON format)
        final_result = {}
        for partial in results:
            for key, value in partial.items():
                if key not in final_result:
                    final_result[key] = value
                else:
                    if isinstance(value, list) and isinstance(final_result[key], list):
                        final_result[key].extend(value)
                    elif isinstance(value, dict) and isinstance(final_result[key], dict):
                        final_result[key].update(value)
                    else:
                        # You can customize how to merge conflicting types here
                        pass

        end_time = time.time()
        print('Total time taken for all chunks (parallel):', end_time - start_time)

        return {
            "status": "success",
            "message": "Contract text converted to json successfully (chunked)",
            "json_response": final_result
        }

    except Exception as e:
        logger.error(f"Error converting contract to json (chunked): {str(e)}")
        return {"status": "error", "message": f"Failed to convert contract to json: {str(e)}"}

##########
async def convert_contract_to_json(contract_text: str, user_id: str):
    """
    This function converts a contract text to a json object.
    arguments:
        contract_text: str
        user_id: str
    returns:
        json_response: str
    """
    try:
        # Convert the contract text to json
        prompt = DOCUMENT_TO_JSON_USER_PROMPT.format(text=contract_text)
        start_time = time.time()
        tokens, json_response, model = await get_response(
            prompt, DOCUMENT_TO_JSON_SYSTEM_PROMPT,response_format='json_object', model='openai',temperature=0.7
        )
        end_time = time.time()
        print('time taken to convert contract to json (api call):::::::>>>>>>', end_time - start_time)        
        print('x---------------'*4)
        print('json response from api call:::::::>>>>>>', type(json_response),json_response[:100],'...')
        print('x---------------'*4)
        parsed_json_response = json.loads(json_response)
        # print("parsed_json_response:::::::>>>>>>>",type(parsed_json_response),str(parsed_json_response[:100]))
        print('x---------------'*4)
        end_time = time.time()
        print('time taken to convert contract to json (total):::::::>>>>>>', end_time - start_time)        
        return {
            "status": "success",
            "message": "Contract text converted to json successfully",
            "json_response": parsed_json_response
        }
    except Exception as e:
        logger.error(f"Error converting contract to json: {str(e)}")
        return {"status": "error", "message": f"Failed to convert contract to json: {str(e)}"}

# Create a supabase vector store
async def create_supabase_vector_store(json_response: dict, user_id: str, document_id: str):
    """
    This function creates a supabase vector store from a contract text.
    arguments:
        json_response: dict
        user_id: str
        document_id: str
    returns:
        status: str
        message: str
    """
    logger.info(f"Creating supabase vector store for user {user_id} and document {document_id}")
    logger.debug(f"Type of json_input: {type(json_response)}")
    print('printing json_response:::>>>>>>>',json_response)
    try:
        # Split the json into kv chunks
        json_chunks = split_json_into_kv_chunks(json_response)
        list_of_chunks = [item for item in json_chunks]
        splitter = get_json_splitter()
        docs = splitter.create_documents(list_of_chunks)
        
        # Update the metadata
        docs = update_metadata(docs, user_id, document_id)
        # Embed the documents
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        # Initialize Supabase client
        supabase: Client = get_supabase_client()
        # Create the vector store
        vector_store = await asyncio.to_thread(
            SupabaseVectorStore.from_documents,
            docs,
            embeddings,
            client=supabase,
            table_name=SUPABASE_TABLE_NAME,
            query_name=SUPABASE_QUERY_NAME,
        )

        # Return the vector store creation status
        logger.info(f"Vector store created successfully for user {user_id} and document {document_id}")
        return {
            "status": "success",
            "message": "Contract vector store created successfully",
            "json_response": json_response
        }
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to create vector store: {str(e)}",
            "json_response": None
        }
   

# Query the supabase vector store for a given question and user id
async def query_supabase_vector_store(question: str, user_id: str):
    """
    This function queries the supabase vector store for a given question and user id.
    arguments:
        question: str
        user_id: str
    returns:
        results: str
    """
    try:
        # Initialize Supabase client
        supabase: Client = get_supabase_client()
        # Initialize the vector store
        vector_store = SupabaseVectorStore(
            client=supabase,
            table_name=SUPABASE_TABLE_NAME,
            query_name=SUPABASE_QUERY_NAME,
            embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        )
        # Query the vector store for 2 documents with the given user id
        results = await asyncio.to_thread(
            vector_store.similarity_search, question, k=CONTRACT_VECTORSTORE_LIMIT, filter={"user_id": user_id}
        )
        # Return the results
        results = " ".join([result.page_content for result in results])
        logger.debug(f"Query results for '{question}': {results[:100]}...")
        return results
    # Handle exceptions
    except Exception as e:
        logger.error(f"Error querying vector store: {str(e)}")
        return {"status": "error", "message": f"Failed to query vector store: {str(e)}"}


if __name__ == "__main__":
    # Set up logging for standalone execution
    from src.v1.config.logging_config import setup_logging

    logger = setup_logging()

    # with open(CONTRACT_FILE_PATH, "r") as file:
    #     text = file.read()
    # result = create_supabase_vector_store(text, "beepboop")

    logger.info("Running test query on vector store")
    result = asyncio.run(
        query_supabase_vector_store("What does mango contain?", "beepboop")
    )
    logger.info(f"Query result: {result}")
    # use > python -m src.v1.memory_engine.p3_contextual to run this file
