# ✈ Airwatch — Flight Price Tracker

Runs daily at 9 AM and emails you the top 5 cheapest flights for your 4 trips.

## Files
- `flight_tracker.py` — main script
- `requirements.txt` — Python dependencies
- `railway.toml` — Railway deployment config

---

## Deploy to Railway (Free)

### Step 1 — Create a GitHub repo
1. Go to github.com and create a **New Repository** (name it `flight-tracker`)
2. Upload all 3 files: `flight_tracker.py`, `requirements.txt`, `railway.toml`

### Step 2 — Deploy on Railway
1. Go to **railway.app** and sign up with your GitHub account
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `flight-tracker` repo
4. Railway will auto-detect the config

### Step 3 — Add Environment Variables
In Railway, go to your project → **Variables** tab → add these:

| Variable        | Value                          |
|-----------------|--------------------------------|
| SERPAPI_KEY     | a95cbff78e99cfcc986845bb8c2e0c90d3865f9d9bbe353aa25bf3c5dcfffab5 |
| GMAIL_ADDRESS   | chiragsshah77@gmail.com        |
| GMAIL_APP_PW    | matu khaq napg zuyq            |
| ALERT_EMAIL     | chiragsshah77@gmail.com        |

### Step 4 — Done!
Railway will run the script every day at **9 AM UTC** and email you a report.

---

## Your 4 Trips
1. **GUA → JFK** — Apr 5, 2026 (nonstop only)
2. **JFK → MEX** — May 1–3, 2026 (up to 1 stop)
3. **JFK → MEX** — May 1–4, 2026 (up to 1 stop)
4. **JFK → SJO** — May 7–11, 2026 (up to 1 stop)

Tracking ends automatically after **April 4, 2026**.

---

## Test Locally (optional)
```bash
pip install -r requirements.txt
python flight_tracker.py
```
