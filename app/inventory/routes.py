from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.inventory import inventory_bp
from app.models import Inventory, InventoryLog, Branch
from app import db
from decimal import Decimal

@inventory_bp.route('/')
@login_required
def index():
    branch_id = None if current_user.is_admin() else current_user.branch_id
    branches = Branch.query.all() if current_user.is_admin() else []
    if current_user.is_admin():
        branch_id = request.args.get('branch_id', type=int)
    items = Inventory.query.filter_by(branch_id=branch_id).all() if branch_id else ([] if current_user.is_admin() else Inventory.query.filter_by(branch_id=current_user.branch_id).all())
    low = [i for i in items if i.is_low()]
    if low:
        flash(f"⚠ Низький залишок: {', '.join(i.product_name for i in low)}", 'warning')
    return render_template('inventory/index.html', items=items, branches=branches, branch_id=branch_id)

@inventory_bp.route('/add', methods=['GET','POST'])
@login_required
def add():
    branches = Branch.query.all() if current_user.is_admin() else []
    if request.method == 'POST':
        branch_id = current_user.branch_id if not current_user.is_admin() else request.form.get('branch_id', type=int)
        item = Inventory(branch_id=branch_id, product_name=request.form['product_name'],
                        quantity=Decimal(request.form.get('quantity','0')),
                        unit=request.form.get('unit','шт.'),
                        min_quantity=Decimal(request.form.get('min_quantity','0')))
        db.session.add(item)
        db.session.commit()
        flash('Позицію додано', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/add.html', branches=branches)

@inventory_bp.route('/<int:id>/operation', methods=['POST'])
@login_required
def operation(id):
    item = Inventory.query.get_or_404(id)
    op_type = request.form.get('operation_type')
    try:
        qty = Decimal(request.form.get('quantity','0'))
        assert qty > 0
    except:
        flash('Невірна кількість', 'danger')
        return redirect(url_for('inventory.index'))
    if op_type == 'in':
        item.quantity += qty
    else:
        if item.quantity < qty:
            flash('Недостатньо залишку', 'danger')
            return redirect(url_for('inventory.index'))
        item.quantity -= qty
    db.session.add(InventoryLog(inventory_id=item.id, operation_type=op_type, quantity=qty,
                                created_by=current_user.id, note=request.form.get('note','')))
    db.session.commit()
    if item.is_low():
        flash(f"⚠ Залишок '{item.product_name}' нижче мінімуму!", 'warning')
    else:
        flash('Операцію зафіксовано', 'success')
    return redirect(url_for('inventory.index'))
