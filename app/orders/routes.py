from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.orders import orders_bp
from app.models import Order, OrderItem, MenuItem, Branch
from app import db
from decimal import Decimal

@orders_bp.route('/')
@login_required
def index():
    if current_user.is_admin():
        orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()
    else:
        orders = Order.query.filter_by(branch_id=current_user.branch_id).order_by(Order.created_at.desc()).limit(100).all()
    return render_template('orders/index.html', orders=orders)

@orders_bp.route('/new', methods=['GET','POST'])
@login_required
def new():
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    branches = Branch.query.all() if current_user.is_admin() else []
    if request.method == 'POST':
        branch_id = current_user.branch_id if not current_user.is_admin() else request.form.get('branch_id', type=int)
        if not branch_id:
            flash('Оберіть філію', 'danger')
            return render_template('orders/new.html', menu_items=menu_items, branches=branches)
        order = Order(branch_id=branch_id, created_by=current_user.id)
        db.session.add(order)
        total = Decimal('0')
        has_items = False
        for item in menu_items:
            try:
                qty = int(request.form.get(f'qty_{item.id}', 0))
            except:
                qty = 0
            if qty > 0:
                subtotal = item.price * qty
                db.session.add(OrderItem(order=order, menu_item_id=item.id, quantity=qty, unit_price=item.price, subtotal=subtotal))
                total += subtotal
                has_items = True
        if not has_items:
            db.session.rollback()
            flash('Додайте хоча б одну позицію', 'warning')
            return render_template('orders/new.html', menu_items=menu_items, branches=branches)
        order.total_amount = total
        db.session.commit()
        flash(f"Замовлення #{order.id} на суму {total} грн створено", 'success')
        return redirect(url_for('orders.detail', id=order.id))
    return render_template('orders/new.html', menu_items=menu_items, branches=branches)

@orders_bp.route('/<int:id>')
@login_required
def detail(id):
    order = Order.query.get_or_404(id)
    if not current_user.is_admin() and order.branch_id != current_user.branch_id:
        flash('Доступ заборонено', 'danger')
        return redirect(url_for('orders.index'))
    return render_template('orders/detail.html', order=order)

@orders_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def change_status(id):
    order = Order.query.get_or_404(id)
    if not current_user.is_admin() and order.branch_id != current_user.branch_id:
        flash('Доступ заборонено', 'danger')
        return redirect(url_for('orders.index'))
    new_status = request.form.get('status')
    if order.can_transition_to(new_status):
        order.status = new_status
        db.session.commit()
        flash(f"Статус: {order.status_label()}", 'success')
    else:
        flash('Недозволений перехід', 'danger')
    return redirect(url_for('orders.detail', id=id))
