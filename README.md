# TN Politics Monitor

**Tamil Nadu Politics Social Listening System** — An AI-powered platform for monitoring political discourse and election-related content across news and social media, designed for use by election oversight bodies (e.g., Election Commission of Tamil Nadu).

---

## Table of Contents

- [Overview](#overview)
- [How the Project Works](#how-the-project-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [How to Get Free API Keys](#how-to-get-free-api-keys)
- [Configuration](#configuration)
- [Documentation](#documentation)

---

## Overview

TN Politics Monitor collects **real** political content from:

- **News (RSS)** — The Hindu (Tamil Nadu), Times of India (Chennai), Dinamalar, Dinakaran, News18 TN (no API keys required).
- **GNews API** — Additional news from multiple publishers (free: 100 requests/day).
- **YouTube** — Video metadata and descriptions (free: 10,000 units/day).
- **Reddit** — Posts from r/TamilNadu, r/india, r/Chennai (works with public JSON; no keys needed).
- **X (Twitter)** — Recent search API (optional; requires paid `X_BEARER_TOKEN`).

Collected posts are analyzed (keyword-based severity/sentiment), stored in a database, and high-severity items generate **alerts** that staff can review in a web dashboard. The system supports roles (duty officer, analyst, senior official, admin, auditor), filtering, analytics, and evidence-style exports.

---

## How the Project Works

### High-level flow

1. **Data collection (backend)**  
   A background task runs every few minutes (configurable). It:
   - Fetches new items from RSS feeds, GNews API, and (if keys are set) YouTube, and Reddit.
   - Filters Reddit posts for Tamil Nadu relevance using configurable keywords.
   - Deduplicates by `(platform, post_id)`.
   - Saves each new item as a **Post** in the database.
   - Logs collection counts and errors to the terminal.

2. **Analysis**  
   Each new post is analyzed using:
   - Configurable **keywords** (stored in DB, managed in Admin).
   - Simple **keyword-based heuristics** to assign severity (e.g. CRITICAL, HIGH, MEDIUM, LOW), sentiment, and detected issues.

3. **Alerts**  
   Posts with **CRITICAL**, **HIGH**, or **MEDIUM** severity automatically get an **Alert** record. Alerts appear on the Dashboard, can be filtered by severity/status/platform, and can be updated (e.g. New → In Review → Actionable / False Positive / Resolved).

4. **Frontend**  
   Users log in (JWT), then:
   - **Dashboard** — Live list of alerts, stats (critical/high/active counts), filters, and pagination.
   - **Alert detail** — View post content, analysis, add notes, change status, generate evidence PDF.
   - **Analytics** — Trends, sentiment over time, geographic distribution, platform breakdown.
   - **Reports** — Custom report generation (e.g. PDF).
   - **Admin** — Users, keywords, system health (role-restricted).

5. **API**  
   The backend exposes REST endpoints under `/api` (auth, alerts, posts, analytics, admin, reports) and an optional WebSocket at `/ws/alerts` for real-time updates.

---

## Tech Stack

| Layer        | Technology        |
|-------------|-------------------|
| Frontend    | React 19, Vite 7, React Router, Axios, Recharts, Lucide icons |
| Backend     | Python 3.10+, FastAPI, Uvicorn |
| Database    | SQLite (default), SQLAlchemy ORM |
| Auth        | JWT (python-jose), bcrypt (passlib) |
| Data ingest | httpx, feedparser, python-dotenv; config-driven API keys |

---

## Project Structure

```
tn-politics-monitor/
├── backend/
│   ├── main.py              # FastAPI app, auth routes, WebSocket, background collector loop
│   ├── config.py            # Environment-based config (DB, API keys, RSS feeds, intervals)
│   ├── database.py          # SQLAlchemy engine, session, init_db
│   ├── models.py            # User, Post, AnalyzedPost, Alert, Keyword, AuditLog
│   ├── auth.py              # Password hashing, JWT, get_current_user, require_role
│   ├── seed_data.py         # Seed users + keywords; optional --demo for sample posts
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Template for API keys (copy to .env)
│   ├── routers/             # alerts, posts, analytics, admin, reports
│   └── services/
│       └── collectors.py    # RSS, GNews, X, YouTube, Reddit collectors; run_collection_cycle()
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Routes, auth wrapper
│   │   ├── main.jsx, index.css
│   │   ├── lib/             # api.js (Axios), auth.jsx (AuthProvider)
│   │   ├── components/      # Layout (sidebar, nav)
│   │   └── pages/           # Login, Dashboard, AlertDetail, Analytics, Reports, Admin
│   ├── package.json
│   └── vite.config.js
├── README.md                # This file
├── WALKTHROUGH.md           # Step-by-step run and use guide
└── PRD.md                   # Product Requirements Document
```

---

## Quick Start

### Prerequisites

- **Python 3.10+** (with `pip`)
- **Node.js 18+** (with `npm`)

### Backend

```bash
cd backend

# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Set up API keys (optional but recommended)
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Then edit .env and add your free API keys (see below)

# 3. Seed database (users + keywords)
python seed_data.py

# 4. Start the server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Default login (after seeding): **admin123** / **TnPolitics@2026**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown (e.g. `http://localhost:5173`), log in, and use the Dashboard.

### Verify real-time data

- **News RSS runs without any keys.** After 1–2 collection cycles (2–4 minutes), new posts with `platform=news` appear. Watch the backend terminal for log messages like `RSS [The Hindu]: +3 new articles`.
- Use Dashboard filters or API: `GET /api/posts?platform=news`.

---

## How to Get Free API Keys

### YouTube Data API v3 (Free — 10,000 units/day)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g. "TN Politics Monitor")
3. Navigate to **APIs & Services → Library**
4. Search for **"YouTube Data API v3"** → click **Enable**
5. Go to **APIs & Services → Credentials** → click **Create Credentials → API Key**
6. *(Recommended)* Click **Restrict Key** → select **YouTube Data API v3** only
7. Copy the key and paste it into your `.env` file as `YOUTUBE_API_KEY=your_key_here`

### GNews API (Free — 100 requests/day)

1. Go to [gnews.io](https://gnews.io)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Paste into `.env` as `GNEWS_API_KEY=your_key_here`

### Reddit (Free — works without keys)

Reddit collection works out of the box using public JSON (10 requests/minute). For higher rate limits (100 req/min):

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"create another app..."**
3. Name: `tn-politics-monitor`, Type: **script**
4. Redirect URI: `http://localhost:8000`
5. Copy the client ID (shown under the app name) and secret
6. Paste into `.env`:
   ```
   REDDIT_CLIENT_ID=your_id
   REDDIT_CLIENT_SECRET=your_secret
   ```

### X / Twitter (Paid — $100/month)

X API access is **not free**. The system works fully without it. If you have a paid subscription:

1. Go to [developer.x.com](https://developer.x.com)
2. Subscribe to Basic tier ($100/month)
3. Create a project → Generate Bearer Token
4. Paste into `.env` as `X_BEARER_TOKEN=your_token`

---

## Configuration

All configuration is loaded from environment variables or a `.env` file in the `backend/` folder. Copy `.env.example` to `.env` and edit as needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | DB connection string | `sqlite:///./tn_politics.db` |
| `COLLECTION_ENABLED` | Run background collector | `true` |
| `COLLECTION_INTERVAL_SECONDS` | Seconds between collection runs | `60` |
| `YOUTUBE_API_KEY` | YouTube Data API key (free) | — |
| `GNEWS_API_KEY` | GNews API key (free) | — |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit app (optional) | — |
| `REDDIT_USER_AGENT` | Reddit User-Agent | `tn-politics-monitor/1.0` |
| `X_BEARER_TOKEN` | X (Twitter) API bearer token (paid) | — |

RSS feed URLs and search queries are in `backend/config.py` and can be edited there.

---

## Documentation

- **[WALKTHROUGH.md](./WALKTHROUGH.md)** — Step-by-step guide to run the app and use main features (for professors and evaluators).
- **[PRD.md](./PRD.md)** — Product Requirements Document: vision, users, features, and requirements.

---

## License and Use

This project is for educational and demonstration purposes. Use of third-party APIs (X, YouTube, Reddit, GNews) must comply with their respective terms of service and rate limits.
