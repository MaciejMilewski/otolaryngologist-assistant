from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

instruction_bp = Blueprint('instruction', __name__)


@instruction_bp.route('/instruction', methods=['GET'])
def instruction_main():
    try:
        return render_template('instruction.html')
    except TemplateNotFound:
        return abort(404)
