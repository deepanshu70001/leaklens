# 📘 LeakLens Technical Documentation

This document covers the core architecture, logic, and algorithms that power LeakLens.

---

## 1. Data Ingestion Pipeline (`/api/ingest`)

LeakLens supports completely unstructured, multi-modal financial data.

1. **Text/SMS/Email (`/api/ingest/sms`)**: 
   - A multi-line string is passed.
   - **Phase 1 (Regex Fast-Path)**: The system attempts to match lines against known bank SMS formats (e.g., HDFC, SBI, Chase, Auto-pay Mandates). If it matches, it parses locally in ~2ms.
   - **Phase 2 (LLM Fallback)**: If Regex fails, the text is passed through a PII Redaction filter (masking card numbers and names) and sent to **Groq (`llama-3.3-70b`)** which structures the unstructured sentence into `{"merchant", "amount", "date"}`.

2. **Statements (`/api/ingest/statement`)**:
   - **CSV**: Processed line by line via Regex/LLM.
   - **PDF**: Uses `pdfplumber` to extract raw text pages, which are then passed into the processing queue.
   - **Images (Screenshots/Receipts)**: If an image is uploaded, it is base64 encoded and sent to **Groq Vision (`llama-3.2-11b-vision`)**. The multimodal LLM performs OCR and extracts all transactions directly into a JSON array, bypassing local Tesseract requirements.

---

## 2. The Recurring Detector Engine

Finding recurring payments in chaotic data is difficult because merchants use varying names (e.g., `NETFLIX.COM`, `Netflix NY`, `POS PUR NETFLIX`).

1. **Normalization & Grouping**:
   - Merchant strings are cleaned (removing cities, POS codes, special characters).
   - `rapidfuzz` (Levenshtein distance) groups similar merchants together (e.g., `Spotify India` and `Spotify AB` become one entity).

2. **Temporal Gap Analysis**:
   - Transactions are sorted chronologically.
   - The engine calculates the average gap (in days) between charges.
   - `~30 days` = Monthly, `~365 days` = Annual, `~7 days` = Weekly.
   - **Exception Rule**: If a transaction is explicitly flagged as an Auto-Pay Setup (e.g., "Mandate registered for Apple"), the engine bypasses the minimum 2-charge requirement and instantly flags it as a recurring monthly subscription.

---

## 3. The "Leak Score" Algorithm

Every subscription is assigned a **Leak Score (0-100)** to determine how aggressively the user should cancel it.

**Formula Components (Weighted)**:
1. **Unused Penalty (40%)**: Calculated based on the days since the last transaction compared to the expected billing frequency. E.g., If a monthly subscription hasn't charged you in 60 days, it is flagged as dormant.
2. **Price Hike Penalty (30%)**: Calculates the percentage increase from the first historical charge to the current charge. 
3. **Redundancy Penalty (20%)**: If a user has `Netflix`, `Prime`, and `Hulu` active, their "Entertainment" category redundancy penalty increases.
4. **Relative Cost Penalty (10%)**: Flags if a subscription costs significantly more than the average cost of other subscriptions in its category.

*If Leak Score > 65 -> Action: Cancel / Downgrade.*

---

## 4. Groq-Powered AI Features

- **Dark Pattern Exposer**: When rendering a high-risk subscription, the `generate_dark_pattern_warning` system prompt asks Groq's reasoning model if the merchant uses deceptive cancellation practices, returning an "Escape Route" (e.g., avoiding early termination fees).
- **Ghost Cancellation**: The `generate_negotiation_script` drafts a highly specific support email. The system then simulates an automated API dispatch to the merchant's support email, closing the loop for the user without them ever leaving the app.
- **WhatsApp Simulator**: A frontend Next.js component simulates real-time conversational interventions, mimicking how the system would send proactive alerts via a Twilio/WhatsApp webhook architecture.
