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
    """Returns a list of all generated PDF reports categorized from the database."""
    try:
        reports = subscribers.get_all_reports_metadata()
        return jsonify(reports)
    except Exception as e:
        print(f"Error fetching reports from DB: {e}")
        return jsonify([]), 500

@app.route('/api/reports/<filename>', methods=['GET'])
def get_report(filename):
    """Serves the requested PDF file directly from the database."""
    if not filename.endswith('.pdf'):
        return "Invalid file format", 400
        
    pdf_bytes = subscribers.get_report_bytes(filename)
    if not pdf_bytes:
        return "Report not found", 404
        
    return pdf_bytes, 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'inline; filename="{filename}"'
    }

@app.route('/api/subscribers', methods=['GET'])
def list_subscribers():
    return jsonify({"subscribers": subscribers.get_active_emails()})

if __name__ == '__main__':
    app.run(debug=False, port=5000)
