import logging

from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from app.models import Patient, Visit, MedicalCertificate
from app import db

from math import ceil

from app.utils.const import typ_badan

ITEMS_PER_PAGE = 5  # Liczba pacjentów na stronę
VISITS_PER_PAGE = 5  # Liczba wizyt na stronę
CERTIFICATES_PER_PAGE = 5

patient_bp = Blueprint('patient', __name__)


# @patient_bp.route('/patient', methods=['GET', 'POST'])
# @login_required
# def patient_main():
#     try:
#         current_page = int(request.args.get('page', 1))  # Paginacja pacjentów
#         visit_page = int(request.args.get('visit_page', 1))  # Paginacja wizyt
#         filters = []
#         typ_badan_dict = {badanie['id']: badanie['name'] for badanie in typ_badan}
#         joins_required = False
#         # Wyniki do przekazania do szablonu (puste domyślnie)
#         patients = []
#         total_pages = 0
#
#         if request.method == 'POST':
#             first_name = request.form.get('first_name')
#             surname = request.form.get('surname')
#             pesel = request.form.get('pesel')
#             city = request.form.get('city')
#             nfz_info = request.form.get('nfz_info')
#             start_date = request.form.get('start_date')
#             end_date = request.form.get('end_date')
#
#             if first_name:
#                 filters.append(Patient.first_name.ilike(f"%{first_name}%"))
#             if surname:
#                 filters.append(Patient.surname.ilike(f"%{surname}%"))
#             if pesel:
#                 filters.append(Patient.pesel == pesel)
#             if city:
#                 filters.append(Patient.city.ilike(f"%{city}%"))
#             if nfz_info:
#                 filters.append(Visit.nfz_info.ilike(f"%{nfz_info}%"))
#                 joins_required = True
#             if start_date and end_date:
#                 filters.append(Visit.examination_date.between(start_date, end_date))
#                 joins_required = True
#
#         # Pobieranie pacjentów z paginacją
#         query = db.session.query(Patient).filter(*filters)
#         # Dodaje filtry tylko jeżeli istnieją, nie wyświetlamy starych wyników
#         # if filters:
#         #     query = query.filter(*filters)
#         total_patients = query.count()
#         total_pages = ceil(total_patients / ITEMS_PER_PAGE)
#
#         patients = query.offset((current_page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
#
#         # Dodanie paginacji wizyt do każdego pacjenta
#         for patient in patients:
#             visit_query = db.session.query(Visit).filter_by(patient_id=patient.id)
#             total_visits = visit_query.count()
#             visit_total_pages = ceil(total_visits / VISITS_PER_PAGE)
#
#             patient.limited_visits = visit_query.offset((visit_page - 1) * VISITS_PER_PAGE).limit(
#                 VISITS_PER_PAGE).all()
#             patient.visit_current_page = visit_page
#             patient.visit_total_pages = visit_total_pages
#             patient.visit_has_prev = visit_page > 1
#             patient.visit_has_next = visit_page < visit_total_pages
#
#         # Przy żądaniu GET, ustal pustą odpowiedź
#         # if request.method == 'GET' and not filters:
#             # patients = []
#             # total_patients = 0
#             # total_pages = 1
#
#         # Zwrot odpowiedzi
#         return render_template(
#             'patient.html',
#             current_user=current_user.login,
#             results=patients,
#             current_page=current_page,
#             total_pages=total_pages,
#             has_prev=current_page > 1,
#             has_next=current_page < total_pages,
#             typ_badan_dict=typ_badan_dict
#         )
#     except Exception as e:
#         print(f"Error in patient_main: {e}")
#         return abort(500)


@patient_bp.route('/patient', methods=['GET', 'POST'])
@login_required
def patient_main():
    try:
        current_page = int(request.args.get('page', 1))  # Paginacja pacjentów
        visit_page = int(request.args.get('visit_page', 1))  # Paginacja wizyt
        certificate_page = int(request.args.get('certificate_page', 1))  # Paginacja orzeczeń
        search_mode = request.form.get('search_mode', 'visit')
        if request.args.get('search_mode'):
            search_mode = request.args.get('search_mode')

        filters = []
        typ_badan_dict = {badanie['id']: badanie['name'] for badanie in typ_badan}
        joins_required = False

        # Wyniki do przekazania do szablonu (puste domyślnie)
        patients = []
        total_pages = 0

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            surname = request.form.get('surname')
            pesel = request.form.get('pesel')
            city = request.form.get('city')
            nfz_info = request.form.get('nfz_info')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

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
                joins_required = True
            if start_date and end_date:
                filters.append(Visit.examination_date.between(start_date, end_date))
                joins_required = True

        # Pobieranie pacjentów z paginacją
        query = db.session.query(Patient).filter(*filters)
        total_patients = query.count()
        total_pages = ceil(total_patients / ITEMS_PER_PAGE)

        patients = query.offset((current_page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

        # Dodanie paginacji wizyt i orzeczeń do każdego pacjenta
        for patient in patients:
            # Wizyty
            visit_query = db.session.query(Visit).filter_by(patient_id=patient.id)
            total_visits = visit_query.count()
            visit_total_pages = ceil(total_visits / VISITS_PER_PAGE)

            patient.limited_visits = visit_query.offset((visit_page - 1) * VISITS_PER_PAGE).limit(VISITS_PER_PAGE).all()
            patient.visit_current_page = visit_page
            patient.visit_total_pages = visit_total_pages
            patient.visit_has_prev = visit_page > 1
            patient.visit_has_next = visit_page < visit_total_pages

            # Orzeczenia
            certificate_query = db.session.query(MedicalCertificate).filter_by(patient_id=patient.id)
            total_certificates = certificate_query.count()
            certificate_total_pages = ceil(total_certificates / CERTIFICATES_PER_PAGE)

            patient.limited_medical_certificates = certificate_query.offset(
                (certificate_page - 1) * CERTIFICATES_PER_PAGE
            ).limit(CERTIFICATES_PER_PAGE).all()
            patient.certificate_current_page = certificate_page
            patient.certificate_total_pages = certificate_total_pages
            patient.certificate_has_prev = certificate_page > 1
            patient.certificate_has_next = certificate_page < certificate_total_pages

        # Zwrot odpowiedzi
        return render_template(
            'patient.html',
            current_user=current_user.login,
            results=patients,
            current_page=current_page,
            total_pages=total_pages,
            has_prev=current_page > 1,
            has_next=current_page < total_pages,
            typ_badan_dict=typ_badan_dict,
            search_mode=search_mode
        )
    except Exception as e:
        logging.error(f"Error in patient_main: {e}")
        return abort(500)
