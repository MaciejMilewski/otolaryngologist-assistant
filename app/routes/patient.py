from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patient', methods=['GET'])
@login_required
def patient_main():
    try:

        return render_template('patient.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
