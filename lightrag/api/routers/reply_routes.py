"""
This module contains all reply-related routes for the LightRAG API.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from ..utils_api import get_api_key_dependency, get_resolved_namespace, get_rag_from_app
from pydantic import BaseModel, Field, field_validator
from lightrag.base import ReplyParam, CoachMessage as BaseCoachMessage, AISuggestion as BaseAISuggestion
from ascii_colors import trace_exception
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reply"])

# Creates or returns rag instance
async def get_rag(
    request: Request,
    namespace: Optional[str] = Depends(get_resolved_namespace)
) -> Any:
    return await get_rag_from_app(request, namespace)

# Reply Roles
role_user = os.getenv("REPLY_ROLE_USER")
role_assistant = os.getenv("REPLY_ROLE_ASSISTANT")

class AISuggestion(BaseModel):
    text: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    technique: Optional[str] = None
    level: Optional[str] = None
    confidence: Optional[float] = None

    @classmethod
    def from_base_message(cls, base_ai_suggestion: BaseAISuggestion | dict | None):
        if isinstance(base_ai_suggestion, (BaseAISuggestion, AISuggestion)):
            base_ai_suggestion = base_ai_suggestion.__dict__
        if isinstance(base_ai_suggestion, dict):
            return cls.model_validate(base_ai_suggestion)
        raise TypeError("Invalid input type. Expected dict, BaseAISuggestion, or AISuggestion instance.")

class UserMessage(BaseModel):
    speaker: Literal['student', 'patient']
    content: str
    timestamp: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    technique: Optional[str] = None
    level: Optional[str] = None

class CoachMessage(BaseModel):
    speaker: Literal['coach', 'doctor']
    content: Optional[str] = None
    aiSuggestions: Optional[List[AISuggestion]] = None
    selectedSuggestionIndex: Optional[int] = None
    isFinalized: bool
    timestamp: str
    
    @classmethod
    def from_base_message(cls, base_message: BaseCoachMessage):
        if isinstance(base_message, BaseCoachMessage):
            base_message = base_message.__dict__
        if "aiSuggestions" in base_message and base_message["aiSuggestions"]:
            base_message["aiSuggestions"] = [AISuggestion.from_base_message(s) for s in base_message["aiSuggestions"]]
        return cls.model_validate(base_message)

class DialogTurn(BaseModel):
    userMessage: Optional[UserMessage] = None
    coachMessage: Optional[CoachMessage] = None

class ReplyRequest(BaseModel):
    student_name: Optional[str] = Field(
        default=None,
        description="Optional student name to personalize the response.",
    )
    speaker: Literal["student"] = Field(
        default="student",
        description="Speaker role of the current message which is always the student.  A coach response is never sent."
    )

    content: str = Field(
        ...,
        description="The current user's message content."
    )

    timestamp: str = Field(
        ...,
        description="Timestamp of the current message."
    )
    topic: Optional[Literal[
        "Social", "Collab", "Friendship", "Thinking", "English", "Diet", "Fitness",
        "Coping", "Learning", "Financial", "Practical", "Problem-solving", 
        "Self-aware", "Self-care", "Reflection", "Stress", "Time", "Unknown"
    ]] = Field(
        default=None,
        description="Topic of the desired response.",
    )

    sub_topic: Optional[str] = Field(
        default=None,
        description="Sub-topic of the desired response.",
    )

    intent: Optional[Literal["Experience", "Emotion", "Guidance", "Unknown"]] = Field(
        default=None,
        description="Intent of the desired response to capture Experience, Emotion, or Guidance.",
    )

    sentiment: Optional[Literal["Positive", "Neutral", "Negative", "Unknown"]] = Field(
        default=None,
        description="Sentiment of the desired response.",
    )

    technique: Optional[Literal["Plow", "Open", "Role", "Stacking", "Callback", "Assign", "Polling", "Pushpull", "Unknown"]] = Field(
        default=None,
        description="Technique of the desired response.",
    )

    level: Optional[Literal["Attraction", "Relate", "Trust", "Unknown"]] = Field(
        default=None,
        description="Level of the desired response.",
    )

    mode: Literal["local", "global", "hybrid", "naive", "mix"] = Field(
        default="hybrid",
        description="Query mode",
    )

    only_need_context: Optional[bool] = Field(
        default=None,
        description="If True, only returns the retrieved context without generating a response.",
    )

    only_need_prompt: Optional[bool] = Field(
        default=None,
        description="If True, only returns the generated prompt without producing a response.",
    )

    top_k: Optional[int] = Field(
        ge=1,
        default=None,
        description="Number of top items to retrieve.",
    )

    max_token_for_text_unit: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allowed for each retrieved text chunk.",
    )

    max_token_for_global_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for relationship descriptions in global retrieval.",
    )

    max_token_for_local_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for entity descriptions in local retrieval.",
    )

    hl_keywords: Optional[List[str]] = Field(
        default=None,
        description="List of high-level keywords to prioritize in retrieval.",
    )

    ll_keywords: Optional[List[str]] = Field(
        default=None,
        description="List of low-level keywords to refine retrieval focus.",
    )

    history_turns: Optional[int] = Field(
        default=None,
        description="Number of historical dialog turns to consider.",
    )
    conversation_history: List[DialogTurn] = Field(
       default_factory=lambda: [
        DialogTurn(
            userMessage=UserMessage(
                speaker="student",
                content="I'm falling behind in math and I don't know what to do.",
                timestamp="2025-03-13T10:00:00Z",
                intent="Guidance",
                sentiment="Concerned",
                topic="Academics",
                sub_topic="Math",
                technique="OpenEnded",
                level="Trust"
            ),
            coachMessage=CoachMessage(
                speaker="coach",
                content="Let's figure out where you're struggling. Can you show me a problem that’s confusing?",
                isFinalized=True,
                selectedSuggestionIndex=-1,
                timestamp="2025-03-13T10:01:00Z",
                aiSuggestions=[
                    AISuggestion(
                        text="You're doing better than you think. Let's work on small wins together.",
                        intent="Guidance",
                        sentiment="Supportive",
                        topic="Motivation",
                        sub_topic="Self-Esteem",
                        technique="Empathy",
                        level="Trust",
                        confidence=0.95
                    ),
                    AISuggestion(
                        text="It's okay to feel overwhelmed. You're not alone, and I'm here to support you.",
                        intent="Empathy",
                        sentiment="Compassionate",
                        topic="Emotional Support",
                        sub_topic="Stress",
                        technique="Validation",
                        level="Support",
                        confidence=0.91
                    )
                ]
            )
        )
    ],
    description="Conversation history including user and coach dialog turns."
    )   

    @field_validator("hl_keywords", mode="after")
    @classmethod
    def hl_keywords_strip_after(cls, hl_keywords: List[str] | None) -> List[str] | None:
        if hl_keywords is None:
            return None
        return [keyword.strip() for keyword in hl_keywords]

    @field_validator("ll_keywords", mode="after")
    @classmethod
    def ll_keywords_strip_after(cls, ll_keywords: List[str] | None) -> List[str] | None:
        if ll_keywords is None:
            return None
        return [keyword.strip() for keyword in ll_keywords]

    def to_reply_params(self, is_stream: bool) -> "ReplyParam":
        #request_data = self.model_dump(exclude_none=True, exclude={"topic", "sub-topic","intent", "sentiment", "technique", "level", "student_name","speaker","content","timestamp","conversation_history"})
        request_data = self.model_dump(exclude_none=True, exclude={"student_name","speaker","content","timestamp","conversation_history"})
        param = ReplyParam(**request_data)
        param.stream = is_stream
        return param

class ReplyResponse(BaseModel):
    coachMessage: Optional[CoachMessage] = None

def create_reply_routes(api_key: Optional[str] = None):
    optional_api_key = get_api_key_dependency(api_key)
    return router


@router.post("/coach_reply", response_model=ReplyResponse)
async def reply_text(
    request: ReplyRequest,
    rag: Any = Depends(get_rag)
) -> ReplyResponse:
    """
    Interaction model: Human-to-human dialog (e.g., student ↔ coach or patient ↔ doctor), with AI assisting the coach/doctor with suggested replies

    Handle a POST request at the /coach_reply endpoint to generate a life coach response.
    """
    try:
        logger.debug(f"Received request: {request.json()}")
        param = request.to_reply_params(False)
        base_coach_msg = await rag.acoach_reply(
            student_name=request.student_name,
            speaker=request.speaker,
            content=request.content,
            timestamp=request.timestamp,
        conversation_history=[turn.model_dump() if isinstance(turn, DialogTurn) else turn for turn in request.conversation_history],
            param=param
        )
        # logger.debug(f"Reply type: {type(coach_msg)}, Reply: {coach_msg}")
        # Ensure coach_msg is a valid CoachMessage instance
        coach_msg = CoachMessage.from_base_message(base_coach_msg)
        if not isinstance(coach_msg, CoachMessage):            
            logger.error(f"Unexpected response type: {type(coach_msg)}")
            raise HTTPException(status_code=500, detail="Unexpected response type. Expected CoachMessage.")

        return ReplyResponse(
            coachMessage=coach_msg
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/coach_reply/stream")
async def query_text_stream(
    request: ReplyRequest,
    rag: Any = Depends(get_rag),
    ) -> ReplyResponse:
    """
    Human-to-human dialog (e.g., student ↔ coach or patient ↔ doctor), with AI assisting the coach/doctor with suggested replies

    This endpoint performs a retrieval-augmented generation (RAG) reply and streams the response.

    Args:
        request (ReplyRequest): The request object containing the reply parameters.
        optional_api_key (Optional[str], optional): An optional API key for authentication. Defaults to None.

    Returns:
        StreamingResponse: A streaming response containing the RAG query results.
    """
    try:
        param = request.to_reply_params(True)
        coach_msg = await rag.acoach_reply(
            conversation_history=[turn.model_dump() if isinstance(turn, DialogTurn) else turn for turn in request.conversation_history],
            student_name=request.student_name,
            speaker=request.speaker,
            content=request.content,
            timestamp=request.timestamp,
            param=param
        )

        from fastapi.responses import StreamingResponse

        async def stream_generator():
            try:
                if coach_msg.aiSuggestions:
                    for suggestion in coach_msg.aiSuggestions:
                        yield f"{json.dumps({'reply': suggestion.text})}\n"
                else:
                    yield f"{json.dumps({'reply': ''})}\n"
            except Exception as e:
                logging.error(f"Streaming error: {str(e)}")
                yield f"{json.dumps({'error': str(e)})}\n"

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-ndjson",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))