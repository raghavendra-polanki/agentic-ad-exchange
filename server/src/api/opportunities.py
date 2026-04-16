from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def signal_opportunity():
    """Supply agent signals a new opportunity on the exchange."""
    pass


@router.post("/{opportunity_id}/propose")
async def submit_proposal(opportunity_id: str):
    """Demand agent submits a proposal for an opportunity."""
    pass


@router.post("/{opportunity_id}/pass")
async def pass_opportunity(opportunity_id: str):
    """Demand agent declines an opportunity."""
    pass
