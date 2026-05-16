from app import create_app, db
from app.models import Branch, Category, MenuItem, Users, Inventory

app = create_app()

with app.app_context():
    db.create_all()
    
    # Якщо адмін вже є - не додаємо
    if not Users.query.filter_by(username='admin').first():
        b1 = Branch(name='Кав'ярня на Хрещатику', address='вул. Хрещатик, 22, Київ', phone='+380441234567')
        b2 = Branch(name='Кав'ярня на Позняках', address='пр. Бажана, 14, Київ', phone='+380442345678')
        b3 = Branch(name='Кав'ярня на Оболоні', address='пр. Героїв Сталінграда, 8, Київ', phone='+380443456789')
        db.session.add_all([b1, b2, b3])
        db.session.flush()

        cat1 = Category(name='Кава', description='Гарячі кавові напої')
        cat2 = Category(name='Чай', description='Чай та трав'яні напої')
        cat3 = Category(name='Холодні напої', description='Лимонади, смузі, холодна кава')
        cat4 = Category(name='Десерти', description='Випічка та солодощі')
        db.session.add_all([cat1, cat2, cat3, cat4])
        db.session.flush()

        menu = [
            MenuItem(name='Еспресо', category_id=cat1.id, price=55, cost_price=12),
            MenuItem(name='Американо', category_id=cat1.id, price=65, cost_price=14),
            MenuItem(name='Капучино', category_id=cat1.id, price=85, cost_price=22),
            MenuItem(name='Латте', category_id=cat1.id, price=90, cost_price=25),
            MenuItem(name='Чай чорний', category_id=cat2.id, price=55, cost_price=8),
            MenuItem(name='Лимонад', category_id=cat3.id, price=75, cost_price=18),
            MenuItem(name='Круасан', category_id=cat4.id, price=55, cost_price=20),
        ]
        db.session.add_all(menu)
        db.session.flush()

        admin = Users(username='admin', full_name='Адміністратор мережі', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        m1 = Users(username='manager1', full_name='Іваненко Оксана', role='manager', branch_id=b1.id)
        m1.set_password('manager123')
        db.session.add(m1)

        db.session.commit()
        print("✓ База заповнена!")

if __name__ == '__main__':
    app.run(debug=True)
