from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Users

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('orders.list_orders'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = Users.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Ласкаво просимо, {user.full_name or user.username}!', 'success')
            return redirect(url_for('orders.list_orders'))
        flash('Невірний логін або пароль.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з системи.', 'info')
    return redirect(url_for('auth.login'))
