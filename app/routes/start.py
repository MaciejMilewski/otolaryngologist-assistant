from datetime import datetime

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from app.utils.gus_api import client_soap

start_bp = Blueprint('start', __name__)


@start_bp.route('/', methods=['GET'])
def home():
    try:
        data_stanu = datetime.now().strftime('%Y-%m-%d')
        result = client_soap.service.PobierzListeWojewodztw(DataStanu=data_stanu)
        # Tworzenie słownika: kluczem jest kod województwa, wartością jego nazwa
        wojewodztwa_dict = {woj.WOJ: woj.NAZWA for woj in result}
        print(wojewodztwa_dict)
        return render_template('index.html')
    except TemplateNotFound:
        return abort(404)
