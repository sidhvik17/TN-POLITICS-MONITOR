from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
def generate_report(body: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report_type = body.get("type", "executive_summary")
    date_from = body.get("date_from")
    date_to = body.get("date_to")
    district = body.get("district")
    output_format = body.get("format", "pdf")

    # Mock report generation
    report_id = f"RPT-{report_type[:3].upper()}-2026-{hash(str(body)) % 10000:04d}"

    return {
        "id": report_id,
        "status": "completed",
        "type": report_type,
        "generated_at": "2026-02-19T10:00:00Z",
        "parameters": {
            "date_from": date_from,
            "date_to": date_to,
            "district": district,
            "format": output_format
        },
        "message": f"Report '{report_type}' generated successfully",
        "download_url": f"/api/reports/{report_id}/download"
    }


@router.get("")
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock recent reports
    return {
        "data": [
            {
                "id": "RPT-EXE-2026-0001",
                "type": "executive_summary",
                "title": "Weekly Summary Feb 12-18",
                "format": "pdf",
                "generated_at": "2026-02-19T10:00:00Z",
                "generated_by": "priya_analyst",
                "size_kb": 245
            },
            {
                "id": "RPT-DIS-2026-0002",
                "type": "district_analysis",
                "title": "Chennai District Analysis",
                "format": "xlsx",
                "generated_at": "2026-02-18T15:30:00Z",
                "generated_by": "priya_analyst",
                "size_kb": 512
            },
            {
                "id": "RPT-MCC-2026-0003",
                "type": "topic_deep_dive",
                "title": "MCC Violations Report",
                "format": "pdf",
                "generated_at": "2026-02-17T11:00:00Z",
                "generated_by": "admin123",
                "size_kb": 189
            },
            {
                "id": "RPT-AUD-2026-0004",
                "type": "alert_audit",
                "title": "Alert Response Audit - Week 7",
                "format": "pdf",
                "generated_at": "2026-02-16T09:00:00Z",
                "generated_by": "priya_analyst",
                "size_kb": 334
            },
            {
                "id": "RPT-PAR-2026-0005",
                "type": "party_comparison",
                "title": "Party Sentiment Comparison Q1",
                "format": "pptx",
                "generated_at": "2026-02-15T14:00:00Z",
                "generated_by": "priya_analyst",
                "size_kb": 678
            }
        ]
    }
