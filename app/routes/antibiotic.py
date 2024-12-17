from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

antibiotic_bp = Blueprint('antibiotic', __name__)


@antibiotic_bp.route('/antibiotic', methods=['GET'])
@login_required
def antibiotic_main():
    try:
        return render_template('antibiotic.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
