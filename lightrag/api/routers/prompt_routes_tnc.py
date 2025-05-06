from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
from pydantic import BaseModel, Field

# File containing all prompts
# Dynamically construct the file path using WORKING_DIR
WORKING_DIR = os.getenv("WORKING_DIR", "./data/rag_storage")
PROMPT_FILE_PATH = os.path.join(WORKING_DIR, "prompt_coach_reply_tnc.py")


def load_prompts() -> Dict[str, Any]:
    """Load the PROMPT_COACH dictionary from the file."""
    if not os.path.exists(PROMPT_FILE_PATH):
        raise HTTPException(status_code=500, detail=f"Prompt file not found: {PROMPT_FILE_PATH}")
    
    context = {}
    with open(PROMPT_FILE_PATH, "r") as file:
        exec(file.read(), context)
    return context.get("PROMPT_COACH", {})

def save_prompts(prompts: Dict[str, Any]) -> None:
    """Save the PROMPT_COACH dictionary back to the file."""
    os.makedirs(os.path.dirname(PROMPT_FILE_PATH), exist_ok=True)
    with open(PROMPT_FILE_PATH, "w") as file:
        file.write("from typing import Any\n\nPROMPT_COACH: dict[str, Any] = {}\n\n")
        for key, value in prompts.items():
            file.write(f'PROMPT_COACH["{key}"] = """{value.strip()}"""\n')

router = APIRouter(tags=["prompts"])

class CreatePromptRequest(BaseModel):
    """Request model for creating a new prompt."""
    prompt_key: str = Field(
        ...,
        description="The unique key for the prompt."
    )
    prompt_value: str = Field(
        ...,
        description="The content of the prompt. Supports multi-line text.",
        example="This is an example of a multi-line prompt.\nIt spans multiple lines."
    )

class UpdatePromptRequest(BaseModel):
    """Request model for updating an existing prompt."""
    prompt_value: str = Field(
        ...,
        description="The updated content of the prompt. Supports multi-line text.",
        example="This is the updated content of the prompt.\nIt spans multiple lines."
    )

def create_prompt_routes():
    """ Create routes for managing prompts in the system.
    This includes loading, saving, creating, updating, and deleting prompts."""

    @router.get("/prompts", response_model=Dict[str, str])
    def get_all_prompts():
        """Retrieve all prompts."""
        return load_prompts()
    
    @router.get("/prompt/keys", response_model=list[str])
    def get_all_prompt_keys():
        """Retrieve all prompt keys."""
        prompts = load_prompts()
        return list(prompts.keys())

    @router.get("/prompts/{prompt_key}", response_model=str)
    def get_prompt(prompt_key: str):
        """Retrieve a specific prompt by key."""
        prompts = load_prompts()
        if prompt_key not in prompts:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_key}' not found.")
        return prompts[prompt_key]

    @router.post("/prompts")
    def create_prompt(request: CreatePromptRequest):
        """Create a new prompt. Use the naming convention school_counselor_<insert your prompt name>_reply to avoid conflicts."""
        prompts = load_prompts()
        if request.prompt_key in prompts:
            raise HTTPException(status_code=400, detail=f"Prompt '{request.prompt_key}' already exists.")
        prompts[request.prompt_key] = request.prompt_value
        save_prompts(prompts)
        return {"message": f"Prompt '{request.prompt_key}' created successfully."}

    @router.put("/prompts/{prompt_key}")
    def update_prompt(prompt_key: str, request: UpdatePromptRequest):
        """Update an existing prompt."""
        prompts = load_prompts()
        if prompt_key not in prompts:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_key}' not found.")
        prompts[prompt_key] = request.prompt_value
        save_prompts(prompts)
        return {"message": f"Prompt '{prompt_key}' updated successfully."}

    @router.delete("/prompts/{prompt_key}")
    def delete_prompt(prompt_key: str):
        """Delete a prompt."""
        prompts = load_prompts()
        if prompt_key not in prompts:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_key}' not found.")
        del prompts[prompt_key]
        save_prompts(prompts)
        return {"message": f"Prompt '{prompt_key}' deleted successfully."}
    
    return router