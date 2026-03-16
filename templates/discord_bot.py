"""
Discord Bot Template: Proactive Multi-Agent Architecture

Pattern extracted from Nidzo (Klub Trejdera). Reusable for any Discord bot
that needs channel-based routing, proactive responses, and multiple AI agents.

Architecture:
    Bot Client → Cog (on_message) → Trigger Check → Router → Agent → Response

Key concepts:
    - ChannelBehavior: defines what bot does in each channel
    - Proactive triggers: bot responds based on context, not just mentions
    - Agent routing: classifies intent → dispatches to specialized agent
    - Authority override: specific users can suppress bot (e.g. server owner)
    - Rate limiting: per-user cooldown + per-channel window + daily cap

Usage:
    1. Define your ChannelBehavior enum and channel map
    2. Create agents by subclassing BaseAgent
    3. Configure trigger patterns for each behavior
    4. Set up authority overrides (optional)
    5. Deploy with health check sidecar

Customize for your domain:
    - Change trading_terms to your domain vocabulary
    - Add/modify channel behaviors for your use case
    - Create domain-specific agents
    - Adjust rate limits based on traffic

Dependencies:
    discord.py >= 2.0, anthropic, pydantic-settings, httpx, tenacity
"""

from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

# ============================================================================
# 1. CHANNEL ROUTING
# ============================================================================


class ChannelBehavior(Enum):
    """Defines bot behavior for each channel type.

    Customize these for your domain. Examples:
    - SETUP_VALIDATION → image analysis channels
    - FAQ → question/answer channels
    - CALENDAR → scheduled content channels
    - PASSIVE → only respond on @mention + proactive trading questions
    - SILENT → never respond (announcements, rules, etc.)
    """

    ACTIVE = "active"     # Responds proactively (images, questions, etc.)
    FAQ = "faq"           # Responds to questions
    SCHEDULED = "scheduled"  # Has scheduled posts + manual triggers
    PASSIVE = "passive"   # @mention + detected relevant questions
    SILENT = "silent"     # Never responds


# Map channel IDs to behaviors
CHANNEL_MAP: dict[int, ChannelBehavior] = {
    # Example:
    # 123456789: ChannelBehavior.ACTIVE,
    # 987654321: ChannelBehavior.FAQ,
}

# Roles allowed to interact with the bot
ALLOWED_ROLES: set[int] = set()

# Users the bot defers to (e.g. server owner)
AUTHORITY_USER_IDS: set[int] = set()


def get_channel_behavior(channel_id: int) -> ChannelBehavior:
    return CHANNEL_MAP.get(channel_id, ChannelBehavior.PASSIVE)


def has_allowed_role(role_ids: set[int]) -> bool:
    if not ALLOWED_ROLES:
        return True  # No role restriction
    return bool(role_ids & ALLOWED_ROLES)


# ============================================================================
# 2. RATE LIMITING
# ============================================================================


class RateLimiter:
    """Per-user cooldown + per-channel window + daily global cap."""

    def __init__(
        self,
        user_cooldown: int = 60,
        channel_max_per_window: int = 3,
        channel_window: int = 300,
        daily_limit: int = 200,
    ) -> None:
        self._user_last: dict[str, float] = {}
        self._channel_hits: dict[str, list[float]] = defaultdict(list)
        self._daily_count = 0
        self._daily_reset = time.time() + 86400
        self._user_cooldown = user_cooldown
        self._channel_max = channel_max_per_window
        self._channel_window = channel_window
        self._daily_limit = daily_limit

    def check(self, user_id: str, channel_id: str) -> bool:
        now = time.monotonic()

        if self._daily_count >= self._daily_limit:
            return False

        if user_id in self._user_last:
            if now - self._user_last[user_id] < self._user_cooldown:
                return False

        hits = self._channel_hits[channel_id]
        cutoff = now - self._channel_window
        self._channel_hits[channel_id] = [t for t in hits if t > cutoff]
        if len(self._channel_hits[channel_id]) >= self._channel_max:
            return False

        self._user_last[user_id] = now
        self._channel_hits[channel_id].append(now)
        self._daily_count += 1
        return True


# ============================================================================
# 3. MODELS
# ============================================================================


@dataclass
class BotContext:
    """All info about the incoming message."""

    user_id: str
    username: str
    channel_id: str
    channel_name: str
    message_content: str
    image_urls: list[str]


@dataclass
class BotResponse:
    """Agent output."""

    content: str
    agent_type: str = "general"
    tokens_used: int = 0
    duration_ms: int = 0


# ============================================================================
# 4. AGENTS
# ============================================================================


class BaseAgent(ABC):
    @abstractmethod
    async def process(self, context: BotContext) -> BotResponse:
        """Process message and return response."""
        ...


# ============================================================================
# 5. PROACTIVE TRIGGER DETECTION
# ============================================================================


class TriggerDetector:
    """Configurable trigger detection for proactive responses.

    Override these methods for your domain.
    """

    # Domain-specific vocabulary for proactive detection
    DOMAIN_TERMS: tuple[str, ...] = ()

    # Question starters in your language
    QUESTION_STARTERS: tuple[str, ...] = (
        "what ", "how ", "why ", "can ", "is ",
    )

    # Request patterns
    REQUEST_PATTERNS: tuple[str, ...] = (
        "explain", "help", "tell me",
    )

    @classmethod
    def has_question(cls, content: str) -> bool:
        if not content:
            return False
        lower = content.lower()
        if "?" in lower:
            return True
        if any(lower.startswith(kw) for kw in cls.QUESTION_STARTERS):
            return True
        return any(kw in lower for kw in cls.REQUEST_PATTERNS)

    @classmethod
    def has_domain_question(cls, content: str) -> bool:
        """Question + domain term = proactive response in passive channels."""
        if not content or len(content) < 20:
            return False
        lower = content.lower()
        has_q = "?" in lower or any(
            lower.startswith(kw) for kw in cls.QUESTION_STARTERS
        )
        if not has_q:
            return False
        return any(term in lower for term in cls.DOMAIN_TERMS)

    @classmethod
    def has_image(cls, message: discord.Message) -> bool:
        return any(
            a.content_type and a.content_type.startswith("image/")
            for a in message.attachments
        )


# ============================================================================
# 6. MESSAGE HANDLER COG
# ============================================================================


class ProactiveCog(commands.Cog):
    """Base cog with proactive response logic.

    Subclass and override:
    - _get_agents() to return your agent mapping
    - _classify_intent() to route messages
    - trigger_detector class attribute
    """

    trigger_detector: type[TriggerDetector] = TriggerDetector
    rate_limiter: RateLimiter = RateLimiter()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not getattr(self.bot, "enabled", True):
            return

        behavior = get_channel_behavior(message.channel.id)
        is_mentioned = (
            self.bot.user is not None
            and self.bot.user.mentioned_in(message)
        )

        # Authority override
        if message.author.id in AUTHORITY_USER_IDS and not is_mentioned:
            return

        # Check if should respond based on channel behavior
        should_respond = self._should_respond(
            message, behavior, is_mentioned,
        )
        if not should_respond:
            return

        # Role check
        if message.guild:
            roles = {role.id for role in message.author.roles}
            if not has_allowed_role(roles):
                return

        # Rate limit
        if not self.rate_limiter.check(
            str(message.author.id), str(message.channel.id),
        ):
            return

        # Build context and respond
        context = self._build_context(message)
        async with message.channel.typing():
            response = await self._process(context, behavior)

        await message.reply(response.content)

    def _should_respond(
        self,
        message: discord.Message,
        behavior: ChannelBehavior,
        is_mentioned: bool,
    ) -> bool:
        td = self.trigger_detector

        if behavior == ChannelBehavior.SILENT:
            return False

        if behavior == ChannelBehavior.ACTIVE:
            if is_mentioned or td.has_image(message):
                return True
            return td.has_question(message.content)

        if behavior == ChannelBehavior.FAQ:
            return is_mentioned or td.has_question(message.content)

        if behavior == ChannelBehavior.SCHEDULED:
            return is_mentioned or td.has_question(message.content)

        # PASSIVE: mention or domain-specific question
        if is_mentioned:
            return True
        return td.has_domain_question(message.content)

    def _build_context(self, message: discord.Message) -> BotContext:
        image_urls = [
            a.url for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]
        return BotContext(
            user_id=str(message.author.id),
            username=message.author.display_name,
            channel_id=str(message.channel.id),
            channel_name=getattr(message.channel, "name", "unknown"),
            message_content=message.content,
            image_urls=image_urls,
        )

    async def _process(
        self, context: BotContext, behavior: ChannelBehavior,
    ) -> BotResponse:
        """Override this to add your agent routing logic."""
        return BotResponse(content="Override _process() in your subclass")


# ============================================================================
# 7. BOT CLIENT
# ============================================================================


class ProactiveBot(commands.Bot):
    """Base bot with standard intents and health check."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.enabled: bool = True

    async def on_ready(self) -> None:
        if self.user:
            logger.info("Bot ready: %s (ID: %s)", self.user.name, self.user.id)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
#
# class TradingTrigger(TriggerDetector):
#     DOMAIN_TERMS = ("forex", "setup", "chart", "entry", "stop loss", ...)
#     QUESTION_STARTERS = ("sta ", "kako ", "koliko ", "zasto ", ...)
#     REQUEST_PATTERNS = ("objasnite", "objasni", "pomozi", ...)
#
# class TradingCog(ProactiveCog):
#     trigger_detector = TradingTrigger
#
#     async def _process(self, context, behavior):
#         intent = await classify_intent(context)
#         if intent == "setup":
#             return await setup_agent.process(context)
#         elif intent == "faq":
#             return await faq_agent.process(context)
#         return await general_agent.process(context)
