from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/schedule', methods=['GET'])
def schedule_main():
    try:
        return render_template('schedule.html')
    except TemplateNotFound:
        return abort(404)
