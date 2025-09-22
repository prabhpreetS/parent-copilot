# Tests for Parent Co-Pilot

This directory contains integration tests for the Parent Co-Pilot application.

## Test Structure

- `conftest.py`: Contains shared pytest fixtures and configuration
- `test_guardrails.py`: Tests for the message classification and safety features
- `test_retrieval_memory.py`: Tests for the vector store memory functionality
- `test_response_handler.py`: Tests for the response generation pipeline
- `test_supabase_chat_history.py`: Tests for the chat history storage and retrieval

## Prerequisites

Before running tests, make sure you have:

1. Installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (put these in a `.env` file or set directly):
   ```
   OPENAI_API_KEY=your_openai_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   
   # For chat history tests
   TEST_USER_ID=existing_user_id_in_your_database
   ALLOW_TEST_DATA=true  # Set to true if we can add test messages, false otherwise
   ```

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_guardrails.py
```

To run tests with verbose output:

```bash
pytest -v
```

To see the print outputs for debugging:

```bash
pytest -v -s
```

## Testing Philosophy

These integration tests are minimal and basic but test the full functionality of:

1. Message classification (guardrails)
2. Vector store creation and querying (retrieval memory)
3. Chat history storage and retrieval
4. Complete response generation pipeline

Each test verifies that the respective functions work as expected with actual API calls.

## Notes

- All tests use a unique user ID to avoid conflicts when possible
- Chat history tests require an existing user ID (set via TEST_USER_ID environment variable)
- Tests that require specific environment variables will be skipped if those variables are not set
- Test files clean up their test data when possible 