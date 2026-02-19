# Product Requirements Document (PRD)

## TN Politics Monitor — Tamil Nadu Politics Social Listening System

**Version:** 1.1  
**Status:** Implementation aligned with core requirements  
**Audience:** Election Commission / oversight bodies, evaluators, professors  

---

## 1. Product Vision

An **AI-powered social listening platform** that monitors political and election-related content across news and social media in (and relevant to) **Tamil Nadu**. The system helps authorities:

- Detect high-severity content (e.g. violence, hate speech, MCC violations, misinformation).
- Review and act on alerts with a clear workflow.
- Use analytics and reports for oversight and evidence.

---

## 2. Problem Statement

- **Volume:** Large number of posts and articles; manual monitoring is slow and inconsistent.
- **Speed:** Critical issues need to be flagged quickly.
- **Coverage:** Multiple platforms (news, X, YouTube, Reddit, etc.) and languages (Tamil, English).
- **Evidence:** Need structured records (alerts, notes, exports) for follow-up and compliance.

---

## 3. Proposed Solution

- **Automated collection** from configurable sources (RSS news, GNews API, X, YouTube, Reddit; more can be added).
- **Analysis** of each post (severity, sentiment, topics, detected issues) using keywords and heuristics (extensible to external AI).
- **Automatic alerting** for CRITICAL and HIGH severity with a review workflow.
- **Web dashboard** for alerts, analytics, reports, and administration.
- **Role-based access** (duty officer, analyst, senior official, admin, auditor).

---

## 4. Target Users

| Role | Purpose |
|------|---------|
| **EC Duty Officer** | Triage and act on alerts; update status; add notes; generate evidence. |
| **EC Analyst** | View trends, sentiment, geography; generate reports. |
| **EC Senior Official** | Review critical incidents; same as duty officer + oversight. |
| **System Admin** | Manage users, keywords, platform/config; view system health. |
| **Auditor** | Read-only access to alerts and reports for compliance. |

---

## 5. Functional Requirements (Summary)

### 5.1 Data collection

- **FR-DC-1** Collect from multiple sources: News (RSS + GNews API), X (Twitter), YouTube, Reddit.
- **FR-DC-2** Filter and deduplicate by platform and post ID.
- **FR-DC-3** Store full post metadata (platform, author, content, URL, timestamp, engagement where available).
- **FR-DC-4** Filter Reddit posts for Tamil Nadu relevance using configurable keywords.

### 5.2 Analysis

- **FR-AI-1** Assign severity (CRITICAL, HIGH, MEDIUM, LOW) and detected issues using configurable keywords and rules.
- **FR-AI-2** Support sentiment and topic tagging (extensible to external NLP/AI).

### 5.3 Alerts and workflow

- **FR-AN-1** Auto-create alerts for CRITICAL and HIGH severity.
- **FR-AN-2** Alert status workflow: New → In Review → Actionable / False Positive / Resolved / Escalated.
- **FR-AN-3** Notes and audit trail (who changed what, when).

### 5.4 Dashboard and reporting

- **FR-DR-1** Real-time alert list with filters (severity, status, platform, date, search).
- **FR-DR-2** Alert detail view with post content, analysis, and actions (status, notes, evidence export).
- **FR-DR-3** Analytics: trends, sentiment over time, geographic distribution, platform breakdown.
- **FR-DR-4** Report generation (e.g. PDF) for selected data.
- **FR-DR-5** Evidence package (e.g. PDF) for individual alerts.

### 5.5 User and system management

- **FR-UM-1** Login with username/password; JWT-based sessions.
- **FR-UM-2** Role-based access control (per role permissions).
- **FR-SA-1** Admin: user management, keyword management, system health (as implemented).

---

## 6. Non-Functional Requirements (Summary)

- **Security:** Passwords hashed (e.g. bcrypt); API protected by JWT; no secrets in code (use `.env` file).
- **Performance:** Pagination on lists; background collection so API stays responsive.
- **Usability:** Clear navigation (Dashboard, Alerts, Analytics, Reports, Admin); filters and search.
- **Data:** All data in the production pipeline comes from **real external sources** (RSS feeds, APIs). No synthetic data is generated at runtime. Seed data only creates users and keywords; demo posts are opt-in via `--demo` flag.
- **Configurability:** RSS feeds, API keys, collection interval, and keywords configurable via `.env` file and Admin panel.
- **Observability:** All collectors log collection counts, errors, and cycle timing to stdout.

---

## 7. Data Sources

| Source | Status | Cost | Notes |
|--------|--------|------|-------|
| **News (RSS)** | ✅ Implemented | Free | The Hindu TN, TOI Chennai, Dinamalar, Dinakaran, News18 TN; no API key needed. |
| **GNews API** | ✅ Implemented | Free (100 req/day) | Sign up at gnews.io for free API key. |
| **YouTube** | ✅ Implemented | Free (10,000 units/day) | Requires YouTube Data API v3 key from Google Cloud Console. |
| **Reddit** | ✅ Implemented | Free | Public JSON; no keys needed. Optional app credentials for higher rate limits. Posts filtered for TN relevance. |
| **X (Twitter)** | ✅ Implemented | Paid ($100/month) | Requires X API Bearer Token (Basic tier). Optional — system works without it. |
| **Facebook / Instagram / WhatsApp** | Placeholder | — | Config present; collectors to be added as needed. |

---

## 8. Out of Scope (v1)

- Audio/video content analysis (transcription, visual AI).
- Predictive analytics / forecasting.
- Automated public response or fact-checking bots.
- Native mobile apps (web responsive only).
- Public-facing API or open registration.

---

## 9. Success Criteria (Indicative)

- **Operational:** System runs end-to-end: collection → analysis → alerts → dashboard and reports.
- **Real data:** News (and optionally YouTube/Reddit) feed real posts; alerts reflect actual content.
- **Usability:** A new user can log in, see alerts, open one, change status, and generate a report within a short demo.
- **Documentation:** README, walkthrough, and this PRD allow an evaluator or professor to understand and run the project.

---

## 10. References

- **README.md** — Overview, how it works, setup, configuration, free API key guides.
- **WALKTHROUGH.md** — Step-by-step run and demo guide for professors/evaluators.

---

*This PRD summarizes the product vision and requirements for the TN Politics Monitor project as implemented. It can be extended with more detailed acceptance criteria or traceability to specific code modules as needed.*
