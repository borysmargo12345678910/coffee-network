from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.staff import staff_bp
from app.models import Users, Shift, Branch
from app import db
from datetime import date

@staff_bp.route('/')
@login_required
def index():
    if current_user.is_admin():
        staff = Users.query.filter_by(role='manager').all()
    else:
        staff = Users.query.filter_by(branch_id=current_user.branch_id).all()
    return render_template('staff/index.html', staff=staff)

@staff_bp.route('/shifts')
@login_required
def shifts():
    if current_user.is_admin():
        shifts = Shift.query.order_by(Shift.shift_date.desc()).limit(100).all()
    else:
        shifts = Shift.query.filter_by(branch_id=current_user.branch_id).order_by(Shift.shift_date.desc()).limit(100).all()
    branches = Branch.query.all() if current_user.is_admin() else []
    return render_template('staff/shifts.html', shifts=shifts, branches=branches)

@staff_bp.route('/shifts/new', methods=['GET','POST'])
@login_required
def new_shift():
    branches = Branch.query.all() if current_user.is_admin() else []
    staff = Users.query.filter_by(role='manager').all()
    if request.method == 'POST':
        branch_id = current_user.branch_id if not current_user.is_admin() else request.form.get('branch_id', type=int)
        shift = Shift(branch_id=branch_id, user_id=int(request.form['user_id']),
                     shift_date=date.fromisoformat(request.form['shift_date']),
                     note=request.form.get('note',''))
        db.session.add(shift)
        db.session.commit()
        flash('Зміну додано', 'success')
        return redirect(url_for('staff.shifts'))
    return render_template('staff/new_shift.html', branches=branches, staff=staff)
