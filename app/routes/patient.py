from flask import Blueprint, render_template, request, abort
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound
from sqlalchemy import and_

from app.models import Patient, Visit
from app import db

from math import ceil

ITEMS_PER_PAGE = 5  # Liczba wyników na stronę


patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patient', methods=['GET', 'POST'])
@login_required
def patient_main():
    results = None
    current_page = int(request.args.get('page', 1))  # Domyślnie pierwsza strona
    total_pages = 1                                  # Domyślnie jedna strona (gdy brak wyników)
    try:
        if request.method == 'POST':
            # Pobierz kryteria wyszukiwania
            first_name = request.form.get('first_name')
            surname = request.form.get('surname')
            pesel = request.form.get('pesel')
            city = request.form.get('city')
            nfz_info = request.form.get('nfz_info')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # Tworzenie dynamicznego filtra
            filters = []
            if first_name:
                filters.append(Patient.first_name.ilike(f"%{first_name}%"))
            if surname:
                filters.append(Patient.surname.ilike(f"%{surname}%"))
            if pesel:
                filters.append(Patient.pesel == pesel)
            if city:
                filters.append(Patient.city.ilike(f"%{city}%"))
            if nfz_info:
                filters.append(Visit.nfz_info.ilike(f"%{nfz_info}%"))
            if start_date and end_date:
                filters.append(Visit.examination_date.between(start_date, end_date))

            # Zapytanie z paginacją
            query = db.session.query(Patient).join(Visit).filter(*filters)
            total_results = query.count()
            total_pages = ceil(total_results / ITEMS_PER_PAGE)
            results = query.offset((current_page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

        return render_template(
            'patient.html',
            user=current_user.login,
            results=results,
            current_page=current_page,
            total_pages=total_pages,
        )
    except Exception as e:
        print(f"Error: {e}")
        return abort(500)

    except TemplateNotFound:
        return abort(404)

