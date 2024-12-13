from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        return abort(404)

