from fastapi import APIRouter

router = APIRouter()


@router.get("/{deal_id}")
async def get_deal(deal_id: str):
    """Get deal status and details."""
    pass


@router.get("/{deal_id}/trace")
async def get_deal_trace(deal_id: str):
    """Get full audit trail for a deal."""
    pass
