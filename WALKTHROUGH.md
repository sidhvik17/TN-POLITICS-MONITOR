# TN Politics Monitor — Walkthrough Guide

This walkthrough helps evaluators and professors run the project and understand its main features step by step.

---

## 1. What You Need

- **Python 3.10 or newer** (check: `python --version`)
- **Node.js 18+** (check: `node --version`)
- A terminal (PowerShell or Command Prompt on Windows; Terminal on macOS/Linux)

---

## 2. Get the Code

Open the project folder:

- **Path:** `tn-politics-monitor` (contains `backend` and `frontend` folders)

---

## 3. Run the Backend

### 3.1 Install Python dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

If you use a virtual environment, activate it first, then run the same command.

### 3.2 Set up API keys (optional)

```bash
copy .env.example .env
```

Edit `.env` and add any API keys you have. **News RSS works without any keys**, so you can skip this for a basic demo. See **README.md → How to Get Free API Keys** for step-by-step guides.

### 3.3 Seed the database

```bash
python seed_data.py
```

This creates:

- **Users:** e.g. `admin123`, `rajesh_officer`, `priya_analyst` (password: **TnPolitics@2026**)
- **Keywords** for the analysis engine

> **Note:** `seed_data.py` does NOT create fake posts. All posts come from real-time collection. If you need sample posts for offline testing, run: `python seed_data.py --demo`

### 3.4 Start the API server

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

You should see something like:

- `Uvicorn running on http://127.0.0.1:8000`
- `Application startup complete`

Leave this terminal open. The backend will:

- Serve the REST API at **http://127.0.0.1:8000**
- Run the **collector** every 60 seconds (or per `COLLECTION_INTERVAL_SECONDS`), pulling real **news (RSS + GNews)** and, if keys are set, YouTube and Reddit.
- **Log collection results** in the terminal (e.g. `RSS [The Hindu]: +3 new articles`).

---

## 4. Run the Frontend

Open a **new** terminal.

### 4.1 Install Node dependencies

```bash
cd frontend
npm install
```

### 4.2 Start the dev server

```bash
npm run dev
```

Note the URL (e.g. **http://localhost:5173**). Open it in your browser.

---

## 5. Log In

1. You should see the **Login** page.
2. Use the seeded credentials:
   - **Username:** `admin123`
   - **Password:** `TnPolitics@2026`
3. Click **Login**. You should be taken to the **Dashboard**.

---

## 6. Main Screens to Show

### 6.1 Dashboard (home)

- **Stats cards:** Critical alerts, high priority, active alerts, posts monitored, resolved today, districts.
- **Alert list:** Each row is one alert (severity, type, snippet, platform, time).
- **Filters:** By severity (Critical/High/Medium/Low), status (New, In Review, Resolved, etc.), and search.
- **Click an alert** to open its detail page.

### 6.2 Verify real-time data is flowing

1. Watch the **backend terminal** — you should see log messages like:
   ```
   10:30:15 [tn_collector] INFO: === Collection cycle starting ===
   10:30:17 [tn_collector] INFO:   RSS [The Hindu]: +2 new articles
   10:30:18 [tn_collector] INFO:   RSS [Times of India]: +4 new articles
   10:30:19 [tn_collector] INFO: === Collection cycle complete: 6 new items ===
   ```
2. After 1–2 collection cycles (5–10 minutes), **refresh the Dashboard**. You should see real news headlines.
3. Filter alerts by **platform = news** to confirm real data from RSS feeds.

### 6.3 Alert detail

- Full **post content** (and translation if present).
- **Analysis:** severity, confidence, detected issues, sentiment, topics.
- **Actions:** Change status (e.g. to Actionable, False Positive, Resolved), add notes, generate evidence package (PDF).

### 6.4 Analytics

- **Trends** (e.g. topics, word cloud).
- **Sentiment** over time.
- **Geographic** distribution (districts).
- **Platform** breakdown.

### 6.5 Reports

- Generate custom reports (e.g. date range, format). Useful to show that the system supports "evidence" and reporting.

### 6.6 Admin (admin user only)

- **Users:** list/create/edit.
- **Keywords:** list/add/remove — these drive the keyword-based analysis.
- **System health.**

Log in as **admin123** / **TnPolitics@2026** to access Admin.

---

## 7. Data Sources and API Keys

| Source | Works without keys? | How to get free key |
|--------|---------------------|---------------------|
| **News RSS** | ✅ Yes | No key needed |
| **GNews API** | Needs free key | Sign up at [gnews.io](https://gnews.io) |
| **YouTube** | Needs free key | [Google Cloud Console](https://console.cloud.google.com) → enable YouTube Data API v3 |
| **Reddit** | ✅ Yes (public JSON) | Optional: [reddit.com/prefs/apps](https://reddit.com/prefs/apps) |
| **X (Twitter)** | ❌ Paid ($100/mo) | Not required for demo |

See **README.md → How to Get Free API Keys** for detailed step-by-step instructions.

---

## 8. Optional: API Documentation

- Open **http://127.0.0.1:8000/docs** in the browser.
- This is Swagger UI for the FastAPI backend. You can try endpoints (e.g. `/api/health`, `/api/alerts`) and see request/response shapes.

---

## 9. Summary for Professor / Evaluator

| Item | Where to see it |
|------|------------------|
| **What the system does** | README.md — overview and "How the project works" |
| **How to run it** | This walkthrough (Sections 3–4) |
| **How to log in** | Section 5 (admin123 / TnPolitics@2026) |
| **Main features** | Dashboard, Alert detail, Analytics, Reports, Admin (Sections 6.1–6.6) |
| **Real-time data proof** | Section 6.2 — check backend logs and dashboard |
| **Free API keys** | Section 7 and README.md |
| **Formal requirements** | PRD.md |

If something does not run (e.g. `pip` or `uvicorn` not found), ensure Python and Node are installed and that you are in the correct folder (`backend` or `frontend`) when running the commands above.
