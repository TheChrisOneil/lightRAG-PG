from typing import List, Dict, Any

def format_conversation_history(conversation_history: List[Dict[str, Any]]) -> str:
    formatted_turns = []

    for i, turn in enumerate(conversation_history, start=1):
        user_str = ""
        coach_str = ""

        # User message is optional in the turn in the case the coach starts the conversation
        user = turn.get("userMessage")
        if user and isinstance(user, dict) and user.get("content"):
            user_str = (
                f"Student [{user.get('timestamp', 'N/A')}]: {user.get('content', '')}\n"
                f"  - Intent: {user.get('intent', '')}\n"
                f"  - Sentiment: {user.get('sentiment', '')}\n"
                f"  - Topic: {user.get('topic', '')}\n"
                f"  - SubTopic: {user.get('subTopic', '')}\n"
                f"  - Technique: {user.get('technique', '')}\n"
                f"  - Level: {user.get('level', '')}"
            )

        # Coach message is optional in the turn in the case the student starts the conversation
        coach = turn.get("coachMessage")
        if coach and isinstance(coach, dict) and coach.get("content"):
            coach_str = f"Coach [{coach.get('timestamp', 'N/A')}]: {coach.get('content', '')}"
            if coach.get("aiSuggestions"):
                suggestions = coach["aiSuggestions"]
                ai_strs = []
                for idx, ai in enumerate(suggestions, start=1):
                    ai_strs.append(
                        f"    Suggestion {idx}: {ai.get('text', '')} "
                        f"(Intent: {ai.get('intent', '')}, Sentiment: {ai.get('sentiment', '')}, "
                        f"Topic: {ai.get('topic', '')}, SubTopic: {ai.get('subTopic', '')}, "
                        f"Technique: {ai.get('technique', '')}, Level: {ai.get('level', '')})"
                    )
                coach_str += "\n  - AI Suggestions:\n" + "\n".join(ai_strs)

        formatted_turn = f"--- Turn {i} ---"
        if user_str:
            formatted_turn += f"\n{user_str}"
        if coach_str:
            formatted_turn += f"\n{coach_str}"

        formatted_turns.append(formatted_turn)

    return "\n\n".join(formatted_turns)

def find_missing_keys_in_history(conversation_history: List[Dict[str, Any]]) -> List[str]:
    missing_keys_report = []

    required_user_keys = {"timestamp", "content", "intent", "sentiment", "topic", "subTopic", "technique", "level"}
    required_coach_keys = {"timestamp", "content", "aiSuggestions", "isFinalized", "selectedSuggestionIndex"}
    required_ai_keys = {"text", "intent", "sentiment", "topic", "subTopic", "technique", "level", "confidence"}

    for i, turn in enumerate(conversation_history, start=1):
        user = turn.get("userMessage")
        if user and isinstance(user, dict):
            missing_user = required_user_keys - user.keys()
            if missing_user:
                missing_keys_report.append(f"Turn {i} → Missing in userMessage: {sorted(list(missing_user))}")

        coach = turn.get("coachMessage", {})

        if coach:
            missing_coach = required_coach_keys - coach.keys()
            if missing_coach:
                missing_keys_report.append(f"Turn {i} → Missing in coachMessage: {sorted(list(missing_coach))}")

            if "aiSuggestions" in coach and isinstance(coach["aiSuggestions"], list):
                for j, ai in enumerate(coach["aiSuggestions"], start=1):
                    missing_ai = required_ai_keys - ai.keys()
                    if missing_ai:
                        missing_keys_report.append(
                            f"Turn {i}, AI Suggestion {j} → Missing in aiSuggestion: {sorted(list(missing_ai))}"
                        )

    return missing_keys_report