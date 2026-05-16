from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Branch
from app.blueprints.decorators import admin_required

branches_bp = Blueprint('branches', __name__)

@branches_bp.route('/')
@login_required
@admin_required
def list_branches():
    branches = Branch.query.all()
    return render_template('branches/list.html', branches=branches)

@branches_bp.route('/add', methods=['GET','POST'])
@login_required
@admin_required
def add_branch():
    if request.method == 'POST':
        b = Branch(name=request.form['name'], address=request.form['address'],
                   phone=request.form.get('phone',''))
        db.session.add(b)
        db.session.commit()
        flash('Філію додано.', 'success')
        return redirect(url_for('branches.list_branches'))
    return render_template('branches/add.html')
