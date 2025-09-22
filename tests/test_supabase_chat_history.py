import asyncio
import logging
import os
import sys
import threading
import time
from datetime import datetime

import pytest

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from supabase import Client, create_client

from src.v1.utils.database.supabase_chat_history import (
    load_chat_history,
    process_chat_history,
)

# Configure logging
logger = logging.getLogger(__name__)

# Sample user ID - this should be an actual user ID that exists in your system
# Ideally this would be set as an environment variable
TEST_USER_ID = os.environ.get("TEST_USER_ID", "test_user")

# Set up Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)


@pytest.mark.asyncio
async def test_load_chat_history():
    """Test loading chat history for a user."""
    # Skip if Supabase credentials are not set
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        pytest.skip("Supabase credentials not set in environment")

    try:
        # Test loading history with the existing user ID
        history = await load_chat_history(TEST_USER_ID, 10)

        # Check that we get a list back
        assert isinstance(history, list)
        logger.info(
            f"Loaded {len(history)} chat history messages for user {TEST_USER_ID}"
        )

    except Exception as e:
        logger.error(f"Error loading chat history: {str(e)}")
        pytest.fail(f"Error loading chat history: {str(e)}")


@pytest.mark.asyncio
async def test_process_chat_history():
    """Test processing chat history for a user."""
    # Skip if Supabase credentials are not set
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        pytest.skip("Supabase credentials not set in environment")

    try:
        # Test processing history with the existing user ID
        processed = await process_chat_history(TEST_USER_ID, 10)

        # Check that we get a string back
        assert isinstance(processed, str)
        logger.info(f"Processed chat history for user {TEST_USER_ID}")

        if processed != "No chat history found":
            logger.info(f"Found existing chat history: {processed[:100]}...")
        else:
            logger.info("No existing chat history found")

    except Exception as e:
        logger.error(f"Error processing chat history: {str(e)}")
        pytest.fail(f"Error processing chat history: {str(e)}")


@pytest.mark.asyncio
async def test_concurrent_chat_history_loading():
    """Test that multiple chat history loads can run concurrently."""
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        pytest.skip("Supabase credentials not set in environment")

    start_time = time.time()

    # Create multiple concurrent tasks
    tasks = [
        load_chat_history(TEST_USER_ID, 10),
        load_chat_history(TEST_USER_ID, 10),
        load_chat_history(TEST_USER_ID, 10),
    ]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    # If truly async, total time should be less than sum of individual times
    logger.info(f"Concurrent execution time: {total_time:.2f} seconds")

    # Verify all results
    for result in results:
        assert isinstance(result, list)
        logger.info(f"Retrieved {len(result)} messages in concurrent request")


@pytest.mark.asyncio
async def test_single_request_timing():
    """Test timing of a single request."""
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        pytest.skip("Supabase credentials not set in environment")

    start_time = time.time()

    result = await load_chat_history(TEST_USER_ID, 10)

    end_time = time.time()
    single_request_time = end_time - start_time

    logger.info(f"Single request time: {single_request_time:.2f} seconds")
    assert isinstance(result, list)
    logger.info(f"Retrieved {len(result)} messages in single request")


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__])
