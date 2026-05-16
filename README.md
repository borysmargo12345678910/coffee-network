# Інформаційна система обліку та управління мережею кав'ярень

Бакалаврська кваліфікаційна робота — Борис Маргарита Юріївна
НУБіП України, 2026

## Стек технологій
- Python 3.11 + Flask 3.0 (MVC, Blueprint)
- PostgreSQL 15 + SQLAlchemy 2.0 ORM
- Flask-Login, Flask-Bcrypt, Flask-Migrate
- Bootstrap 5.3 + Chart.js 4.4

## Локальний запуск

```bash
pip install -r requirements.txt
cp .env.example .env
# Відредагуйте .env (DATABASE_URL, SECRET_KEY)
flask db upgrade
python seed.py
python run.py
```

Відкрийте http://localhost:5000

## Облікові дані (seed)
- admin / admin123
- manager1 / manager123
- manager2 / manager123
- manager3 / manager123

## Розгортання на Render.com
1. Завантажте код на GitHub
2. Створіть Web Service (Python, gunicorn run:app)
3. Створіть PostgreSQL базу
4. Додайте змінні: DATABASE_URL, SECRET_KEY, FLASK_ENV=production
5. flask db upgrade && python seed.py
