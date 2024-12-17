from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

procedure_bp = Blueprint('procedure', __name__)


@procedure_bp.route('/procedure', methods=['GET'])
@login_required
def procedure_main():
    try:
        return render_template('procedure.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
