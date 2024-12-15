import sqlite3

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from jinja2 import TemplateNotFound
from sqlalchemy import exc
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import User

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users')
@login_required
def users():
    try:
        if current_user.is_admin:
            users = db.session.query(User).all()
            return render_template('admin.html', users=users)
        return redirect(url_for('visit.main_form'))
    except TemplateNotFound:
        return abort(404)


@admin_bp.route('/users/update', methods=['GET', 'POST'])
@login_required
def user_update():
    if current_user.is_admin:
        try:
            user_to_update = db.session.query(User).filter_by(id=request.form.get('id')).first()
            user_to_update.login = request.form.get('login_new')
            user_to_update.name = request.form.get('name_new')
            user_to_update.email = request.form.get('email_new')
            user_to_update.pwd = request.form.get('pwd')
            if 'actual_password':
                user_to_update.pwd = generate_password_hash(request.form.get('actual_password'))
            user_to_update.is_admin = False
            if 'admin_new' in request.form:
                user_to_update.is_admin = True
            user_to_update.isActive = False
            if 'aktywny_new' in request.form:
                user_to_update.isActive = True
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            flash('Podobny login lub e-mail już istnieje !', 'info')
            return redirect(url_for('admin'))
        except sqlite3.Error as e:
            db.session.rollback()
            flash('Nie ma połączenia z bazą danych {}'.format(e), 'danger')
            return redirect(url_for('admin.users'))
        flash(f'Dane użytkownika "{user_to_update.login}" zaktualizowano !', 'success')
        return redirect(url_for('admin.users'))
    flash('Nieautoryzowana próba dostępu !', 'danger')
    return redirect(url_for('visit.main_form'))


@admin_bp.route('/users/insert', methods=['GET', 'POST'])
@login_required
def user_insert():
    if current_user.is_admin:
        surname = request.form.get('surname_new')
        mylogin = request.form.get('login')
        email = request.form.get('email')
        # pswds = generate_password_hash(request.form.get('password'), method='sha256')
        pswds = generate_password_hash(request.form.get('password'))
        admins = False
        if 'admin' in request.form:
            admins = True
        aktywny = False
        if 'aktywny' in request.form:
            aktywny = True

        new_user = User(mylogin, surname, pswds, email, admins, aktywny)
        try:
            db.session.add(new_user)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            flash('Podobny login lub e-mail już istnieje !', 'info')
            return redirect(url_for('admin'))
        except sqlite3.Error as e:
            db.session.rollback()
            flash('Nie ma połączenia z bazą danych {}'.format(e), 'danger')
            return redirect(url_for('admin.users'))
        flash(f'Pomyślnie dodano nowego użytkownika !', 'success')
        return redirect(url_for('admin.users'))
    flash('Nieautoryzowana próba dostępu !', 'danger')
    return redirect(url_for('visit.main_form'))


@admin_bp.route('/users/delete/<string:id_user>', methods=['POST', 'GET'])
@login_required
def user_delete(id_user):
    if current_user.is_admin:
        try:
            user_to_delete = db.session.query(User).filter_by(id=id_user).first()
            db.session.delete(user_to_delete)
            db.session.commit()
        except sqlite3.Error:
            db.session.rollback()
            flash('Nie ma połączenia z bazą danych !', 'danger')
            return redirect(url_for('admin'))
        flash(f'Użytkownika "{user_to_delete.login}"  usunięto!', 'success')
        return redirect(url_for('admin.users'))
    return redirect(url_for('visit.main_form'))
