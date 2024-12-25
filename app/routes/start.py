from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from app import dane_woj, parquet_data
from app.utils.gus_api import get_wojewodztwa
from app.utils.parquet_util import get_streets_from_memory

start_bp = Blueprint('start', __name__)


@start_bp.route('/', methods=['GET'])
def home():
    try:
        print("Województwa wywołane w start.py: ", dane_woj)

        if 'POMORSKIE' in parquet_data:
            miejscowosc_choices = parquet_data["POMORSKIE"]['Nazwa'].tolist()  # Wczytaj miejscowości
        else:
            miejscowosc_choices = []  # Pusta lista, jeśli nie zostały wczytane

        default_miejscowosc = "Pruszcz Gdański"

        # Pobierz ulice dla domyślnej miejscowości
        ulica_choices = get_streets_from_memory("POMORSKIE", default_miejscowosc)
        print("ulica_choices: ", ulica_choices)

        return render_template('index.html')
    except TemplateNotFound:
        return abort(404)
