from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import MenuItem, Category, Branch
from app.blueprints.decorators import admin_required

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/')
@login_required
def list_menu():
    items = MenuItem.query.join(Category).order_by(Category.name, MenuItem.name).all()
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
    flash(f'Позиція «{item.name}» оновлена.', 'info')
    return redirect(url_for('menu.list_menu'))
