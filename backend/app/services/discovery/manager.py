import json
import logging
from sqlalchemy import select

from app.core.config import settings
from app.models.tables import Request, RequestResult, RequestStatus, Influencer
from app.services.discovery.search import DiscoverySearch
from app.workers.tasks import run_discovery


logger = logging.getLogger(__name__)


class DiscoveryManager:
    def __init__(self):
        self.search_service = DiscoverySearch()

    def create_request(self, db, description: str, constraints: str) -> Request:
        logger.info("Create request")
        request = Request(description=description, constraints=constraints)
        db.add(request)
        db.commit()
        db.refresh(request)

        intent, embedding, matches = self.search_service.search(description, constraints, top_k=12)
        request.intent = intent
        request.query_embedding = json.dumps(embedding) if embedding else ""
        request.status = RequestStatus.PARTIAL
        db.commit()

        self._store_results(db, request, matches)

        if len(matches) < settings.min_search_results:
            logger.info("Insufficient results (%s). Enqueue discovery job.", len(matches))
            run_discovery.delay(request.id)
            request.status = RequestStatus.PROCESSING
            db.commit()

        return request

    def _store_results(self, db, request: Request, matches: list[dict]) -> None:
        """
        Store search results by creating RequestResult entries.
        
        IMPORTANT: This method does NOT create or update Influencer records.
        It only stores references (handle -> score/rank mapping).
        
        SQLite is the single source of truth for influencer data.
        Pinecone is only used for search (returns handle + score).
        """
        db.query(RequestResult).filter(RequestResult.request_id == request.id).delete()
        db.commit()

        stored_count = 0
        skipped_count = 0
        
        for rank, match in enumerate(matches, start=1):
            # Get handle from Pinecone match
            handle = match.get("id")
            if not handle:
                logger.warning(f"Skipping match with no handle/id: {match.keys()}")
                skipped_count += 1
                continue
            
            # Look up influencer in SQLite (do NOT create from Pinecone metadata)
            influencer = db.execute(
                select(Influencer).where(Influencer.handle == handle)
            ).scalar_one_or_none()
            
            if not influencer:
                # This influencer exists in Pinecone but not in SQLite
                # This indicates data inconsistency
                logger.warning(
                    f"Influencer @{handle} found in Pinecone (score: {match.get('score', 0):.3f}) "
                    f"but not in SQLite. Skipping. Run async discovery to fetch this profile."
                )
                skipped_count += 1
                # TODO: Optionally trigger async task to scrape this profile
                # from app.workers.tasks import scrape_influencer
                # scrape_influencer.delay(handle)
                continue
            
            # Create result reference (only stores relationship + score + rank)
            result = RequestResult(
                request_id=request.id,
                influencer_id=influencer.id,
                score=float(match.get("score", 0)),
                rank=rank - skipped_count,  # Adjust rank for skipped entries
            )
            db.add(result)
            stored_count += 1
        
        db.commit()
        logger.info(
            f"Stored {stored_count} results for request {request.id}. "
            f"Skipped {skipped_count} due to missing SQLite entries."
        )
