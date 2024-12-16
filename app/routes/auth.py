import sqlite3

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# W template url_for('nazwa_blueprint.nazwa_funkcji_z_route')
# W funkcji z route return return render_template('nazwa_template')
# W funkcji z route w rule 'adres url jaki ma się wyświetlić'


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
            return redirect(url_for('visit.main_form'))  # Zmień 'main.home' na endpoint Twojej głównej strony
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
        if request.form.get('psw') != request.form.get('psw-repeat'):
            flash('WPISANE HASŁA SĄ RÓŻNE !', 'danger')
            return redirect('change_password', code=302)
        try:
            user = db.session.execute(db.select(User).filter(User.login == current_user.login)).first()
            user[0].pwd = generate_password_hash(request.form['psw'])
            db.session.flush()
            db.session.commit()
        except sqlite3.Error:
            db.session.rollback()
            flash('- nie ma połączenia z bazą danych !', 'danger')
            return redirect(url_for('login'))
        flash('Hasło zostało zmienione !', 'success')
        return redirect(url_for('auth.login'))

    return render_template('change_password.html')


@auth_bp.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            hashed_password = generate_password_hash(password)
            user = User(login=username, pwd=hashed_password)
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            return 'User created successfully!'
        return 'Invalid input!'
    return '''
        <form method="POST">
            <label>Username:</label>
            <input type="text" name="username"><br>
            <label>Password:</label>
            <input type="password" name="password"><br>
            <button type="submit">Create User</button>
        </form>
    '''
