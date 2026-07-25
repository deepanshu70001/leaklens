# 🔍 LeakLens — Find Your Money Leaks, Then Watch Them Grow

> **Hackathon MVP** — Scan SMS alerts and bank statements to detect hidden subscriptions, flag silent price hikes, assign Leak Scores, and redirect recovered money into a simulated growth fund.

---

## 🚀 Why LeakLens?

1. **Works from SMS alone** — No bank API or account linking required. Works for people who get SMS alerts but don't have modern banking apps. Financial inclusion by design.
2. **Detection + Action + Growth** — Most subscription trackers stop at detection. LeakLens closes the loop: detect the leak → act on it → see what happens to the recovered money.
3. **Privacy-first** — PII (card numbers, phone numbers, OTPs) is redacted before any data leaves the server, including to the LLM provider. No raw financial data is ever sent externally.

---

## 🏗️ Architecture

```
[SMS text / CSV / PDF Statement]
          │
          ▼
  Extraction Service (regex first, Groq LLM fallback)
  PII redacted before any external call
          │
          ▼
  Merchant Normalization (rapidfuzz grouping)
  + Recurring Detection (gap analysis)
          │
    ┌─────┴──────┐
    ▼            ▼
Price Anomaly   Leak Score Engine
Detection       (unused + hike + redundancy + cost)
    └─────┬──────┘
          ▼
  Recommendation Engine (Keep/Downgrade/Renegotiate/Cancel)
  + Groq reasoning (with static fallback)
          │
    ┌─────┴──────┐
    ▼            ▼
  User Actions   Growth Engine
  via API        (compounding projection)
          │
          ▼
  Next.js Dashboard (Vercel)
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+ (App Router, TypeScript), Tailwind CSS, Recharts, TanStack Query |
| Backend | Python 3.11, FastAPI, Motor (async MongoDB) |
| Database | MongoDB Atlas (free M0 tier) |
| LLM | Groq API (llama-3.3-70b-versatile / llama-3.1-8b-instant) |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Rate Limiting | slowapi (in-memory, no Redis) |
| Fuzzy Matching | rapidfuzz |
| File Parsing | pandas (CSV), pdfplumber (PDF) |

---

## 📦 Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (free M0 cluster) or local MongoDB
- Groq API key (free at [console.groq.com](https://console.groq.com)) — optional, app works without it

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MONGODB_URI, GROQ_API_KEY, JWT_SECRET

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local if backend is not on localhost:8000

# Run
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and click **"Try Demo Data"** to see it in action.

---

## 🎯 Key Features

| Feature | Status |
|---|---|
| Demo data loads with zero external deps | ✅ |
| SMS text parsing (6+ regex patterns) | ✅ |
| CSV bank statement parsing | ✅ |
| PDF statement parsing | ✅ |
| Merchant normalization + fuzzy grouping | ✅ |
| Recurring subscription detection | ✅ |
| Price hike detection + visualization | ✅ |
| Leak Score (weighted formula, 0-100) | ✅ |
| Keep / Downgrade / Renegotiate / Cancel | ✅ |
| Groq-powered recommendation reasoning | ✅ |
| Groq-powered negotiation script generation | ✅ |
| Growth fund with compounding projection | ✅ |
| PII redaction before LLM calls | ✅ |
| JWT authentication | ✅ |
| Rate limiting on LLM endpoints | ✅ |
| Graceful Groq timeout fallback | ✅ |
| Mobile-responsive dashboard | ✅ |

---

## 🔒 Security & Privacy

### Implemented
- **PII Redaction**: Card/account numbers masked to last 4 digits, phone numbers masked, OTP patterns stripped entirely — all before any LLM call
- **Data Minimization**: Only merchant name, amount, date stored. Raw SMS truncated after parsing
- **JWT Auth**: Passwords hashed with bcrypt, short-lived tokens, no sensitive data in claims
- **CORS**: Restricted to frontend domain only (never `*`)
- **Input Validation**: File size limits, MIME type checks, text sanitization
- **Rate Limiting**: In-memory `slowapi` on LLM-calling endpoints

### Production Roadmap (Not Yet Implemented)
- **Trusted Execution Environment (TEE)**: Raw statement/SMS parsing would run inside an **AWS Nitro Enclave** or similar hardware-isolated environment, with only tokenized/anonymized transaction data leaving the enclave boundary for LLM calls or analytics. Render and Vercel do not offer enclave hosting, so this is out of scope for hackathon deployment — but it's the logical next step for the security model.
- **Managed Redis**: For Groq response caching and stronger rate limiting
- **Network Restrictions**: MongoDB Atlas restricted to Render egress IPs
- **Audit Logging**: Track data access patterns

---

## 📊 Leak Score Formula

```
score = 100 × (
    0.40 × min(days_since_last_activity / 90, 1)
  + 0.30 × min(max_price_increase_pct / 50, 1)
  + 0.20 × (1 if other_active_subs_in_same_category > 1 else 0)
  + 0.10 × min(amount / category_average_amount, 1)
)
```

| Score Range | Recommendation |
|---|---|
| 0–30 | Keep ✅ |
| 31–55 | Downgrade ⬇️ |
| 56–75 | Renegotiate 💬 |
| 76–100 | Cancel ❌ |

The "unused" component uses the last transaction date as a proxy for activity. This is a heuristic approximation — real usage data (app logins, streaming hours) would require direct integration with each service.

---

## 🚀 Deployment

### Backend → Render
1. New Web Service → connect repo → root directory `backend/`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars: `MONGODB_URI`, `GROQ_API_KEY`, `JWT_SECRET`, `ALLOWED_ORIGINS`

### Frontend → Vercel
1. Import repo → root directory `frontend/`
2. Framework preset auto-detects Next.js
3. Env var: `NEXT_PUBLIC_API_URL` = Render backend URL

### MongoDB Atlas
1. Free M0 cluster
2. Network access: `0.0.0.0/0` for hackathon (restrict in production)
3. Copy connection string to `MONGODB_URI`

**No Docker, no Redis** — by design for hackathon speed.

---

## 📝 Known Limitations

- **Usage tracking is approximate**: "Days since last use" is based on last transaction date, not actual service usage
- **Single demo user fallback**: Auth is implemented but the app falls back to a demo user if no JWT is provided, for hackathon convenience
- **MongoDB Atlas network access**: Currently open (`0.0.0.0/0`); should be restricted to Render egress IPs in production
- **No email receipt parsing**: Only SMS and bank statements are supported in this MVP
- **Growth simulation is illustrative**: Uses an assumed 8% annual return — clearly labeled as not investment advice

---

## 📄 License

MIT — Built for a fintech hackathon.
