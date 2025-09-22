import asyncio
import logging
import os

from dotenv import load_dotenv
from supabase import Client, create_client

from src.v1.config.config import CHAT_HISTORY_K

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")
if not url or not key:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
    )

supabase: Client = create_client(url, key)


async def load_chat_history(user_id: str, history_k: int = CHAT_HISTORY_K):
    try:
        logger.debug(f"Loading chat history for user_id: {user_id}, limit: {history_k}")

        def _execute_query():
            query = (
                supabase.table("messages")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(history_k)
            )
            return query.execute()

        response = await asyncio.to_thread(_execute_query)
        # print('response in print statement', response)
        logger.debug(f"Retrieved {len(response.data) } messages from chat history")
        return response.data
    except Exception as e:
        logger.error(f"Error loading chat history: {str(e)}", exc_info=True)
        return []


async def process_chat_history(user_id: str, history_k: int = CHAT_HISTORY_K):
    """
    This function processes the chat history for a given user id.
    arguments:
        user_id: str
        history_k: int
    returns:
        results: str
    """
    try:
        processed_history = await load_chat_history(user_id, history_k)
        results = []
        for i in processed_history[::-1]:
            try:
                # Find the text content in the content array
                text_value = ""
                document_context = ""
                
                for content_item in i['content']:
                    if content_item.get('type') == 'text' and 'text' in content_item:
                        text_value = content_item['text']['value']
                        document_context = content_item['text'].get('documentContext', '')
                        break
                
                # Skip if no text content found
                if not text_value:
                    continue
                
                # Append document context if it exists
                if document_context:
                    text_value += f" [Context: {document_context}]"
                
                results.append(f"{i['role']}: {text_value}")
            except (KeyError, IndexError, TypeError):
                continue  # Skip malformed items
        results = "\n".join(results)
        logger.debug(
            f"Processed chat history for user_id: {user_id}, {len(processed_history)} messages"
        )
        if len(results) > 0:
            logger.debug(f"Chat history sample: {results[:100]}...")
        return results
    except Exception as e:
        logger.error(f"Error processing chat history: {str(e)}", exc_info=True)
        return "No chat history found"


if __name__ == "__main__":
    # Set up logging for standalone execution
    from src.v1.config.logging_config import setup_logging

    logger = setup_logging()

    logger.info("Testing chat history processing")
    result = asyncio.run(process_chat_history("e2ba33a0-4d2d-48ba-b0d8-95248440e7fb"))
    if result == "No chat history found":
        logger.warning("No chat history found for user_1")
    else:
        logger.info(
            f"Successfully retrieved chat history with {result.count(chr(10)) } messages"
        )
