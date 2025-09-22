from src.v1.utils.prompts import REPHRASE_DM_PROMPT
from src.v1.services.model import get_response

async def rephrase_dm(direct_message: str):
    tokens,response, model = await get_response(REPHRASE_DM_PROMPT.format(direct_message=direct_message), system_prompt='return rephrased text only')
    print(f"Rephrased direct message: {response}")
    return response

