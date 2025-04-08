
from dataclasses import dataclass, field
import os
from typing import (
    Any,
    Literal,
    TypedDict,
    TypeVar,
    List,
    Optional,
)
## __Hack__ to avoid circular import
@dataclass
class AISuggestion:
    text: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    technique: Optional[str] = None
    level: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class UserMessage:
    speaker: Literal['student', 'patient']
    content: str
    timestamp: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    technique: Optional[str] = None
    level: Optional[str] = None

@dataclass
class CoachMessage:
    isFinalized: bool
    timestamp: str
    speaker: Literal['coach', 'doctor']
    content: Optional[str] = None
    aiSuggestions: Optional[List[AISuggestion]] = None
    selectedSuggestionIndex: Optional[int] = None


@dataclass
class DialogTurn:
    userMessage: UserMessage
    coachMessage: Optional[CoachMessage] = None
    
@dataclass
class ConversationHistory:
    turns: List[DialogTurn] = field(default_factory=list)
## __Hack__ to avoid circular import


@dataclass
class ReplyParam:
    """Configuration parameters for reply generation in LightRAG."""

    intent: Optional[str] = None
    """The intent emoution, experience, guidance of the message."""
    sentiment: Optional[str] = None
    """The sentiment of the message."""
    topic: Optional[str] = None
    """The topic of the message."""
    sub_topic: Optional[str] = None
    """The subtopic of the message."""
    technique: Optional[str] = None
    """The technique of the message."""
    level: Optional[str] = None
    """The level of the message."""

    mode: Literal["local", "global", "hybrid", "naive", "mix"] = "global"
    """Specifies the retrieval mode:
    - "local": Focuses on context-dependent information.
    - "global": Utilizes global knowledge.
    - "hybrid": Combines local and global retrieval methods.
    - "naive": Performs a basic search without advanced techniques.
    - "mix": Integrates knowledge graph and vector retrieval.
    """

    only_need_context: bool = False
    """If True, only returns the retrieved context without generating a response."""

    only_need_prompt: bool = False
    """If True, only returns the generated prompt without producing a response."""

    response_type: str = "Multiple Paragraphs"
    """Defines the response format. Examples: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'."""

    stream: bool = False
    """If True, enables streaming output for real-time responses."""

    top_k: int = int(os.getenv("TOP_K", "60"))
    """Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode."""

    max_token_for_text_unit: int = int(os.getenv("MAX_TOKEN_TEXT_CHUNK", "4000"))
    """Maximum number of tokens allowed for each retrieved text chunk."""

    max_token_for_global_context: int = int(os.getenv("MAX_TOKEN_RELATION_DESC", "4000"))
    """Maximum number of tokens allocated for relationship descriptions in global retrieval."""

    max_token_for_local_context: int = int(os.getenv("MAX_TOKEN_ENTITY_DESC", "4000"))
    """Maximum number of tokens allocated for entity descriptions in local retrieval."""

    hl_keywords: list[str] = field(default_factory=list)
    """List of high-level keywords to prioritize in retrieval."""

    ll_keywords: list[str] = field(default_factory=list)
    """List of low-level keywords to refine retrieval focus."""

    history_turns: int = 3
    """Number of complete conversation turns (user-assistant pairs) to consider in the response context."""
   
