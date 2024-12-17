from flask import Blueprint, render_template, abort
from flask_login import login_required
from jinja2 import TemplateNotFound

visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/visit', methods=['GET'])
@login_required
def main_form():
    try:
        return render_template('visit.html')
    except TemplateNotFound:
        return abort(404)