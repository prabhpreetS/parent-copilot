import asyncio
import json
import logging

from src.v1.utils.guardrails_prompts import (
    GUARDRAILS_HARDCODED_RESPONSES,
    GUARDRAILS_PROMPT,
    GUARDRAILS_USER_PROMPT,
)

from .model import get_response

# Configure logging
logger = logging.getLogger(__name__)


async def classify_message(user_message: str) -> dict:
    """
    Classifies user message intent using the guardrails prompt.
    Returns a dictionary with the classification label.

    Args:
        user_message: The user's input message to classify

    Returns:
        dict: A dictionary with the classification label (e.g., {"label": "greeting"})
    """
    try:
        # Import here to avoid circular imports

        # Format the prompt with the user message
        formatted_prompt = GUARDRAILS_USER_PROMPT.format(user_message=user_message)

        # Get the classification from the model as a JSON string
        tokens, json_response, model = await get_response(
            prompt=formatted_prompt,
            system_prompt=GUARDRAILS_PROMPT,
            response_format="json_object",
            temperature=0.9,
            model='openai'
        )

        # Parse the JSON response
        try:
            result = json.loads(json_response)
            logger.info(f"Message classified as: {result.get('label', 'unknown')}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {json_response}")
            return {"label": "error", "message": "Failed to parse classification"}

    except Exception as e:
        logger.error(f"Error in openai json type response: {str(e)}", exc_info=True)
        return {"label": "error", "message": str(e)}


async def is_safe_message(user_message: str) -> bool:
    """
    Determines if a message is safe to process based on its classification.

    Args:
        user_message: The user's input message to check

    Returns:
        bool: True if the message is safe, False otherwise
    """
    classification = await classify_message(user_message)

    # Messages are unsafe if they're classified as NSFW
    if classification.get("label") == "nsfw":
        logger.warning(f"Unsafe message detected: {user_message[:20]}...")
        return False

    # Messages are also considered unsafe if there was an error in classification
    if classification.get("label") == "error":
        logger.warning(f"Could not classify message safety: {user_message[:20]}...")
        return False

    return True


# Test function for the guardrails
async def test_guardrails():
    """Test function to verify guardrails classification"""
    test_messages = [
        "Hello, how are you today?",
        "Thanks for your help, goodbye!",
        "akjsdlkaj2903j2lkjsd",
        "I'm feeling really sad about my divorce.",
        "Let me tell you about my sexual fantasies",
    ]

    results = {}
    for message in test_messages:
        classification = await classify_message(message)
        results[message] = classification

    return results


# If the file is run directly, it will run the test
if __name__ == "__main__":
    # Set up logging for standalone execution
    from ..config.logging_config import setup_logging

    logger = setup_logging()

    logger.info("Testing guardrails classification")
    # test_results = asyncio.run(test_guardrails())
    label = asyncio.run(classify_message("Can you review this text:\n\nWhy are you not allowing me to see our son. You are alienating Mrs"))
    print(label)
    # for message, result in test_results.items():
    #     logger.info(f"Message: {message[:30]}... | Classification: {result}")
