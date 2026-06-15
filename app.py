from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv

from tradezint.config import get_settings
from tradezint.jobs import generate_report_job, send_latest_reports
from tradezint.store import Store

load_dotenv()

settings = get_settings()
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.app_secret_key
store = Store(settings.database_path)
store.init_db()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify({
        "timezone": settings.timezone,
        "scheduler": [
            {"time": "08:00", "label": "Generate Nifty and FNO reports", "delivery": "Internal"},
            {"time": "09:00", "label": "Email Nifty and FNO reports", "delivery": "PDF email"},
            {"time": "09:30", "label": "Email CNBC Awaaz intraday report", "delivery": "PDF email"},
        ],
        "integrations": settings.integration_status(),
        "subscriber_count": len(store.list_subscribers()),
        "report_count": len(store.list_reports()),
        "latest_logs": store.list_delivery_logs(limit=10),
    })


@app.get("/api/reports")
def reports():
    category = request.args.get("category")
    return jsonify(store.list_reports(category=category if category != "All" else None))


@app.get("/api/reports/<int:report_id>/download")
def download_report(report_id):
    report = store.get_report(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    return send_file(
        report["path"],
        mimetype="application/pdf",
        as_attachment=False,
        download_name=report["filename"],
    )


@app.get("/api/subscribers")
def subscribers():
    return jsonify({"subscribers": store.list_subscribers()})


@app.post("/api/subscribers")
def add_subscriber():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    if not store.add_subscriber(email):
        return jsonify({"error": "Enter a valid email address"}), 400
    return jsonify({"status": "saved", "email": email})


@app.post("/api/run/<report_type>")
def run_report(report_type):
    if report_type not in {"nifty", "fno", "intraday"}:
        return jsonify({"error": "Unknown report type"}), 404
    report = generate_report_job(report_type, store, settings)
    return jsonify(report)


@app.post("/api/send/<report_type>")
def send_report(report_type):
    if report_type not in {"nifty", "fno", "intraday", "all"}:
        return jsonify({"error": "Unknown report type"}), 404
    result = send_latest_reports(report_type, store, settings)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
