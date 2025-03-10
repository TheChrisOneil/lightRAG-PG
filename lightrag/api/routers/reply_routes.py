"""
This module contains all reply-related routes for the LightRAG API.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from ..utils_api import get_api_key_dependency, get_resolved_namespace, get_rag_from_app
from pydantic import BaseModel, Field, field_validator

from ascii_colors import trace_exception

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reply"])

# Creates or returns rag instance
async def get_rag(
    request: Request,
    namespace: Optional[str] = Depends(get_resolved_namespace)
) -> Any:
    return await get_rag_from_app(request, namespace)


class ReplyRequest(BaseModel):
    last_message: str = Field(
        min_length=1,
        description="The last message from the student to generate a reply.",
    )

    student_name: Optional[str] = Field(
        default=None,
        description="Optional student name to personalize the response.",
    )

    include_history: Optional[bool] = Field(
        default=True,
        description="Whether to include conversation history in reply generation.",
    )

    conversation_history: List[Dict[str, Any]] = Field(
        default=...,
        description="Stores past conversation history to maintain context.",
    )

    @field_validator("last_message", mode="after")
    @classmethod
    def last_message_strip_after(cls, last_message: str) -> str:
        return last_message.strip()

    @field_validator("conversation_history", mode="after")
    @classmethod
    def conversation_history_check(
        cls, conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for msg in conversation_history:
            if "role" not in msg or msg["role"] not in {"user", "assistant"}:
                raise ValueError(
                    "Each message must have a 'role' key with value 'user' or 'assistant'."
                )
        return conversation_history


class ReplyResponse(BaseModel):
    reply: str = Field(
        description="The generated reply text.",
    )

def create_reply_routes(api_key: Optional[str] = None):
    optional_api_key = get_api_key_dependency(api_key)
    return router


@router.post("/coach_reply", response_model=ReplyResponse)
async def reply_text(
    request: ReplyRequest,
    rag: Any = Depends(get_rag)
) -> ReplyResponse:
    """
    Handle a POST request at the /coach_reply endpoint to generate a life coach response.
    """
    try:
        response_text = await rag.acoach_reply(request.conversation_history)
        return ReplyResponse(reply=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
