from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

instruction_bp = Blueprint('instruction', __name__)


@instruction_bp.route('/instruction', methods=['GET'])
@login_required
def instruction_main():
    try:
        return render_template('instruction.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
