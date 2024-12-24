import sqlite3
from datetime import date, timedelta, datetime
from sqlite3 import connect

from flask import Blueprint, render_template, abort, flash, request, redirect, url_for, jsonify
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Schedule
from app.utils.utils import validate_event_collision

schedule_bp = Blueprint('schedule', __name__)


def get_schedule_events(user_id, start, end):
    try:
        events = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_date >= start,
            Schedule.start_date <= end
        ).all()
        return [
            {
                "id": event.id,
                "id_user": current_user.id,
                "title": event.title,
                "url": event.url,
                "description": event.description,
                "start_date": event.start_date.strftime("%Y-%m-%d"),
                "start_time": event.start_time,
                "end_date": event.end_date.strftime("%Y-%m-%d"),
                "end_time": event.end_time,
                "color_back": event.color_back,
                "color_fore": event.color_fore
            }
            for event in events
        ]
    except SQLAlchemyError as e:
        flash(f"Błąd bazy danych: {str(e)}", 'danger')
        return []


@schedule_bp.route('/schedule', methods=['GET'])
@login_required
def schedule_main():
    try:
        start = date.today().replace(day=1)
        end = date.today().replace(day=1) + timedelta(days=120)

        calendar_view = 'dayGridMonth'
        events = get_schedule_events(current_user.id, start, end)
        print(events)
        return render_template('schedule.html', events=events, calendar_view=calendar_view, user=current_user.login)
    except TemplateNotFound:
        return abort(404)


@schedule_bp.route('/schedule/insert', methods=["GET", "POST"])
@login_required
def schedule_insert():
    calendar_view = request.form.get('modal_dodaj_view', 'dayGridMonth')

    if request.method == "POST":
        title = request.form.get('title', '').strip()
        start = request.form.get('start', '').strip()
        end = request.form.get('end', '').strip() or start
        url = request.form.get('url', '').strip()
        desc = request.form.get('desc', '').strip()
        color_back = request.form.get('setcolor', "#FFFFFF").strip()
        color_fore = request.form.get('setlitery', "#000000").strip()
        start_time = request.form.get('start_time', "00:00").strip()
        end_time = request.form.get('end_time', "23:59").strip()

        # Tworzenie obiektów datetime
        try:
            start_date = datetime.strptime(f"{start} {start_time}", "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(f"{end} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            flash("Nieprawidłowy format daty lub czasu.", "danger")
            return redirect(url_for('schedule.schedule_main'))

        event_collision, error_message = validate_event_collision(current_user.id, start_date, end_date)
        if not event_collision:
            flash(error_message, "danger")
            return redirect(url_for('schedule.schedule_main'))

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()

            new_event = Schedule(
                user_id=current_user.id,
                title=title,
                description=desc,
                url=url,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                color_back=color_back,
                color_fore=color_fore
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Wydarzenie zostało dodane!', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Błąd podczas dodawania wydarzenia: {str(e)}", 'danger')

    start = date.today().replace(day=1)
    ender = date.today().replace(day=1) + timedelta(days=120)
    list_events = get_schedule_events(current_user.id, start, ender)
    print("Po dodaniu")
    print(list_events)

    return render_template("schedule.html", events=list_events, calendar_view=calendar_view, user=current_user.login)


@schedule_bp.route("/schedule/delete", methods=["POST"])
@login_required
def schedule_delete():
    # Pobierz widok kalendarza i ID wydarzenia z formularza
    calendar_view = request.form.get('modal_delete_view', 'dayGridMonth')
    data = request.get_json()
    event_id = data.get('id')

    if not event_id:
        flash("Nie podano ID wydarzenia do usunięcia.", "danger")
        return redirect(url_for('schedule.schedule_main'))

    try:
        # Znajdź wydarzenie w bazie danych
        event = Schedule.query.filter_by(id=event_id, user_id=current_user.id).first()

        if event:
            # Usuń wydarzenie
            db.session.delete(event)
            db.session.commit()
            flash("Wydarzenie zostało usunięte.", "success")
        else:
            flash("Nie znaleziono wydarzenia do usunięcia.", "warning")

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Błąd podczas usuwania wydarzenia: {str(e)}", "danger")

    # Przeładuj kalendarz z wydarzeniami
    start = date.today().replace(day=1)
    ender = date.today().replace(day=1) + timedelta(days=120)
    list_events = get_schedule_events(current_user.id, start, ender)

    return render_template("schedule.html", events=list_events, calendar_view=calendar_view, user=current_user.login)


@schedule_bp.route('/schedule/drop', methods=["POST"])
@login_required
def schedule_drop():
    data = request.get_json()
    event_id = data.get('id')
    start = data.get('start')
    end = data.get('end', start)
    start_time = data.get('start_time', "00:00")
    end_time = data.get('end_time', "23:59")

    # Tworzenie obiektów datetime
    try:
        start_date = datetime.strptime(f"{start} {start_time}", "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(f"{end} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"status": "error", "message": "Nieprawidłowy format daty lub czasu."}), 400

    # Walidacja kolizji z innymi wydarzeniami
    event_collision, error_message = validate_event_collision(
        current_user.id, start_date, end_date, exclude_event_id=event_id
    )
    if not event_collision:
        # flash(error_message, "danger")
        return jsonify({"status": "error", "message": error_message}), 400

    try:
        # Znalezienie wydarzenia w bazie danych
        event = Schedule.query.filter_by(id=event_id, user_id=current_user.id).first()

        if event:
            # Aktualizacja pól wydarzenia
            event.start_date = start_date.date()
            event.end_date = end_date.date()
            event.start_time = start_time
            event.end_time = end_time
            db.session.commit()
            return jsonify({"status": "success", "message": "Wydarzenie zostało zaktualizowane."}), 200
        else:
            return jsonify({"status": "error", "message": "Nie znaleziono wydarzenia do zaktualizowania."}), 404

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Błąd podczas aktualizacji wydarzenia: {str(e)}"}), 500


@schedule_bp.route('/schedule/update', methods=["POST", "GET"])
@login_required
def schedule_update():
    calendar_view = request.form.get('modal_edit_view', 'dayGridMonth')
    event_id = request.form.get('modal_edit_id')
    title = request.form.get('edittitle', '').strip()
    start_date = request.form.get('editstart', '').strip()
    end_date = request.form.get('editend', start_date).strip()
    description = request.form.get('editklasa', '').strip()
    url = request.form.get('editurl', '').strip()
    color_back = request.form.get('editsetcolor', '#FFFFFF').strip()
    color_fore = request.form.get('editsetlitery', '#000000').strip()
    start_time = request.form.get('editstart_time', '00:00').strip()
    end_time = request.form.get('editend_time', '23:59').strip()

    if not event_id:
        return redirect(url_for('schedule.schedule_main'))

    # Tworzenie obiektów datetime
    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return redirect(url_for('schedule.schedule_main'))

    event_collision, error_message = validate_event_collision(
        current_user.id, start_datetime, end_datetime, exclude_event_id=event_id
    )
    if not event_collision:
        return redirect(url_for('schedule.schedule_main'))

    try:
        # Znalezienie wydarzenia w bazie danych
        event = Schedule.query.filter_by(id=event_id, user_id=current_user.id).first()

        if event:
            # Aktualizacja pól wydarzenia
            event.title = title
            event.start_date = start_datetime.date()
            event.end_date = end_datetime.date()
            event.start_time = start_time
            event.end_time = end_time
            event.description = description
            event.url = url
            event.color_back = color_back
            event.color_fore = color_fore

            db.session.commit()
            flash("Wydarzenie zostało zaktualizowane.", "success")
        else:
            flash("Nie znaleziono wydarzenia do zaktualizowania.", "warning")

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Błąd podczas aktualizacji wydarzenia: {str(e)}", "danger")

    # Przeładuj kalendarz z wydarzeniami
    start_month = date.today().replace(day=1)
    end_month = date.today().replace(day=1) + timedelta(days=120)
    list_events = get_schedule_events(current_user.id, start_month, end_month)

    return render_template("schedule.html", events=list_events, calendar_view=calendar_view, user=current_user.login)
