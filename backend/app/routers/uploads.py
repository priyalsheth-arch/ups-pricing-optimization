from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.upload import UploadBatch
from app.models.transaction import Transaction
from app.schemas.upload import UploadBatchSchema, UploadPreviewRow, UploadConfirmResponse, ValidationReport
from app.dependencies import get_current_user
from app.services import csv_ingestion
from app.services.pricing_engine import run_gap_analysis
from app.services.upsell_engine import run_upsell_analysis
import json

router = APIRouter(prefix="/uploads", tags=["uploads"])

# In-memory store for pending CSVs (keyed by batch_id)
_pending_dataframes: dict[int, object] = {}


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    store_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stage a CSV for preview. Returns batch_id + validation report + preview rows."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    file_bytes = await file.read()
    try:
        valid_df, report = csv_ingestion.validate_and_preview(file_bytes, store_id)
    except csv_ingestion.IngestionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Create a pending batch record
    batch = UploadBatch(
        store_id=store_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        row_count=report["valid_rows"],
        status="pending",
        date_range_start=report["date_range_start"],
        date_range_end=report["date_range_end"],
    )
    db.add(batch)
    await db.flush()
    await db.refresh(batch)

    batch_id = batch.id
    _pending_dataframes[batch_id] = valid_df

    preview_rows = csv_ingestion.get_preview_rows(valid_df, limit=50)

    return {
        "batch_id": batch_id,
        "validation_report": report,
        "preview_rows": preview_rows,
        "batch": UploadBatchSchema.model_validate(batch),
    }


@router.post("/{batch_id}/confirm", response_model=UploadConfirmResponse)
async def confirm_upload(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Confirm a staged upload. Persists transactions and triggers analysis."""
    result = await db.execute(select(UploadBatch).where(UploadBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")
    if batch.status == "complete":
        raise HTTPException(status_code=409, detail="Batch already confirmed")

    valid_df = _pending_dataframes.get(batch_id)
    if valid_df is None:
        raise HTTPException(status_code=410, detail="Upload session expired. Please re-upload the file.")

    batch.status = "processing"
    await db.flush()

    try:
        rows_inserted = await csv_ingestion.persist_batch(valid_df, batch.store_id, batch_id, db)
        batch.status = "complete"
        batch.row_count = rows_inserted
        await db.flush()

        # Trigger analysis engines
        await run_gap_analysis(batch.store_id, db)
        await run_upsell_analysis(batch.store_id, db)

        del _pending_dataframes[batch_id]

        return UploadConfirmResponse(
            batch_id=batch_id,
            rows_inserted=rows_inserted,
            status="complete",
            analysis_triggered=True,
        )
    except Exception as e:
        batch.status = "error"
        batch.error_message = str(e)
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.get("/history", response_model=list[UploadBatchSchema])
async def upload_history(
    store_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(UploadBatch).order_by(UploadBatch.uploaded_at.desc()).limit(20)
    if store_id:
        q = q.where(UploadBatch.store_id == store_id)
    elif current_user.role == "staff" and current_user.store_id:
        q = q.where(UploadBatch.store_id == current_user.store_id)
    result = await db.execute(q)
    return result.scalars().all()
