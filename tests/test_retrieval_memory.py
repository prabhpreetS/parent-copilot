import asyncio
import os
import sys
from datetime import datetime

import pytest

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v1.services.memory_engine.retrieval_memory import (
    create_supabase_vector_store,
    query_supabase_vector_store,
)

# Sample contract text for testing
SAMPLE_CONTRACT = """
CUSTODY AGREEMENT

1. Child Custody Arrangement:
   The parties shall have joint custody of the minor children.
   Parent A shall have the children on weekdays.
   Parent B shall have visitation every other weekend.

2. Child Support:
   Parent B shall pay child support in the amount of $800 per month.
"""


@pytest.mark.asyncio
async def test_vector_store_workflow():
    """Test the complete workflow of creating and querying a vector store."""
    # Skip test if credentials aren't available
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
        pytest.skip("Supabase credentials not set in environment")

    # Generate a unique test user ID
    test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Step 1: Create the vector store
    create_result = await create_supabase_vector_store(SAMPLE_CONTRACT, test_user_id)
    assert isinstance(create_result, dict)
    assert "status" in create_result
    assert create_result["status"] == "success"
    print(f"Vector store creation result: {create_result}")

    # Wait a moment for indexing to complete
    await asyncio.sleep(3)

    # Step 2: Query the vector store
    query_result = await query_supabase_vector_store(
        "What is the custody arrangement?", test_user_id
    )
    assert isinstance(query_result, str)
    assert len(query_result) > 0
    print(f"Query result: {query_result[:100]}...")

    # Step 3: Test another query
    support_result = await query_supabase_vector_store(
        "How much is child support?", test_user_id
    )
    assert isinstance(support_result, str)
    assert len(support_result) > 0
    print(f"Support query result: {support_result[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_vector_store_workflow())
