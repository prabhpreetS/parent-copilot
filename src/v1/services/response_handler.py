# Imports
import asyncio
import logging
import time
from functools import lru_cache

import tiktoken
from fastapi import FastAPI

from ..config.config import CHAT_HISTORY_K, OPENAI_MODEL
from ..services.guardrails import classify_message
from ..services.memory_engine.retrieval_memory import query_supabase_vector_store
from ..services.summarize_chat import get_chat_summary
from ..services.memory_engine.retrieval_memory import router as p3_contextual_router
from ..services.rephrase_dm import rephrase_dm
# from .utils.database.deprecated import append_to_file, read_file
from ..utils.database.supabase_chat_history import process_chat_history
from ..utils.guardrails_prompts import GUARDRAILS_HARDCODED_RESPONSES
from ..utils.modelclass import Conversation_Input, Conversation_Output
from ..utils.prompts import CONVERSATION_PROMPT, THERAPIST_SYSTEM_PROMPT

# Local Imports
from .model import get_response

# Configure logging
logger = logging.getLogger(__name__)

# FastAPI Instance
app = FastAPI()

app.include_router(p3_contextual_router)


# @lru_cache(maxsize=1)
# def get_encoding():
#     return tiktoken.encoding_for_model(OPENAI_MODEL)


# encoding = get_encoding()


# Handle Response
async def handle_response(user_input: str, user_id: str, child_id: str,user_name: str):
    """
    This function handles the response from the user and returns
    the response and the relevant contract statements.
    arguments: {
    user_input: str
    user_id: str
    }
    returns: {
    response: str
    relevant_contract_statements: str
    """
    # Guardrails
    start_time = time.time()
    label = await classify_message(user_input)
    label = str(label.get("label"))
    logger.info(f'user_input: {user_input}')
    logger.info(f"Label in response handler: {label}")
    if label == "general" or label == "direct_message":
        
        # Handle direct message
        if label == "direct_message":
            logger.info(f"handling direct message")
            rephrased_dm = await rephrase_dm(user_input)
            logger.info(f"Rephrased direct message: {rephrased_dm}")
            time_taken = round(time.time() - start_time, 2)
            logger.info(f"Time taken: {time_taken}")
            return Conversation_Output(
                response=str(rephrased_dm),
                relevant_contract_statements="",
                total_tokens=0,
                label=label,
                chat_history="",
                llm_model='none',
                chat_summary="",
                time_taken=time_taken
            )
        
        # Read the chat history (P1 context)
        logger.info(f"Handling general message for user {user_id}")
        print('x--------------------------------'*3)
        
        # Make all three database calls in parallel
        chat_history_start_time = time.time()
        cropped_history, chat_summary, contract_result = await asyncio.gather(
            process_chat_history(user_id, CHAT_HISTORY_K),
            get_chat_summary(user_input, user_id, child_id),
            query_supabase_vector_store(user_input, user_id)
        )
        
        # Log time taken for all database calls
        db_calls_time_taken = round(time.time() - chat_history_start_time, 2)
        logger.warning(f"All database calls time taken: {db_calls_time_taken}")
        
        logger.info(f"Cropped history: {cropped_history}")
        print('x--------------------------------'*3)
        
        logger.info(f"Chat summary in response handler: {chat_summary}")
        
        divorce_contract_statements = (
            str(contract_result)
            if contract_result
            else "No relevant contract information found."
        )
        logger.info(f"Contract statements: {divorce_contract_statements}")

        # Create the prompt that includes both history and question
        formatted_conversation_prompt = CONVERSATION_PROMPT.format(
            chat_history=cropped_history,
            user_question=user_input,
            divorce_contract_statements=divorce_contract_statements,
            chat_summary=chat_summary,
            user_name=user_name
        )
        logger.debug(f"Formatted prompt: {formatted_conversation_prompt}")

        # Pass the formatted prompt as the user message
        response_start_time = time.time()
        tokens, response, model = await get_response(
            formatted_conversation_prompt, THERAPIST_SYSTEM_PROMPT,model='openai'
        )
        response_time_taken = round(time.time() - response_start_time, 2)
        logger.warning(f"Response from model time taken: {response_time_taken}")
        response = response if response else "No response from the model"
        logger.info(f"Response: {response}")

        # # Append the new interaction to the chat history
        # append_to_file(CHAT_HISTORY_FILE_PATH, f"User: {user_input}\nAI: {response}\n")

        time_taken = round(time.time() - start_time, 2)
        logger.info(f"Time taken: {time_taken}")
        return Conversation_Output(
            response=response,
            relevant_contract_statements=divorce_contract_statements,
            total_tokens=int(tokens) if tokens is not None else 0, #total_tokens,
            label=label,
            chat_history=cropped_history,
            llm_model=model if model else 'none',
            chat_summary=str(chat_summary) if chat_summary else "",
            time_taken=time_taken
        )

    else:
        response = (
            GUARDRAILS_HARDCODED_RESPONSES[label]
            if label in GUARDRAILS_HARDCODED_RESPONSES
            else "I'm sorry, I can't respond to that."
        )
        time_taken = round(time.time() - start_time, 2)
        logger.info(f"Time taken: {time_taken}")
        return Conversation_Output(
            response=response,
            relevant_contract_statements="",
            total_tokens=0,
            label=label,
            chat_history="",
            llm_model='none',
            chat_summary="",
            time_taken=time_taken
        )


if __name__ == "__main__":
    # Set up logging for standalone execution
    from ..config.logging_config import setup_logging

    logger = setup_logging()

    # Test the endpoint with a sample input
    async def test():
        test_input = "what is the custody arrangement?"
        test_user_id = "user_1"
        test_child_id = "child_1"
        logger.info(
            f"Running test with input: '{test_input}' and user_id: '{test_user_id}'"
        )
        response = await handle_response(test_input, test_user_id, test_child_id)
        logger.info(f"Test response: {response}")

    asyncio.run(test())


# to run this file > python -m src.v1.response_handler or uvicorn src.v1.response_handler:app --reload
