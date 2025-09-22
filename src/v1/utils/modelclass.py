import json
from pydantic import BaseModel
from typing import List


# Dummy Model Classes
class Prediction_Input(BaseModel):
    text: str
    language: str = "en"


class Prediction_Output(BaseModel):
    input_text: str
    language: str
    prediction: str
    confidence: float


# Conversational bot input
class Conversation_Input(BaseModel):
    user_input: str
    user_id: str
    parent_shared_id: str
    user_name: str

# Conversational bot output
class Conversation_Output(BaseModel):
    response: str
    relevant_contract_statements: str
    total_tokens: int
    label: str
    chat_history: str
    llm_model: str
    chat_summary: str
    time_taken: float

# Convert Contract Text to Json: Input
class Convert_to_json(BaseModel):
    text: str
    user_id: str


# Convert Contract Text to Json: Response
class ConvertToJsonResponse(BaseModel):
    status: str
    message: str
    json_response: dict


# Create Vector Store: Input
class Create_vector_store(BaseModel):
    json_response: dict
    user_id: str
    document_id: str


# Create Vector Store: Response
class CreateVectorStoreResponse(BaseModel):
    status: str
    message: str
    json_response: dict


# Chat Summary Response
class ChatSummaryResponse(BaseModel):
    status: str
    message: str

class ChatSummary(BaseModel):
    chat: str
    parent_shared_id: str
    user_id: str

# Tip of the Day: Input
class TipOfTheDayInput(BaseModel):
    user_id: str

# Tip of the Day: Response
class TipOfTheDayResponse(BaseModel):
    status: str
    message: str
    tip: str


# Activities: Input
class ActivitiesInput(BaseModel):
    user_id: str

# Activities: Response
class ActivitiesResponse(BaseModel):
    status: str
    message: str
    activities: List[str]

# Reminders: Input
class ReminderInput(BaseModel):
    text: str
    user_id: str
    document_id: str

# Reminders: Response
class ReminderResponse(BaseModel):
    status: str
    message: str
    events: List[dict] = []
    metadata: dict = None
    error: str = None

# Guardrails Test: Input
class GuardrailsTestInput(BaseModel):
    message: str

# Guardrails Test: Response
class GuardrailsTestResponse(BaseModel):
    status: str
    message: str
    classification: dict
    input_message: str