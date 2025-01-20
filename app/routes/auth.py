from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, verify_csrf_token
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form.get('login')
        password = request.form.get('pwd')

        user = User.query.filter_by(login=username).first()
        if user and check_password_hash(user.pwd, password):
            login_user(user)
            if 'change_password' in request.form:
                return redirect(url_for('auth.change_password'))
            flash('Zalogowano pomyślnie!', 'success')
            if user.is_admin:
                return redirect(url_for('admin.users'))
            return redirect(url_for('visit.main_form'))
        else:
            flash('Nieprawidłowy login lub hasło.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('start.home'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':

        verify_csrf_token()  # Weryfikuj token CSRF

        if request.form.get('psw') != request.form.get('psw-repeat'):
            flash('WPISANE HASŁA SĄ RÓŻNE !', 'danger')
            return redirect('change_password', code=302)
        try:
            user = db.session.execute(db.select(User).filter(User.login == current_user.login)).first()
            user[0].pwd = generate_password_hash(request.form['psw'])
            db.session.flush()
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('- nie ma połączenia z bazą danych !', 'danger')
            return redirect(url_for('login'))
        flash('Hasło zostało zmienione !', 'success')
        return redirect(url_for('auth.login'))

    return render_template('change_password.html')
