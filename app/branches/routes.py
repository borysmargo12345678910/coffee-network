from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.branches import branches_bp
from app.models import Branch, Users
from app import db

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash('Доступ лише для адміністраторів', 'danger')
            return redirect(url_for('orders.index'))
        return f(*args, **kwargs)
    return decorated

@branches_bp.route('/')
@login_required
@admin_required
def index():
    branches = Branch.query.all()
    return render_template('branches/index.html', branches=branches)

@branches_bp.route('/new', methods=['GET','POST'])
@login_required
@admin_required
def new():
    if request.method == 'POST':
        b = Branch(name=request.form['name'], address=request.form['address'], phone=request.form.get('phone',''))
        db.session.add(b)
        db.session.commit()
        flash('Філію додано', 'success')
        return redirect(url_for('branches.index'))
    return render_template('branches/new.html')
