"""
Simple usage tracking service.
Tracks API calls per user for ROI calculation and scam detection.
"""
import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func

from app.models.tables import UsageTracking, APIType

logger = logging.getLogger(__name__)


def track_api_call(
    db: Session,
    user_id: int,
    api_type: APIType,
    input_tokens: int = 0,
    output_tokens: int = 0
) -> None:
    """
    Track an API call for a user.
    Uses upsert to increment counter if record exists for today.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        # Check if record exists for today
        existing = db.query(UsageTracking).filter(
            UsageTracking.user_id == user_id,
            UsageTracking.api_type == api_type,
            UsageTracking.date == today
        ).first()

        if existing:
            existing.call_count += 1
            existing.input_tokens += input_tokens
            existing.output_tokens += output_tokens
        else:
            new_record = UsageTracking(
                user_id=user_id,
                api_type=api_type,
                date=today,
                call_count=1,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            db.add(new_record)

        db.commit()
    except Exception as e:
        logger.error(f"Failed to track usage for user {user_id}: {e}")
        db.rollback()


def get_user_usage_summary(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """
    Get usage summary for a user within date range.
    Returns dict with counts per API type.
    """
    query = db.query(
        UsageTracking.api_type,
        func.sum(UsageTracking.call_count).label('total_calls'),
        func.sum(UsageTracking.input_tokens).label('total_input_tokens'),
        func.sum(UsageTracking.output_tokens).label('total_output_tokens')
    ).filter(UsageTracking.user_id == user_id)

    if start_date:
        query = query.filter(UsageTracking.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(UsageTracking.date <= datetime.combine(end_date, datetime.max.time()))

    query = query.group_by(UsageTracking.api_type)

    results = query.all()

    summary = {}
    for row in results:
        summary[row.api_type.value] = {
            'calls': row.total_calls or 0,
            'input_tokens': row.total_input_tokens or 0,
            'output_tokens': row.total_output_tokens or 0
        }

    return summary


def get_all_users_usage(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list:
    """
    Get usage summary for all users (admin view).
    Returns list of users with their usage stats.
    """
    query = db.query(
        UsageTracking.user_id,
        func.sum(UsageTracking.call_count).label('total_calls'),
        func.sum(UsageTracking.input_tokens).label('total_input_tokens'),
        func.sum(UsageTracking.output_tokens).label('total_output_tokens')
    )

    if start_date:
        query = query.filter(UsageTracking.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(UsageTracking.date <= datetime.combine(end_date, datetime.max.time()))

    query = query.group_by(UsageTracking.user_id).order_by(func.sum(UsageTracking.call_count).desc())

    results = query.all()

    return [
        {
            'user_id': row.user_id,
            'total_calls': row.total_calls or 0,
            'total_input_tokens': row.total_input_tokens or 0,
            'total_output_tokens': row.total_output_tokens or 0
        }
        for row in results
    ]
