from typing import Optional
import os
from .base_tnc import DialogTurn, CoachMessage, AISuggestion, ReplyParam
from .prompt import PROMPTS
from .prompt_coach_reply_tnc import PROMPT_COACH
from lightrag.utils import always_get_an_event_loop
from .operate_coach_reply_tnc import format_conversation_history
from lightrag.lightrag import LightRAG
import logging

logger = logging.getLogger(__name__)

class CoachReply:
    def __init__(self, rag: LightRAG):
        self.rag = rag

    async def acoach_reply(
        self,
        student_name: str,
        speaker: str,
        content: str,
        timestamp: str,
        conversation_history: list[DialogTurn],
        param: ReplyParam,
    ) -> CoachMessage:
        try:
            role_user = os.getenv("REPLY_ROLE_USER", "student")
            role_assistant = os.getenv("REPLY_ROLE_ASSISTANT", "school_counselor")

            if not content:
                sample_opener = "How has your day been?"
                ai_suggestions = [AISuggestion(text=sample_opener, intent="N/A", topic="N/A", sentiment="N/A", level="N/A")]
                return CoachMessage(
                    speaker="coach",
                    content=sample_opener,
                    aiSuggestions=ai_suggestions,
                    selectedSuggestionIndex=0,
                    isFinalized=True,
                    timestamp=timestamp
                )

            if param.history_turns is None:
                param.history_turns = 5
            conversation_history = sorted(conversation_history, key=lambda x: x.get("timestamp", ""), reverse=True)[:param.history_turns]
            conversation_history = list(reversed(conversation_history))
            formatted_history = format_conversation_history(conversation_history)

            intent_reply_prompt = PROMPT_COACH[f"{role_assistant}_intent_classification"].format(
                history=formatted_history,
                last_message=content,
            )
            intent = await self.rag.llm_model_func(intent_reply_prompt)
            if not intent or ":" not in intent:
                logger.warning(f"Invalid intent format: '{intent}'")
                intent = "Unknown : Unknown"
            logger.debug(f"Detected intent: {intent}")

            topic_reply_prompt = PROMPT_COACH[f"{role_assistant}_topic_classification"].format(
                history=formatted_history,
                last_message=content,
            )
            topic = await self.rag.llm_model_func(topic_reply_prompt)
            logger.debug(f"Detected topic: {topic}")
            if not topic or ":" not in topic:
                topic = "Unknown : Unknown"
                topic_only = "unknown"
            else:
                topic_only = topic.split(":")[0].strip().lower()
            # ---- Capture convo sentiment ----
            prompt = f"{role_assistant.lower()}_sentiment_{topic_only}"
            reply_prompt = PROMPT_COACH[prompt].format(
                history=formatted_history,
                last_message=content,
            )
            sentiment = await self.rag.llm_model_func(reply_prompt)
            if not sentiment or ":" not in sentiment:
                sentiment = "Unknown : Unknown"
            logger.debug(f"Detected sentiment: {sentiment}")
            # ---- Capture convo level ----
            prompt = f"{role_assistant}_level_classification"
            reply_prompt = PROMPT_COACH[prompt].format(
                history=formatted_history,
                last_message=content,
            )
            level = await self.rag.llm_model_func(reply_prompt)
            if not level or ":" not in level:
                level = "Unknown : Unknown"
            logger.debug(f"Detected Level: {level}")
            # ---- Create Coach Reply ----
            reply_prompt = PROMPT_COACH[f"{role_assistant}_reply"].format(
                history=formatted_history,
                last_message=content,
                intent=intent,
                topic=topic,
                sentiment=sentiment,
                level=level,
            )
            logger.debug(f" coach reply prompt: {reply_prompt}")    
            response = await self.rag.llm_model_func(reply_prompt)
            logger.debug(f"Captured coach reply: {response}")    
            ai_suggestions = [AISuggestion(text=response, intent=intent, topic=topic, sub_topic="Unknown", technique="Unknown", sentiment=sentiment, level=level)]
            new_reply = CoachMessage(
                speaker="coach",
                content=response,
                aiSuggestions=ai_suggestions,
                selectedSuggestionIndex=0,
                isFinalized=False,
                timestamp=timestamp
            )
            logger.debug(f"New reply: {new_reply}")
            return new_reply
        except Exception as e:
            logger.error(f"Error in acoach_reply: {e}")
            return CoachMessage(
                speaker="coach",
                content="I'm having trouble generating a response. Can we try again?",
                isFinalized=True,
                selectedSuggestionIndex=-1,
                timestamp=timestamp,
                aiSuggestions=[]
            )

    def coach_reply(
        self,
        student_name: str,
        speaker: str,
        content: str,
        timestamp: str,
        conversation_history: list[DialogTurn],
        param: ReplyParam,
    ) -> str:
        loop = always_get_an_event_loop()
        return loop.run_until_complete(
            self.acoach_reply(student_name, speaker, content, timestamp, conversation_history, param)
        )
