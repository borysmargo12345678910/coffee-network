import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderItem, MenuItem, Branch
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    return sales()

@reports_bp.route('/sales')
@login_required
def sales():
    branch_id = request.args.get('branch_id', type=int)
    if not current_user.is_admin:
        branch_id = current_user.branch_id
    date_from = request.args.get('date_from', (datetime.date.today() - datetime.timedelta(days=30)).isoformat())
    date_to = request.args.get('date_to', datetime.date.today().isoformat())

    q = Order.query.filter(Order.status == 'done',
        Order.created_at >= date_from,
        Order.created_at <= date_to + ' 23:59:59')
    if branch_id:
        q = q.filter_by(branch_id=branch_id)
    orders = q.all()

    total_revenue = sum(float(o.total_amount) for o in orders)
    total_orders = len(orders)
    avg_check = total_revenue / total_orders if total_orders else 0

    top_q = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.subtotal).label('total_sum'),
    ).join(OrderItem).join(Order).filter(Order.status=='done',
        Order.created_at >= date_from, Order.created_at <= date_to + ' 23:59:59')
    if branch_id:
        top_q = top_q.filter(Order.branch_id == branch_id)
    top_items = top_q.group_by(MenuItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()

    branches = Branch.query.all() if current_user.is_admin else []
    return render_template('reports/sales.html',
        orders=orders, total_revenue=total_revenue, total_orders=total_orders,
        avg_check=avg_check, top_items=top_items, branches=branches,
        branch_id=branch_id, date_from=date_from, date_to=date_to)
