import sqlite3
from datetime import date, timedelta, datetime
from sqlite3 import connect

from flask import Blueprint, render_template, abort, flash, request, redirect, url_for
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Schedule

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


# def get_sqlite_json(start, ends):
#     result = []
#     try:
#         data_range = (current_user.id, start, ends)
#         query = "SELECT * FROM terminarz WHERE id_user = ? AND start_date BETWEEN ? AND ? "
#         connect.row_factory = sqlite3.Row
#         events_sqlite_data = connect.execute(query, data_range).fetchall()
#         result = [{key: item[key] for key in item.keys()} for item in events_sqlite_data]
#     except SQLAlchemyError as e:
#         flash(e.__dict__['orig'], 'danger')
#     finally:
#         if connect:
#             connect.close()
#     return result


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

        try:
            # Konwersja dat na obiekty datetime.date
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


@schedule_bp.route('/schedule/drop', methods=["POST", "GET"])
@login_required
def schedule_drop():
    # Pobranie danych z formularza
    data = request.get_json()
    event_id = data.get('id')
    start_date = data.get('start')
    end_date = data.get('end')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    calendar_view = request.form.get('modal_drop_view', 'dayGridMonth')

    if not event_id:
        flash("Nie podano ID wydarzenia do zaktualizowania.", "danger")
        return redirect(url_for('schedule.schedule_main'))

    try:
        # Znalezienie wydarzenia w bazie danych
        event = Schedule.query.filter_by(id=event_id, user_id=current_user.id).first()

        if event:
            # Aktualizacja pól wydarzenia
            event.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            event.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            event.start_time = start_time
            event.end_time = end_time

            db.session.commit()
            flash("Wydarzenie zostało zaktualizowane.", "success")
        else:
            flash("Nie znaleziono wydarzenia do zaktualizowania.", "warning")

    except ValueError as ve:
        flash(f"Nieprawidłowy format daty: {str(ve)}", "danger")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Błąd podczas aktualizacji wydarzenia: {str(e)}", "danger")

    # Przeładuj kalendarz z wydarzeniami
    start = date.today().replace(day=1)
    ender = date.today().replace(day=1) + timedelta(days=120)
    list_events = get_schedule_events(current_user.id, start, ender)

    return render_template("schedule.html", events=list_events, calendar_view=calendar_view, user=current_user.login)


@schedule_bp.route('/schedule/update', methods=["POST", "GET"])
@login_required
def schedule_update():
    # Pobranie danych z formularza
    calendar_view = request.form.get('modal_edit_view', 'dayGridMonth')
    event_id = request.form.get('modal_edit_id')
    title = request.form.get('edittitle', '')
    start_date = request.form.get('editstart', '')
    end_date = request.form.get('editend', start_date)
    description = request.form.get('editklasa', '')
    url = request.form.get('editurl', '')
    color_back = request.form.get('editsetcolor', '')
    color_fore = request.form.get('editsetlitery', '')
    start_time = request.form.get('editstart_time', '00:00')
    end_time = request.form.get('editend_time', '24:00')

    if not event_id:
        flash("Nie podano ID wydarzenia do zaktualizowania.", "danger")
        return redirect(url_for('schedule.schedule_main'))

    try:
        # Znalezienie wydarzenia w bazie danych
        event = Schedule.query.filter_by(id=event_id, user_id=current_user.id).first()

        if event:
            # Aktualizacja pól wydarzenia
            event.title = title
            event.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            event.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
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

    except ValueError as ve:
        flash(f"Nieprawidłowy format daty: {str(ve)}", "danger")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Błąd podczas aktualizacji wydarzenia: {str(e)}", "danger")

    # Przeładuj kalendarz z wydarzeniami
    start = date.today().replace(day=1)
    ender = date.today().replace(day=1) + timedelta(days=120)
    list_events = get_schedule_events(current_user.id, start, ender)

    return render_template("schedule.html", events=list_events, calendar_view=calendar_view, user=current_user.login)
