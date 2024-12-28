from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from app import dane_woj, parquet_data
from app.utils.gus_api import get_wojewodztwa
from app.utils.parquet_util import get_streets_from_memory

start_bp = Blueprint('start', __name__)


@start_bp.route('/', methods=['GET'])
def home():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        return abort(404)
