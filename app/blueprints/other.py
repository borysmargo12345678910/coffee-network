# ── menu ───────────────────────────────────────────────────────────────────
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import MenuItem, Category
from app.blueprints.decorators import admin_required

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/')
@login_required
def list_menu():
    items = MenuItem.query.order_by(MenuItem.name).all()
    categories = Category.query.all()
    return render_template('menu/list.html', items=items, categories=categories)

@menu_bp.route('/add', methods=['GET','POST'])
@login_required
@admin_required
def add_item():
    categories = Category.query.all()
    if request.method == 'POST':
        item = MenuItem(
            name=request.form['name'],
            category_id=request.form.get('category_id', type=int),
            price=request.form.get('price', type=float),
            cost_price=request.form.get('cost_price', type=float),
            description=request.form.get('description',''),
            is_available=request.form.get('is_available') == 'on',
        )
        db.session.add(item)
        db.session.commit()
        flash('Позицію меню додано.', 'success')
        return redirect(url_for('menu.list_menu'))
    return render_template('menu/add.html', categories=categories)

@menu_bp.route('/<int:item_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_availability(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    status = 'доступна' if item.is_available else 'недоступна'
    flash(f'Позиція «{item.name}» тепер {status}.', 'info')
    return redirect(url_for('menu.list_menu'))


# ── branches ────────────────────────────────────────────────────────────────
from flask import Blueprint as B2
from app.models import Branch

branches_bp = B2('branches', __name__)

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
        b = Branch(
            name=request.form['name'],
            address=request.form['address'],
            phone=request.form.get('phone',''),
        )
        db.session.add(b)
        db.session.commit()
        flash('Філію додано.', 'success')
        return redirect(url_for('branches.list_branches'))
    return render_template('branches/add.html')


# ── staff ────────────────────────────────────────────────────────────────────
from flask import Blueprint as B3
from app.models import Users, Shift
import datetime

staff_bp = B3('staff', __name__)

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
        u = Users(
            username=request.form['username'],
            full_name=request.form['full_name'],
            role=request.form['role'],
            branch_id=request.form.get('branch_id', type=int) or None,
        )
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        flash('Користувача додано.', 'success')
        return redirect(url_for('staff.list_users'))
    return render_template('staff/add.html', branches=branches)

@staff_bp.route('/shifts')
@login_required
def list_shifts():
    if current_user.is_admin:
        shifts = Shift.query.order_by(Shift.shift_date.desc()).limit(100).all()
    else:
        shifts = Shift.query.filter_by(branch_id=current_user.branch_id)\
                     .order_by(Shift.shift_date.desc()).limit(50).all()
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


# ── reports ──────────────────────────────────────────────────────────────────
from flask import Blueprint as B4, jsonify
from app.models import Order, OrderItem
from sqlalchemy import func
import datetime

reports_bp = B4('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    branches = Branch.query.all() if current_user.is_admin else [Branch.query.get(current_user.branch_id)]
    return render_template('reports/index.html', branches=branches)

@reports_bp.route('/sales')
@login_required
def sales():
    branch_id = request.args.get('branch_id', type=int)
    date_from = request.args.get('date_from', (datetime.date.today() - datetime.timedelta(days=30)).isoformat())
    date_to = request.args.get('date_to', datetime.date.today().isoformat())

    q = Order.query.filter(
        Order.status == 'done',
        Order.created_at >= date_from,
        Order.created_at <= date_to + ' 23:59:59',
    )
    if branch_id and not current_user.is_admin:
        branch_id = current_user.branch_id
    if branch_id:
        q = q.filter_by(branch_id=branch_id)
    elif not current_user.is_admin:
        q = q.filter_by(branch_id=current_user.branch_id)

    orders = q.all()
    total_revenue = sum(float(o.total_amount) for o in orders)
    total_orders = len(orders)
    avg_check = total_revenue / total_orders if total_orders else 0

    # Top menu items
    top_q = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.subtotal).label('total_sum'),
    ).join(OrderItem).join(Order).filter(
        Order.status == 'done',
        Order.created_at >= date_from,
        Order.created_at <= date_to + ' 23:59:59',
    )
    if branch_id:
        top_q = top_q.filter(Order.branch_id == branch_id)
    elif not current_user.is_admin:
        top_q = top_q.filter(Order.branch_id == current_user.branch_id)
    top_items = top_q.group_by(MenuItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()

    branches = Branch.query.all() if current_user.is_admin else []
    return render_template('reports/sales.html',
        orders=orders, total_revenue=total_revenue, total_orders=total_orders,
        avg_check=avg_check, top_items=top_items, branches=branches,
        branch_id=branch_id, date_from=date_from, date_to=date_to)
