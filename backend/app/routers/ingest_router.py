"""
Ingest router — /api/ingest/sms, /statement, /demo, /transactions (§5).
Parses input, runs the full detection pipeline, and stores results.

Data model:
  - Demo: Every load wipes ALL user data, loads fresh sample. Fully isolated.
  - User (SMS/Upload): Appends transactions. Subscriptions rebuilt from ALL user txns.
  - Transactions API: View, delete individual, or clear all.
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId

from app.database import get_database
from app.auth import get_current_user
from app.services.extraction_service import parse_sms_text, parse_csv_statement, parse_pdf_statement
from app.services.merchant_normalizer import normalize_merchant, group_merchants, categorize_merchant
from app.services.recurring_detector import detect_recurring
from app.services.price_anomaly import detect_price_hikes, build_price_history, get_max_price_increase_pct
from app.services.recommendation import generate_full_recommendation
from app.utils.validators import validate_file_size, sanitize_text
from app.config import settings

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


class SMSIngestRequest(BaseModel):
    raw_text: str


class DemoIngestRequest(BaseModel):
    dataset_id: str = "sample_sms_1"


class IngestResponse(BaseModel):
    transactions_parsed: int
    subscriptions_detected: int
    message: str


class TransactionOut(BaseModel):
    id: str
    merchant_raw: str
    merchant_normalized: str
    amount: float
    currency: str
    date: Optional[str] = None
    source_type: str
    category: str


class TransactionListResponse(BaseModel):
    transactions: List[TransactionOut]
    total: int


# ── Shared Helpers ───────────────────────────────────────────────────

async def _wipe_all_user_data(user_id: str, db):
    """
    Nuclear wipe: remove ALL data for a user (transactions, subscriptions,
    leak_scores, price_history, actions). Used by demo and clear-all.
    """
    user_oid = ObjectId(user_id)

    # Cascade: get subscription IDs first, then delete children, then parents
    sub_ids = [s["_id"] async for s in db.subscriptions.find({"user_id": user_oid}, {"_id": 1})]
    if sub_ids:
        await db.leak_scores.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.price_history.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.actions.delete_many({"subscription_id": {"$in": sub_ids}})
    await db.subscriptions.delete_many({"user_id": user_oid})
    await db.transactions.delete_many({"user_id": user_oid})


async def _rebuild_subscriptions(user_id: str, db) -> int:
    """
    Rebuild subscriptions from ALL stored transactions for this user.
    1. Fetch all transactions from DB
    2. Run recurring detection
    3. Cascade-delete old subscriptions + scores + history
    4. Insert new subscriptions + scores + history
    Returns: number of subscriptions detected
    """
    user_oid = ObjectId(user_id)

    # Fetch all stored transactions
    all_txns = [t async for t in db.transactions.find({"user_id": user_oid})]

    if not all_txns:
        # No transactions → wipe any stale subscriptions
        sub_ids = [s["_id"] async for s in db.subscriptions.find({"user_id": user_oid}, {"_id": 1})]
        if sub_ids:
            await db.leak_scores.delete_many({"subscription_id": {"$in": sub_ids}})
            await db.price_history.delete_many({"subscription_id": {"$in": sub_ids}})
            await db.actions.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.subscriptions.delete_many({"user_id": user_oid})
        return 0

    # Run detection
    recurring = detect_recurring(all_txns)

    # Cascade-delete old subscription data
    sub_ids = [s["_id"] async for s in db.subscriptions.find({"user_id": user_oid}, {"_id": 1})]
    if sub_ids:
        await db.leak_scores.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.price_history.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.actions.delete_many({"subscription_id": {"$in": sub_ids}})
    await db.subscriptions.delete_many({"user_id": user_oid})

    if not recurring:
        return 0

    # Insert new subscriptions
    sub_docs = []
    for sub in recurring:
        sub_doc = {
            "user_id": user_oid,
            "merchant_normalized": sub["merchant_normalized"],
            "category": sub.get("category", categorize_merchant(sub["merchant_normalized"])),
            "frequency": sub["frequency"],
            "first_seen": sub["first_seen"],
            "last_seen": sub["last_seen"],
            "current_amount": sub["current_amount"],
            "currency": sub.get("currency", "INR"),
            "status": "active",
        }
        result = await db.subscriptions.insert_one(sub_doc)
        sub_doc["_id"] = result.inserted_id
        sub_doc["amounts"] = sub.get("amounts", [])
        sub_doc["dates"] = sub.get("dates", [])
        sub_docs.append(sub_doc)

    # Price history
    for sub_doc in sub_docs:
        amounts = sub_doc.get("amounts", [])
        dates = sub_doc.get("dates", [])
        if amounts and dates:
            price_history = build_price_history(amounts, dates)
            for ph in price_history:
                await db.price_history.insert_one({
                    "subscription_id": sub_doc["_id"],
                    "amount": ph["amount"],
                    "effective_date": ph["effective_date"],
                })

    # Leak scores
    all_subs_for_scoring = [
        {
            "merchant_normalized": s["merchant_normalized"],
            "category": s.get("category", "other"),
            "current_amount": s["current_amount"],
            "last_seen": s["last_seen"],
            "status": s.get("status", "active"),
            "amounts": s.get("amounts", []),
        }
        for s in sub_docs
    ]

    for sub_doc in sub_docs:
        score_input = {
            "merchant_normalized": sub_doc["merchant_normalized"],
            "category": sub_doc.get("category", "other"),
            "current_amount": sub_doc["current_amount"],
            "last_seen": sub_doc["last_seen"],
            "status": sub_doc.get("status", "active"),
            "amounts": sub_doc.get("amounts", []),
        }

        rec = await generate_full_recommendation(score_input, all_subs_for_scoring)

        await db.leak_scores.insert_one({
            "subscription_id": sub_doc["_id"],
            "score": rec["score"],
            "components": rec["components"],
            "recommendation": rec["recommendation"],
            "reason": rec["reason"],
            "dark_pattern": rec.get("dark_pattern"),
            "computed_at": datetime.now(timezone.utc),
        })

    return len(sub_docs)


async def _normalize_and_store_transactions(
    transactions: list[dict], user_id: str, db
) -> int:
    """
    Normalize merchant names, store transactions in DB.
    Returns: number of transactions stored.
    """
    if not transactions:
        return 0

    # Normalize merchant names
    for txn in transactions:
        txn["merchant_normalized"] = normalize_merchant(txn.get("merchant", txn.get("merchant_raw", "")))
        txn["merchant_raw"] = txn.get("merchant", txn.get("merchant_raw", ""))

    # Group by fuzzy matching
    all_normalized = [txn["merchant_normalized"] for txn in transactions if txn["merchant_normalized"]]
    canonical_map = group_merchants(all_normalized)

    for txn in transactions:
        original = txn["merchant_normalized"]
        txn["merchant_normalized"] = canonical_map.get(original, original)
        txn["category"] = categorize_merchant(txn["merchant_normalized"])

    # Store in DB
    txn_docs = []
    for txn in transactions:
        txn_docs.append({
            "user_id": ObjectId(user_id),
            "raw_text": txn.get("raw_text", "")[:500],
            "merchant_raw": txn.get("merchant_raw", ""),
            "merchant_normalized": txn["merchant_normalized"],
            "amount": txn["amount"],
            "currency": txn.get("currency", "INR"),
            "date": txn["date"],
            "source_type": txn.get("source_type", "sms"),
            "is_explicit_setup": txn.get("is_explicit_setup", False),
            "category": txn.get("category", "other"),
        })

    if txn_docs:
        await db.transactions.insert_many(txn_docs)

    return len(txn_docs)


# ── Ingest Endpoints ─────────────────────────────────────────────────

@router.post("/sms", response_model=IngestResponse)
async def ingest_sms(
    request: SMSIngestRequest,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Parse pasted SMS text and APPEND to user's transaction history.
    Then rebuild subscriptions from ALL accumulated transactions.
    """
    sanitized = sanitize_text(request.raw_text)
    if not sanitized:
        raise HTTPException(status_code=400, detail="No text provided")

    transactions = await parse_sms_text(sanitized)

    user_id = str(current_user["_id"])
    stored_count = await _normalize_and_store_transactions(transactions, user_id, db)
    sub_count = await _rebuild_subscriptions(user_id, db)

    return IngestResponse(
        transactions_parsed=stored_count,
        subscriptions_detected=sub_count,
        message=f"Successfully parsed {stored_count} transactions and detected {sub_count} recurring subscriptions.",
    )


@router.post("/statement", response_model=IngestResponse)
async def ingest_statement(
    file: UploadFile = File(...),
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Parse uploaded CSV/PDF bank statement and APPEND to user's transaction history.
    Then rebuild subscriptions from ALL accumulated transactions.
    """
    content = await file.read()
    if not validate_file_size(len(content)):
        raise HTTPException(status_code=400, detail=f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB")

    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    import base64
    from app.services.groq_client import extract_transaction_from_image

    if ext == "csv":
        transactions = parse_csv_statement(content.decode("utf-8", errors="replace"))
        for txn in transactions:
            txn["source_type"] = "statement"
    elif ext == "pdf":
        transactions = parse_pdf_statement(content)
        for txn in transactions:
            txn["source_type"] = "statement"
    elif ext in ["png", "jpg", "jpeg"]:
        mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"
        base64_img = base64.b64encode(content).decode("utf-8")
        transactions = await extract_transaction_from_image(base64_img, mime_type)
        for txn in transactions:
            txn["source_type"] = "screenshot"
            txn["is_explicit_setup"] = True
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV, PDF, or Image file (PNG/JPG).")

    user_id = str(current_user["_id"])
    stored_count = await _normalize_and_store_transactions(transactions, user_id, db)
    sub_count = await _rebuild_subscriptions(user_id, db)

    return IngestResponse(
        transactions_parsed=stored_count,
        subscriptions_detected=sub_count,
        message=f"Successfully parsed {stored_count} transactions and detected {sub_count} recurring subscriptions.",
    )


@router.post("/demo", response_model=IngestResponse)
async def ingest_demo(
    request: DemoIngestRequest,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Load a bundled sample dataset.
    ALWAYS wipes ALL user data first for a completely fresh demo experience.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_datasets")

    dataset_files = {
        "sample_sms_1": "sample_sms_1.txt",
        "sample_sms_2": "sample_sms_2.txt",
        "sample_statement_1": "sample_statement_1.csv",
    }

    filename = dataset_files.get(request.dataset_id)
    if not filename:
        raise HTTPException(status_code=400, detail=f"Unknown dataset: {request.dataset_id}")

    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail=f"Sample dataset file not found: {filename}")

    user_id = str(current_user["_id"])

    # WIPE everything for a clean demo
    await _wipe_all_user_data(user_id, db)

    # Parse the sample file
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if filename.endswith(".csv"):
        transactions = parse_csv_statement(content)
        for txn in transactions:
            txn["source_type"] = "statement"
    else:
        # For demo, use regex-only parsing (no Groq dependency)
        from app.services.extraction_service import parse_sms_line
        transactions = []
        for line in content.strip().split("\n"):
            parsed = parse_sms_line(line.strip())
            if parsed and parsed.get("merchant") and parsed.get("amount"):
                parsed["source_type"] = "sms"
                transactions.append(parsed)

    stored_count = await _normalize_and_store_transactions(transactions, user_id, db)
    sub_count = await _rebuild_subscriptions(user_id, db)

    return IngestResponse(
        transactions_parsed=stored_count,
        subscriptions_detected=sub_count,
        message=f"Demo data loaded! Found {sub_count} recurring subscriptions from {stored_count} transactions.",
    )


# ── Transaction Management Endpoints ─────────────────────────────────

@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """List all transactions for the current user."""
    user_id = ObjectId(str(current_user["_id"]))

    transactions = []
    async for txn in db.transactions.find({"user_id": user_id}).sort("date", -1):
        date_str = None
        if txn.get("date"):
            try:
                date_str = txn["date"].isoformat() if hasattr(txn["date"], "isoformat") else str(txn["date"])
            except Exception:
                date_str = str(txn["date"])

        transactions.append(TransactionOut(
            id=str(txn["_id"]),
            merchant_raw=txn.get("merchant_raw", ""),
            merchant_normalized=txn.get("merchant_normalized", ""),
            amount=txn.get("amount", 0),
            currency=txn.get("currency", "INR"),
            date=date_str,
            source_type=txn.get("source_type", "sms"),
            category=txn.get("category", "other"),
        ))

    return TransactionListResponse(transactions=transactions, total=len(transactions))


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """Delete a single transaction and rebuild subscriptions."""
    user_id = str(current_user["_id"])
    user_oid = ObjectId(user_id)

    try:
        txn_oid = ObjectId(transaction_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")

    # Verify ownership
    txn = await db.transactions.find_one({"_id": txn_oid, "user_id": user_oid})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Delete the transaction
    await db.transactions.delete_one({"_id": txn_oid})

    # Rebuild subscriptions from remaining transactions
    sub_count = await _rebuild_subscriptions(user_id, db)

    return {
        "status": "deleted",
        "message": f"Transaction removed. {sub_count} subscriptions detected from remaining data.",
        "subscriptions_detected": sub_count,
    }


@router.delete("/transactions")
async def clear_all_data(
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """Clear ALL user data: transactions, subscriptions, scores, history, actions."""
    user_id = str(current_user["_id"])
    await _wipe_all_user_data(user_id, db)

    return {
        "status": "cleared",
        "message": "All data has been cleared successfully.",
    }
