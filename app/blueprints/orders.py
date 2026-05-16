from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderItem, MenuItem, Branch

orders_bp = Blueprint('orders', __name__)


def get_branch_query():
    if current_user.is_admin:
        return Order.query
    return Order.query.filter_by(branch_id=current_user.branch_id)


@orders_bp.route('/')
@login_required
def list_orders():
    status = request.args.get('status', '')
    q = get_branch_query().order_by(Order.created_at.desc())
    if status:
        q = q.filter_by(status=status)
    orders = q.paginate(page=request.args.get('page', 1, type=int), per_page=25)
    branches = Branch.query.all() if current_user.is_admin else []
    return render_template('orders/list.html', orders=orders, branches=branches,
                           status_filter=status, status_labels=Order.STATUS_LABELS)


@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_order():
    branches = Branch.query.all() if current_user.is_admin else [Branch.query.get(current_user.branch_id)]
    menu_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.name).all()

    if request.method == 'POST':
        branch_id = request.form.get('branch_id', type=int) or current_user.branch_id
        if not current_user.is_admin and branch_id != current_user.branch_id:
            abort(403)

        items_data = []
        for item in menu_items:
            qty = request.form.get(f'qty_{item.id}', 0, type=int)
            if qty > 0:
                items_data.append((item, qty))

        if not items_data:
            flash('Оберіть хоча б одну позицію меню.', 'warning')
            return render_template('orders/new.html', menu_items=menu_items, branches=branches)

        order = Order(branch_id=branch_id, created_by=current_user.id)
        db.session.add(order)
        db.session.flush()

        total = 0
        for item, qty in items_data:
            subtotal = float(item.price) * qty
            oi = OrderItem(order_id=order.id, menu_item_id=item.id,
                           quantity=qty, unit_price=item.price, subtotal=subtotal)
            db.session.add(oi)
            total += subtotal

        order.total_amount = total
        db.session.commit()
        flash(f'Замовлення #{order.id} створено на суму {total:.2f} грн.', 'success')
        return redirect(url_for('orders.detail', order_id=order.id))

    return render_template('orders/new.html', menu_items=menu_items, branches=branches)


@orders_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)
    if not current_user.is_admin and order.branch_id != current_user.branch_id:
        abort(403)
    return render_template('orders/detail.html', order=order,
                           status_labels=Order.STATUS_LABELS)


@orders_bp.route('/<int:order_id>/transition', methods=['POST'])
@login_required
def transition(order_id):
    order = Order.query.get_or_404(order_id)
    if not current_user.is_admin and order.branch_id != current_user.branch_id:
        abort(403)
    new_status = request.form.get('new_status')
    if not order.can_transition_to(new_status):
        flash('Недозволений перехід статусу.', 'danger')
    else:
        order.status = new_status
        db.session.commit()
        label = Order.STATUS_LABELS[new_status][0]
        flash(f'Статус замовлення змінено на «{label}».', 'success')
    return redirect(url_for('orders.detail', order_id=order_id))
