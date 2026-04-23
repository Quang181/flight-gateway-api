from fastapi import APIRouter, Depends

from app.application.use_cases.get_offer_detail import GetOfferDetail
from app.entrypoints.api.decorators import require_token
from app.entrypoints.api.dependencies import get_offer_detail_use_case
from app.entrypoints.api.routers.flight.offer.schema import OfferDetailResponse

router = APIRouter(prefix="/flight/offers")


@router.get("/{offer_id}", response_model=OfferDetailResponse)
# @require_token
async def get_offer_detail(
    offer_id: str,
    use_case: GetOfferDetail = Depends(get_offer_detail_use_case),
) -> OfferDetailResponse:
    detail_offer = await use_case.execute(offer_id=offer_id)
    response = OfferDetailResponse(**detail_offer)
    return response
