"""
Feedback and prompt versioning service.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger

from backend.models.schemas import FeedbackEntry, PromptVersion


DATA_DIR = Path("data")
FEEDBACK_FILE = DATA_DIR / "feedbacks.json"
PROMPT_FILE = DATA_DIR / "prompts.json"


DEFAULT_SYSTEM_PROMPT = """You are FinBot, a professional and friendly AI financial assistant specialized in:
- Cryptocurrency market data and analysis
- Financial education and concepts
- Investment strategies and risk management

Guidelines:
- Always provide accurate, up-to-date information using your tools when asked about prices or market data.
- Explain complex financial concepts in simple, accessible language.
- When discussing investments, always mention the associated risks.
- Be concise but thorough in your explanations.
- Use emojis sparingly to make conversations more engaging.
- If you don't know something, say so honestly rather than guessing.
- Respond in the same language the user writes to you.
"""


class FeedbackService:

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._feedbacks: list[FeedbackEntry] = self._load_feedbacks()
        self._prompt_versions: list[PromptVersion] = self._load_prompts()

        # Ensure we have at least the default prompt
        if not self._prompt_versions:
            initial = PromptVersion(
                version=1,
                prompt_text=DEFAULT_SYSTEM_PROMPT,
                reason="Initial default prompt",
            )
            self._prompt_versions.append(initial)
            self._save_prompts()
            logger.info("Initialized default system prompt (v1).")



    def _load_feedbacks(self) -> list[FeedbackEntry]:
        if FEEDBACK_FILE.exists():
            try:
                raw = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
                return [FeedbackEntry(**f) for f in raw]
            except Exception as e:
                logger.error(f"Error loading feedbacks: {e}")
        return []

    def _save_feedbacks(self) -> None:
        FEEDBACK_FILE.write_text(
            json.dumps([f.model_dump(mode="json") for f in self._feedbacks], indent=2, default=str),
            encoding="utf-8",
        )

    def _load_prompts(self) -> list[PromptVersion]:
        if PROMPT_FILE.exists():
            try:
                raw = json.loads(PROMPT_FILE.read_text(encoding="utf-8"))
                return [PromptVersion(**p) for p in raw]
            except Exception as e:
                logger.error(f"Error loading prompts: {e}")
        return []

    def _save_prompts(self) -> None:
        PROMPT_FILE.write_text(
            json.dumps([p.model_dump(mode="json") for p in self._prompt_versions], indent=2, default=str),
            encoding="utf-8",
        )



    def get_current_prompt(self) -> str:
        """Get the current active system prompt."""
        return self._prompt_versions[-1].prompt_text

    def get_current_version(self) -> int:
        """Get the current prompt version number."""
        return self._prompt_versions[-1].version

    def get_prompt_history(self) -> list[PromptVersion]:
        """Get full prompt version history."""
        return list(self._prompt_versions)

    def get_feedbacks(self) -> list[FeedbackEntry]:
        """Get all stored feedbacks."""
        return list(self._feedbacks)

    def add_feedback(self, rating: int, comment: str, suggestion: str, message_id: str | None = None) -> FeedbackEntry:
        entry = FeedbackEntry(
            id=str(uuid.uuid4()),
            rating=rating,
            comment=comment,
            suggestion=suggestion,
        )
        self._feedbacks.append(entry)
        self._save_feedbacks()
        logger.info(f"Feedback recorded: rating={rating}, id={entry.id}")
        return entry

    def update_prompt(self, new_prompt: str, reason: str) -> PromptVersion:
        new_version = PromptVersion(
            version=self.get_current_version() + 1,
            prompt_text=new_prompt,
            reason=reason,
        )
        self._prompt_versions.append(new_version)
        self._save_prompts()


        for fb in self._feedbacks:
            if not fb.applied:
                fb.applied = True
        self._save_feedbacks()

        logger.info(f"Prompt updated to v{new_version.version}: {reason}")
        return new_version

    def get_unapplied_feedbacks(self) -> list[FeedbackEntry]:
        """Get feedbacks that haven't been applied to a prompt update yet."""
        return [f for f in self._feedbacks if not f.applied]


# Singleton
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """Get or create the FeedbackService singleton."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
