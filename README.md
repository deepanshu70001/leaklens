<div align="center">
  <img src="https://img.shields.io/badge/LeakLens-FinTech-0F6E56?style=for-the-badge&logo=appveyor" alt="LeakLens Logo" />
  <h1>LeakLens</h1>
  <p><b>Plug the silent money leaks in your bank account.</b></p>
</div>

Most people quietly lose money every month to forgotten subscriptions, unannounced price hikes, and redundant services buried inside cluttered bank statements and SMS alerts. LeakLens is a smart financial guardian that scans your transaction history to detect these leaks automatically.

## ✨ Features

- **Multi-modal Ingestion**: Upload CSV/PDF bank statements or just copy-paste SMS/Email alerts.
- **🖼️ Vision OCR**: Upload a screenshot of a payment receipt, and LeakLens uses Groq's `llama-3.2-11b-vision` model to extract transactions perfectly.
- **📈 Silent Price Hike Detection**: Tracks pricing over time and flags you when a service increases your monthly bill without you noticing.
- **🕵️ Dark Pattern Exposer**: Warns you if a company uses deceptive cancellation practices and provides a step-by-step escape route.
- **👻 Ghost Cancellation**: Don't want to deal with support? LeakLens will automatically draft and dispatch cancellation emails on your behalf.
- **💬 WhatsApp Intervention Simulator**: Connects directly with users on WhatsApp to proactively detect non-usage.
- **🌱 Growth Simulation**: Shows you exactly how much wealth you could build by redirecting your "leaked" money into an Index Fund.

## 🚀 Quick Start (Local Setup)

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```
Set your environment variables in `backend/.env`:
```env
MONGODB_URI=your_mongodb_connection_string
DATABASE_NAME=leaklens
GROQ_API_KEY=your_groq_api_key
JWT_SECRET=dev-secret
ALLOWED_ORIGINS=http://localhost:3000
```
Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
```
Set your environment variables in `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
Run the client:
```bash
npm run dev
```

## 🏗️ Architecture Stack
- **Frontend**: Next.js 14 (App Router), TailwindCSS, Recharts, React Query
- **Backend**: Python FastAPI, Motor (Async MongoDB), RapidFuzz (String matching)
- **AI/LLM**: Groq API (`llama-3.3-70b-versatile` for extraction, `llama-3.2-11b-vision-preview` for OCR, `llama-3.1-8b-instant` for reasoning)
- **Database**: MongoDB Atlas

For a deep dive into the transaction detection logic, leak score math, and architecture, see [DOCUMENTATION.md](./DOCUMENTATION.md).
