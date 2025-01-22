import logging
from datetime import date
from io import BytesIO
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, abort, jsonify, send_file, flash, redirect
from flask_login import login_required, current_user

from jinja2 import TemplateNotFound

from app import db, parquet_data, region_data, search_cities_in_trie, search_streets_in_trie
from app.models import Procedure, Patient
from app.utils.const import place
from app.utils.parquet_util import get_streets_from_memory

from app.utils.utils import (ogolne_items, orl_items, validate_request_badania, validate_request_structure_main,
                             validate_request_szept, zalecenia, generate_pdf, save_visit_to_db,
                             object_to_dict)

from typing import List, Optional

ALLOWED_FIELDS = {'pesel', 'surname'}


def get_data_to_autocomplete(query: str, field: str) -> Optional[List[List]]:
    if field not in ALLOWED_FIELDS:
        raise ValueError("Invalid -field- parameter in autocomplete")
    try:
        # Otwórz nową sesję
        # Dynamiczne filtrowanie za pomocą getattr
        result = db.session.query(Patient).filter(getattr(Patient, field).like(f"{query}%")).all()
        # Zwrócenie tylko pożądanych pól
        fields_to_return = ['id', 'first_name', 'surname', 'pesel', 'gender', 'state', 'city', 'street',
                            'apartment_number']
        # Konwersja wyników na listę krotek z wszystkimi kolumnami
        return [[getattr(row, field) for field in fields_to_return] for row in result]
    except Exception as e:
        logging.error(f"Problem with database and data downloaded for autocomplete: {e}")
        return []


visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/visit', methods=['GET'])
@login_required
def main_form():
    try:
        surgical_routine = db.session.query(Procedure).all()

        if not surgical_routine:
            logging.error("No surgical procedures found in the database.")
            surgical_routine_json = []
        else:
            surgical_routine_json = [object_to_dict(routine) for routine in surgical_routine]

        return render_template('visit.html', user=current_user.login, zabiegi=surgical_routine_json)
    except TemplateNotFound:
        return abort(404)


@visit_bp.route('/generuj', methods=['POST'])
@login_required
def generuj():
    try:
        dane = request.form

        surgical_routines = dane.getlist('selectZabiegi')
        general_conditions = validate_request_badania(ogolne_items, dane)
        orl_validation_result = validate_request_badania(orl_items, dane)
        orl = validate_request_structure_main(dane)
        whisper = validate_request_szept(dane)
        recommendations = zalecenia(dane)

        today = date.today().strftime("%d-%m-%Y")

        voivodeship_default = '22'  # Domyślne województwo - "POMORSKIE" (kod '22')

        # Sprawdź, czy dane województwa są wczytane poprawnie
        if 'POMORSKIE' in parquet_data:
            pomorskie_cities = parquet_data["POMORSKIE"]['Nazwa'].tolist()  # Wczytaj miejscowości
        else:
            pomorskie_cities = []  # Pusta lista, jeśli nie zostały wczytane
            logging.error('Pomeranian Voivodeship missing in parquet_data?')

        default_city = "Pruszcz Gdański"

        # Pobierz ulice dla domyślnej miejscowości
        streets_list = get_streets_from_memory("POMORSKIE", default_city)

        return render_template('visit_result.html', today=today, wywiad=dane['wywiad'],
                               ogolne=general_conditions, laryngolog=orl_validation_result,
                               data_szeptu=dane.get('data_badania'),
                               orl=orl, szept=whisper, zabiegi=surgical_routines, zalecenia=recommendations,
                               UL_250=dane.get('UL_250'),
                               UL_500=dane.get('UL_500'), UL_1000=dane.get('UL_1000'), UL_2000=dane.get('UL_2000'),
                               UL_3000=dane.get('UL_3000'), UL_4000=dane.get('UL_4000'), UL_6000=dane.get('UL_6000'),
                               UL_8000=dane.get('UL_8000'), UP_250=dane.get('UP_250'), UP_500=dane.get('UP_500'),
                               UP_1000=dane.get('UP_1000'), UP_2000=dane.get('UP_2000'), UP_3000=dane.get('UP_3000'),
                               UP_4000=dane.get('UP_4000'), UP_6000=dane.get('UP_6000'), UP_8000=dane.get('UP_8000'),
                               data_audiogramu=dane.get('data_badania_audiogramu'),
                               place=place,
                               woj=region_data,
                               woj_default=voivodeship_default,
                               cities=pomorskie_cities,
                               city_default=default_city,
                               streets=streets_list)

    except TemplateNotFound:
        return abort(404)


@visit_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '').strip()
    field = request.args.get('field', '').strip()

    try:
        results = get_data_to_autocomplete(query, field)
        if results:
            results = [list(row) for row in results]  # Konwersja tupli na listy
        else:
            results = []
    except Exception as e:
        logging.error(f"Internal server error, {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    return jsonify(results)


@visit_bp.route('/get_miejscowosci', methods=['GET','POST'])
def get_miejscowosci():
    try:
        data = request.get_json()

        prefix = data.get('q', '').lower()
        province_name = data.get('province_name', '')

        print("Province:", province_name)
        print("Prefix city:", prefix)

        if len(prefix) < 2:
            return jsonify([])

        if not prefix or not province_name:
            return jsonify([]), 400

        results = search_cities_in_trie(prefix, province_name)
        print("Cities", results)
        return jsonify(results), 200
    except Exception as e:
        print("Error:", e)
        return jsonify([]), 500


@visit_bp.route('/get_ulice', methods=['GET','POST'])
def get_ulice():
    try:
        data = request.get_json()
        prefix = data.get('q', '').strip().lower()
        sym = data.get('sym')

        print("Prefix street", prefix)
        print("sym", sym)

        if not prefix or len(prefix) < 3:
            return jsonify([])  # Za mało znaków w zapytaniu

        if not prefix or not sym:
            return jsonify([])

        results = search_streets_in_trie(prefix, sym)
        print("Streets", results)
        return jsonify(results)
    except ValueError:
        return jsonify([])


@visit_bp.route('/drukuj', methods=['POST'])
@login_required
def drukuj():
    dane = request.form
    try:
        save_visit_to_db(dane, current_user.id)

        pdf = generate_pdf(dane)

        buffer = BytesIO(pdf)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf',
                         download_name=f"{dane.get("first_name")}_{dane.get("surname")}.pdf",
                         as_attachment=True)
    except IntegrityError as e:
        logging.error(f"Błąd podczas generowania PDF: {str(e)}")
        return redirect('/visit')
    except Exception as e:
        logging.error(f"Nieoczekiwany błąd podczas generowania PDF: {str(e)}")
        return redirect('/visit')


@visit_bp.route('/zapis', methods=['POST'])
@login_required
def zapis_wizyty_do_bazy():
    dane = request.form
    try:
        save_visit_to_db(dane, current_user.id)

        flash("Zapisano pomyślnie dane wizyty w bazie danych!", "success")
        return redirect('/visit')
    except IntegrityError as e:
        logging.error(f"Database write error: {e}")
        flash(f"Błąd zapisu bazy danych: {e}", "danger")
        return redirect('/visit')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        flash(f"Nieoczekiwany błąd: {e}", "danger")
        return redirect('/visit')
