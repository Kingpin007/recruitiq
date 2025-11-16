import asyncio
import inspect

from decouple import config
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError


class TelegramNotifier:
    """Service for sending notifications via Telegram."""

    def __init__(self):
        self.bot_token = config("TELEGRAM_BOT_TOKEN", default="")
        self.chat_id = config("TELEGRAM_CHAT_ID", default="")

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is not set")

        self.bot = Bot(token=self.bot_token)

    def send_evaluation_summary(self, evaluation):
        """
        Send candidate evaluation summary to hiring team.

        Args:
            evaluation: Evaluation model instance

        Returns:
            str: Telegram message ID
        """
        candidate = evaluation.candidate
        job_desc = candidate.job_description

        # Format the message
        message = self._format_evaluation_message(evaluation, candidate, job_desc)

        # Create inline keyboard for actions
        keyboard = self._create_action_keyboard(evaluation.id, candidate.id)

        try:
            # Send message (handle both sync and async python-telegram-bot APIs)
            response = self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            # python-telegram-bot v20+ returns a coroutine, earlier versions return a Message
            if inspect.iscoroutine(response):
                response = asyncio.run(response)

            return str(getattr(response, "message_id", ""))

        except TelegramError as e:
            raise Exception(f"Failed to send Telegram message: {e}")

    def _format_evaluation_message(self, evaluation, candidate, job_desc):
        """Format the evaluation as a Telegram message."""
        score_emoji = self._get_score_emoji(evaluation.overall_score)
        recommendation_emoji = "✅" if evaluation.recommendation == "interview" else "❌"

        message = f"""
🎯 *New Candidate Evaluation*

*Candidate:* {candidate.name}
*Email:* {candidate.email}
*Position:* {job_desc.title}

{score_emoji} *Overall Score:* {evaluation.overall_score}/10
{recommendation_emoji} *Recommendation:* {evaluation.recommendation.upper()}

"""

        # Add key highlights
        detailed = evaluation.detailed_analysis
        if "key_highlights" in detailed and detailed["key_highlights"]:
            message += "*💡 Key Highlights:*\n"
            for highlight in detailed["key_highlights"][:3]:
                message += f"  • {highlight}\n"
            message += "\n"

        # Add concerns if any
        if "concerns" in detailed and detailed["concerns"]:
            message += "*⚠️ Concerns:*\n"
            for concern in detailed["concerns"][:3]:
                message += f"  • {concern}\n"
            message += "\n"

        # Add skill matches summary
        if "skill_matches" in detailed:
            matched_skills = [
                skill for skill, data in detailed["skill_matches"].items() if data.get("matched")
            ]
            message += f"*✓ Matched Skills:* {len(matched_skills)}/{len(detailed['skill_matches'])}\n\n"

        # Add summary
        if "summary" in detailed:
            message += f"*Summary:*\n{detailed['summary']}\n\n"

        # Add recommendation reasoning
        if "recommendation_reasoning" in detailed:
            message += f"*Reasoning:*\n{detailed['recommendation_reasoning'][:200]}...\n"

        return message

    def _get_score_emoji(self, score):
        """Get emoji based on score."""
        if score >= 9:
            return "🌟"
        elif score >= 7:
            return "⭐"
        elif score >= 5:
            return "👍"
        else:
            return "👎"

    def _create_action_keyboard(self, evaluation_id, candidate_id):
        """Create inline keyboard with action buttons."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Approve", callback_data=f"approve_{evaluation_id}"
                ),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{evaluation_id}"),
            ],
            [
                InlineKeyboardButton(
                    "💬 Add Comment", callback_data=f"comment_{evaluation_id}"
                ),
                InlineKeyboardButton(
                    "📄 View Details", url=f"https://your-app.com/candidates/{candidate_id}"
                ),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    def send_message(self, text, parse_mode=None):
        """Send a simple text message."""
        try:
            response = self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )

            # Handle async API (coroutine) vs sync Message instance
            if inspect.iscoroutine(response):
                response = asyncio.run(response)

            return str(getattr(response, "message_id", ""))
        except TelegramError as e:
            raise Exception(f"Failed to send Telegram message: {e}")

    def handle_callback(self, callback_data, user_id, user_name):
        """
        Handle callback from inline keyboard buttons.

        Args:
            callback_data: str like "approve_123" or "reject_123"
            user_id: Telegram user ID
            user_name: Telegram user display name

        Returns:
            dict with action details
        """
        parts = callback_data.split("_")
        if len(parts) != 2:
            raise ValueError("Invalid callback data format")

        action, evaluation_id = parts

        # Store feedback in database
        from ..models import Evaluation, StakeholderFeedback

        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)

            feedback = StakeholderFeedback.objects.create(
                evaluation=evaluation,
                stakeholder_identifier=str(user_id),
                stakeholder_name=user_name,
                feedback_type=action,  # approve, reject, or comment
                telegram_message_id=f"callback_{callback_data}",
                telegram_chat_id=self.chat_id,
            )

            return {
                "success": True,
                "action": action,
                "evaluation_id": evaluation_id,
                "feedback_id": feedback.id,
            }

        except Evaluation.DoesNotExist:
            raise Exception(f"Evaluation {evaluation_id} not found")

