import logging
from supabase import Client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
import asyncio
from langchain_core.documents import Document

from src.v1.utils.prompts import SUMMARIZE_CHAT_PROMPT_SYSTEM, SUMMARIZE_CHAT_PROMPT_USER
from src.v1.utils.text_chunking import update_metadata
from src.v1.services.model import get_response
from src.v1.services.memory_engine.retrieval_memory import get_supabase_client
from src.v1.config.config import EMBEDDING_MODEL, SUPABASE_SUMMARY_TABLE_NAME, SUPABASE_SUMMARY_QUERY_NAME
logger = logging.getLogger(__name__)


# Summarize the chat history and save the summary to the database
async def summarize_chat(chat_history: str, user_id: str, child_id: str):
    try:
        # chat_history = chat_history.strip()
        # if chat_history == "":
        #     logger.info(f"No chat history found for user {user_id}, skipping summary creation")
        #     return {
        #         "status": "success",
        #         "message": "No chat history found, skipping summary creation",
        #         "summary": None
        #     }
        
        # Get the summary from the chat history
        tokens, summary, model = await get_response(
            SUMMARIZE_CHAT_PROMPT_USER.format(chat_history=chat_history),
            system_prompt=SUMMARIZE_CHAT_PROMPT_SYSTEM
        )
        
        summary_doc = [Document(page_content=summary)]
        # Update the metadata of the summary document
        summary_doc = update_metadata(summary_doc,user_id, child_id)
        logger.info(f"Summarized chat: {summary}")
        # Initialize Supabase client
        supabase: Client = get_supabase_client()
        # Update the summary in the database
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        chat_summary_vector_store = await asyncio.to_thread(
                SupabaseVectorStore.from_documents,
                summary_doc,
                embeddings,
                client=supabase,
                table_name=SUPABASE_SUMMARY_TABLE_NAME,
                query_name=SUPABASE_SUMMARY_QUERY_NAME,
            )

        # Return the vector store creation status
        logger.info(f"1 day Chat Summary added in Vector store successfully for user {user_id}")
        return {
            "status": "success",
            "message": "Chat summary created successfully",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error adding 1 day Chat Summary in Vector store: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to add 1 day Chat Summary in Vector store: {str(e)}",
            "summary": None
        }

async def get_chat_summary(question: str, user_id: str, child_id: str):
    try:
        # Initialize Supabase client
        supabase: Client = get_supabase_client()
        # Initialize the vector store
        vector_store = SupabaseVectorStore(
            client=supabase,
            table_name=SUPABASE_SUMMARY_TABLE_NAME,
            query_name=SUPABASE_SUMMARY_QUERY_NAME,
            embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        )
        # Query the vector store for 2 summaries with the given user id
        results = await asyncio.to_thread(
            vector_store.similarity_search, question, k=2, filter={"child_id": child_id}
        )
        # Return the results
        results = " ".join([result.page_content for result in results])
        logger.debug(f"Query results for '{question}': {results[:100]}...")
        return results
    except Exception as e:
        logger.error(f"Error querying vector store: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to query vector store: {str(e)}",
        }