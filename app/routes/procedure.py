from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

procedure_bp = Blueprint('procedure', __name__)


@procedure_bp.route('/procedure', methods=['GET'])
def procedure_main():
    try:
        return render_template('procedure.html')
    except TemplateNotFound:
        return abort(404)
