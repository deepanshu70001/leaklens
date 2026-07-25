"""
Ingest router — /api/ingest/sms, /statement, /demo (§5).
Parses input, runs the full detection pipeline, and stores results.
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import Optional
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


async def _run_detection_pipeline(transactions: list[dict], user_id: str, db) -> dict:
    """
    Full detection pipeline:
    1. Normalize merchants
    2. Group by fuzzy matching
    3. Detect recurring patterns
    4. Detect price hikes
    5. Compute leak scores + recommendations
    6. Store everything in MongoDB
    """
    if not transactions:
        return {"transactions_parsed": 0, "subscriptions_detected": 0}

    # Step 1: Normalize merchant names
    for txn in transactions:
        txn["merchant_normalized"] = normalize_merchant(txn.get("merchant", txn.get("merchant_raw", "")))
        txn["merchant_raw"] = txn.get("merchant", txn.get("merchant_raw", ""))

    # Step 2: Group by fuzzy matching
    all_normalized = [txn["merchant_normalized"] for txn in transactions if txn["merchant_normalized"]]
    canonical_map = group_merchants(all_normalized)

    for txn in transactions:
        original = txn["merchant_normalized"]
        txn["merchant_normalized"] = canonical_map.get(original, original)
        txn["category"] = categorize_merchant(txn["merchant_normalized"])

    # Step 3: Store transactions
    txn_docs = []
    for txn in transactions:
        txn_docs.append({
            "user_id": ObjectId(user_id),
            "raw_text": txn.get("raw_text", "")[:500],  # Truncate for data minimization
            "merchant_raw": txn.get("merchant_raw", ""),
            "merchant_normalized": txn["merchant_normalized"],
            "amount": txn["amount"],
            "currency": txn.get("currency", "INR"),
            "date": txn["date"],
            "source_type": txn.get("source_type", "sms"),
        })

    if txn_docs:
        await db.transactions.insert_many(txn_docs)

    # Step 4: Detect recurring subscriptions
    recurring = detect_recurring(transactions)

    if not recurring:
        return {"transactions_parsed": len(transactions), "subscriptions_detected": 0}

    # Step 5: Store subscriptions and compute scores
    # First, clear existing data for this user (re-ingest replaces)
    await db.subscriptions.delete_many({"user_id": ObjectId(user_id)})
    await db.leak_scores.delete_many({
        "subscription_id": {"$in": [
            s["_id"] async for s in db.subscriptions.find({"user_id": ObjectId(user_id)}, {"_id": 1})
        ]}
    })

    sub_docs = []
    for sub in recurring:
        sub_doc = {
            "user_id": ObjectId(user_id),
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

    # Step 6: Price history + hike detection
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

    # Step 7: Compute leak scores
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
            "computed_at": datetime.now(timezone.utc),
        })

    return {
        "transactions_parsed": len(transactions),
        "subscriptions_detected": len(sub_docs),
    }


@router.post("/sms", response_model=IngestResponse)
async def ingest_sms(
    request: SMSIngestRequest,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """Parse pasted SMS text and run detection pipeline."""
    sanitized = sanitize_text(request.raw_text)
    if not sanitized:
        raise HTTPException(status_code=400, detail="No text provided")

    transactions = await parse_sms_text(sanitized)

    user_id = str(current_user["_id"])
    result = await _run_detection_pipeline(transactions, user_id, db)

    return IngestResponse(
        transactions_parsed=result["transactions_parsed"],
        subscriptions_detected=result["subscriptions_detected"],
        message=f"Successfully parsed {result['transactions_parsed']} transactions and detected {result['subscriptions_detected']} recurring subscriptions.",
    )


@router.post("/statement", response_model=IngestResponse)
async def ingest_statement(
    file: UploadFile = File(...),
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """Parse uploaded CSV/PDF bank statement and run detection pipeline."""
    # Validate file
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
            # Explicitly flag image extractions as setup if they have an amount,
            # as OCR receipts often only have 1 entry.
            txn["is_explicit_setup"] = True
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV, PDF, or Image file (PNG/JPG).")

    user_id = str(current_user["_id"])
    result = await _run_detection_pipeline(transactions, user_id, db)

    return IngestResponse(
        transactions_parsed=result["transactions_parsed"],
        subscriptions_detected=result["subscriptions_detected"],
        message=f"Successfully parsed {result['transactions_parsed']} transactions and detected {result['subscriptions_detected']} recurring subscriptions.",
    )


@router.post("/demo", response_model=IngestResponse)
async def ingest_demo(
    request: DemoIngestRequest,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Load a bundled sample dataset — must always work with zero external dependency.
    This endpoint does NOT require Groq or any external API.
    """
    # Resolve sample data file
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

    # Clear existing user data for fresh demo
    user_id = str(current_user["_id"])
    user_oid = ObjectId(user_id)
    await db.transactions.delete_many({"user_id": user_oid})

    # Get subscription IDs before deleting
    sub_ids = [s["_id"] async for s in db.subscriptions.find({"user_id": user_oid}, {"_id": 1})]
    if sub_ids:
        await db.leak_scores.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.price_history.delete_many({"subscription_id": {"$in": sub_ids}})
        await db.actions.delete_many({"subscription_id": {"$in": sub_ids}})
    await db.subscriptions.delete_many({"user_id": user_oid})

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

    result = await _run_detection_pipeline(transactions, user_id, db)

    return IngestResponse(
        transactions_parsed=result["transactions_parsed"],
        subscriptions_detected=result["subscriptions_detected"],
        message=f"Demo data loaded! Found {result['subscriptions_detected']} recurring subscriptions from {result['transactions_parsed']} transactions.",
    )
