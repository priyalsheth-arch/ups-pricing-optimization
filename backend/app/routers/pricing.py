from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from app.database import get_db
from app.models.pricing import OurPrice, CompetitorPrice
from app.schemas.pricing import (
    OurPriceSchema, OurPriceCreate,
    CompetitorPriceSchema, CompetitorPriceCreate,
)
from app.dependencies import get_current_user, require_manager

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/our", response_model=list[OurPriceSchema])
async def list_our_prices(
    store_id: int | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(OurPrice).order_by(OurPrice.effective_date.desc())
    if store_id:
        q = q.where(OurPrice.store_id == store_id)
    if category:
        q = q.where(OurPrice.service_category == category)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/our", response_model=OurPriceSchema)
async def upsert_our_price(
    data: OurPriceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    existing = await db.execute(
        select(OurPrice).where(
            and_(
                OurPrice.store_id == data.store_id,
                OurPrice.service_code == data.service_code,
                OurPrice.effective_date == data.effective_date,
            )
        )
    )
    obj = existing.scalar_one_or_none()
    if obj:
        obj.price = data.price
        obj.notes = data.notes
        obj.updated_by = current_user.id
    else:
        obj = OurPrice(**data.model_dump(), updated_by=current_user.id)
        db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/competitors", response_model=list[CompetitorPriceSchema])
async def list_competitor_prices(
    category: str | None = None,
    competitor: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(CompetitorPrice).order_by(CompetitorPrice.updated_at.desc())
    if category:
        q = q.where(CompetitorPrice.service_category == category)
    if competitor:
        q = q.where(CompetitorPrice.competitor_name == competitor)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/competitors", response_model=CompetitorPriceSchema)
async def upsert_competitor_price(
    data: CompetitorPriceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    existing = await db.execute(
        select(CompetitorPrice).where(
            and_(
                CompetitorPrice.competitor_name == data.competitor_name,
                CompetitorPrice.service_code == data.service_code,
                CompetitorPrice.effective_date == data.effective_date,
            )
        )
    )
    obj = existing.scalar_one_or_none()
    if obj:
        obj.price = data.price
        obj.source_notes = data.source_notes
        obj.entered_by = current_user.id
    else:
        obj = CompetitorPrice(**data.model_dump(), entered_by=current_user.id)
        db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/competitors/{price_id}")
async def delete_competitor_price(
    price_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(select(CompetitorPrice).where(CompetitorPrice.id == price_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(obj)
    return {"deleted": True}
