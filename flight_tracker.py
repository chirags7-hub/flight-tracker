import os
import json
import smtplib
import requests
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIG ────────────────────────────────────────────────────────────────────
SERPAPI_KEY   = os.environ.get("SERPAPI_KEY", "a95cbff78e99cfcc986845bb8c2e0c90d3865f9d9bbe353aa25bf3c5dcfffab5")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "chiragsshah77@gmail.com")
GMAIL_APP_PW  = os.environ.get("GMAIL_APP_PW",  "matu khaq napg zuyq")
ALERT_EMAIL   = os.environ.get("ALERT_EMAIL",   "chiragsshah77@gmail.com")
PRICE_FILE    = "price_history.json"
END_DATE      = date(2026, 4, 4)   # stop tracking after this date

TRIPS = [
    {
        "id":           "trip1",
        "label":        "GUA → JFK (Apr 5)",
        "departure_id": "GUA",
        "arrival_id":   "JFK",
        "outbound_date":"2026-04-05",
        "return_date":  None,
        "type":         "2",          # one-way
        "nonstop_only": True,
        "max_stops":    0,
    },
    {
        "id":           "trip2",
        "label":        "JFK → MEX (May 1–3)",
        "departure_id": "JFK",
        "arrival_id":   "MEX",
        "outbound_date":"2026-05-01",
        "return_date":  "2026-05-03",
        "type":         "1",          # round-trip
        "nonstop_only": False,
        "max_stops":    1,
    },
    {
        "id":           "trip3",
        "label":        "JFK → MEX (May 1–4)",
        "departure_id": "JFK",
        "arrival_id":   "MEX",
        "outbound_date":"2026-05-01",
        "return_date":  "2026-05-04",
        "type":         "1",
        "nonstop_only": False,
        "max_stops":    1,
    },
    {
        "id":           "trip4",
        "label":        "JFK → SJO (May 7–11)",
        "departure_id": "JFK",
        "arrival_id":   "SJO",
        "outbound_date":"2026-05-07",
        "return_date":  "2026-05-11",
        "type":         "1",
        "nonstop_only": False,
        "max_stops":    1,
    },
]
# ─────────────────────────────────────────────────────────────────────────────


def load_history():
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE) as f:
            return json.load(f)
    return {}


def save_history(history):
    with open(PRICE_FILE, "w") as f:
        json.dump(history, f, indent=2)


def fetch_flights(trip):
    params = {
        "engine":         "google_flights",
        "departure_id":   trip["departure_id"],
        "arrival_id":     trip["arrival_id"],
        "outbound_date":  trip["outbound_date"],
        "type":           trip["type"],
        "adults":         "1",
        "currency":       "USD",
        "hl":             "en",
        "api_key":        SERPAPI_KEY,
    }
    if trip["return_date"]:
        params["return_date"] = trip["return_date"]

    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_flights(data, trip):
    """Return top-5 cheapest flights matching stop criteria."""
    best   = data.get("best_flights", [])
    other  = data.get("other_flights", [])
    all_flights = best + other

    results = []
    for flight in all_flights:
        legs  = flight.get("flights", [])
        stops = len(legs) - 1

        if trip["nonstop_only"] and stops != 0:
            continue
        if not trip["nonstop_only"] and stops > trip["max_stops"]:
            continue

        price = flight.get("price")
        if not price:
            continue

        first = legs[0]  if legs else {}
        last  = legs[-1] if legs else {}

        airline    = first.get("airline", "Unknown")
        flight_num = first.get("flight_number", "")
        dep_time   = (first.get("departure_airport") or {}).get("time", "--")
        arr_time   = (last.get("arrival_airport")   or {}).get("time", "--")
        duration   = flight.get("total_duration", 0)
        dur_str    = f"{duration//60}h {duration%60}m" if duration else "--"
        stop_label = "Nonstop" if stops == 0 else f"{stops} stop{'s' if stops>1 else ''}"

        results.append({
            "price":      price,
            "airline":    airline,
            "flight_num": flight_num,
            "dep_time":   dep_time[:5] if dep_time else "--",
            "arr_time":   arr_time[:5] if arr_time else "--",
            "duration":   dur_str,
            "stops":      stop_label,
        })

    results.sort(key=lambda x: x["price"])
    return results[:5]


def build_email_html(report):
    today = datetime.now().strftime("%B %d, %Y")
    rows  = ""

    for item in report:
        trip    = item["trip"]
        flights = item["flights"]
        prev    = item["prev_low"]
        curr    = item["curr_low"]

        if prev and curr and curr < prev:
            delta = f'<span style="color:#00c853">▼ ${prev - curr:.0f} drop!</span>'
        elif prev and curr and curr > prev:
            delta = f'<span style="color:#e53935">▲ ${curr - prev:.0f} increase</span>'
        else:
            delta = '<span style="color:#888">No change</span>'

        rows += f"""
        <tr>
          <td colspan="6" style="background:#1a2235;padding:12px 16px;font-weight:700;
              font-size:15px;border-top:2px solid #00d4ff;color:#00d4ff;">
            ✈ {trip['label']}
            <span style="float:right;font-size:12px;color:#aaa">{delta}</span>
          </td>
        </tr>
        """

        if not flights:
            rows += """
            <tr><td colspan="6" style="padding:12px 16px;color:#888;font-style:italic">
              No matching flights found today.
            </td></tr>"""
        else:
            rows += """
            <tr style="background:#0d1423;font-size:11px;color:#6b7a99;text-transform:uppercase;letter-spacing:.08em">
              <td style="padding:8px 16px">Airline</td>
              <td style="padding:8px">Flight</td>
              <td style="padding:8px">Depart</td>
              <td style="padding:8px">Arrive</td>
              <td style="padding:8px">Duration / Stops</td>
              <td style="padding:8px;text-align:right">Price</td>
            </tr>"""
            for i, f in enumerate(flights):
                bg    = "#111827" if i % 2 == 0 else "#0f1520"
                badge = ' <span style="background:#00c85322;color:#00c853;padding:1px 6px;border-radius:3px;font-size:10px">BEST</span>' if i == 0 else ""
                rows += f"""
                <tr style="background:{bg}">
                  <td style="padding:10px 16px;color:#e8f0fe">{f['airline']}{badge}</td>
                  <td style="padding:10px 8px;color:#aaa;font-size:12px">{f['flight_num']}</td>
                  <td style="padding:10px 8px;color:#e8f0fe;font-weight:700">{f['dep_time']}</td>
                  <td style="padding:10px 8px;color:#e8f0fe;font-weight:700">{f['arr_time']}</td>
                  <td style="padding:10px 8px;color:#aaa;font-size:12px">{f['duration']} · {f['stops']}</td>
                  <td style="padding:10px 16px;text-align:right;color:#00e5a0;font-weight:700;font-size:16px">${f['price']:,}</td>
                </tr>"""

    html = f"""
    <html><body style="margin:0;padding:0;background:#0a0e1a;font-family:'Courier New',monospace">
    <div style="max-width:700px;margin:0 auto;padding:32px 16px">

      <div style="text-align:center;margin-bottom:32px">
        <div style="font-size:11px;letter-spacing:.3em;color:#00d4ff;text-transform:uppercase;margin-bottom:8px">
          ✈ Airwatch
        </div>
        <h1 style="margin:0;font-size:28px;color:#fff;font-family:Arial,sans-serif">
          Daily Flight Price Report
        </h1>
        <p style="color:#6b7a99;font-size:13px;margin-top:6px">{today}</p>
      </div>

      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-radius:12px;overflow:hidden;border:1px solid #1e2d45">
        {rows}
      </table>

      <p style="color:#444;font-size:11px;text-align:center;margin-top:24px">
        Powered by SerpApi · Google Flights data · Unsubscribe by stopping the scheduler
      </p>
    </div>
    </body></html>
    """
    return html


def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✈ Flight Price Report — {datetime.now().strftime('%b %d')}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = ALERT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PW)
        server.sendmail(GMAIL_ADDRESS, ALERT_EMAIL, msg.as_string())
    print("✅ Email sent successfully.")


def run():
    today = date.today()
    if today > END_DATE:
        print(f"Tracking period ended ({END_DATE}). Exiting.")
        return

    print(f"🔍 Running flight check — {today}")
    history = load_history()
    report  = []

    for trip in TRIPS:
        print(f"  Checking {trip['label']}...")
        try:
            data    = fetch_flights(trip)
            flights = parse_flights(data, trip)
            curr_low = flights[0]["price"] if flights else None
            prev_low = history.get(trip["id"], {}).get("low_price")

            # Save today's low
            history[trip["id"]] = {
                "low_price":   curr_low,
                "last_checked": today.isoformat(),
            }

            report.append({
                "trip":     trip,
                "flights":  flights,
                "curr_low": curr_low,
                "prev_low": prev_low,
            })
            print(f"    → Lowest: ${curr_low}" if curr_low else "    → No flights found")

        except Exception as e:
            print(f"    ⚠ Error fetching {trip['label']}: {e}")
            report.append({"trip": trip, "flights": [], "curr_low": None, "prev_low": None})

    save_history(history)

    html = build_email_html(report)
    send_email(html)


if __name__ == "__main__":
    run()
