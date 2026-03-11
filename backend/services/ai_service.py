"""
LangChain agent with tool calling and RAG.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from loguru import logger

from backend.config import get_settings
from backend.services.tools_service import TOOLS
from backend.services.vector_service import get_vector_service
from backend.services.feedback_service import get_feedback_service


class AIService:

    def __init__(self) -> None:
        settings = get_settings()
        self._llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
        self._chat_histories: dict[str, list] = {}
        logger.info("AI Service initialized with gpt-4o-mini")

    def _build_agent(self) -> AgentExecutor:
        """Build/rebuild the agent with the current system prompt."""
        feedback_svc = get_feedback_service()
        current_prompt = feedback_svc.get_current_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", current_prompt),
            ("system", (
                "SELF-MODIFICATION INSTRUCTIONS:\n"
                "You have the ability to dynamically update your own system prompt. "
                "If the user asks you to change your behavior, tone, language, personality, "
                "or any other aspect of how you respond, you MUST:\n"
                "1. First use the 'get_current_prompt' tool to read your current prompt.\n"
                "2. Then use the 'update_my_prompt' tool with the modified prompt text and a reason.\n"
                "Keep your core financial assistant identity and tool capabilities when updating.\n"
                "After updating, confirm to the user that your behavior has been adjusted.\n"
                "\n"
                "Relevant context from knowledge base:\n{context}"
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self._llm, TOOLS, prompt)
        return AgentExecutor(
            agent=agent,
            tools=TOOLS,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

    def _get_history(self, session_id: str) -> list:
        """Get or create chat history for a session."""
        if session_id not in self._chat_histories:
            self._chat_histories[session_id] = []
        return self._chat_histories[session_id]

    async def chat(self, message: str, session_id: str = "streamlit") -> dict:
        logger.info(f"[{session_id}] User: {message[:80]}...")


        vector_svc = get_vector_service()
        context_docs = vector_svc.query(message, n_results=3)
        context = "\n---\n".join(context_docs) if context_docs else "No specific context available."


        executor = self._build_agent()
        history = self._get_history(session_id)


        try:
            result = await executor.ainvoke({
                "input": message,
                "context": context,
                "chat_history": history,
            })
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return {
                "response": f"Sorry, I encountered an error processing your request. Please try again.",
                "tools_used": [],
                "session_id": session_id,
            }

        response_text = result.get("output", "I couldn't generate a response.")


        tools_used = []
        for step in result.get("intermediate_steps", []):
            if len(step) >= 2:
                action, observation = step[0], step[1]
                tools_used.append({
                    "tool_name": action.tool,
                    "tool_input": action.tool_input if isinstance(action.tool_input, dict) else {"input": str(action.tool_input)},
                    "tool_output": str(observation)[:500],
                })


        history.append(HumanMessage(content=message))
        history.append(AIMessage(content=response_text))


        if len(history) > 20:
            self._chat_histories[session_id] = history[-20:]

        logger.info(f"[{session_id}] Bot: {response_text[:80]}... | Tools: {[t['tool_name'] for t in tools_used]}")
        return {
            "response": response_text,
            "tools_used": tools_used,
            "session_id": session_id,
        }

    async def analyze_and_update_prompt(self) -> dict | None:
        feedback_svc = get_feedback_service()
        unapplied = feedback_svc.get_unapplied_feedbacks()

        if not unapplied:
            logger.debug("No unapplied feedbacks to process.")
            return None


        has_suggestions = any(f.suggestion.strip() for f in unapplied)
        avg_rating = sum(f.rating for f in unapplied) / len(unapplied)

        if len(unapplied) < 2 and not has_suggestions and avg_rating > 3.5:
            logger.debug("Not enough feedback to trigger prompt update.")
            return None

        current_prompt = feedback_svc.get_current_prompt()

        feedback_summary = "\n".join([
            f"- Rating: {f.rating}/5 | Comment: {f.comment} | Suggestion: {f.suggestion}"
            for f in unapplied
        ])

        meta_prompt = f"""You are a prompt engineering expert. Analyze the user feedback below and improve the current system prompt.

CURRENT SYSTEM PROMPT:
---
{current_prompt}
---

USER FEEDBACK:
{feedback_summary}

RULES:
1. Keep the core identity and financial assistant role.
2. Incorporate valid user suggestions.
3. Address issues indicated by low ratings.
4. Keep the prompt concise and clear.
5. Output ONLY the improved prompt text, nothing else.
"""

        try:
            result = await self._llm.ainvoke([HumanMessage(content=meta_prompt)])
            new_prompt = result.content.strip()

            if new_prompt and new_prompt != current_prompt:
                reason = f"Auto-update based on {len(unapplied)} feedback(s). Avg rating: {avg_rating:.1f}"
                version = feedback_svc.update_prompt(new_prompt, reason)
                logger.info(f"Prompt auto-updated to v{version.version}")
                return {
                    "new_version": version.version,
                    "reason": reason,
                    "prompt_preview": new_prompt[:200] + "...",
                }
        except Exception as e:
            logger.error(f"Prompt auto-update failed: {e}")

        return None


# Singleton
_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    """Get or create the AIService singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
