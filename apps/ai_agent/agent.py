import json
from typing import Dict, Any, List, Optional
from apps.profiles.models import UserProfile
from apps.preferences.services import PreferenceManager
from apps.ai_agent.models import Conversation, ChatMessage
from apps.ai_agent.tools import GuardedToolDispatcher
from apps.ai_agent.llm_gateway import LLMGateway


class ConversationalAgentOrchestrator:
    """
    Stateful conversational agent managing multi-turn dialog, guarded tool calling,
    cross-session preference synchronization, and recommendation alignment.
    """

    SYSTEM_PROMPT_TEMPLATE = """You are MatchForge, an expert AI career advisor and opportunity discovery agent.
Your mission is to understand the candidate's skills, desires, and dealbreakers through natural conversation.
Always ground your answers in the candidate's actual profile and the opportunity dataset.

CURRENT CANDIDATE STATE:
Name: {name}
Headline: {headline}
Experience: {experience_months} months
Location: {location} (Relocate: {relocate})
Active Preferences: {preferences}
Active Dealbreakers: {dealbreakers}

RULES:
1. When the candidate mentions preferences or dealbreakers, call 'update_user_preferences'.
2. When the candidate asks for jobs or recommendations, call 'search_opportunities'.
3. When the candidate asks about missing skills, call 'identify_skill_gaps'.
4. Do NOT hallucinate jobs or compensation. Use tools to query the verified backend.
"""

    @classmethod
    def process_message(
        cls,
        profile: UserProfile,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming user message, runs the agent tool-calling loop,
        executes guarded backend tools, persists state, and returns the assistant response.
        """
        # 1. Retrieve or create conversation session
        if conversation_id:
            try:
                conv = Conversation.objects.get(id=conversation_id, profile=profile)
            except Conversation.DoesNotExist:
                conv = Conversation.objects.create(profile=profile, title=user_message[:40])
        else:
            conv = Conversation.objects.create(profile=profile, title=user_message[:40])

        # 2. Persist incoming user message
        ChatMessage.objects.create(
            conversation=conv,
            sender_type='USER',
            content=user_message
        )

        # 3. Assemble active context
        active_prefs = PreferenceManager.get_user_preferences(profile)
        dealbreakers = PreferenceManager.get_dealbreakers(profile)

        system_prompt = cls.SYSTEM_PROMPT_TEMPLATE.format(
            name=profile.full_name,
            headline=profile.headline or "Candidate",
            experience_months=profile.experience_months,
            location=profile.current_location or "Unspecified",
            relocate="Yes" if profile.willing_to_relocate else "No",
            preferences=json.dumps(active_prefs),
            dealbreakers=json.dumps(dealbreakers)
        )

        # Build message history for LLM
        recent_messages = conv.messages.all().order_by('-created_at')[:8]
        messages_payload = [{"role": "system", "content": system_prompt}]
        for msg in reversed(list(recent_messages)):
            role = "user" if msg.sender_type == 'USER' else "assistant"
            messages_payload.append({"role": role, "content": msg.content})

        # 4. Invoke LLM Gateway
        llm_result = LLMGateway.call_agent(
            messages=messages_payload,
            tools=GuardedToolDispatcher.TOOL_DEFINITIONS,
            active_preferences=active_prefs
        )

        tool_calls = llm_result.get('tool_calls', [])
        assistant_content = llm_result.get('content', '')
        executed_tool_results = []

        # 5. Execute guarded tools
        if tool_calls:
            for tc in tool_calls:
                func_name = tc['function']['name']
                raw_args = tc['function']['arguments']
                args_dict = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                tool_output = GuardedToolDispatcher.execute_tool(
                    tool_name=func_name,
                    arguments=args_dict,
                    profile=profile,
                    conversation_id=str(conv.id)
                )

                executed_tool_results.append({
                    "tool": func_name,
                    "arguments": args_dict,
                    "result": tool_output
                })

        # 6. Persist assistant turn with tool metadata
        ChatMessage.objects.create(
            conversation=conv,
            sender_type='ASSISTANT',
            content=assistant_content,
            tool_calls=tool_calls if tool_calls else None,
            tool_responses=executed_tool_results if executed_tool_results else None,
            metadata={"engine": llm_result.get('engine')}
        )

        # Refresh updated preferences for response envelope
        updated_prefs = PreferenceManager.get_user_preferences(profile)

        return {
            "conversation_id": str(conv.id),
            "title": conv.title,
            "message": assistant_content,
            "tool_calls_executed": len(executed_tool_results),
            "tool_results": executed_tool_results,
            "active_preferences": updated_prefs,
            "engine": llm_result.get('engine')
        }
