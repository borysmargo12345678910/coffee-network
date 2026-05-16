from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt, login_manager

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='branch', lazy='dynamic', foreign_keys='Order.branch_id')
    inventory = db.relationship('Inventory', backref='branch', lazy='dynamic')
    shifts = db.relationship('Shift', backref='branch', lazy='dynamic')
    def __repr__(self): return f'<Branch {self.name}>'

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    items = db.relationship('MenuItem', backref='category', lazy='dynamic')
    def __repr__(self): return f'<Category {self.name}>'

class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    cost_price = db.Column(db.Numeric(8, 2))
    description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    order_items = db.relationship('OrderItem', backref='menu_item', lazy='dynamic')
    def __repr__(self): return f'<MenuItem {self.name}>'

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'manager', name='user_role'), nullable=False, default='manager')
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    branch = db.relationship('Branch', foreign_keys=[branch_id])
    orders = db.relationship('Order', backref='creator', lazy='dynamic', foreign_keys='Order.created_by')
    shifts = db.relationship('Shift', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self): return self.role == 'admin'
    def __repr__(self): return f'<Users {self.username}>'

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.Enum('new','in_progress','done','cancelled', name='order_status'), default='new', nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    STATUS_LABELS = {'new': 'Нове', 'in_progress': 'Готується', 'done': 'Виконано', 'cancelled': 'Скасовано'}
    STATUS_COLORS = {'new': 'primary', 'in_progress': 'warning', 'done': 'success', 'cancelled': 'secondary'}

    def status_label(self): return self.STATUS_LABELS.get(self.status, self.status)
    def status_color(self): return self.STATUS_COLORS.get(self.status, 'secondary')

    ALLOWED_TRANSITIONS = {'new': ['in_progress', 'cancelled'], 'in_progress': ['done', 'cancelled']}

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def __repr__(self): return f'<Order #{self.id}>'

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(8, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    def __repr__(self): return f'<OrderItem {self.menu_item_id} x{self.quantity}>'

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False, default='шт.')
    min_quantity = db.Column(db.Numeric(10, 3), default=0)
    logs = db.relationship('InventoryLog', backref='inventory', lazy='dynamic', cascade='all, delete-orphan')

    def is_low(self): return float(self.quantity) <= float(self.min_quantity)
    def __repr__(self): return f'<Inventory {self.product_name}>'

class InventoryLog(db.Model):
    __tablename__ = 'inventory_log'
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    operation_type = db.Column(db.Enum('in', 'out', name='op_type'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)
    operator = db.relationship('Users', foreign_keys=[created_by])
    def __repr__(self): return f'<InventoryLog {self.operation_type} {self.quantity}>'

class Shift(db.Model):
    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    note = db.Column(db.Text)
    def __repr__(self): return f'<Shift {self.shift_date}>'
