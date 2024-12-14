from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

start_bp = Blueprint('start', __name__)


@start_bp.route('/', methods=['GET'])
def home():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        return abort(404)
