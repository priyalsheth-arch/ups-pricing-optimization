from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.store import Store
from app.schemas.store import StoreSchema
from app.dependencies import get_current_user

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreSchema])
async def list_stores(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "admin":
        result = await db.execute(select(Store))
    elif current_user.role == "manager":
        result = await db.execute(select(Store))
    else:
        # Staff see only their assigned store
        if current_user.store_id is None:
            return []
        result = await db.execute(select(Store).where(Store.id == current_user.store_id))
    return result.scalars().all()


@router.get("/{store_id}", response_model=StoreSchema)
async def get_store(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    # Staff can only view their own store
    if current_user.role == "staff" and current_user.store_id != store_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return store
