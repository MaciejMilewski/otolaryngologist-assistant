from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
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
