import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Users, Shift, Branch
from app.blueprints.decorators import admin_required

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/')
@login_required
@admin_required
def list_users():
    users = Users.query.order_by(Users.full_name).all()
    return render_template('staff/list.html', users=users)

@staff_bp.route('/add', methods=['GET','POST'])
@login_required
@admin_required
def add_user():
    branches = Branch.query.all()
    if request.method == 'POST':
        u = Users(username=request.form['username'], full_name=request.form['full_name'],
                  role=request.form['role'],
                  branch_id=request.form.get('branch_id', type=int) or None)
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        flash('Користувача додано.', 'success')
        return redirect(url_for('staff.list_users'))
    return render_template('staff/add.html', branches=branches)

@staff_bp.route('/shifts')
@login_required
def list_shifts():
    q = Shift.query if current_user.is_admin else Shift.query.filter_by(branch_id=current_user.branch_id)
    shifts = q.order_by(Shift.shift_date.desc()).limit(100).all()
    branches = Branch.query.all() if current_user.is_admin else []
    return render_template('staff/shifts.html', shifts=shifts, branches=branches)

@staff_bp.route('/shifts/add', methods=['GET','POST'])
@login_required
def add_shift():
    branches = Branch.query.all() if current_user.is_admin else [Branch.query.get(current_user.branch_id)]
    users = Users.query.filter_by(role='manager').all()
    if request.method == 'POST':
        s = Shift(
            branch_id=request.form.get('branch_id', type=int) or current_user.branch_id,
            user_id=request.form.get('user_id', type=int),
            shift_date=datetime.date.fromisoformat(request.form['shift_date']),
            start_time=datetime.time.fromisoformat(request.form['start_time']) if request.form.get('start_time') else None,
            end_time=datetime.time.fromisoformat(request.form['end_time']) if request.form.get('end_time') else None,
            note=request.form.get('note',''),
        )
        db.session.add(s)
        db.session.commit()
        flash('Зміну додано.', 'success')
        return redirect(url_for('staff.list_shifts'))
    return render_template('staff/add_shift.html', branches=branches, users=users)
