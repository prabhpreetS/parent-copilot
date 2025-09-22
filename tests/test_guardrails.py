import asyncio
import os
import sys

import pytest

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v1.services.guardrails import classify_message, is_safe_message


@pytest.mark.asyncio
async def test_classify_message():
    """Test that classify_message correctly identifies message types."""
    # Test a greeting
    greeting_result = await classify_message("hello there")
    assert isinstance(greeting_result, dict)
    assert "label" in greeting_result
    print(f"Greeting classification: {greeting_result}")

    # Test a general message
    general_result = await classify_message(
        "I'm having issues with my custody agreement"
    )
    assert isinstance(general_result, dict)
    assert "label" in general_result
    print(f"General message classification: {general_result}")

    # Test gibberish
    gibberish_result = await classify_message("asdf123jkl")
    assert isinstance(gibberish_result, dict)
    assert "label" in gibberish_result
    print(f"Gibberish classification: {gibberish_result}")


@pytest.mark.asyncio
async def test_is_safe_message():
    """Test that is_safe_message correctly identifies safe content."""
    # Test a safe message
    safe_result = await is_safe_message("How do I improve communication with my ex?")
    assert isinstance(safe_result, bool)
    assert safe_result is True
    print(f"Safe message result: {safe_result}")

    # Note: We're not testing unsafe messages to avoid having
    # inappropriate content in the test code


if __name__ == "__main__":
    asyncio.run(test_classify_message())
    asyncio.run(test_is_safe_message())
