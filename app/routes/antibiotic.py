from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

antibiotic_bp = Blueprint('antibiotic', __name__)


@antibiotic_bp.route('/antibiotic', methods=['GET'])
def antibiotic_main():
    try:
        return render_template('antibiotic.html')
    except TemplateNotFound:
        return abort(404)
