import asyncio
import os
from fastapi import FastAPI, HTTPException

from src.v1.config.logging_config import setup_logging
from src.v1.services.memory_engine.retrieval_memory import (
    create_supabase_vector_store,
    convert_contract_to_json1,
    convert_contract_to_json,
    query_supabase_vector_store,
)
from src.v1.services.response_handler import handle_response
from src.v1.utils.modelclass import (
    Convert_to_json,
    ConvertToJsonResponse,
    Conversation_Input,
    Conversation_Output,
    ChatSummaryResponse,
    ChatSummary,
    Create_vector_store,
    CreateVectorStoreResponse,
    TipOfTheDayInput,
    TipOfTheDayResponse,
    ActivitiesInput,
    ActivitiesResponse,
    ReminderInput,
    ReminderResponse,
    GuardrailsTestInput,
    GuardrailsTestResponse
)
from src.v1.services.summarize_chat import summarize_chat
from src.v1.services.tip_of_day import tip_of_the_day
from src.v1.services.activities import activities
from src.v1.services.reminders import reminder,reminder1
from src.v1.services.guardrails import classify_message
from src.v1.version import __version__, API_TITLE, API_DESCRIPTION

# Configure logging
logger = setup_logging()

# start the logging process
logger.info("Starting Parent Co-Pilot API")

# FastAPI app instance with versioning
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# TODO: Apply tenacity to the API calls
# TODO: Setup cors and security token authentication after beta testing
# TODO: Update jenkins file to pull the latest code from the main branch and deploy to test environment


# LangSmith tracing
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")


# Health check API
@app.get("/api/health")
async def health_check():
    """
    Simple health check endpoint to verify API is running
    """
    logger.info("Health check endpoint called")
    return {"status": "healthy", "service": "parent-co-pilot", "version": __version__}


# API for handling conversation responses
@app.post("/api/conversation", response_model=Conversation_Output)
async def get_conversation_response(conversation: Conversation_Input):
    """
    Process a user message and return an AI response with relevant context
    """
    logger.info(f"Conversation request received from user_id: {conversation.user_id}")
    logger.debug(f"User input: {conversation.user_input}")
    try:
        response = await handle_response(conversation.user_input, conversation.user_id, conversation.parent_shared_id, conversation.user_name)
        logger.info(
            f"Successfully processed conversation for user_id: {conversation.user_id}"
        )
        logger.debug(f"Response: {response.response[:100]}...")
        return response
    except Exception as e:
        logger.error(f"Error processing conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing conversation: {str(e)}"
        )


# API for creating user specific vector store
@app.post("/api/convert-to-json", response_model=ConvertToJsonResponse)
async def convert_to_json_api(contract: Convert_to_json):
    """
    Convert contract text to json
    """
    logger.info(
        f"Convert contract text to json request received for user_id: {contract.user_id}"
    )
    logger.debug(f"Contract text length: {len(contract.text)} characters")
    try:
        result = await convert_contract_to_json(contract.text, contract.user_id)
        logger.info(
            f"Convert contract text to json result: {result['status']} for user_id: {contract.user_id}"
        )
        return result
    except Exception as e:
        logger.error(f"Error converting contract text to json: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error converting contract text to json: {str(e)}"
        )
    

# API for creating user specific vector store
@app.post("/api/vector-store", response_model=CreateVectorStoreResponse)
async def create_vector_store_api(contract: Create_vector_store):
    """
    Store document in vector database for RAG retrieval
    """
    logger.info(
        f"Vector store creation request received for user_id: {contract.user_id} and document_id: {contract.document_id}"
    )
    logger.debug(f"Contract JSON keys: {list(contract.json_response.keys())}")
    try:
        result = await create_supabase_vector_store(contract.json_response, contract.user_id, contract.document_id)
        return result
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error creating vector store: {str(e)}"
        )


# API for getting chat summary
@app.post("/api/chat-summary", response_model=ChatSummaryResponse)
async def summarize_chat_api(chat: ChatSummary):
    """
    Get chat summary from vector database
    """
    try:
        result = await summarize_chat(chat.chat, chat.user_id, chat.parent_shared_id)
        return result
    except Exception as e:
        logger.error(f"Error getting chat summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting chat summary: {str(e)}")


# API for getting tip of the day
@app.post("/api/tip-of-the-day", response_model=TipOfTheDayResponse)
async def get_tip_of_the_day_api(request: TipOfTheDayInput):
    """
    Get personalized tip of the day based on user's chat history
    """
    logger.info(f"Tip of the day request received for user_id: {request.user_id}")
    try:
        tip = await tip_of_the_day(request.user_id)
        logger.info(f"Successfully generated tip of the day for user_id: {request.user_id}")
        return {
            "status": "success",
            "message": "Tip of the day generated successfully",
            "tip": tip
        }
    except Exception as e:
        logger.error(f"Error generating tip of the day: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating tip of the day: {str(e)}"
        )


# API for getting personalized activities
@app.post("/api/activities", response_model=ActivitiesResponse)
async def get_activities_api(request: ActivitiesInput):
    """
    Get personalized activities based on user's chat history
    """
    logger.info(f"Activities request received for user_id: {request.user_id}")
    try:
        activities_list = await activities(request.user_id)
        logger.info(f"Successfully generated {len(activities_list)} activities for user_id: {request.user_id}")
        return activities_list
    except Exception as e:
        logger.error(f"Error generating activities: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating activities: {str(e)}"
        )


# API for getting reminders from text
@app.post("/api/reminders", response_model=ReminderResponse)
async def get_reminders_api(request: ReminderInput):
    """
    Extract reminders and events from text and store them in the database
    """
    logger.info(f"Reminders request received for user_id: {request.user_id}")
    try:
        result = await reminder1(request.text, request.user_id, request.document_id)
        logger.info(f"Successfully processed reminders for user_id: {request.user_id}")
        
        if isinstance(result, dict) and "error" in result:
            return ReminderResponse(
                status="error",
                message=result["error"],
                events=[],
                metadata={"error": True},
                error=result["error"]
            )
            
        return ReminderResponse(
            status="success",
            message="Reminders extracted and stored successfully",
            events=result if isinstance(result, list) else [],
            metadata={"processed": True}
        )
    except Exception as e:
        logger.error(f"Error processing reminders: {str(e)}", exc_info=True)
        return ReminderResponse(
            status="error",
            message=f"Error processing reminders: {str(e)}",
            events=[],
            metadata={"error": True},
            error=str(e)
        )


# API for testing guardrails
@app.post("/api/test-guardrails", response_model=GuardrailsTestResponse)
async def test_guardrails_api(request: GuardrailsTestInput):
    """
    Test the guardrails classification for a given message
    """
    logger.info(f"Guardrails test request received for message: {request.message[:30]}...")
    try:
        classification = await classify_message(request.message)
        logger.info(f"Guardrails classification result: {classification}")
        
        return GuardrailsTestResponse(
            status="success",
            message="Guardrails classification completed successfully",
            classification=classification,
            input_message=request.message
        )
    except Exception as e:
        logger.error(f"Error testing guardrails: {str(e)}", exc_info=True)
        return GuardrailsTestResponse(
            status="error",
            message=f"Error testing guardrails: {str(e)}",
            classification={"label": "error", "message": str(e)},
            input_message=request.message
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server")
    uvicorn.run("src.v1.main:app", host="0.0.0.0", port=8000, reload=True)
