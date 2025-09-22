import asyncio
import os
import sys
from datetime import datetime

import pytest

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v1.services.response_handler import handle_response
from src.v1.utils.modelclass import Conversation_Output

# Get test user ID from environment
TEST_USER_ID = os.environ.get("TEST_USER_ID", "test_user")


@pytest.mark.asyncio
async def test_handle_response_basic():
    """Test that handle_response processes a basic query correctly."""
    # Skip test if credentials aren't available
    openai_key = os.environ.get("OPENAI_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not openai_key or not supabase_url or not supabase_key:
        pytest.skip("API credentials not set in environment")

    # Use the environment-provided test user ID
    test_user_id = TEST_USER_ID

    # Test with a general question
    user_input = "What does my custody agreement say about holidays?"
    child_id = "test_child"
    # Get response
    response = await handle_response(user_input, test_user_id, child_id)

    # Validate the response
    assert isinstance(response, Conversation_Output)
    assert response.response is not None
    assert isinstance(response.response, str)
    # assert len(response.response) > 0
    # assert isinstance(response.total_tokens, int)
    # assert response.total_tokens > 0
    assert isinstance(response.label, str)

    print(f"User question: {user_input}")
    print(f"Response: {response.response[:150]}...")
    print(f"Label: {response.label}")
    # print(f"Total tokens: {response.total_tokens}")

    return response


@pytest.mark.asyncio
async def test_handle_response_greeting():
    """Test that handle_response correctly processes a greeting."""
    # Skip test if credentials aren't available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not set in environment")

    # Use the environment-provided test user ID
    test_user_id = TEST_USER_ID

    # Test with a greeting
    user_input = "Hello there"
    child_id = "test_child"
    # Get response
    response = await handle_response(user_input, test_user_id, child_id)

    # Validate the response
    assert isinstance(response, Conversation_Output)
    assert response.response is not None
    assert isinstance(response.response, str)
    assert len(response.response) > 0
    assert response.label is not None

    print(f"User greeting: {user_input}")
    print(f"Response: {response.response}")
    print(f"Label: {response.label}")

    return response
