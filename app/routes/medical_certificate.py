from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

medical_certificate_bp = Blueprint('medical_certificate', __name__)


@medical_certificate_bp.route('/medical_certificate', methods=['GET'])
@login_required
def medical_certificate_main():
    try:
        return render_template('medical_certificate.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
