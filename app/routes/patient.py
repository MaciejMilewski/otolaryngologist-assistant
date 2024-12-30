from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from app.models import Patient, Visit, MedicalCertificate
from app import db

from math import ceil

ITEMS_PER_PAGE = 5  # Liczba pacjentów na stronę
VISITS_PER_PAGE = 5  # Liczba wizyt na stronę

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patient', methods=['GET', 'POST'])
@login_required
def patient_main():
    try:
        current_page = int(request.args.get('page', 1))  # Paginacja pacjentów
        search_mode = request.form.get('search_mode', 'visit')  # Domyślny tryb to 'visit'

        filters = []
        joins_required = False
        results = []
        total_pages = 0

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            surname = request.form.get('surname')
            pesel = request.form.get('pesel')
            city = request.form.get('city')
            nfz_info = request.form.get('nfz_info')  # Tylko dla wizyt
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # Filtry wspólne dla obu trybów
            if first_name:
                filters.append(Patient.first_name.ilike(f"%{first_name}%"))
            if surname:
                filters.append(Patient.surname.ilike(f"%{surname}%"))
            if pesel:
                filters.append(Patient.pesel == pesel)
            if city:
                filters.append(Patient.city.ilike(f"%{city}%"))

            # Tryb wyszukiwania badań (visit)
            if search_mode == 'visit':
                if nfz_info:
                    filters.append(Visit.nfz_info.ilike(f"%{nfz_info}%"))
                    joins_required = True
                if start_date and end_date:
                    filters.append(Visit.examination_date.between(start_date, end_date))
                    joins_required = True

                # Zapytanie dla wizyt
                query = db.session.query(Patient).filter(*filters)
                if joins_required:
                    query = query.join(Visit)

                total_results = query.count()
                total_pages = ceil(total_results / ITEMS_PER_PAGE)

                results = query.offset((current_page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

                # Paginacja wizyt
                for patient in results:
                    visit_query = db.session.query(Visit).filter_by(patient_id=patient.id)
                    total_visits = visit_query.count()
                    visit_total_pages = ceil(total_visits / VISITS_PER_PAGE)

                    patient.limited_visits = visit_query.offset((current_page - 1) * VISITS_PER_PAGE).limit(
                        VISITS_PER_PAGE).all()
                    patient.visit_current_page = current_page
                    patient.visit_total_pages = visit_total_pages
                    patient.visit_has_prev = current_page > 1
                    patient.visit_has_next = current_page < visit_total_pages

            # Tryb wyszukiwania orzeczeń (medical_certificate)
            elif search_mode == 'medical_certificate':
                if start_date and end_date:
                    filters.append(MedicalCertificate.created_at.between(start_date, end_date))

                # Zapytanie dla orzeczeń
                query = db.session.query(Patient).filter(*filters).join(MedicalCertificate)

                total_results = query.count()
                total_pages = ceil(total_results / ITEMS_PER_PAGE)

                results = query.offset((current_page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

                # Paginacja orzeczeń
                for patient in results:
                    certificate_query = db.session.query(MedicalCertificate).filter_by(patient_id=patient.id)
                    total_certificates = certificate_query.count()
                    certificate_total_pages = ceil(total_certificates / VISITS_PER_PAGE)

                    patient.limited_certificates = certificate_query.offset((current_page - 1) * VISITS_PER_PAGE).limit(
                        VISITS_PER_PAGE).all()
                    patient.certificate_current_page = current_page
                    patient.certificate_total_pages = certificate_total_pages
                    patient.certificate_has_prev = current_page > 1
                    patient.certificate_has_next = current_page < certificate_total_pages

        # Zwrot odpowiedzi
        return render_template(
            'patient.html',
            current_user=current_user.login,
            results=results,
            search_mode=search_mode,
            current_page=current_page,
            total_pages=total_pages,
            has_prev=current_page > 1,
            has_next=current_page < total_pages
        )
    except Exception as e:
        print(f"Error in patient_main: {e}")
        return abort(500)
