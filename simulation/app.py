"""
Simulation web app that mimics HealthConnect for testing.
"""
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import os

app = Flask(__name__)

# Storage for uploaded files
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
TEST_DATA_FOLDER = Path(__file__).parent / "test_data"
UPLOAD_FOLDER.mkdir(exist_ok=True)
TEST_DATA_FOLDER.mkdir(exist_ok=True)

# In-memory storage for attachments
attachments = []


def initialize_test_files():
    """Create test .txt files if they don't exist."""
    test_files = [
        {
            "name": "brief_neurologie_stam.txt",
            "content": """
SPECIALISTENBRIEF NEUROLOGIE

Van: Dr. J. Stam, Neuroloog
Aan: Huisarts

Betreft: Controle Multiple Sclerose

Geachte collega,

Patiënt bezocht mij op de polikliniek voor controle van de bekende Multiple Sclerose.

BEVINDINGEN:
Het klinisch beeld is stabiel. Geen nieuwe uitvalsverschijnselen.
MRI toont geen nieuwe laesies.

BELEID:
Voortzetting huidige medicatie (Interferon beta-1a).
Volgende controle over 6 maanden.

Met vriendelijke groet,
Dr. J. Stam
Neuroloog
""".strip()
        },
        {
            "name": "brief_longarts_boven_ij.txt",
            "content": """
SPECIALISTENBRIEF LONGZIEKTEN

Van: BovenIJ Ziekenhuis, afdeling Longziekten
Aan: Huisarts

Betreft: Spirometrie onderzoek

Geachte collega,

Patiënt onderging spirometrie onderzoek op onze afdeling.

BEVINDINGEN:
FEV1 60% van voorspeld, reversibiliteit 15% na bronchodilatatie.
Passend bij matig ernstig COPD GOLD II.

BELEID:
Start combinatietherapie ICS/LABA.
Adviseer stoppen roken.
Controle over 3 maanden.

Met vriendelijke groet,
Longarts BovenIJ Ziekenhuis
""".strip()
        },
        {
            "name": "brief_cardiologie_jansen.txt",
            "content": """
SPECIALISTENBRIEF CARDIOLOGIE

Van: Dr. P. Jansen, Cardioloog
Aan: Huisarts

Betreft: Hartfalen controle

Geachte collega,

Patiënt bezocht de hartfalenpoli voor controle.

BEVINDINGEN:
Klinisch beeld verbeterd sinds start sacubitril/valsartan.
Echo toont LVEF toegenomen naar 35%.
NT-proBNP gedaald naar 450 pg/mL.

BELEID:
Voortzetting huidige medicatie.
Diuretica dosering iets verlaagd.
Controle over 3 maanden.

Met vriendelijke groet,
Dr. P. Jansen
Cardioloog
""".strip()
        }
    ]

    for file_info in test_files:
        file_path = TEST_DATA_FOLDER / file_info["name"]
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])

        # Add to attachments list
        if not any(a["name"] == file_info["name"] for a in attachments):
            attachments.append({
                "id": len(attachments) + 1,
                "name": file_info["name"],
                "type": "txt",
                "logical_name": "",
                "summary": "",
                "path": str(file_path)
            })


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', attachments=attachments)


@app.route('/api/attachments')
def get_attachments():
    """Get list of attachments."""
    return jsonify(attachments)


@app.route('/api/download/<int:attachment_id>')
def download_attachment(attachment_id):
    """Download an attachment."""
    attachment = next((a for a in attachments if a["id"] == attachment_id), None)
    if not attachment:
        return jsonify({"error": "Attachment not found"}), 404

    file_path = Path(attachment["path"])
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)


@app.route('/api/upload', methods=['POST'])
def upload_attachment():
    """Upload a new attachment."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    logical_name = request.form.get('logical_name', '')
    summary = request.form.get('summary', '')
    document_type = request.form.get('document_type', 'specialistenbrief')

    # Save file
    filename = file.filename
    file_path = UPLOAD_FOLDER / filename
    file.save(file_path)

    # Add to attachments
    attachment = {
        "id": len(attachments) + 1,
        "name": filename,
        "type": "pdf",
        "logical_name": logical_name,
        "summary": summary,
        "document_type": document_type,
        "path": str(file_path)
    }
    attachments.append(attachment)

    return jsonify({
        "success": True,
        "attachment": attachment
    })


@app.route('/api/delete/<int:attachment_id>', methods=['DELETE'])
def delete_attachment(attachment_id):
    """Delete an attachment."""
    global attachments

    attachment = next((a for a in attachments if a["id"] == attachment_id), None)
    if not attachment:
        return jsonify({"error": "Attachment not found"}), 404

    # Remove from list
    attachments = [a for a in attachments if a["id"] != attachment_id]

    return jsonify({"success": True})


@app.route('/api/finalize', methods=['POST'])
def finalize_contact():
    """Finalize contact."""
    data = request.json
    financial_handling = data.get('financial_handling', 'none')

    # Just acknowledge the finalization
    return jsonify({
        "success": True,
        "financial_handling": financial_handling
    })


if __name__ == '__main__':
    initialize_test_files()
    app.run(host='0.0.0.0', port=3000, debug=True)
