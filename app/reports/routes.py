from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.reports import reports_bp
from app.models import Order, OrderItem, MenuItem, Branch
from app import db
from sqlalchemy import func
from datetime import datetime, date, timedelta

@reports_bp.route('/')
@login_required
def index():
    branches = Branch.query.all() if current_user.is_admin() else []
    date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).isoformat())
    date_to = request.args.get('date_to', date.today().isoformat())
    branch_id = request.args.get('branch_id', type=int)

    q = db.session.query(Order).filter(
        Order.status == 'done',
        Order.created_at >= date_from,
        Order.created_at <= date_to + ' 23:59:59'
    )
    if branch_id:
        q = q.filter(Order.branch_id == branch_id)
    elif not current_user.is_admin():
        q = q.filter(Order.branch_id == current_user.branch_id)

    orders = q.all()
    total_revenue = sum(float(o.total_amount) for o in orders)
    order_count = len(orders)
    avg_check = total_revenue / order_count if order_count else 0

    # Top menu items
    top_q = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.subtotal).label('total_sum')
    ).join(OrderItem).join(Order).filter(
        Order.status == 'done',
        Order.created_at >= date_from,
        Order.created_at <= date_to + ' 23:59:59'
    )
    if branch_id:
        top_q = top_q.filter(Order.branch_id == branch_id)
    elif not current_user.is_admin():
        top_q = top_q.filter(Order.branch_id == current_user.branch_id)
    top_items = top_q.group_by(MenuItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()

    # Revenue by branch (admin only)
    branch_data = []
    if current_user.is_admin():
        branch_q = db.session.query(
            Branch.name, func.sum(Order.total_amount).label('revenue')
        ).join(Order).filter(
            Order.status == 'done',
            Order.created_at >= date_from,
            Order.created_at <= date_to + ' 23:59:59'
        ).group_by(Branch.name).all()
        branch_data = branch_q

    return render_template('reports/index.html',
        total_revenue=total_revenue, order_count=order_count,
        avg_check=round(avg_check, 2), top_items=top_items,
        branch_data=branch_data, branches=branches,
        date_from=date_from, date_to=date_to, branch_id=branch_id)
