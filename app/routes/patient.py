from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patient', methods=['GET'])
def patient_main():
    try:
        return render_template('patient.html')
    except TemplateNotFound:
        return abort(404)
