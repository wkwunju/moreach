"""
Streaming Reddit Polling Service

SSE-enabled polling service that yields events during the polling process.
Thin adapter over the unified PollEngine.
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.orm import Session

from app.models.tables import RedditLead
from app.services.reddit.poll_engine import PollEngine, PollEngineCallbacks, run_poll_sync


logger = logging.getLogger(__name__)


class StreamingSSECallbacks(PollEngineCallbacks):
    """Converts PollEngine callbacks into SSE event dicts via an asyncio.Queue."""

    def __init__(self):
        self.events: asyncio.Queue = asyncio.Queue()

    async def on_progress(self, phase: str, current: int, total: int,
                          message: str, **extra) -> None:
        await self.events.put({
            "type": "progress",
            "data": {"phase": phase, "current": current, "total": total,
                     "message": message, **extra}
        })

    async def on_lead_created(self, lead: RedditLead) -> None:
        await self.events.put({
            "type": "lead",
            "data": {
                "id": lead.id,
                "title": lead.title[:100],
                "relevancy_score": lead.relevancy_score,
                "subreddit_name": lead.subreddit_name,
                "has_suggestions": lead.has_suggestions,
                "author": lead.author,
            }
        })

    async def on_complete(self, stats: Dict[str, Any]) -> None:
        await self.events.put({"type": "complete", "data": stats})

    async def on_error(self, message: str) -> None:
        await self.events.put({"type": "error", "data": {"message": message}})


# Sentinel to signal the engine task is done
_DONE = object()


class StreamingPollService:
    """
    Streaming poll service that yields SSE events during polling.

    Event types:
    - progress: {"phase": "fetching"|"scoring"|"suggestions", "current": N, "total": M, ...}
    - lead: {"id": N, "title": "...", "relevancy_score": 90, ...}
    - complete: {"total_leads": N, "total_posts_fetched": M, "summary": {...}}
    - error: {"message": "..."}
    """

    def __init__(self):
        self.engine = PollEngine()

    async def poll_campaign_streaming(
        self,
        db: Session,
        campaign_id: int,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Poll campaign with streaming progress updates.
        Delegates to PollEngine and converts callbacks to SSE events.
        """
        callbacks = StreamingSSECallbacks()

        async def run_engine():
            try:
                await self.engine.run_poll(
                    db, campaign_id, trigger="manual", callbacks=callbacks
                )
            except Exception as e:
                # Error already emitted via callbacks.on_error in PollEngine
                logger.error(f"Engine error: {e}")
            finally:
                await callbacks.events.put(_DONE)

        task = asyncio.create_task(run_engine())

        while True:
            try:
                event = await asyncio.wait_for(callbacks.events.get(), timeout=1.0)
                if event is _DONE:
                    break
                yield event
            except asyncio.TimeoutError:
                if task.done():
                    # Drain remaining events
                    while not callbacks.events.empty():
                        event = callbacks.events.get_nowait()
                        if event is not _DONE:
                            yield event
                    break


# Synchronous wrapper for non-SSE usage (background tasks, non-SSE endpoints)
def poll_campaign_with_batch_scoring(db: Session, campaign_id: int) -> Dict[str, Any]:
    """
    Non-streaming version of the batch scoring poll.
    Used for background tasks or non-SSE endpoints.
    """
    poll_job = run_poll_sync(db, campaign_id, trigger="manual")
    return {
        "total_leads": poll_job.leads_created,
        "total_posts_fetched": poll_job.posts_fetched,
        "subreddits_polled": poll_job.subreddits_polled,
        "message": f"Created {poll_job.leads_created} new leads from {poll_job.posts_fetched} posts",
    }
