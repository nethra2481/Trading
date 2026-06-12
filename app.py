import os
from flask import Flask, jsonify, render_template, send_from_directory, request
import subscribers

app = Flask(__name__)

# Directory where the PDFs are generated (current directory)
REPORTS_DIR = os.path.dirname(os.path.abspath(__file__))
subscribers.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/set_email', methods=['POST'])
def set_email():
    data = request.json
    email = (data.get('email') or "").strip().lower()
    if subscribers.upsert_subscriber(email):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/reports', methods=['GET'])
def list_reports():
    """Returns a list of all generated PDF reports categorized."""
    files = os.listdir(REPORTS_DIR)
    reports = []
    
    for f in files:
        if f.endswith('.pdf'):
            category = "Unknown"
            if f.startswith('Nifty_'):
                category = "Nifty"
            elif f.startswith('FNO_'):
                category = "FNO"
            elif f.startswith('Intraday_'):
                category = "Intraday"
                
            # Extract date if it matches our pattern *_YYYY-MM-DD.pdf
            # e.g., Nifty_Daily_Analysis_2026-05-20.pdf
            # Just grab the last part before .pdf
            name_parts = f.replace('.pdf', '').split('_')
            date_str = name_parts[-1] if len(name_parts) > 1 else "Unknown Date"
            
            # Use os.path.getmtime to get exact creation/modification time
            mtime = os.path.getmtime(os.path.join(REPORTS_DIR, f))
            
            reports.append({
                'filename': f,
                'category': category,
                'date_str': date_str,
                'mtime': mtime
            })
            
    # Sort by modification time descending (newest first)
    reports.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify(reports)

@app.route('/api/reports/<filename>', methods=['GET'])
def get_report(filename):
    """Serves the requested PDF file."""
    if not filename.endswith('.pdf'):
        return "Invalid file format", 400
    return send_from_directory(REPORTS_DIR, filename)

@app.route('/api/subscribers', methods=['GET'])
def list_subscribers():
    return jsonify({"subscribers": subscribers.get_active_emails()})

if __name__ == '__main__':
    app.run(debug=False, port=5000)
