# ── inventory ──────────────────────────────────────────────────────────────
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Inventory, InventoryLog, Branch

inventory_bp = Blueprint('inventory', __name__)

def branch_inventory(branch_id=None):
    if current_user.is_admin:
        q = Inventory.query
        if branch_id:
            q = q.filter_by(branch_id=branch_id)
        return q
    return Inventory.query.filter_by(branch_id=current_user.branch_id)

@inventory_bp.route('/')
@login_required
def list_inventory():
    branch_id = request.args.get('branch_id', type=int)
    items = branch_inventory(branch_id).order_by(Inventory.product_name).all()
    branches = Branch.query.all() if current_user.is_admin else []
    low_items = [i for i in items if i.is_low]
    if low_items:
        flash(f'⚠ Нестача запасів: {", ".join(i.product_name for i in low_items)}', 'warning')
    return render_template('inventory/list.html', items=items, branches=branches, branch_id=branch_id)

@inventory_bp.route('/add', methods=['GET','POST'])
@login_required
def add_item():
    branches = Branch.query.all() if current_user.is_admin else [Branch.query.get(current_user.branch_id)]
    if request.method == 'POST':
        branch_id = request.form.get('branch_id', type=int) or current_user.branch_id
        item = Inventory(
            branch_id=branch_id,
            product_name=request.form['product_name'],
            quantity=request.form.get('quantity', 0, type=float),
            unit=request.form['unit'],
            min_quantity=request.form.get('min_quantity', 0, type=float),
        )
        db.session.add(item)
        db.session.commit()
        flash('Позицію додано.', 'success')
        return redirect(url_for('inventory.list_inventory'))
    return render_template('inventory/add.html', branches=branches)

@inventory_bp.route('/<int:item_id>/operation', methods=['POST'])
@login_required
def operation(item_id):
    item = Inventory.query.get_or_404(item_id)
    if not current_user.is_admin and item.branch_id != current_user.branch_id:
        abort(403)
    op_type = request.form.get('op_type')
    qty = request.form.get('quantity', 0, type=float)
    if qty <= 0:
        flash('Кількість має бути більше нуля.', 'danger')
        return redirect(url_for('inventory.list_inventory'))
    if op_type == 'out' and float(item.quantity) < qty:
        flash('Недостатньо залишків.', 'danger')
        return redirect(url_for('inventory.list_inventory'))
    log = InventoryLog(inventory_id=item.id, operation_type=op_type,
                       quantity=qty, created_by=current_user.id,
                       note=request.form.get('note', ''))
    db.session.add(log)
    if op_type == 'in':
        item.quantity = float(item.quantity) + qty
    else:
        item.quantity = float(item.quantity) - qty
    db.session.commit()
    if item.is_low:
        flash(f'⚠ Залишок «{item.product_name}» нижче мінімуму!', 'warning')
    else:
        flash('Операцію зафіксовано.', 'success')
    return redirect(url_for('inventory.list_inventory'))
