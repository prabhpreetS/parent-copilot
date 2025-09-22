import asyncio
import logging
import os

from dotenv import load_dotenv
from supabase import Client, create_client
from src.v1.config.config import SUPABASE_SUMMARY_TABLE_NAME
from src.v1.services.model import get_response
from src.v1.config.config import CHAT_HISTORY_K
from src.v1.utils.prompts import (
    TIP_OF_THE_DAY_SYSTEM_PROMPT,
    TIP_OF_THE_DAY_USER_PROMPT
                                )

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


async def load_summary(user_id: str, history_k: int = CHAT_HISTORY_K):
    try:
        logger.debug(f"Loading chat history for user_id: {user_id}, limit: {history_k}")

        def _execute_query():
            query = (
                supabase.table(SUPABASE_SUMMARY_TABLE_NAME)
                .select("content")
                .filter("metadata->>user_id", "eq", user_id)  # filter by JSONB key
                .order("created_at", desc=False)
                .limit(history_k)
            )
            return query.execute()

        response = await asyncio.to_thread(_execute_query)
        print('response in print statement', type(response))
        logger.debug(f"Retrieved {len(response.data) } messages from chat history")
        processed_response = '\n'.join([summary['content'] for summary in response.data])
        return processed_response
    except Exception as e:
        logger.error(f"Error loading chat history: {str(e)}", exc_info=True)
        return []
    

async def tip_of_the_day(user_id):
    try:
        logger.info(f"Generating tip of the day for user_id: {user_id}")
        processed_response = await load_summary(user_id)
        
        if not processed_response:
            logger.warning(f"No chat history found for user_id: {user_id}")
            # return "No chat history available to generate a personalized tip."
            processed_response = "No chat history available. Please generate a random tip related to legal and emotional wellness after divorce"
            
        totd_user_prompt = TIP_OF_THE_DAY_USER_PROMPT.format(summaries=processed_response)
        logger.debug(f"Generated prompt for tip of the day")
        
        token, totd, model = await get_response(
            totd_user_prompt, 
            TIP_OF_THE_DAY_SYSTEM_PROMPT,
            model='anthropic',
            temperature=0.9
        )
        insert_data = {
             "user_id": user_id,
            "content": totd,
            
        }

        response = supabase.table("tips").insert([insert_data]).execute()
        logger.info(f"Inserted tip into Supabase for user_id: {user_id}. Response: {response.data}")


        logger.info(f"Successfully generated tip of the day for user_id: {user_id}")
        return totd
        
    except Exception as e:
        logger.error(f"Error generating tip of the day for user_id {user_id}: {str(e)}", exc_info=True)
        return "Sorry, I encountered an error while generating your tip of the day. Please try again later."


    
if __name__ == "__main__":
    import sys

    # logging.basicConfig(level=logging.DEBUG)

    async def main():
        user_id = 'e2ba33a0-4d2d-48ba-b0d8-95248440e7fb'
        history = await load_summary(user_id)
        print('history:::::>>>>',len(history))
        # print(history)
        # processed_response = '\n'.join([summary['content'] for summary in history])
        print('processed_response:::::::::::::>>>>>>>>>>>>>>>', history)
        # print(f"Loaded chat history for user_id={user_id}:\n{history}")
        tip =await tip_of_the_day(history)
        print('tip---------*x'*4)
        print(tip)

    asyncio.run(main())