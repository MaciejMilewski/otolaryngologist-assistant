from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/schedule', methods=['GET'])
@login_required
def schedule_main():
    try:
        return render_template('schedule.html', user=current_user.login)
    except TemplateNotFound:
        return abort(404)
