from flask import Blueprint, render_template, abort, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.inspection import inspect
from jinja2 import TemplateNotFound

from app import db
from app.models import Procedure
from app.utils.const import W0, W1, W2, W3, W9, W10, W16
from app.utils.utils import get_icd_10, object_to_dict

procedure_bp = Blueprint('procedure', __name__)


# Zmienna globalna przechowująca dane ICD-10
data_icd = get_icd_10()


@procedure_bp.route('/procedure', methods=['GET'])
@login_required
def procedure_main():
    try:
        zabiegi = db.session.query(Procedure).all()

        zabiegi_json = [object_to_dict(zabieg) for zabieg in zabiegi]

        return render_template('procedure.html',
                               user=current_user.login,
                               lista_W0=W0,
                               lista_W1=W1,
                               lista_W2=W2,
                               lista_W3=W3,
                               lista_W9=W9,
                               lista_W10=W10,
                               lista_W16=W16,
                               the_best=2,
                               data=zabiegi_json
        )
    except TemplateNotFound:
        return abort(404)


@procedure_bp.route('/procedure_wynik_nfz', methods=['POST'])
@login_required
def procedure_wynik_nfz():
    try:
        lista_w1 = request.form.getlist('selektor_W1')
        lista_w2 = request.form.getlist('selektor_W2')
        lista_w3 = request.form.getlist('selektor_W3')
        lista_wx = request.form.getlist('selektor_WX')
        result_w01 = len(lista_w1)
        result_w02 = len(lista_w2)
        result_w03 = len(lista_w3)
        result_w09 = 0
        result_w10 = 0
        result_w16 = 0

        if len(lista_wx) > 0:
            for i in lista_wx:
                if int(i) < 100:
                    result_w09 += 1
                if (int(i) > 100) and (int(i) < 200):
                    result_w10 += 1
                if int(i) > 200:
                    result_w16 += 1
        best = 2
        if result_w01 > 0:
            best = 3
        if result_w16 > 0:
            best = 7
        if result_w09 > 0 or result_w10 > 0:
            best = 8
        if result_w01 > 2 or result_w02 == 1:
            best = 4
        if (result_w01 > 2 and result_w02 == 1) or (result_w02 == 1 and result_w16 > 0) or (result_w02 > 1) \
                or (result_w03 == 1):
            best = 5
        if (result_w01 > 2 and result_w03 == 1) or (result_w03 > 1) or (result_w10 > 1):
            best = 6

        zabiegi = db.session.query(Procedure).all()
        zabiegi_json = [object_to_dict(zabieg) for zabieg in zabiegi]

        return render_template('procedure.html',
                               user=current_user.login,
                               lista_W0=W0,
                               lista_W1=W1,
                               lista_W2=W2,
                               lista_W3=W3,
                               lista_W9=W9,
                               lista_W10=W10,
                               lista_W16=W16,
                               the_best=best,
                               data=zabiegi_json
        )
    except TemplateNotFound:
        return abort(404)


@procedure_bp.route('/body_mass_index', methods=['POST'])
@login_required
def body_mass_index():
    try:
        # Pobieranie danych z żądania JSON
        mass = request.json.get('weight', None)
        height = request.json.get('height', None)

        # Walidacja obecności danych
        if mass is None or height is None:
            return jsonify({'error': 'Dane są wymagane!'}), 400

        try:
            # Konwersja danych na float
            index_mass = float(mass)
            index_height = float(height)

            # Walidacja wartości
            if index_mass <= 0 or index_height <= 0:
                return jsonify({'error': 'Wartości muszą być dodatnie!', 'bmi': ' - wszystkie liczby muszą być dodatnie'}), 400

            # Obliczenie BMI
            bmi = round(index_mass / (index_height * index_height * 0.0001), 1)
            return jsonify({'bmi': bmi}), 200

        except ValueError:
            # Obsługa błędu przy rzutowaniu na float
            return jsonify({'error': 'Nieprawidłowe dane wejściowe. Podaj liczby!'}), 400

    except Exception as e:
        # Ogólna obsługa błędów
        return jsonify({'error': f'Wystąpił nieoczekiwany błąd: {str(e)}'}), 500


@procedure_bp.route('/search_icd10', methods=['GET', 'POST'])
@login_required
def search_icd10():
    try:
        if request.method == "POST":
            search_term = request.json.get("icd10Code", None)

            if not search_term:
                return jsonify({'error': 'tekst jest wymagany!'}), 400

            search_term = search_term.lower()

            code = []
            for paragraph in data_icd:
                if search_term in paragraph.lower():
                    code.append(paragraph)
            if len(code) < 1:
                code.append(search_term.upper() + ' - nie znaleziono !')

            return jsonify({'result': code}), 200

    except TemplateNotFound:
        return abort(404)
