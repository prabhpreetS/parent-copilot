# The file is used to get the response from the openai model
import asyncio
import json
import logging
import os
from functools import lru_cache

from openai import AsyncOpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable

from ..config.config import OPENAI_MODEL, OPENAI_TEMPERATURE
from dotenv import load_dotenv
load_dotenv()
# print('--------------------------------'*3)
# print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
# print('--------------------------------'*3)
# Configure logging
logger = logging.getLogger(__name__)



@lru_cache(maxsize=1)
def get_openai_client(api_key: str, base_url: str):
    return wrap_openai(AsyncOpenAI(api_key= api_key,base_url = base_url))


@traceable
async def get_response(prompt, system_prompt, response_format=None, model="openai",temperature=OPENAI_TEMPERATURE):

    try:
        # Format the API call correctly
        if model == "openai":
            client = get_openai_client(
                api_key=os.getenv("OPENAI_API_KEY"),  # Your Anthropic API key
                base_url="https://api.openai.com/v1/"  # Anthropic's API endpoint
            )
            completion_args = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }

        if model == "anthropic":
            client = get_openai_client(
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # Your Anthropic API key
                base_url="https://api.anthropic.com/v1/"  # Anthropic's API endpoint
            )
            completion_args = {
                "model": "claude-3-7-sonnet-20250219",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": OPENAI_TEMPERATURE,
            }
        # Only add response_format if it's specified and not None
        if response_format and response_format != "none":
            # Properly format as expected by the API
            completion_args["response_format"] = {"type": response_format}

        response = await client.chat.completions.create(**completion_args)
        if response is None:
            logger.warning("Received None response from OpenAI API")
            return "No response from the model"

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        logger.debug(
            f"Received response from OpenAI: {len(content) if content else 0} characters"
        )
        return tokens, content, model
    
    except Exception as e:
        logger.error(f"Error getting response from {model}: {str(e)}", exc_info=True)
        return None,f"Error: {str(e)}", None


# # Response Api
# def openai_response_api(prompt, system_prompt):
#     client = get_openai_client()
#     response = client.responses.create(
#         model=OPENAI_MODEL, instructions=system_prompt, input=prompt
#     )
#     return response


# Test function for JSON response format
async def test_json_response():
    """Test function to verify JSON response format works correctly"""
    prompt = "Generate a response with information about divorce laws in California regarding child custody"
    system_prompt = "You are a legal assistant. Provide information about divorce laws in JSON format with these fields: state, custodyType, description."

    # First test without JSON formatting
    logger.info("Testing standard text response...")
    tokens, text_response, client = await get_response(prompt, system_prompt)
    logger.info(f"Text response: {text_response[:100]}...")

    # Then test with JSON formatting
    logger.info("Testing JSON response format...")
    tokens, json_response, client = await get_response(
        prompt, system_prompt, response_format="json_object"
    )
    logger.info(f"JSON response: {json_response[:100]}...")

    # Verify JSON parsing works
    try:
        parsed_json = json.loads(json_response)
        logger.info(f"Successfully parsed JSON: {list(parsed_json.keys())}")
        return {
            "text_response": text_response[:100] + "...",
            "json_response": parsed_json,
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return {
            "text_response": text_response[:100] + "...",
            "json_response": "Error: Invalid JSON format",
        }


# If the file is run directly, it will run the following code
if __name__ == "__main__":
    # Set up logging for standalone execution
    from ..config.logging_config import setup_logging

    logger = setup_logging()

    # Run standard test
    prompt = "hi"
    logger.info(f"Running basic test with prompt: '{prompt}'")
    tokens, response, model = asyncio.run(get_response(prompt, system_prompt="say opposite words"))
    logger.info(f"Basic test response: {response}")

    # Run JSON format test
    logger.info("Running JSON format test")
    test_result = asyncio.run(test_json_response())
    logger.info(f"JSON test results: {test_result}")
