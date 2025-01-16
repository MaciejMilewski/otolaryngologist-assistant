import logging
import os

from flask import Blueprint, render_template, abort, send_from_directory, jsonify
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

instruction_bp = Blueprint('instruction', __name__)

# Katalog zawierający pliki Instrukcji PDF
PDF_FOLDER = os.getcwd() + '\\app\\static\pdfs'
if not os.path.exists(PDF_FOLDER):
    os.makedirs('PDF_FOLDER', exist_ok=True)


@instruction_bp.route('/instruction', methods=['GET'])
@login_required
def instruction_main():
    try:
        # Pobieranie listy plików PDF
        pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
        return render_template('instruction.html', user=current_user.login, pdf_files=pdf_files)
    except TemplateNotFound:
        return abort(404)
    except Exception as e:
        logging.error(('Error: %s' % e))
        return jsonify({'error': str(e)}), 500


@instruction_bp.route('/pdfs/<filename>')
@login_required
def serve_pdf(filename):
    try:
        # Serwowanie pliku PDF
        return send_from_directory(PDF_FOLDER, filename)
    except TemplateNotFound:
        return abort(404)


# Endpoint zwracający listę plików w formacie JSON
@instruction_bp.route('/list_pdfs', methods=['GET'])
@login_required
def list_pdfs():
    try:
        pdf_files = [
            {
                "name": file,
                "date": os.path.getmtime(os.path.join(PDF_FOLDER, file))
            }
            for file in os.listdir(PDF_FOLDER) if file.endswith('.pdf')
        ]
        pdf_files.sort(key=lambda x: x['name'])  # Domyślne sortowanie po nazwie
        return jsonify(pdf_files)
    except Exception as e:
        logging.error(('Error: %s' % e))
        return jsonify({"error": str(e)}), 500
    except TemplateNotFound:
        return abort(404)
