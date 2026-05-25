"""
GreenOps — Export Routes

GET /api/export/csv — Export user's API calls to a CSV file.
"""

import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from database import stream_csv_calls
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
def export_csv(user=Depends(get_current_user)):
    """
    Export all API calls for the authenticated user as a CSV file.
    Streams directly from the database to prevent memory crashes.
    """
    return StreamingResponse(
        stream_csv_calls(user["id"]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=greenops_export_{user['name'].replace(' ', '_').lower()}.csv"
        }
    )
