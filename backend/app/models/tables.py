"""
SQLAlchemy ORM models.
Schema matches §4 of the architecture doc exactly — generic from day one.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey, ForeignKeyConstraint,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SourceType(str, enum.Enum):
    """Supported content source types. New types require a matching fetcher in services/fetcher.py."""
    rss = "rss"
    youtube = "youtube"
    reddit = "reddit"
    html = "html"


class FeedbackSignal(str, enum.Enum):
    """User feedback signals recorded per briefing item. Used in later phases to personalize ranking."""
    more_like_this = "more_like_this"
    less_like_this = "less_like_this"
    not_interested = "not_interested"
    saved = "saved"


class User(Base):
    """A registered user, identified solely by email — no password auth in Phase 1."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topics: Mapped[list["Topic"]] = relationship(back_populates="user")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="user")


class Topic(Base):
    """A research topic owned by a user that groups one or more content sources."""
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="topics")
    sources: Mapped[list["Source"]] = relationship(back_populates="topic")
    briefings: Mapped[list["Briefing"]] = relationship(back_populates="topic")


class Source(Base):
    """A single content feed (RSS, YouTube channel, etc.) attached to a topic."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    topic: Mapped["Topic"] = relationship(back_populates="sources")
    items: Mapped[list["Item"]] = relationship(back_populates="source")


class Item(Base):
    """A single piece of content fetched from a source. Deduplicated by (source_id, external_id)."""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["Source"] = relationship(back_populates="items")
    briefing_items: Mapped[list["BriefingItem"]] = relationship(back_populates="item")


class Briefing(Base):
    """A digest email generated and sent for one topic. Records cost and model for accounting."""
    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str] = mapped_column(String(100), default="")
    total_cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    topic: Mapped["Topic"] = relationship(back_populates="briefings")
    briefing_items: Mapped[list["BriefingItem"]] = relationship(back_populates="briefing")


class BriefingItem(Base):
    """Junction between a briefing and each item it contains, storing the per-item summary, rank, and LLM reasoning."""
    __tablename__ = "briefing_items"

    briefing_id: Mapped[int] = mapped_column(ForeignKey("briefings.id", ondelete="CASCADE"), primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")

    briefing: Mapped["Briefing"] = relationship(back_populates="briefing_items")
    item: Mapped["Item"] = relationship(back_populates="briefing_items")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="briefing_item")


class Feedback(Base):
    """Explicit user signal on a specific briefing item, used in later phases to tune ranking."""
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    briefing_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    signal: Mapped[FeedbackSignal] = mapped_column(Enum(FeedbackSignal), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["briefing_id", "item_id"],
            ["briefing_items.briefing_id", "briefing_items.item_id"],
            ondelete="CASCADE",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="feedback")
    briefing_item: Mapped["BriefingItem"] = relationship(back_populates="feedback")


class LlmLog(Base):
    """Every Anthropic API call is recorded here from day one — §8 observability."""
    __tablename__ = "llm_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    calling_function: Mapped[str] = mapped_column(String(255), default="")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    prompt: Mapped[str] = mapped_column(Text, default="")
    response: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
