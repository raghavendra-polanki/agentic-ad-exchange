from fastapi import APIRouter

router = APIRouter()


@router.post("/deals/{deal_id}/content")
async def submit_content(deal_id: str):
    """Supply agent submits generated content for validation."""
    pass
