from src.v1.services.tip_of_day import load_summary
from src.v1.services.model import get_response
from src.v1.utils.prompts import ACTIVITIES_SYSTEM_PROMPT, ACTIVITIES_USER_PROMPT
from src.v1.services.memory_engine.retrieval_memory import get_supabase_client

import logging
import traceback

logger = logging.getLogger(__name__)

async def activities(user_id):
    try:
        logger.info(f"Loading chat summary for user_id: {user_id}")
        chat_summary = await load_summary(user_id, history_k=1)

        logger.info("Formatting activity user prompt")
        activity_user_prompt = ACTIVITIES_USER_PROMPT.format(summary=chat_summary)

        logger.info("Calling get_response to generate activities")
        model, activities, token = await get_response(
            activity_user_prompt,
            ACTIVITIES_SYSTEM_PROMPT,
            model="anthropic"
        )

        logger.info("Parsing activities into list")
        activities_list = [activity.strip() for activity in activities.split(',')]
        activities_json = {
            "activities": activities_list
        }
        supabase = get_supabase_client()

        insert_data = {
             "user_id": user_id,
            "content": activities_json,
            
        }

        response = supabase.table("activities").insert([insert_data]).execute()
        logger.info(f"Inserted tip into Supabase for user_id: {user_id}. Response: {response.data}")
        

        logger.info("Activity extraction successful")
        return {
            "status": "successful",
            "message": "activities extraction successful",
            "activities": activities_list
        }

    except Exception as e:
        logger.error(f"Error in activities function: {str(e)}")
        logger.debug(traceback.format_exc())
        return {
            "status": "failed",
            "message": f"Error extracting activities: {str(e)}",
            "activities": []
        }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        user_id = 'e2ba33a0-4d2d-48ba-b0d8-95248440e7fb'
        response = await activities(user_id)
        print("Activities response (as list):")
        for i, activity in enumerate(response, 1):
            print(f"{i}. {activity}")
        print(f"\nTotal activities: {len(response)}")
    
    asyncio.run(main())