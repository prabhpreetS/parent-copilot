# Imports
import asyncio
import logging
import json
from functools import lru_cache
from typing import Optional

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveJsonSplitter
from src.v1.config.config import (
    BREAKPOINT_THRESHOLD_AMOUNT,
    BREAKPOINT_THRESHOLD_TYPE,
    EMBEDDING_MODEL,
    MIN_CHUNK_SIZE,
)

# Configure logging
logger = logging.getLogger(__name__)

# Cache the text splitter to avoid creating a new one for each chunk
@lru_cache(maxsize=1)
# Get the text splitter to use in chunk_text function
def get_text_splitter():
    """
    This function returns the text splitter to use in chunk_text function.
    """
    text_splitter = SemanticChunker(
        OpenAIEmbeddings(model=EMBEDDING_MODEL),
        breakpoint_threshold_type=BREAKPOINT_THRESHOLD_TYPE,
        breakpoint_threshold_amount=BREAKPOINT_THRESHOLD_AMOUNT,
        min_chunk_size=MIN_CHUNK_SIZE,
    )
    return text_splitter


@lru_cache(maxsize=1)
def get_json_splitter():
    """
    This function returns the json splitter to use in split_json_into_kv_chunks function.
    """
    return RecursiveJsonSplitter()


async def chunk_text(text: str):
    """
    This function chunks the text into smaller chunks of text.
    """
    text_splitter = get_text_splitter()
    docs = await asyncio.to_thread(text_splitter.create_documents, [text])
    logger.debug(f"Created {len(docs)} chunks from text of length {len(text)}")
    return docs


def split_json_into_kv_chunks(json_text):
    """
    This function splits the json text into smaller chunks of text.
    """
    # data = json.loads(json_text)
    data = json_text
    chunks = []

    for key, value in data.items():
        chunk = {key: value}
        chunks.append(chunk)
    
    return chunks


def update_metadata(docs: list, user_id: str, document_id: Optional[str] = None, child_id: Optional[str] = None):
    """
    This function updates the metadata of the documents by adding the user_id, document_id, and optionally child_id.
    """
    for doc in docs:
        if doc.metadata is None:
            doc.metadata = {}
        doc.metadata["user_id"] = user_id
        if document_id:
            doc.metadata["document_id"] = document_id
        if child_id:
            doc.metadata["child_id"] = child_id
    logger.debug(f"Updated metadata for {len(docs)} chunks with user_id: {user_id}" + 
                (f", document_id: {document_id}" if document_id else "") +
                (f" and child_id: {child_id}" if child_id else ""))
    return docs


def split_by_4000_chars(text):
    return [text[i:i+4000] for i in range(0, len(text), 4000)]


if __name__ == "__main__":
    # Set up logging for standalone execution
    from src.v1.config.logging_config import setup_logging

    logger = setup_logging()

    file_path = "/Users/icode/Desktop/parent_co-pilot/data.txt"
    logger.info(f"Reading text from {file_path}")

    with open(file_path, "r") as file:
        text = file.read()

    docs = asyncio.run(chunk_text(text))
    logger.info(f"Generated {len(docs)} chunks from text")
    for i, doc in enumerate(docs[:3]):  # Log first 3 chunks as examples
        logger.info(f"Chunk {i+1}: {doc.page_content[:100]}...")

    if len(docs) > 3:
        logger.info(f"... and {len(docs) - 3} more chunks")
# type uvicorn src.v1.utils.text_chunking:app --reload to run the file
