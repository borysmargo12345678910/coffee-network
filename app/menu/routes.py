from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.menu import menu_bp
from app.models import MenuItem, Category
from app import db
from decimal import Decimal

@menu_bp.route('/')
@login_required
def index():
    categories = Category.query.all()
    items = MenuItem.query.order_by(MenuItem.category_id).all()
    return render_template('menu/index.html', items=items, categories=categories)

@menu_bp.route('/new', methods=['GET','POST'])
@login_required
def new():
    categories = Category.query.all()
    if request.method == 'POST':
        item = MenuItem(name=request.form['name'], category_id=int(request.form['category_id']),
                       price=Decimal(request.form['price']),
                       cost_price=Decimal(request.form.get('cost_price','0') or '0'),
                       description=request.form.get('description',''))
        db.session.add(item)
        db.session.commit()
        flash('Позицію додано до меню', 'success')
        return redirect(url_for('menu.index'))
    return render_template('menu/new.html', categories=categories)

@menu_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    item = MenuItem.query.get_or_404(id)
    item.is_available = not item.is_available
    db.session.commit()
    flash(f"{'Доступно' if item.is_available else 'Недоступно'}: {item.name}", 'info')
    return redirect(url_for('menu.index'))
