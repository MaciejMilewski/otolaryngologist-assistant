import logging
from math import ceil
from app.utils.const import typ_badan, place
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Patient, Visit, MedicalCertificate, Audiogram

ITEMS_PER_PAGE = 5  # Liczba pacjentów na stronę
VISITS_PER_PAGE = 5  # Liczba wizyt na stronę
CERTIFICATES_PER_PAGE = 5 # Liczba orzeczeń na stronę


patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/patient', methods=['GET', 'POST'])
@login_required
def patient_main():
    try:
        # Paginacja
        current_page = int(request.args.get('page', 1))
        visit_page = int(request.args.get('visit_page', 1))
        certificate_page = int(request.args.get('certificate_page', 1))
        search_mode = request.form.get('search_mode', 'visit')
        if request.args.get('search_mode'):
            search_mode = request.args.get('search_mode')

        # Filtry
        filters = []
        joins_required = False
        search_what_prefix = ""

        # Obsługa filtrów z formularza
        first_name = request.form.get('first_name')
        surname = request.form.get('surname')
        pesel = request.form.get('pesel')
        city = request.form.get('city')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if first_name:
            filters.append(Patient.first_name.ilike(f"%{first_name}%"))
            search_what_prefix += f"{first_name} "
        if surname:
            filters.append(Patient.surname.ilike(f"%{surname}%"))
            search_what_prefix += f"{surname} "
        if pesel:
            filters.append(Patient.pesel == pesel)
            search_what_prefix += f"{pesel} "
        if city:
            filters.append(Patient.city.ilike(f"%{city}%"))
            search_what_prefix += f"{city} "
        if start_date and end_date:
            filters.append(Visit.examination_date.between(start_date, end_date))
            search_what_prefix += f"{start_date} - {end_date} "
            joins_required = True

        # Pobieranie pacjentów powiązanych z aktualnym użytkownikiem
        visit_query = (
            db.session.query(Patient.id)
            .join(Visit, Visit.patient_id == Patient.id)  # Jawne łączenie
            .filter(Visit.user_id == current_user.id, Visit.is_active == True)
        )

        certificate_query = (
            db.session.query(Patient.id)
            .join(MedicalCertificate, MedicalCertificate.patient_id == Patient.id)  # Jawne łączenie
            .filter(MedicalCertificate.user_id == current_user.id, MedicalCertificate.is_active == True)
        )

        # Łączenie wyników z wizyt i certyfikatów
        patient_ids = visit_query.union(certificate_query).subquery()

        query = db.session.query(Patient).filter(Patient.id.in_(db.session.query(patient_ids)))
        if filters:
            query = query.filter(*filters)

        total_patients = query.count()
        total_pages = ceil(total_patients / ITEMS_PER_PAGE)

        patients = (
            query.offset((current_page - 1) * ITEMS_PER_PAGE)
            .limit(ITEMS_PER_PAGE)
            .all()
        )

        # Obsługa szczegółowych danych (wizyty, audiogramy, certyfikaty)
        for patient in patients:
            visit_query = (
                db.session.query(Visit)
                .outerjoin(Audiogram, Audiogram.visit_id == Visit.id)  # Audiogramy
                .filter(Visit.patient_id == patient.id, Visit.is_active == True)
                .options(db.contains_eager(Visit.audiograms))
            )

            total_visits = visit_query.count()
            visit_total_pages = ceil(total_visits / VISITS_PER_PAGE)

            visits = visit_query.offset((visit_page - 1) * VISITS_PER_PAGE).limit(VISITS_PER_PAGE).all()

            # Uzupełnienie wizyt o audiogramy
            for visit in visits:
                visit.audiogram_data = (
                    db.session.query(Audiogram).filter_by(visit_id=visit.id).first()
                )

            patient.limited_visits = visits
            patient.visit_current_page = visit_page
            patient.visit_total_pages = visit_total_pages
            patient.visit_has_prev = visit_page > 1
            patient.visit_has_next = visit_page < visit_total_pages

            # Obsługa certyfikatów
            certificate_query = (
                db.session.query(MedicalCertificate)
                .filter_by(patient_id=patient.id, is_active=True)
            )
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
            search_mode=search_mode,
            typ_badan_dict=typ_badan,
            search_what=search_what_prefix.strip(),
        )
    except Exception as e:
        logging.error(f"Error in patient_main: {e}")
        return abort(500)


@patient_bp.route('/edit/<string:visit_type>/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_visit(visit_type, record_id):
    # Pobranie rekordu na podstawie typu
    if visit_type == 'visit':
        record = Visit.query.get_or_404(record_id)
        model_class = Visit
    elif visit_type == 'medical_certificate':
        record = MedicalCertificate.query.get_or_404(record_id)
        model_class = MedicalCertificate
    else:
        flash('Nieprawidłowy typ rekordu.', 'danger')
        return redirect(url_for('patient.patient_main'))

    # Pobranie audiogramu dla wizyty, jeśli istnieje
    audio_record = None
    if visit_type == 'visit':
        audio_record = Audiogram.query.filter_by(visit_id=record_id, audiogram_date=record.examination_date).first()

    if request.method == 'POST':
        try:
            # Skopiowanie istniejącego rekordu
            new_record = model_class(**{column.name: getattr(record, column.name)
                                        for column in model_class.__table__.columns if column.name != 'id'})

            # Aktualizacja danych dla nowego rekordu
            if visit_type == 'medical_certificate':
                new_record.type = int(request.form.get('type', record.type))
                new_record.info = request.form.get('info', record.info)
                new_record.is_able_to_work = 'is_able_to_work' in request.form
                selected_location = next(
                    (item['name'] for item in place if item['id'] == request.form.get('location')),
                    record.location
                )
                new_record.location = selected_location
                created_at = request.form.get('created_at')
                if created_at:
                    new_record.created_at = datetime.strptime(created_at, '%Y-%m-%d').date()
                else:
                    flash('Pole "Data utworzenia" jest wymagane.', 'danger')
                    return redirect(request.url)

            elif visit_type == 'visit':
                new_record.location = request.form.get('location', record.location)
                new_record.examination_date = datetime.strptime(
                    request.form.get('examination_date', record.examination_date), '%Y-%m-%d'
                ).date()
                new_record.interview = request.form.get('interview', record.interview)
                new_record.general_info = request.form.get('general_info', record.general_info)
                new_record.examination = request.form.get('examination', record.examination)
                new_record.orl = request.form.get('orl', record.orl)
                new_record.whisper_test = request.form.get('whisper_test', record.whisper_test)
                new_record.routine = request.form.get('routine', record.routine)
                new_record.diagnosis = request.form.get('diagnosis', record.diagnosis)
                new_record.nfz_info = request.form.get('nfz_info', record.nfz_info)
                new_record.recommendations = request.form.get('recommendations', record.recommendations)

                # Aktualizacja audiogramu, jeśli istnieje
                if audio_record:
                    audio_record.audiogram_date = datetime.strptime(
                        request.form.get('audiogram_date', audio_record.audiogram_date), '%Y-%m-%d'
                    ).date()
                    for freq in ['ul_250', 'ul_500', 'ul_1000', 'ul_2000', 'ul_3000', 'ul_4000', 'ul_6000', 'ul_8000',
                                 'up_250', 'up_500', 'up_1000', 'up_2000', 'up_3000', 'up_4000', 'up_6000', 'up_8000']:
                        setattr(audio_record, freq, request.form.get(freq, getattr(audio_record, freq)))

            # Ustawienie starego rekordu jako nieaktywnego
            record.is_active = False

            # Dodanie nowego rekordu do bazy
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('patient.patient_main'))
        except Exception as e:
            db.session.rollback()
            logging.error(f'Błąd podczas zapisu: {str(e)}', {current_user.login})
            return redirect(request.url)

    return render_template('patient_visit_edit.html',
                           visit_type=visit_type,
                           record=record,
                           audiogram=audio_record,
                           typ_badan=typ_badan,
                           place=place,
                           current_user=current_user.login)


@patient_bp.route('/visit/delete/<int:visit_id>', methods=['POST'])
@login_required
# Nie ma usuwania rekordów, tylko ich dezaktywacja is_active = False, czyli 0
def delete_visit(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    db.session.delete(visit)
    db.session.commit()

    return redirect(url_for('patient.patient_main'))


@patient_bp.route('/visit/deactivate/<int:visit_id>', methods=['POST'])
@login_required
def deactivate_visit(visit_id):
    visit = Visit.query.get_or_404(visit_id)

    # Sprawdź, czy użytkownik ma prawo edytować
    if visit.user_id != current_user.id:
        flash('Nie masz uprawnień do dezaktywacji tej wizyty.', 'danger')
        return redirect(url_for('patient.patient_main'))

    visit.is_active = False
    db.session.commit()

    return redirect(url_for('patient.patient_main'))


@patient_bp.route('/certificate/deactivate/<int:record_id>', methods=['POST'])
@login_required
def deactivate_certificate(record_id):
    # Pobranie orzeczenia z bazy danych
    certificate = MedicalCertificate.query.get_or_404(record_id)

    # Sprawdzenie, czy użytkownik ma prawo do dezaktywacji
    if certificate.user_id != current_user.id:
        flash('Nie masz uprawnień do dezaktywacji tego orzeczenia.', 'danger')
        return redirect(url_for('patient.patient_main'))

    certificate.is_active = False
    db.session.commit()

    flash('Orzeczenie zostało dezaktywowane!', 'success')
    return redirect(url_for('patient.patient_main'))