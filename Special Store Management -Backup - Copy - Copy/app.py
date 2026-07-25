from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import xlsxwriter
import openpyxl
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr, createBarcodeDrawing
from reportlab.lib.units import mm
from functools import wraps
from datetime import datetime, timedelta, timezone

import sys
import requests
import os
import ssl
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
#print("ENV EMAIL_USER:", os.getenv("EMAIL_USER"))
#print("ENV EMAIL_PASSWORD:", os.getenv("EMAIL_PASSWORD"))
now = datetime.now().replace(microsecond=0)
print(now) 
# ---------------------- APP CONFIG ----------------------
# app = Flask(__name__)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static')
)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(hours=2)
db = SQLAlchemy(app)
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
from flask_migrate import Migrate

migrate = Migrate(app, db)
from pos import pos_bp
app.register_blueprint(pos_bp)
#      model definitions
from datetime import datetime

class Grade(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    price_adjustment = db.Column(
        db.Float,
        default=0
    )
class ProductVariant(db.Model):
     id = db.Column(db.Integer, primary_key=True)

     product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
     )

     storage = db.Column(db.String(50))
     color = db.Column(db.String(50))

     product = db.relationship(
        'Product',
        backref=db.backref(
            'variants',
            cascade="all, delete-orphan"
        )
    )
class DeviceInventory(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('product_variant.id'),
        nullable=False
    )

    imei = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    grade_id = db.Column(
        db.Integer,
        db.ForeignKey('grade.id'),
        nullable=True
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('supplier.id')
    )

    purchase_id = db.Column(
        db.Integer,
        db.ForeignKey('purchase.id')
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=True
    )

    store_id = db.Column(
        db.Integer,
        db.ForeignKey('store.id'),
        nullable=False
    )

    cost_price = db.Column(
        db.Float,
        default=0
    )

    sell_price = db.Column(
        db.Float,
        default=0
    )

    battery_health = db.Column(
        db.Integer,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default='in_stock'
    )
    # in_stock / sold / returned

    notes = db.Column(db.Text)

    added_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    variant = db.relationship('ProductVariant')

    grade = db.relationship('Grade')

    supplier = db.relationship('Supplier')

    purchase = db.relationship('Purchase')

    customer = db.relationship('Customer')

    store = db.relationship('Store')


    

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    participants = db.relationship('Participant', backref='store', cascade="all, delete-orphan")
    products = db.relationship('Product', backref='store', cascade="all, delete-orphan")
    suppliers = db.relationship('Supplier', backref='store', cascade="all, delete-orphan")
    purchases = db.relationship('Purchase', backref='store', cascade="all, delete-orphan")
    sales = db.relationship('Sale', backref='store', cascade="all, delete-orphan")
    customers = db.relationship('Customer', backref='store', cascade="all, delete-orphan")
    # New
    address = db.Column(db.String(200))
    currency = db.Column(db.String(10), default="PKR")
    tax_percent = db.Column(db.Float, default=0)
    invoice_footer = db.Column(db.String(200))

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))

class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    # product_code = db.Column(db.String(50), nullable=True)

    product_code = db.Column(db.String(50), unique=True, nullable=False)

    # OPTIONAL MAIN PRODUCT IMEI
    # (usually not needed anymore)
    imei = db.Column(db.String(50), nullable=True)

    name = db.Column(db.String(100))

    category = db.Column(db.String(50))

    # PURCHASE PRICE
    buy_price = db.Column(db.Float, default=0.0)

    # DEFAULT SELL PRICE
    sell_price = db.Column(db.Float, default=0.0)

    # TOTAL STOCK
    stock = db.Column(db.Integer, default=0)

    # SOLD COUNT
    sold = db.Column(db.Integer, default=0)

    in_stock = db.Column(db.Boolean, default=True)

    store_id = db.Column(
        db.Integer,
        db.ForeignKey('store.id')
    )

    # MAIN SUPPLIER
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('supplier.id'),
        nullable=True
    )

    supplier = db.relationship(
        'Supplier',
        backref=db.backref(
            'products',
            cascade="all, delete-orphan"
        )
    )
    sales = db.relationship(
    "Sale",
    back_populates="product",
    cascade="all, delete-orphan")
#     sales = db.relationship("Sale", back_populates="product")
#     # sales = db.relationship(
    #     'Sale',
    #     backref='product',
    #     cascade="all, delete-orphan"
    # )

    purchases = db.relationship(
        'Purchase',
        backref='product',
        cascade="all, delete-orphan"
    )

    devices = db.relationship(
    'DeviceInventory',
    secondary='product_variant',
    primaryjoin='Product.id==ProductVariant.product_id',
    secondaryjoin='ProductVariant.id==DeviceInventory.variant_id',
    viewonly=True
)

    @property
    def calculated_stock(self):

        purchased = sum(
            p.quantity for p in self.purchases
        )

        sold = sum(
            s.quantity for s in self.sales
        )

        return purchased - sold

    # @property
    # def total_profit(self):

    #     return sum(
    #         (
    #             (s.price - self.buy_price)
    #             * s.quantity
    #         )
    #         for s in self.sales
    #     )
    # @property
    # def total_profit(self):
    #  return sum(
    #     ((s.selling_price or 0) - (self.buy_price or 0))
    #     * (s.quantity or 0)
    #     for s in self.sales
    # )

    @property
    def total_profit(self):
     return sum(
        s.profit or 0
        for s in self.sales
    )

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
   
    location = db.Column(db.String(200))
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    purchases = db.relationship('Purchase', backref='supplier', cascade="all, delete-orphan")


    devices = db.relationship(
    'DeviceInventory',
    backref='device_supplier',
    cascade="all, delete-orphan"
    )
    def total_supplied(self):
        return sum([p.total_price() for p in self.purchases]) if self.purchases else 0
    
    


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_name = db.Column(db.String(100), nullable=False)  # kept for compatibility
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    #purchase_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)

    devices = db.relationship( 
    'DeviceInventory',
    backref='device_purchase',
    cascade="all, delete-orphan")
    
    def total_price(self):
        return self.quantity * self.unit_price

class Cashier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200))
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))


class CartItem(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
    db.String(100),
    nullable=False)
    # user_id = db.Column(
    #     db.Integer,
    #     nullable=False
    # )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id')
    )

    quantity = db.Column(
        db.Integer,
        default=1
    )

    price = db.Column(db.Float)

    store_id = db.Column(
        db.Integer,
        db.ForeignKey('store.id')
    )

    product = db.relationship('Product')
# class CartItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)

#     user_id = db.Column(db.Integer, nullable=False)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

#     quantity = db.Column(db.Integer, default=1)
#     price = db.Column(db.Float)

#     store_id = db.Column(db.Integer, db.ForeignKey('store.id'))
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    customer_number = db.Column(db.String(50))
    
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    sales = db.relationship('Sale', backref='customer', cascade="all, delete-orphan")

    def total_spent(self):
        return sum([s.product.sell_price * s.quantity for s in self.sales if s.product])
    def total_mobiles(self):
        return sum([s.quantity for s in self.sales])

# class Sale(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
#     customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
#     customer_name = db.Column(db.String(100))
#     customer_number = db.Column(db.String(50))
#     quantity = db.Column(db.Integer, nullable=False)
#     sale_date = db.Column(db.DateTime, default=datetime.utcnow)
#     store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
#     #sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
#      # --- ADDED: total_price method ---
#     def total_price(self):
#         if self.product:
#             return self.product.sell_price * self.quantity
#         return 0
#     # --- END ADDED ---

class Sale(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    payment_method = db.Column(db.String(30), default='cash')

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=True
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)
    selling_price = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    profit = db.Column(db.Float, default=0)

    customer_name = db.Column(db.String(100))
    customer_number = db.Column(db.String(50))

    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)

    product = db.relationship('Product', back_populates='sales')
    @property
    def total_price(self):
      return (self.quantity * self.selling_price) - (self.quantity * self.selling_price * self.discount / 100)


class CustomerLedger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    reference_type = db.Column(db.String(30), nullable=False)  # sale
    reference_id = db.Column(db.Integer, nullable=True)

    total_amount = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    due_amount = db.Column(db.Float, default=0)

    due_date = db.Column(db.DateTime, nullable=True)
    settled_at = db.Column(db.DateTime, nullable=True)

    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref=db.backref('ledgers', cascade='all, delete-orphan'))


class SupplierLedger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)

    reference_type = db.Column(db.String(30), nullable=False)  # purchase
    reference_id = db.Column(db.Integer, nullable=True)

    total_amount = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    due_amount = db.Column(db.Float, default=0)

    due_date = db.Column(db.DateTime, nullable=True)
    settled_at = db.Column(db.DateTime, nullable=True)

    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref=db.backref('ledgers', cascade='all, delete-orphan'))

    # NOTE:
    # SupplierLedger is independent from Sale/Product.
    # Removed incorrect relationship to Product that caused app startup failure.

    def total_price(self):
        return (self.total_amount or 0)


# ---------------------- INITIAL SETUP ----------------------
with app.app_context():

    db.create_all()

    default_grades = ['A+', 'A', 'B', 'C']

    for g in default_grades:

        exists = Grade.query.filter_by(name=g).first()

        if not exists:

            db.session.add(
                Grade(
                    name=g,
                    price_adjustment=0
                )
            )

    db.session.commit()

    if not Store.query.first():

        default_store = Store(
            name="admin",
            password_hash=generate_password_hash("admin123")
        )

        db.session.add(default_store)

        db.session.commit()

        # Create default cashier
        default_cashier = Cashier(
            name="Default Cashier",
            username="cashier1",
            password_hash=generate_password_hash("cashier123"),
            store_id=default_store.id
        )
        db.session.add(default_cashier)
        db.session.commit()

        # Create sample products for testing POS
        sample_products = [
            {"code": "PROD001", "name": "iPhone 13", "buy": 50000, "sell": 65000},
            {"code": "PROD002", "name": "Samsung Galaxy", "buy": 40000, "sell": 52000},
            {"code": "PROD003", "name": "OnePlus 9", "buy": 35000, "sell": 45000},
            {"code": "PROD004", "name": "Screen Protector", "buy": 300, "sell": 500},
            {"code": "PROD005", "name": "Phone Case", "buy": 400, "sell": 800},
            {"code": "PROD006", "name": "USB Cable", "buy": 200, "sell": 350},
            {"code": "PROD007", "name": "Charger", "buy": 1500, "sell": 2500},
        ]
        
        for prod in sample_products:
            product = Product(
                product_code=prod["code"],
                name=prod["name"],
                buy_price=prod["buy"],
                sell_price=prod["sell"],
                stock=100,
                store_id=default_store.id
            )
            db.session.add(product)
        
        db.session.commit()

        print("✅ Default store created: username=admin, password=admin123")
        print("✅ Default cashier created: username=cashier1, password=cashier123")
        print("✅ Sample products created (use codes like PROD001, PROD002, etc.)")

# ---------------------- LOGIN DECORATOR ----------------------

# ---------------------- LOGIN DECORATOR ----------------------
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):

#         store_id = session.get('store_id')
        
#         # If no session exists
#         if not store_id:
#             flash("🔒 Please login first!")
#             return redirect(url_for('login'))

#         # Check if store exists in database
#         store = Store.query.get(store_id)

#         # If store deleted or invalid
#         if not store:
#             session.clear()
#             flash("❌ Store not found. Please login again.")
#             return redirect(url_for('login'))

#         return f(*args, **kwargs)

#     return decorated_function


from functools import wraps
from flask import session, redirect, url_for, flash

# def login_required(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):

#         if not session.get("user_id"):
#             flash("🔒 Please login first!")
#             return redirect(url_for("login"))

#         store = Store.query.get(session.get("store_id"))

#         if not store:
#             session.clear()
#             flash("❌ Store not found. Please login again.")
#             return redirect(url_for("login"))

#         return f(*args, **kwargs)

#     return wrapper
# # Admin login is handled through the store login route. Existing admin stores authenticate using /login.

# ---------------------- LOGIN DECORATOR ----------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        store_id = session.get('store_id')

        # If no session exists
        if not store_id:
            flash("🔒 Please login first!")
            return redirect(url_for('login'))

        # Check if store exists in database
        store = Store.query.get(store_id)

        # If store deleted or invalid
        if not store:
            session.clear()
            flash("❌ Store not found. Please login again.")
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('🔒 Admin access required')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        store_name = request.form['store_name'].strip()
        password = request.form['password']

        store = Store.query.filter_by(
            name=store_name
        ).first()

        if store and check_password_hash(
            store.password_hash,
            password
        ):
           
            
            session.clear()

            session['user_id'] = store.id
            session['store_id'] = store.id
            session['role'] = 'admin'

            flash("✅ Admin login successful")

            return redirect(url_for('dashboard'))

        flash("❌ Invalid admin credentials")

    return render_template('login.html')

def current_user_id():

    return (
        session.get("cashier_id")
        or session.get("admin_id")
    )

@app.route('/logout')
@login_required
def logout():

    session.clear()

    flash("✅ Logged out")

    return redirect(url_for('login'))
# @app.route('/logout')
# @login_required
# def logout():
#     session.pop('store_id', None)
#     session.pop('user_id', None)
#     session.pop('role', None)
#     flash("Logged out successfully")
#     return redirect(url_for('login'))
# Context processor: makes 'now' available in all templates
'''@app.context_processor
def inject_now():
    return {'now': datetime.now().replace(microsecond=0)}'''


@app.route('/')
@login_required
def dashboard():
    store = Store.query.get_or_404(session['store_id'])

    # filters (admin dashboard)
    q = request.args.get('q', '').strip()
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    payment_method = request.args.get('payment_method', '').strip()

    start_date = end_date = None
    if start_raw:
        try:
            start_date = datetime.strptime(start_raw, '%Y-%m-%d')
        except ValueError:
            start_date = None
    if end_raw:
        try:
            end_date = datetime.strptime(end_raw, '%Y-%m-%d')
        except ValueError:
            end_date = None

    products = store.products
    if q:
        like = f"%{q}%"
        # filter in python because store.products is relationship collection
        products = [p for p in products if (p.name and q.lower() in p.name.lower()) or (p.product_code and q.lower() in p.product_code.lower())]

    # total_profit based on filtered sales
    sales_q = Sale.query.filter(Sale.store_id == store.id)
    if start_date and end_date:
        sales_q = sales_q.filter(Sale.sale_date.between(start_date, end_date))
    elif start_date:
        sales_q = sales_q.filter(Sale.sale_date >= start_date)
    elif end_date:
        sales_q = sales_q.filter(Sale.sale_date <= end_date)
    if payment_method:
        sales_q = sales_q.filter(Sale.payment_method == payment_method)

    filtered_sales = sales_q.all()
    total_profit = sum([s.profit or 0 for s in filtered_sales])

    # stock value uses current calculated stock (not filtered by time)
    total_stock_value = sum([p.buy_price * p.calculated_stock for p in store.products])

    participants = store.participants
    num_participants = len(participants)
    profit_per_participant = total_profit / num_participants if num_participants > 0 else 0

    # per-product filtered profit
    filtered_profit_by_pid = {}
    for s in filtered_sales:
        pid = s.product_id
        filtered_profit_by_pid[pid] = filtered_profit_by_pid.get(pid, 0) + (s.profit or 0)

    for p in products:
        p.filtered_profit = filtered_profit_by_pid.get(p.id, None)

    return render_template('dashboard.html', store=store, products=products,
                           total_profit=round(total_profit, 2), total_stock_value=round(total_stock_value, 2),
                           participants=participants, profit_per_participant=round(profit_per_participant, 2))


# KPI exports (filtered by same query params)
@app.route('/dashboard/export/kpi/excel')
@login_required
def export_dashboard_kpi_excel():
    store = Store.query.get_or_404(session['store_id'])
    q = request.args.get('q', '').strip()
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    payment_method = request.args.get('payment_method', '').strip()

    start_date = end_date = None
    if start_raw:
        try:
            start_date = datetime.strptime(start_raw, '%Y-%m-%d')
        except ValueError:
            start_date = None
    if end_raw:
        try:
            end_date = datetime.strptime(end_raw, '%Y-%m-%d')
        except ValueError:
            end_date = None

    sales_q = Sale.query.filter(Sale.store_id == store.id)
    if start_date and end_date:
        sales_q = sales_q.filter(Sale.sale_date.between(start_date, end_date))
    elif start_date:
        sales_q = sales_q.filter(Sale.sale_date >= start_date)
    elif end_date:
        sales_q = sales_q.filter(Sale.sale_date <= end_date)
    if payment_method:
        sales_q = sales_q.filter(Sale.payment_method == payment_method)

    filtered_sales = sales_q.all()
    total_profit = sum([s.profit or 0 for s in filtered_sales])
    total_stock_value = sum([p.buy_price * p.calculated_stock for p in store.products])
    participants = store.participants
    num_participants = len(participants)
    profit_per_participant = total_profit / num_participants if num_participants > 0 else 0

    # product filtered profits
    filtered_profit_by_pid = {}
    for s in filtered_sales:
        pid = s.product_id
        filtered_profit_by_pid[pid] = filtered_profit_by_pid.get(pid, 0) + (s.profit or 0)

    # optional product list filter by q
    products = store.products
    if q:
        ql = q.lower()
        products = [p for p in products if (p.name and ql in p.name.lower()) or (p.product_code and ql in p.product_code.lower())]

    df = pd.DataFrame([
        {
            'Product Code': p.product_code,
            'Name': p.name,
            'Category': p.category,
            'Stock (Calculated)': p.calculated_stock,
            'Sold': p.sold,
            'Filtered Profit': round(filtered_profit_by_pid.get(p.id, 0), 2),
        }
        for p in products
    ])

    kpi = pd.DataFrame([
        {'KPI': 'Total Profit (Filtered)', 'Value': round(total_profit, 2)},
        {'KPI': 'Total Stock Value (Current)', 'Value': round(total_stock_value, 2)},
        {'KPI': 'Profit per Participant (Filtered)', 'Value': round(profit_per_participant, 2)},
        {'KPI': 'Payment Method', 'Value': payment_method or 'All'},
        {'KPI': 'Start Date', 'Value': start_raw or ''},
        {'KPI': 'End Date', 'Value': end_raw or ''},
        {'KPI': 'Search', 'Value': q or ''},
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        kpi.to_excel(writer, index=False, sheet_name='KPI')
        df.to_excel(writer, index=False, sheet_name='Products')

    output.seek(0)
    return send_file(output, download_name=f"{store.name}_dashboard_kpi.xlsx", as_attachment=True)


@app.route('/dashboard/export/kpi/pdf')
@login_required
def export_dashboard_kpi_pdf():
    store = Store.query.get_or_404(session['store_id'])
    q = request.args.get('q', '').strip()
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    payment_method = request.args.get('payment_method', '').strip()

    start_date = end_date = None
    if start_raw:
        try:
            start_date = datetime.strptime(start_raw, '%Y-%m-%d')
        except ValueError:
            start_date = None
    if end_raw:
        try:
            end_date = datetime.strptime(end_raw, '%Y-%m-%d')
        except ValueError:
            end_date = None

    sales_q = Sale.query.filter(Sale.store_id == store.id)
    if start_date and end_date:
        sales_q = sales_q.filter(Sale.sale_date.between(start_date, end_date))
    elif start_date:
        sales_q = sales_q.filter(Sale.sale_date >= start_date)
    elif end_date:
        sales_q = sales_q.filter(Sale.sale_date <= end_date)
    if payment_method:
        sales_q = sales_q.filter(Sale.payment_method == payment_method)

    filtered_sales = sales_q.all()
    total_profit = sum([s.profit or 0 for s in filtered_sales])
    total_stock_value = sum([p.buy_price * p.calculated_stock for p in store.products])
    participants = store.participants
    num_participants = len(participants)
    profit_per_participant = total_profit / num_participants if num_participants > 0 else 0

    filtered_profit_by_pid = {}
    for s in filtered_sales:
        pid = s.product_id
        filtered_profit_by_pid[pid] = filtered_profit_by_pid.get(pid, 0) + (s.profit or 0)

    products = store.products
    if q:
        ql = q.lower()
        products = [p for p in products if (p.name and ql in p.name.lower()) or (p.product_code and ql in p.product_code.lower())]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    elements.append(Paragraph(f"{store.name} - Dashboard KPI Report", getSampleStyleSheet()['Title']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Payment Method: <b>{payment_method or 'All'}</b>", getSampleStyleSheet()['Normal']))
    elements.append(Paragraph(f"Start: <b>{start_raw or '-'}</b> | End: <b>{end_raw or '-'}</b>", getSampleStyleSheet()['Normal']))
    elements.append(Paragraph(f"Search: <b>{q or '-'}</b>", getSampleStyleSheet()['Normal']))
    elements.append(Spacer(1, 12))

    kpi_data = [
        ['Total Profit (Filtered)', f"{round(total_profit, 2):.2f}"],
        ['Total Stock Value (Current)', f"{round(total_stock_value, 2):.2f}"],
        ['Profit per Participant (Filtered)', f"{round(profit_per_participant, 2):.2f}"],
    ]
    kpi_table = Table(kpi_data, colWidths=[260, 120])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 18))

    data = [["Code", "Name", "Category", "Stock", "Sold", "Filtered Profit"]]
    for p in products:
        data.append([
            p.product_code,
            p.name,
            p.category,
            str(p.calculated_stock),
            str(p.sold),
            f"{round(filtered_profit_by_pid.get(p.id, 0), 2):.2f}",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{store.name}_dashboard_kpi.pdf", mimetype='application/pdf')



@app.route('/cashiers')
@login_required
@admin_required
def cashier_list():
    store = Store.query.get_or_404(session['store_id'])
    cashiers = Cashier.query.filter_by(store_id=store.id).all()
    return render_template('cashier_list.html', cashiers=cashiers)


@app.route('/cashier/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_cashier():
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']

        if Cashier.query.filter_by(username=username).first():
            flash('❌ Username already exists')
            return redirect(url_for('add_cashier'))

        cashier = Cashier(
            name=name,
            username=username,
            password_hash=generate_password_hash(password),
            store_id=session['store_id']
        )
        db.session.add(cashier)
        db.session.commit()
        flash('✅ Cashier added successfully')
        return redirect(url_for('cashier_list'))

    return render_template('cashier_add.html')


@app.route('/cashier/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cashier(id):
    cashier = Cashier.query.get_or_404(id)
    if cashier.store_id != session['store_id']:
        flash('❌ Cashier not found')
        return redirect(url_for('cashier_list'))

    if request.method == 'POST':
        cashier.name = request.form['name'].strip()
        username = request.form['username'].strip()
        if username != cashier.username and Cashier.query.filter_by(username=username).first():
            flash('❌ Username already exists')
            return redirect(url_for('edit_cashier', id=id))
        cashier.username = username
        if request.form['password']:
            cashier.password_hash = generate_password_hash(request.form['password'])
        db.session.commit()
        flash('✅ Cashier updated successfully')
        return redirect(url_for('cashier_list'))

    return render_template('cashier_edit.html', cashier=cashier)


@app.route('/cashier/delete/<int:id>')
@login_required
@admin_required
def delete_cashier(id):
    cashier = Cashier.query.get_or_404(id)
    if cashier.store_id != session['store_id']:
        flash('❌ Cashier not found')
        return redirect(url_for('cashier_list'))
    db.session.delete(cashier)
    db.session.commit()
    flash('🗑️ Cashier deleted')
    return redirect(url_for('cashier_list'))


# ---------------------- STORE MANAGEMENT ----------------------
@app.route('/stores')
def store_list():
    stores = Store.query.all()
    return render_template('store_list.html', stores=stores)

@app.route('/store/add', methods=['GET', 'POST'])
def add_store():
    if request.method == 'POST':
        name = request.form['name']
        password = generate_password_hash(request.form['password'])
        store = Store(name=name, password_hash=password)
        db.session.add(store)
        db.session.commit()
        flash("✅ Store added!")
        return redirect(url_for('store_list'))
    return render_template('store_edit.html')

@app.route('/store/edit/<int:id>', methods=['GET', 'POST'])
def edit_store(id):
    store = Store.query.get(id)
    if request.method == 'POST':
        store.name = request.form['name']
        if request.form['password']:
            store.password_hash = generate_password_hash(request.form['password'])
        db.session.commit()
        flash("✅ Store updated!")
        return redirect(url_for('store_list'))
    return render_template('store_edit.html', store=store)


@app.route('/store/delete/<int:id>')
@login_required
def delete_store(id):

    # Prevent deleting current logged-in store
    if session['store_id'] == id:
        flash("❌ You cannot delete your own store!")
        return redirect(url_for('store_list'))

    store = Store.query.get_or_404(id)

    db.session.delete(store)
    db.session.commit()

    flash("🗑️ Store deleted!")
    return redirect(url_for('store_list'))

@app.route('/product/sell/<int:product_id>', methods=['GET', 'POST'])
@login_required
def sell_product(product_id):
    store = Store.query.get(session['store_id'])
    product = Product.query.get_or_404(product_id)
    customers = store.customers

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        customer_name = request.form.get('customer_name') or ''
        customer_number = request.form.get('customer_number') or ''
        quantity = int(request.form['quantity'])
        discount = float(request.form.get('discount', 0) or 0)

        final_price = product.sell_price * (1 - discount / 100)

        customer = None

        # 🔴 CASE 1: Existing customer selected
        if customer_id:
            customer = Customer.query.get(int(customer_id))

        # 🔴 CASE 2: New customer
        else:
            customer = Customer.query.filter_by(customer_number=customer_number).first()

            if not customer:
                if not customer_name or not customer_number:
                    flash("❌ New customer details required!")
                    return redirect(url_for('product_list'))

                customer = Customer(
                    name=customer_name,
                    customer_number=customer_number,
                    store_id=store.id
                )
                db.session.add(customer)
                db.session.flush()  # get ID without commit

        # 🔴 Stock validation
        if quantity > product.calculated_stock:
            flash("❌ Not enough stock available!")
            return redirect(url_for('product_list'))

        # 🔴 Create sale
        # sale = Sale(
        #     product_id=product.id,
        #     customer_id=customer.id if customer else None,
        #     customer_name=customer.name if customer else customer_name,
        #     customer_number=customer.customer_number if customer else customer_number,
        #     quantity=quantity,
        #     selling_price=product.sell_price,
        #     # discount = float(request.form.get('discount', 0))

            
        #     discount=0,
        #     profit=round((product.sell_price - product.buy_price) * quantity, 2),
        #     sale_date=datetime.utcnow(),
        #     store_id=store.id
        # )
        sale = Sale(
           product_id=product.id,
           customer_id=customer.id if customer else None,
           customer_name=customer.name if customer else customer_name,
           customer_number=customer.customer_number if customer else customer_number,
           quantity=quantity,

    # ✅ FIXED PRICE (IMPORTANT)
          selling_price=round(final_price, 2),

    # only for display
          discount=discount,

         profit=round((final_price - product.buy_price) * quantity, 2),

         sale_date=datetime.utcnow(),
         store_id=store.id
)

        product.sold = (product.sold or 0 ) + quantity
        db.session.add(sale)
        db.session.commit()

        flash("✅ Sale recorded successfully!")
        return redirect(url_for('receipt', sale_id=sale.id))

    return render_template('sell_product.html', product=product, customers=customers)
@app.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    product = Product.query.get(sale.product_id)

    # If the sale is created from selling a device, Product.imei is usually empty.
    # We'll try to find the sold device by matching the stored customer_id and product.
    sold_device = None
    if sale.customer_id:
        sold_device = (
            DeviceInventory.query
            .join(ProductVariant, ProductVariant.id == DeviceInventory.variant_id)
            .filter(
                DeviceInventory.status == 'sold',
                DeviceInventory.customer_id == sale.customer_id,
                ProductVariant.product_id == sale.product_id,
            )
            .first()
        )

    return render_template(
        'receipt.html',
        sale=sale,
        product=product,
        device=sold_device,
    )

# ---------------------- ADVANCED SEARCH ----------------------
from datetime import datetime
from flask import render_template, request, session, flash, send_file
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ...existing code...
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    store = Store.query.get(session['store_id'])
    suppliers = store.suppliers
    q = request.form.get('query', '').strip()
    supplier_id = request.form.get('supplier_id')
    start = request.form.get('start')
    end = request.form.get('end')
    search_type = request.form.get('type', 'products')

    start_date = end_date = None
    if start or end:
        try:
            if start:
                start_date = datetime.strptime(start, '%Y-%m-%d')
            if end:
                end_date = datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "warning")

    results = []

    if search_type == 'products':
        query = Product.query.filter_by(store_id=store.id)
        if q:
            like = f"%{q}%"
            query = query.filter(
                (Product.name.ilike(like)) |
                (Product.product_code.ilike(like)) |
                (Product.imei.ilike(like))
            )
        results = query.all()

    elif search_type == 'purchases':
        query = Purchase.query.filter_by(store_id=store.id)
        if supplier_id:
            query = query.filter(Purchase.supplier_id == int(supplier_id))
        if start_date and end_date:
            query = query.filter(Purchase.purchase_date.between(start_date, end_date))
        elif start_date:
            query = query.filter(Purchase.purchase_date >= start_date)
        elif end_date:
            query = query.filter(Purchase.purchase_date <= end_date)
        if q:
            query = query.filter(Purchase.product_name.ilike(f"%{q}%"))
        results = query.all()

    elif search_type == 'receipts':
        query = Sale.query.filter_by(store_id=store.id)
        if start_date and end_date:
            query = query.filter(Sale.sale_date.between(start_date, end_date))
        elif start_date:
            query = query.filter(Sale.sale_date >= start_date)
        elif end_date:
            query = query.filter(Sale.sale_date <= end_date)
        if q:
            query = query.filter(Sale.customer_name.ilike(f"%{q}%"))
        results = query.all()

    elif search_type == 'customers':
        query = Customer.query.filter_by(store_id=store.id)
        if q:
            query = query.filter(
                (Customer.name.ilike(f"%{q}%")) |
                (Customer.customer_number.ilike(f"%{q}%"))
            )
        results = query.all()

    return render_template('search.html', results=results, suppliers=suppliers, search_type=search_type)
# ...existing code...
@app.route('/export_excel')
@login_required
def export_excel1():
    # For demo, export all products (you can filter based on search results)
    store = Store.query.get(session['store_id'])
    products = Product.query.filter_by(store_id=store.id).all()

    data = [{'ID': p.id, 'Name': p.name, 'Code': p.product_code, 'Stock': p.stock} for p in products]
    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

    output.seek(0)
    return send_file(output, download_name="search_results.xlsx", as_attachment=True)

@app.route('/export_pdf')
@login_required
def export_pdf1():
    store = Store.query.get(session['store_id'])
    products = Product.query.filter_by(store_id=store.id).all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, "Search Results (Products)")
    y = 720
    for prod in products:
        p.drawString(100, y, f"{prod.id}. {prod.name} — Stock: {prod.stock}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 750
    p.save()
    buffer.seek(0)
    return send_file(buffer, download_name="search_results.pdf", as_attachment=True)

# ---------------------- PARTICIPANTS ----------------------
@app.route('/participants')
@admin_required
@login_required
def participant_list():
    store = Store.query.get(session['store_id'])
    return render_template('participant_list.html', participants=store.participants)

@app.route('/participant/add', methods=['GET', 'POST'])
@login_required
def add_participant():
    store = Store.query.get(session['store_id'])
    if request.method == 'POST':
        name = request.form['name']
        participant = Participant(name=name, store=store)
        db.session.add(participant)
        db.session.commit()
        flash("✅ Participant added!")
        return redirect(url_for('participant_list'))
    return render_template('participant_edit.html')

@app.route('/participant/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_participant(id):
    participant = Participant.query.get(id)
    if request.method == 'POST':
        participant.name = request.form['name']
        db.session.commit()
        flash("✅ Participant updated!")
        return redirect(url_for('participant_list'))
    return render_template('participant_edit.html', participant=participant)

@app.route('/participant/delete/<int:id>')
@login_required
def delete_participant(id):
    participant = Participant.query.get(id)
    db.session.delete(participant)
    db.session.commit()
    flash("🗑️ Participant deleted!")
    return redirect(url_for('participant_list'))

# ----------------/product/edit/<int:id>'------ PRODUCTS ----------------------
@app.route('/products')
@login_required
def product_list():
    # store = Store.query.get(session['store_id'])
    store = Store.query.get_or_404(session['store_id'])
    return render_template('product_list.html', products=store.products)


from datetime import datetime








# ...existing code...
@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get(id)
    store = Store.query.get(session['store_id'])
    suppliers = store.suppliers
    if request.method == 'POST':
        product.product_code = request.form['product_code']
        product.imei = request.form['imei']
        product.name = request.form['name']
        product.category = request.form['category']
        product.buy_price = float(request.form['buy_price'])
        product.sell_price = float(request.form['sell_price'])
        product.stock = int(request.form['stock'])
        supplier_id = request.form.get('supplier_id')
        product.supplier_id = int(supplier_id) if supplier_id else None
       
        db.session.commit()
        flash("✅ Product updated!")
        return redirect(url_for('product_list'))
    return render_template('product_edit.html', product=product, suppliers=suppliers)





@app.route('/product/delete/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    flash("🗑️ Product deleted!")
    return redirect(url_for('product_list'))

# ---------------------- EXPORTS ----------------------
@app.route('/export/excel')
@login_required
def export_excel():
    store = Store.query.get(session['store_id'])
    data = [{
        'Product Code': p.product_code,
        'Name': p.name,
        'IMEI': p.imei,
        'Category': p.category,
        'Buy Price (PKR)': p.buy_price,
        'Sell Price (PKR)': p.sell_price,
        'Stock': p.stock,
        'Sold': p.sold,
        'Profit': (p.sell_price - p.buy_price) * p.sold
    } for p in store.products]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
    output.seek(0)
    return send_file(output, download_name="store_report.xlsx", as_attachment=True)


@app.route('/export/pdf')
@login_required
def export_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch

    store = Store.query.get(session['store_id'])

    # Prepare PDF in memory
    output = BytesIO()
    pdf = SimpleDocTemplate(output, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = ParagraphStyle('Subtitle', fontSize=12, spaceAfter=10)
    normal_style = styles['Normal']

    # Title and store name
    elements.append(Paragraph(f"Store Inventory Report", title_style))
    elements.append(Paragraph(f"Store Name: <b>{store.name}</b>", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Table header
    data = [["Product", "Category", "Buy Price (PKR)", "Sell Price (PKR)",
             "Stock", "Sold", "Profit (PKR)"]]

    total_profit = 0
    for p in store.products:
        profit = (p.sell_price - p.buy_price) * p.sold
        total_profit += profit
        data.append([
            p.name, p.category, f"{p.buy_price:.2f}", f"{p.sell_price:.2f}",
            str(p.stock), str(p.sold), f"{profit:.2f}"
        ])

    # Create and style table
    table = Table(data, colWidths=[1.4*inch, 1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#E6F0FF")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

    # Profit summary
    participants = store.participants
    num_participants = len(participants)
    profit_per_participant = total_profit / num_participants if num_participants > 0 else 0

    elements.append(Paragraph(f"<b>Total Profit (PKR):</b> {total_profit:.2f}", normal_style))
    elements.append(Paragraph(f"<b>Number of Participants:</b> {num_participants}", normal_style))
    elements.append(Paragraph(f"<b>Profit per Participant (PKR):</b> {profit_per_participant:.2f}", normal_style))

    pdf.build(elements)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name=f"{store.name}_report.pdf", mimetype='application/pdf')



@app.route('/dues/customers')
@login_required
def customer_ledger_list():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = CustomerLedger.query.filter_by(store_id=store_id)
    if q:
        # match by customer name or number
        query = query.join(Customer).filter(
            (Customer.name.ilike(f'%{q}%')) | (Customer.customer_number.ilike(f'%{q}%'))
        )
    if status == 'due':
        query = query.filter(CustomerLedger.due_amount > 0, CustomerLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(CustomerLedger.settled_at.isnot(None))

    ledgers = query.order_by(CustomerLedger.due_date.asc().nullsfirst(), CustomerLedger.id.desc()).all()

    return render_template('customer_ledger_list.html', ledgers=ledgers, q=q, status=status)


@app.route('/dues/customers/add', methods=['GET','POST'])
@login_required
def add_customer_ledger():
    if request.method == 'POST':
        store_id = session['store_id']
        customer_number = (request.form.get('customer_number') or '').strip()
        customer_name = (request.form.get('customer_name') or '').strip()
        reference_type = request.form.get('reference_type')
        reference_id = request.form.get('reference_id')
        total_amount = float(request.form.get('total_amount') or 0)
        paid_amount = float(request.form.get('paid_amount') or 0)
        due_date_raw = request.form.get('due_date')
        note = request.form.get('note')

        if not customer_number:
            flash('Customer number is required', 'warning')
            return redirect(url_for('add_customer_ledger'))

        customer = Customer.query.filter_by(store_id=store_id, customer_number=customer_number).first()
        if not customer:
            if not customer_name:
                flash('Customer name is required for new customer', 'warning')
                return redirect(url_for('add_customer_ledger'))
            customer = Customer(name=customer_name, customer_number=customer_number, store_id=store_id)
            db.session.add(customer)
            db.session.flush()

        if reference_id:
            try:
                reference_id = int(reference_id)
            except ValueError:
                reference_id = None
        else:
            reference_id = None

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, '%Y-%m-%dT%H:%M')
            except ValueError:
                due_date = None

        due_amount = max(0.0, total_amount - paid_amount)

        ledger = CustomerLedger(
            store_id=store_id,
            customer_id=customer.id,
            reference_type=reference_type,
            reference_id=reference_id,
            total_amount=total_amount,
            paid_amount=paid_amount,
            due_amount=due_amount,
            due_date=due_date,
            note=note,
        )

        if due_amount == 0:
            ledger.settled_at = datetime.utcnow()

        db.session.add(ledger)
        db.session.commit()

        flash('✅ Customer credit saved', 'success')
        return redirect(url_for('customer_ledger_list'))

    return render_template('customer_ledger_add.html', customer_number='', customer_name='')


@app.route('/dues/customers/<int:ledger_id>/pay', methods=['GET','POST'])
@login_required
def customer_ledger_pay(ledger_id):
    store_id = session['store_id']
    ledger = CustomerLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    if request.method == 'POST':
        received_amount = float(request.form.get('received_amount') or 0)
        note = request.form.get('note')
        paid_at_raw = request.form.get('paid_at')

        paid_at = datetime.utcnow()
        if paid_at_raw:
            try:
                paid_at = datetime.strptime(paid_at_raw, '%Y-%m-%dT%H:%M')
            except ValueError:
                paid_at = datetime.utcnow()

        ledger.paid_amount = (ledger.paid_amount or 0) + received_amount
        ledger.due_amount = max(0.0, (ledger.total_amount or 0) - ledger.paid_amount)
        if ledger.due_amount == 0:
            ledger.settled_at = paid_at
        db.session.commit()

        flash('✅ Payment recorded', 'success')
        return redirect(url_for('customer_ledger_list'))

    return render_template('customer_ledger_pay.html', ledger=ledger, now=datetime.now())


@app.route('/dues/customers/<int:ledger_id>/export/excel')
@login_required
def customer_ledger_export_excel(ledger_id):
    store_id = session['store_id']
    ledger = CustomerLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    df = pd.DataFrame([{ 
        'Ledger ID': ledger.id,
        'Customer': ledger.customer.name,
        'Customer Number': ledger.customer.customer_number,
        'Reference Type': ledger.reference_type,
        'Reference ID': ledger.reference_id,
        'Total Amount': ledger.total_amount,
        'Paid Amount': ledger.paid_amount,
        'Due Amount': ledger.due_amount,
        'Due Date': ledger.due_date,
        'Settled At': ledger.settled_at,
        'Note': ledger.note
    }])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Customer Due')
    output.seek(0)
    return send_file(output, download_name=f'customer_due_{ledger.id}.xlsx', as_attachment=True)


@app.route('/dues/customers/<int:ledger_id>/export/pdf')
@login_required
def customer_ledger_export_pdf(ledger_id):
    store_id = session['store_id']
    ledger = CustomerLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph('Customer Due Summary', styles['Title']))
    elements.append(Spacer(1, 12))

    data = [
        ['Customer', f"{ledger.customer.name} ({ledger.customer.customer_number})"],
        ['Reference', f"{ledger.reference_type} #{ledger.reference_id if ledger.reference_id else '-'}"],
        ['Total Amount', f"{ledger.total_amount:.2f}"],
        ['Paid Amount', f"{ledger.paid_amount:.2f}"],
        ['Due Amount', f"{ledger.due_amount:.2f}"],
        ['Due Date', str(ledger.due_date) if ledger.due_date else '-'],
        ['Settled At', str(ledger.settled_at) if ledger.settled_at else '-'],
        ['Note', ledger.note or '-'],
    ]

    table = Table(data, colWidths=[140, 380])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'customer_due_{ledger.id}.pdf', mimetype='application/pdf')


# ---------------------- DUES (ALL-EXPORTS) ----------------------
@app.route('/dues/customers/export/excel')
@login_required
def customer_dues_export_excel_all():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = CustomerLedger.query.filter_by(store_id=store_id)
    if q:
        query = query.join(Customer).filter(
            (Customer.name.ilike(f'%{q}%')) | (Customer.customer_number.ilike(f'%{q}%'))
        )

    if status == 'due':
        query = query.filter(CustomerLedger.due_amount > 0, CustomerLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(CustomerLedger.settled_at.isnot(None))

    ledgers = query.order_by(CustomerLedger.due_date.asc().nullsfirst(), CustomerLedger.id.desc()).all()

    df = pd.DataFrame([
        {
            'Ledger ID': l.id,
            'Customer': l.customer.name,
            'Customer Number': l.customer.customer_number,
            'Reference Type': l.reference_type,
            'Reference ID': l.reference_id,
            'Total Amount': l.total_amount,
            'Paid Amount': l.paid_amount,
            'Due Amount': l.due_amount,
            'Due Date': l.due_date,
            'Settled At': l.settled_at,
            'Note': l.note,
        }
        for l in ledgers
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Customer Dues')
    output.seek(0)

    store = Store.query.get_or_404(store_id)
    safe_status = status or 'all'
    return send_file(output, download_name=f'{store.name}_customer_dues_{safe_status}.xlsx', as_attachment=True)


@app.route('/dues/customers/export/pdf')
@login_required
def customer_dues_export_pdf_all():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = CustomerLedger.query.filter_by(store_id=store_id)
    if q:
        query = query.join(Customer).filter(
            (Customer.name.ilike(f'%{q}%')) | (Customer.customer_number.ilike(f'%{q}%'))
        )

    if status == 'due':
        query = query.filter(CustomerLedger.due_amount > 0, CustomerLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(CustomerLedger.settled_at.isnot(None))

    ledgers = query.order_by(CustomerLedger.due_date.asc().nullsfirst(), CustomerLedger.id.desc()).all()
    store = Store.query.get_or_404(store_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"{store.name} - Customer Dues Export", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Status: <b>{status}</b>" if status else "", styles['Normal']))
    if q:
        elements.append(Paragraph(f"Search: <b>{q}</b>", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [[
        'Ledger ID', 'Customer', 'Customer #', 'Reference', 'Total', 'Paid', 'Due', 'Due Date', 'Settled At', 'Note'
    ]]
    for l in ledgers:
        data.append([
            str(l.id),
            l.customer.name,
            l.customer.customer_number,
            f"{l.reference_type} #{l.reference_id if l.reference_id else '-'}",
            f"{l.total_amount:.2f}",
            f"{l.paid_amount:.2f}",
            f"{l.due_amount:.2f}",
            str(l.due_date) if l.due_date else '-',
            str(l.settled_at) if l.settled_at else '-',
            l.note or '-',
        ])

    table = Table(data, repeatRows=1, colWidths=[60, 120, 90, 120, 60, 60, 60, 80, 80, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    safe_status = status or 'all'
    return send_file(buffer, as_attachment=True, download_name=f'{store.name}_customer_dues_{safe_status}.pdf', mimetype='application/pdf')


@app.route('/dues/suppliers/export/excel')
@login_required
def supplier_dues_export_excel_all():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = SupplierLedger.query.filter_by(store_id=store_id)
    if q:
        query = query.join(Supplier).filter(
            (Supplier.name.ilike(f'%{q}%')) | (Supplier.phone.ilike(f'%{q}%'))
        )

    if status == 'due':
        query = query.filter(SupplierLedger.due_amount > 0, SupplierLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(SupplierLedger.settled_at.isnot(None))

    ledgers = query.order_by(SupplierLedger.due_date.asc().nullsfirst(), SupplierLedger.id.desc()).all()

    df = pd.DataFrame([
        {
            'Ledger ID': l.id,
            'Supplier': l.supplier.name,
            'Supplier Phone': l.supplier.phone,
            'Reference Type': l.reference_type,
            'Reference ID': l.reference_id,
            'Total Amount': l.total_amount,
            'Paid Amount': l.paid_amount,
            'Due Amount': l.due_amount,
            'Due Date': l.due_date,
            'Settled At': l.settled_at,
            'Note': l.note,
        }
        for l in ledgers
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Supplier Dues')
    output.seek(0)

    store = Store.query.get_or_404(store_id)
    safe_status = status or 'all'
    return send_file(output, download_name=f'{store.name}_supplier_dues_{safe_status}.xlsx', as_attachment=True)


@app.route('/dues/suppliers/export/pdf')
@login_required
def supplier_dues_export_pdf_all():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = SupplierLedger.query.filter_by(store_id=store_id)
    if q:
        query = query.join(Supplier).filter(
            (Supplier.name.ilike(f'%{q}%')) | (Supplier.phone.ilike(f'%{q}%'))
        )

    if status == 'due':
        query = query.filter(SupplierLedger.due_amount > 0, SupplierLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(SupplierLedger.settled_at.isnot(None))

    ledgers = query.order_by(SupplierLedger.due_date.asc().nullsfirst(), SupplierLedger.id.desc()).all()
    store = Store.query.get_or_404(store_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"{store.name} - Supplier Dues Export", styles['Title']))
    elements.append(Spacer(1, 12))
    if status:
        elements.append(Paragraph(f"Status: <b>{status}</b>", styles['Normal']))
    if q:
        elements.append(Paragraph(f"Search: <b>{q}</b>", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [[
        'Ledger ID', 'Supplier', 'Phone', 'Reference', 'Total', 'Paid', 'Due', 'Due Date', 'Settled At', 'Note'
    ]]
    for l in ledgers:
        data.append([
            str(l.id),
            l.supplier.name,
            l.supplier.phone or '-',
            f"{l.reference_type} #{l.reference_id if l.reference_id else '-'}",
            f"{l.total_amount:.2f}",
            f"{l.paid_amount:.2f}",
            f"{l.due_amount:.2f}",
            str(l.due_date) if l.due_date else '-',
            str(l.settled_at) if l.settled_at else '-',
            l.note or '-',
        ])

    table = Table(data, repeatRows=1, colWidths=[60, 140, 90, 120, 60, 60, 60, 80, 80, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    safe_status = status or 'all'
    return send_file(buffer, as_attachment=True, download_name=f'{store.name}_supplier_dues_{safe_status}.pdf', mimetype='application/pdf')





@app.route('/suppliers')
@admin_required
@login_required
def supplier_list():
    # store = Store.query.get(session['store_id'])
    store = Store.query.get_or_404(session['store_id'])
    return render_template('supplier_list.html', suppliers=store.suppliers)





@app.route('/supplier/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    store = Store.query.get(session['store_id'])
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']  # ✅ match model field
        location=request.form['location']
        supplier = Supplier(name=name, phone=phone,location=location, store=store)
        db.session.add(supplier)
        db.session.commit()
        flash("✅ Supplier added!")
        return redirect(url_for('supplier_list'))
    return render_template('supplier_edit.html')  # same template works for add/edit


@app.route('/supplier/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier.name = request.form['name']
        supplier.phone = request.form['phone']  # ✅ match model field
        supplier.location=request.form['location']
        db.session.commit()
        flash("✅ Supplier updated!")
        return redirect(url_for('supplier_list'))
    return render_template('supplier_edit.html', supplier=supplier)


@app.route('/supplier/delete/<int:id>')
@login_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash("🗑️ Supplier deleted!")
    return redirect(url_for('supplier_list'))



# ---------------------- SUPPLIER LEDGER (Purchases view) ----------------------
@app.route('/supplier/<int:supplier_id>/ledger')
@login_required
def supplier_ledger(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    purchases = supplier.purchases  # All purchases from this supplier
    total = sum(p.total_price() for p in purchases)
    return render_template('supplier_ledger.html', supplier=supplier, purchases=purchases, total=total)


# ---------------------- SUPPLIER DUES (Ledgers) ----------------------
@app.route('/dues/suppliers')
@login_required
def supplier_ledger_list():
    store_id = session['store_id']
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = SupplierLedger.query.filter_by(store_id=store_id)

    if q:
        query = query.join(Supplier).filter(
            (Supplier.name.ilike(f'%{q}%')) | (Supplier.phone.ilike(f'%{q}%'))
        )

    if status == 'due':
        query = query.filter(SupplierLedger.due_amount > 0, SupplierLedger.settled_at.is_(None))
    elif status == 'settled':
        query = query.filter(SupplierLedger.settled_at.isnot(None))

    ledgers = query.order_by(SupplierLedger.due_date.asc().nullsfirst(), SupplierLedger.id.desc()).all()
    return render_template('supplier_ledger_list.html', ledgers=ledgers, q=q, status=status)


@app.route('/dues/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier_ledger():
    if request.method == 'POST':
        store_id = session['store_id']
        supplier_name = (request.form.get('supplier_name') or '').strip()
        supplier_phone = (request.form.get('supplier_phone') or '').strip()
        supplier_location = (request.form.get('supplier_location') or '').strip()
        reference_type = request.form.get('reference_type')
        reference_id = request.form.get('reference_id')
        total_amount = float(request.form.get('total_amount') or 0)
        paid_amount = float(request.form.get('paid_amount') or 0)
        due_date_raw = request.form.get('due_date')
        note = request.form.get('note')

        if not supplier_name:
            flash('Supplier name is required', 'warning')
            return redirect(url_for('add_supplier_ledger'))

        supplier = Supplier.query.filter_by(store_id=store_id, name=supplier_name).first()
        if not supplier:
            supplier = Supplier(
                name=supplier_name,
                phone=supplier_phone or None,
                location=supplier_location or None,
                store_id=store_id
            )
            db.session.add(supplier)
            db.session.flush()

        if reference_id:
            try:
                reference_id = int(reference_id)
            except ValueError:
                reference_id = None
        else:
            reference_id = None

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, '%Y-%m-%dT%H:%M')
            except ValueError:
                due_date = None

        due_amount = max(0.0, total_amount - paid_amount)

        ledger = SupplierLedger(
            store_id=store_id,
            supplier_id=supplier.id,
            reference_type=reference_type,
            reference_id=reference_id,
            total_amount=total_amount,
            paid_amount=paid_amount,
            due_amount=due_amount,
            due_date=due_date,
            note=note,
        )

        if due_amount == 0:
            ledger.settled_at = datetime.utcnow()

        db.session.add(ledger)
        db.session.commit()

        flash('✅ Supplier credit saved', 'success')
        return redirect(url_for('supplier_ledger_list'))

    return render_template('supplier_ledger_add.html', supplier_name='', supplier_phone='', supplier_location='')


@app.route('/dues/suppliers/<int:ledger_id>/pay', methods=['GET', 'POST'])
@login_required
def supplier_ledger_pay(ledger_id):
    store_id = session['store_id']
    ledger = SupplierLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    if request.method == 'POST':
        received_amount = float(request.form.get('received_amount') or 0)
        note = request.form.get('note')
        paid_at_raw = request.form.get('paid_at')

        paid_at = datetime.utcnow()
        if paid_at_raw:
            try:
                paid_at = datetime.strptime(paid_at_raw, '%Y-%m-%dT%H:%M')
            except ValueError:
                paid_at = datetime.utcnow()

        ledger.paid_amount = (ledger.paid_amount or 0) + received_amount
        ledger.due_amount = max(0.0, (ledger.total_amount or 0) - ledger.paid_amount)
        if ledger.due_amount == 0:
            ledger.settled_at = paid_at
        db.session.commit()

        flash('✅ Payment recorded', 'success')
        return redirect(url_for('supplier_ledger_list'))

    return render_template('supplier_ledger_pay.html', ledger=ledger, now=datetime.now())


@app.route('/dues/suppliers/<int:ledger_id>/export/excel')
@login_required
def supplier_ledger_export_excel(ledger_id):
    store_id = session['store_id']
    ledger = SupplierLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    df = pd.DataFrame([{
        'Ledger ID': ledger.id,
        'Supplier': ledger.supplier.name,
        'Supplier Phone': ledger.supplier.phone,
        'Reference Type': ledger.reference_type,
        'Reference ID': ledger.reference_id,
        'Total Amount': ledger.total_amount,
        'Paid Amount': ledger.paid_amount,
        'Due Amount': ledger.due_amount,
        'Due Date': ledger.due_date,
        'Settled At': ledger.settled_at,
        'Note': ledger.note
    }])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Supplier Due')
    output.seek(0)

    return send_file(output, download_name=f'supplier_due_{ledger.id}.xlsx', as_attachment=True)


@app.route('/dues/suppliers/<int:ledger_id>/export/pdf')
@login_required
def supplier_ledger_export_pdf(ledger_id):
    store_id = session['store_id']
    ledger = SupplierLedger.query.filter_by(id=ledger_id, store_id=store_id).first_or_404()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph('Supplier Due Summary', styles['Title']))
    elements.append(Spacer(1, 12))

    data = [
        ['Supplier', f"{ledger.supplier.name} ({ledger.supplier.phone or '-'} )"],
        ['Reference', f"{ledger.reference_type} #{ledger.reference_id if ledger.reference_id else '-'}"],
        ['Total Amount', f"{ledger.total_amount:.2f}"],
        ['Paid Amount', f"{ledger.paid_amount:.2f}"],
        ['Due Amount', f"{ledger.due_amount:.2f}"],
        ['Due Date', str(ledger.due_date) if ledger.due_date else '-'],
        ['Settled At', str(ledger.settled_at) if ledger.settled_at else '-'],
        ['Note', ledger.note or '-'],
    ]

    table = Table(data, colWidths=[140, 380])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f'supplier_due_{ledger.id}.pdf', mimetype='application/pdf')


# ---------------------- SALES REPORTS & RECEIPTS ----------------------

@app.route('/sales')
@login_required
def sales_list():
    store = Store.query.get(session['store_id'])
    sales = Sale.query.filter_by(store_id=store.id).all()
    return render_template('sales_list.html', sales=sales)

@app.route('/export/sales/excel')
@login_required
def export_sales_excel():
    store = Store.query.get(session['store_id'])
    data = [{
        'ID': s.id,
        'Product': s.product.name,
        'Customer Name': s.customer_name,
        'Customer Number': s.customer_number,
        'Quantity': s.quantity,
        'Sale Date': s.sale_date
    } for s in store.sales]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales')
    output.seek(0)
    return send_file(output, download_name="sales_report.xlsx", as_attachment=True)

@app.route('/export/sales/pdf')
@login_required
def export_sales_pdf():
    store = Store.query.get(session['store_id'])
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"{store.name} Sales Report", styles['Title']))

    data = [['ID', 'Product', 'Customer Name', 'Customer Number', 'Quantity', 'Sale Date']]
    for s in store.sales:
        data.append([s.id, s.product.name, s.customer_name, s.customer_number, s.quantity, s.sale_date])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return send_file(output, download_name="sales_report.pdf", as_attachment=True)

@app.route('/receipt/<int:sale_id>/download')
@login_required
def download_receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    product = Product.query.get(sale.product_id)
    store = Store.query.get(session['store_id'])

    receipt_url = url_for('receipt', sale_id=sale.id, _external=True)
    qr_code = qr.QrCodeWidget(receipt_url)
    bounds = qr_code.getBounds()
    qr_size = 80
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    qr_drawing = Drawing(qr_size, qr_size, transform=[qr_size/width, 0, 0, qr_size/height, 0, 0])
    qr_drawing.add(qr_code)

    barcode_drawing = createBarcodeDrawing('Code128', value=str(sale.id), barHeight=18 * mm, barWidth=0.6)

    unit_price = sale.selling_price or product.sell_price
    line_total = unit_price * sale.quantity
    discount_amount = line_total * (sale.discount or 0) / 100
    total_payable = line_total - discount_amount
    discount_label = f"{sale.discount:.0f}%" if sale.discount else '0%'

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 1
    normal = styles['Normal']
    heading = styles['Heading4']

    elements.append(Paragraph(store.name, title_style))
    elements.append(Paragraph('Official Sales Receipt', heading))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph('A smart professional invoice for mobile sales', normal))
    elements.append(Spacer(1, 16))

    header_data = [
        ['Store:', store.name, 'Receipt #', f"#{sale.id}"],
        ['Date:', sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'), 'Payment:', (getattr(sale, 'payment_method', None) or 'cash').replace('_', ' ').title()],

        ['Customer:', sale.customer_name or 'Walk-in', 'Phone:', sale.customer_number or '-'],
    ]

    header_table = Table(header_data, colWidths=[70, 180, 70, 110])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 16))

    item_data = [
        ['Item', 'Code', 'IMEI', 'Qty', 'Unit Price', 'Discount', 'Line Total'],
        [
            product.name,
            product.product_code or '-',
            product.imei or '-',
            str(sale.quantity),
            f"Rs {unit_price:.2f}",
            f"{discount_label}",
            f"Rs {total_payable:.2f}"
        ]
    ]

    item_table = Table(item_data, colWidths=[150, 70, 90, 40, 70, 60, 70])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 18))

    summary_data = [
        ['Subtotal', f"Rs {line_total:.2f}"],
        ['Discount', f"{discount_label} ({'Rs %.2f' % discount_amount})"],
        ['Total Payable', f"Rs {total_payable:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[350, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    payment_method = getattr(sale, 'payment_method', None) or 'cash'
    elements.append(Paragraph(f'Payment Method: {payment_method.replace("_", " ").title()}', normal))


    elements.append(Spacer(1, 12))
    elements.append(Paragraph('Scan this QR to view the receipt online:', normal))
    elements.append(Spacer(1, 8))
    elements.append(qr_drawing)
    elements.append(Spacer(1, 18))
    elements.append(Paragraph(f'Receipt Reference: #{sale.id}', normal))
    elements.append(Spacer(1, 8))
    elements.append(barcode_drawing)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph('Thank you for shopping with us!', styles['Italic']))

    doc.build(elements)
    output.seek(0)
    return send_file(output, download_name=f"receipt_{sale.id}.pdf", as_attachment=True, mimetype='application/pdf')



@app.route('/receipt/<int:sale_id>/send_email', methods=['POST'])
@login_required
def send_receipt_email(sale_id):
    to_email = request.form.get('to_email', '').strip()
    if not to_email:
        flash("❌ Recipient email required", "warning")
        return redirect(url_for('receipt', sale_id=sale_id))

    sale = Sale.query.get_or_404(sale_id)
    product = Product.query.get(sale.product_id)
    store = Store.query.get(session['store_id'])

    # Generate PDF in-memory (same layout as download_receipt)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"{store.name} - Receipt", styles['Title']))
    elements.append(Paragraph(f"Sale ID: {sale.id}", styles['Normal']))
    elements.append(Paragraph(f"Date: {sale.sale_date}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))

    data = [
        ['Product', product.name if product else "N/A"],
        ['Product Code', product.product_code if product else "N/A"],
        ['IMEI', product.imei or 'N/A'],
        ['Category', product.category or 'N/A'],
        ['Customer Name', sale.customer_name or 'N/A'],
        ['Customer Number', sale.customer_number or 'N/A'],
        ['Quantity', sale.quantity],
        ['Unit Price (PKR)', product.sell_price if product else 0],
        ['Total Price (PKR)', (product.sell_price * sale.quantity) if product else 0]
    ]

    table = Table(data, hAlign='LEFT', colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Paragraph(" ", styles['Normal']))
    elements.append(Paragraph("Thank you for your purchase!", styles['Italic']))

    doc.build(elements)
    output.seek(0)
    pdf_bytes = output.read()

    # SMTP config from environment variables
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 465))
    smtp_user = os.environ.get('EMAIL_USER')
    smtp_pass = os.environ.get('EMAIL_PASSWORD')
    print("Loaded EMAIL_USER:", smtp_user)
    print("Loaded EMAIL_PASS:", smtp_pass)

  


    if not smtp_user or not smtp_pass:
        flash("❌ Email credentials not configured. Set EMAIL_USER and EMAIL_PASSWORD env vars.", "danger")
        return redirect(url_for('receipt', sale_id=sale_id))

    try:
        msg = EmailMessage()
        msg['Subject'] = f"Receipt #{sale.id} - {store.name}"
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg.set_content(f"Dear customer,\n\nPlease find attached the receipt for your purchase (Sale ID: {sale.id}).\n\nThank you,\n{store.name}")

        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"receipt_{sale.id}.pdf")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)

        flash(f"✅ Receipt emailed to {to_email}", "success")
    except Exception as e:
        current_app.logger.exception("Error sending receipt email")
        flash(f"❌ Failed to send email: {e}", "danger")
   
    return redirect(url_for('receipt', sale_id=sale_id))

@app.route('/receipt/<int:sale_id>/send_whatsapp', methods=['POST'])
@login_required
def send_receipt_whatsapp(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    product = Product.query.get(sale.product_id)

    customer_number = sale.customer_number
    if not customer_number:
        flash("❌ Customer number missing in sale record.", "warning")
        return redirect(url_for('receipt', sale_id=sale_id))

    # Convert Pakistan mobile 03XXXXXXXXX → 92XXXXXXXXXX
    customer_number = customer_number.strip().replace(" ", "")
    if customer_number.startswith("0"):
        customer_number = "92" + customer_number[1:]

    store = Store.query.get(session['store_id'])

    # Re-generate PDF (same as email)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"{store.name} - Receipt", styles['Title']))
    elements.append(Paragraph(f"Sale ID: {sale.id}", styles['Normal']))
    elements.append(Paragraph(f"Date: {sale.sale_date}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))

    data = [
        ['Product', product.name],
        ['Product Code', product.product_code],
        ['IMEI', product.imei or 'N/A'],
        ['Category', product.category],
        ['Customer Name', sale.customer_name],
        ['Customer Number', sale.customer_number],
        ['Quantity', sale.quantity],
        ['Unit Price (PKR)', product.sell_price],
        ['Total Price (PKR)', product.sell_price * sale.quantity]
    ]

    table = Table(data, hAlign='LEFT', colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)
    output.seek(0)
    pdf_bytes = output.read()

    # Send via WhatsApp API
    response = send_whatsapp_invoice(customer_number, pdf_bytes, sale_id)

    if "messages" in response:
        flash(f"✅ WhatsApp invoice sent to {sale.customer_number}", "success")
    else:
        flash(f"❌ Failed to send WhatsApp invoice: {response}", "danger")

    return redirect(url_for('receipt', sale_id=sale_id))


# ---------------------- REPORTS ----------------------

@app.route('/reports', methods=['GET'])
@login_required
def reports():
    store = Store.query.get(session['store_id'])
    start = request.args.get('start')
    end = request.args.get('end')
    q = Sale.query.filter_by(store_id=store.id)
    if start: q = q.filter(Sale.sale_date >= start)
    if end: q = q.filter(Sale.sale_date <= end)
    sales = q.all()
    # Also provide export links with same query params
    return render_template('reports.html', sales=sales)

# ---------------------- STOCK MANAGEMENT ----------------------    


# @app.route('/product/restock/<int:id>', methods=['GET', 'POST'])
# def restock_product(id):
#     product = Product.query.get_or_404(id)
#     if request.method == 'POST':
#         add_qty = int(request.form['quantity'])
#         product.stock += add_qty
#         db.session.commit()
#         flash('Product restocked successfully!', 'success')
#         return redirect(url_for('dashboard'))
#     return render_template('restock.html', product=product)

# ---------------------- CUSTOMERS ----------------------
@app.route('/customers')
@login_required
def customer_list():
    store = Store.query.get(session['store_id'])
    return render_template('customer_list.html', customers=store.customers)

@app.route('/customer/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    store = Store.query.get(session['store_id'])
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['customer_number']
        customer = Customer(name=name, customer_number=phone, store=store)
        db.session.add(customer)
        db.session.commit()
        flash("✅ Customer added!")
        return redirect(url_for('customer_list'))
    return render_template('customer_edit.html')



@app.route('/customer/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.customer_number = request.form['customer_number']
        db.session.commit()
        flash("✅ Customer updated!")
        return redirect(url_for('customer_list'))
    return render_template('customer_edit.html', customer=customer)

@app.route('/customer/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash("🗑️ Customer deleted!")
    return redirect(url_for('customer_list'))

@app.route('/customer/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('customer_detail.html', customer=customer)


@app.route('/customer/<int:customer_id>/export')
@login_required
def export_customer_sales(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = [{
        'Product': s.product.name,
        'IMEI': s.product.imei or '',
        'Quantity': s.quantity,
        'Unit Price': s.product.sell_price,
        'Total Price': s.product.sell_price * s.quantity,
        'Date': s.sale_date
    } for s in customer.sales]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Customer Sales')
    output.seek(0)
    return send_file(output, download_name=f"{customer.name}_sales.xlsx", as_attachment=True)

from flask import current_app
from datetime import timedelta, datetime

# Replace add_product with this safer version
@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    store = Store.query.get(session['store_id'])
    suppliers = store.suppliers

    if request.method == 'POST':
        # debug print of incoming form
        current_app.logger.debug("add_product form: %s", dict(request.form))

        try:
            product_code = request.form.get('product_code', '').strip() or None
            name = request.form.get('name', '').strip()
            imei = request.form.get('imei', '').strip() or None
            category = request.form.get('category', '').strip()
            buy_price = float(request.form.get('buy_price') or 0)
            sell_price = float(request.form.get('sell_price') or 0)
            stock = int(request.form.get('stock') or 0)
            supplier_id = request.form.get('supplier_id') or None
            supplier_id = int(supplier_id) if supplier_id else None
            quantity = int(request.form.get('quantity') or 0)
            unit_price = float(request.form.get('unit_price') or 0)

            if not name or not category:
                flash("Please fill required product fields", "warning")
                return redirect(url_for('add_product'))

            # Try find existing by product_code or imei within this store
            existing = None
            if product_code:
                existing = Product.query.filter_by(product_code=product_code, store_id=store.id).first()
            if not existing and imei:
                existing = Product.query.filter_by(imei=imei, store_id=store.id).first()

            if existing:
                # add purchased quantity to existing stock
                existing.stock = (existing.stock or 0) + quantity
                existing.buy_price = buy_price
                existing.sell_price = sell_price
                existing.supplier_id = supplier_id
                db.session.add(existing)
                db.session.flush()
                product_id = existing.id
            else:
                p = Product(
                    product_code=product_code,
                    name=name,
                    imei=imei,
                    category=category,
                    buy_price=buy_price,
                    sell_price=sell_price,
                #   stock=(stock or 0) + (quantity or 0), 
                stock=0,
                    store=store,
                    supplier_id=supplier_id
                )
                db.session.add(p)
                db.session.flush()
                product_id = p.id

            purchase = Purchase(
                supplier_id=supplier_id if supplier_id else None,
                product_id=product_id,
                product_name=name,
                quantity=quantity,
                unit_price=unit_price,
                purchase_date=datetime.utcnow(),
                store_id=store.id
            )
            db.session.add(purchase)
            db.session.commit()
            flash("✅ Product & Purchase saved", "success")
            return redirect(url_for('product_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error in add_product")
            flash(f"Error saving product: {e}", "danger")
            return redirect(url_for('add_product'))

    return render_template('product_edit.html', suppliers=suppliers)
# ...existing code...


# Replace add_purchase with robust handler

@app.route('/add_purchase', methods=['GET', 'POST'])
@app.route('/add_purchase/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_purchase(product_id=None):
# def add_purchase():
    store = Store.query.get(session['store_id'])
    suppliers = store.suppliers
    # product = None

    product = None

# 🔹 Load existing product if purchase opened from product list
    if product_id:
        product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        current_app.logger.debug("add_purchase form: %s", dict(request.form))
        try:
            product_code = request.form.get('product_code', '').strip() or None
            name = request.form.get('product_name', '').strip()
            imei = request.form.get('imei', '').strip() or None
            category = request.form.get('category', '').strip()
            buy_price = float(request.form.get('buy_price') or 0)
            sell_price = float(request.form.get('sell_price') or 0)
            stock = int(request.form.get('stock') or 0)
            supplier_id = request.form.get('supplier_id') or None
            supplier_id = int(supplier_id) if supplier_id else None
            quantity = int(request.form.get('quantity') or 0)
            unit_price = float(request.form.get('unit_price') or 0)

            if not name:
                flash("Product name is required", "warning")
                return redirect(url_for('add_purchase'))

            # existing_product = None
            # if product_code:
            #     existing_product = Product.query.filter_by(product_code=product_code, store_id=store.id).first()
            # if not existing_product and imei:
            #     existing_product = Product.query.filter_by(imei=imei, store_id=store.id).first()

            existing_product = product

            if not existing_product and product_code:
              existing_product = Product.query.filter_by(
              product_code=product_code,
              store_id=store.id
              ).first()

            if not existing_product and imei:
              existing_product = Product.query.filter_by(
              imei=imei,
              store_id=store.id
              ).first()
            if existing_product:
                # INCREASE STOCK
                existing_product.stock = (
                    existing_product.stock or 0
                ) + quantity

                # UPDATE PRICES
                existing_product.buy_price = buy_price

                existing_product.sell_price = sell_price

                # UPDATE SUPPLIER
                existing_product.supplier_id = supplier_id

                # STOCK STATUS
                existing_product.in_stock = True

                db.session.add(existing_product)

                db.session.flush()

                product = existing_product
            else:
                new_product = Product(
                    product_code=product_code,
                    name=name,
                    imei=imei,
                    category=category,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    # stock=(stock or 0) + (quantity or 0),
                    stock=quantity,
                    store=store,
                    supplier_id=supplier_id
                )
                db.session.add(new_product)
                db.session.flush()
                product = new_product

            new_purchase = Purchase(
                supplier_id=supplier_id,
                product_id=product.id if product else None,
                product_name=name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price,
                purchase_date=datetime.utcnow(),
                store_id=store.id
            )
            db.session.add(new_purchase)
            db.session.commit()
            flash('✅ Product and Purchase saved successfully!', 'success')
            return redirect(url_for('add_purchase'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error in add_purchase")
            flash(f"Error saving purchase: {e}", "danger")
            return redirect(url_for('add_purchase'))

    return render_template('purchase_edit.html', suppliers=suppliers, product=product)
# ...existing code...







@app.route('/purchases')
@login_required
def purchase_list():
    store = Store.query.get(session['store_id'])
    purchases = Purchase.query.filter_by(store_id=store.id).all()
    return render_template('purchase_list.html', purchases=purchases)

'''@app.route('/supplier/<int:supplier_id>')
@login_required
def supplier_detail(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    return render_template('supplier_detail.html', supplier=supplier)'''







def send_whatsapp_invoice(customer_number, pdf_bytes, sale_id):
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")

    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return {"error": "WhatsApp API credentials missing"}

    # 1) Upload PDF first
    upload_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/media"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    files = {
        "file": (f"invoice_{sale_id}.pdf", pdf_bytes, "application/pdf")
    }

    data = {
        "messaging_product": "whatsapp",
        "type": "document"
    }

    upload_response = requests.post(upload_url, headers=headers, files=files, data=data)
    upload_json = upload_response.json()

    if "id" not in upload_json:
        return upload_json   # return error from API

    media_id = upload_json["id"]

    # 2) Send the PDF to customer
    msg_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": customer_number,   # 92xxxxxxxxxx
        "type": "document",
        "document": {
            "id": media_id,
            "filename": f"invoice_{sale_id}.pdf"
        }
    }

    message_response = requests.post(
        msg_url,
        headers={
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    return message_response.json()


from datetime import datetime

@app.route('/dashboard')
def dashboard1():
    return render_template("main.html", current_year=datetime.now().year)


# def format_datetime(dt):
#     if not dt:
#         return ""
#     return dt.strftime("%Y-%m-%d %I:%M %p")  # clean readable format

# now@app.template_filter('dt')
# def dt(value):
#     if not value:
#         return ""
#     return value.strftime("%Y-%m-%d %I:%M %p")
# from datetime import timezone, timedelta

# PKT = timezone(timedelta(hours=5))

# @app.template_filter('dt')
# def dt(value):
#     if not value:
#         return ""

#     # convert UTC → PKT
#     if value.tzinfo is None:
#         value = value.replace(tzinfo=timezone.utc)

#     local_time = value.astimezone(PKT)

#     return local_time.strftime("%Y-%m-%d %I:%M %p" now now also nice way down best way)
import pytz

PKT = pytz.timezone("Asia/Karachi")

@app.template_filter('dt')
def dt(value):
    if not value:
        return ""

    if value.tzinfo is None:
        value = pytz.utc.localize(value)

    return value.astimezone(PKT).strftime("%Y-%m-%d %I:%M %p")

@app.route('/device/add', methods=['GET', 'POST'])
@login_required
def add_device():

    store = Store.query.get(session['store_id'])

    products = store.products

    if request.method == 'POST':

        product_id = int(request.form['product_id'])

        storage = request.form.get('storage')

        color = request.form.get('color')

        imei = request.form['imei']

        grade_id = request.form.get('grade_id')
        grade_id = int(grade_id) if grade_id else None

        battery_health = request.form.get('battery_health')

        notes = request.form.get('notes')

        # CHECK IMEI EXISTS
        existing_device = DeviceInventory.query.filter_by(
            imei=imei
        ).first()

        if existing_device:
            flash("❌ IMEI already exists")
            return redirect(url_for('add_device'))

        # FIND PRODUCT
        product = Product.query.get_or_404(product_id)
        
       
        remaining_slots = product.calculated_stock - len([d for d in product.devices if d.status == 'in_stock'])
        # IMPORTANT:
        # CHECK AVAILABLE STOCK SLOTS
        # remaining_slots = product.calculated_stock  - len([
        #     d for d in product.devices
        
        # ])

        if remaining_slots <= 0:
            flash("❌ No remaining stock slots for this product")
            return redirect(url_for('add_device'))

        # FIND OR CREATE VARIANT
        variant = ProductVariant.query.filter_by(
            product_id=product_id,
            storage=storage,
            color=color
        ).first()

        if not variant:

            variant = ProductVariant(
                product_id=product_id,
                storage=storage,
                color=color
            )

            db.session.add(variant)
            db.session.flush()

        # CREATE DEVICE ONLY
        # DO NOT CREATE PURCHASE
        # DO NOT CHANGE PRODUCT STOCK

        device = DeviceInventory(

            variant_id=variant.id,

            imei=imei,

            grade_id=grade_id,

            supplier_id=product.supplier_id,

            store_id=store.id,

            cost_price=product.buy_price,

            sell_price=product.sell_price,

            battery_health=int(battery_health) if battery_health else None,

            notes=notes,

            status='in_stock'
        )

        db.session.add(device)

        db.session.commit()

        flash(f"✅ Device added! Remaining slots: {remaining_slots - 1}")

        return redirect(url_for('device_list'))

    return render_template(
        'device_add.html',
        products=products,
        grades=Grade.query.all(),
        store=store
    )


@app.route('/devices')
@login_required
def device_list():

    store = Store.query.get(session['store_id'])

    devices = DeviceInventory.query.filter_by(
        store_id=store.id
    ).all()

    return render_template(
        'device_list.html',
        devices=devices
    )


@app.route('/device/sell/<int:id>', methods=['GET', 'POST'])
@login_required
def sell_device(id):

    device = DeviceInventory.query.get_or_404(id)

    # PREVENT DOUBLE SELL
    if device.status == 'sold':

        flash("❌ Device already sold")

        return redirect(url_for('device_list'))

    store = Store.query.get(session['store_id'])

    if request.method == 'POST':

        customer_name = request.form['customer_name']

        customer_number = request.form['customer_number']

        discount = float(request.form.get('discount') or 0)

        # FINAL PRICE
        final_price = (device.sell_price or 0) - discount

        # PROFIT
        profit = final_price - (device.cost_price or 0)

        # FIND CUSTOMER
        customer = Customer.query.filter_by(
            customer_number=customer_number
        ).first()

        # CREATE CUSTOMER IF NOT EXISTS
        if not customer:

            customer = Customer(
                name=customer_name,
                customer_number=customer_number,
                store_id=store.id
            )

            db.session.add(customer)
            db.session.flush()

        # CREATE SALE
        sale = Sale(
            product_id=device.variant.product.id,

            customer_id=customer.id,

            customer_name=customer.name,

            customer_number=customer.customer_number,

            quantity=1,

            selling_price=final_price,

            discount=discount,

            profit=profit,

            store_id=store.id
        )

        db.session.add(sale)

        # MARK DEVICE SOLD
        device.status = 'sold'

        # SAVE CUSTOMER TO DEVICE
        device.customer_id = customer.id

        db.session.commit()

        flash("✅ Device sold successfully!")

        return redirect(url_for('receipt', sale_id=sale.id))

    return render_template(
        'sell_device.html',
        device=device
    )


from sqlalchemy import func
from datetime import datetime

# @app.route("/reports")
# def reports1():
#     from_date = request.args.get("from")
#     to_date = request.args.get("to")

#     query = Sale.query

#     # DATE FILTER
#     if from_date:
#         query = query.filter(Sale.sale_date >= datetime.strptime(from_date, "%Y-%m-%d"))
#     if to_date:
#         query = query.filter(Sale.sale_date <= datetime.strptime(to_date, "%Y-%m-%d"))

#     sales = query.all()

#     # TOTALS
#     total_sales = sum((s.selling_price * s.quantity * (1 - (s.discount or 0)/100)) for s in sales)
#     total_profit = sum((s.profit or 0) for s in sales)
#     total_discount = sum(((s.selling_price * s.quantity) * (s.discount or 0)/100) for s in sales)
#     total_orders = len(sales)

#     return render_template(
#         "reports.html",
#         sales=sales,
#         total_sales=round(total_sales, 2),
#         total_profit=round(total_profit, 2),
#         total_discount=round(total_discount, 2),
#         total_orders=total_orders
#     )

from datetime import datetime, time
from flask import request, render_template

# @app.route("/reports")
# def reports1():

#     from_date = request.args.get("from")
#     to_date = request.args.get("to")

#     query = Sale.query

#     # DATE FILTER (FIXED)
#     if from_date:
#         start = datetime.combine(
#             datetime.strptime(from_date, "%Y-%m-%d").date(),
#             time.min
#         )
#         query = query.filter(Sale.sale_date >= start)

#     if to_date:
#         end = datetime.combine(
#             datetime.strptime(to_date, "%Y-%m-%d").date(),
#             time.max
#         )
#         query = query.filter(Sale.sale_date <= end)

#     sales = query.all()


#     total_sales = 0
#     total_profit = 0
#     total_discount = 0
    
    
#     total_sales = sum((s.selling_price or 0) * (s.quantity or 0) for s in sales)

#     total_profit = sum(s.profit or 0 for s in sales)
    
#     total_discount = sum(0 for s in sales)

#     total_orders = len(sales)

#     # for s in sales:
#     #     price = float(s.selling_price or 0)
#     #     qty = float(s.quantity or 0)
#     #     discount = float(s.discount or 0)
#     #     profit = float(s.profit or 0)

#     #     line_total = price * qty

#     #     total_sales += line_total * (1 - discount / 100)
#     #     total_profit += profit
#     #     total_discount += line_total * (discount / 100)

#     # total_orders = len(sales)


#     # # TOTALS (FIXED SAFE CALCULATION)
#     # total_sales = sum(
#     #     (s.selling_price or 0) * (s.quantity or 0) * (1 - (s.discount or 0) / 100)
#     #     for s in sales
#     # )

#     # total_profit = sum(s.profit or 0 for s in sales)

#     # total_discount = sum(
#     #     ((s.selling_price or 0) * (s.quantity or 0)) * ((s.discount or 0) / 100)
#     #     for s in sales
#     # )

#     # total_orders = len(sales)

#     return render_template(
#         "reports.html",
#         sales=sales,
#         total_sales=round(total_sales, 2),
#         total_profit=round(total_profit, 2),
#         total_discount=round(total_discount, 2),
#         total_orders=total_orders,
#         request=request   # IMPORTANT FIX
#     now)
@app.route("/reports")
def reports1():

    from_date = request.args.get("from")
    to_date = request.args.get("to")

    query = Sale.query

    # DATE FILTER
    if from_date:
        start = datetime.combine(
            datetime.strptime(from_date, "%Y-%m-%d").date(),
            time.min
        )
        query = query.filter(Sale.sale_date >= start)

    if to_date:
        end = datetime.combine(
            datetime.strptime(to_date, "%Y-%m-%d").date(),
            time.max
        )
        query = query.filter(Sale.sale_date <= end)

    sales = query.all()

    # 🟢 SAFE CALCULATIONS (FINAL FIX)
    total_sales = sum(
        (s.selling_price or 0) * (s.quantity or 0)
        for s in sales
    )

    total_profit = sum(
        (s.profit or 0)
        for s in sales
    )

    total_discount = sum(
        ((s.selling_price or 0) * (s.quantity or 0)) * ((s.discount or 0) / 100)
        for s in sales
    )

    total_orders = len(sales)

    return render_template(
        "reports.html",
        sales=sales,
        total_sales=round(total_sales, 2),
        total_profit=round(total_profit, 2),
        total_discount=round(total_discount, 2),
        total_orders=total_orders,
        request=request
    )
import csv
from flask import Response

@app.route("/export-reports")
def export_reports():
    sales = Sale.query.all()

    def generate():
        yield "ID,Date,Customer,Product,Qty,Price,Discount,Profit\n"
        for s in sales:
            yield f"{s.id},{s.sale_date},{s.customer_name},{s.product.name},{s.quantity},{s.selling_price},{s.discount},{s.profit}\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=reports.csv"})

@app.route("/store-settings", methods=["GET", "POST"])
def store_settings():
    store = Store.query.first()  # single store system

    if request.method == "POST":
        store.name = request.form.get("name")
        store.phone = request.form.get("phone")
        store.address = request.form.get("address")
        store.currency = request.form.get("currency")
        store.tax_percent = float(request.form.get("tax_percent") or 0)
        store.invoice_footer = request.form.get("invoice_footer")

        db.session.commit()
        flash("Store settings updated successfully!", "success")

    return render_template("store_settings.html", store=store)


from flask import Flask, request, redirect, flash
from apscheduler.schedulers.background import BackgroundScheduler

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import smtplib
import os
import shutil
from datetime import datetime

# app = Flask(__name__)

# app.secret_key = "secret-key"


# =========================
# EMAIL SETTINGS
# =========================

EMAIL_ADDRESS = "mobilezonepeshawar@gmail.com"
APP_PASSWORD = "eidfmbwfidagzqsw"

# default owner email
OWNER_EMAIL = "attagive@gmail.com"


# =========================
# SEND DATABASE BACKUP
# =========================

def send_database_backup(custom_email=None):

    try:

        receiver_email = custom_email or OWNER_EMAIL

        original_db = "instance/database.db"
        # create backup copy
        backup_folder = "backups"

        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        backup_db = os.path.join(
            backup_folder,
            f"backup_{timestamp}.db"
        )

        shutil.copy(original_db, backup_db)

        # create email
        msg = MIMEMultipart()

        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = "Weekly Database Backup"
        # body = render_template("backup_email.html",date=datetime.now().strftime("%Y-%m-%d %H:%M"))

        # msg.attach(MIMEText(body, "html"))

        body = """
Hello,

Attached is the automatic database backup.

Regards,
Store Management System
"""

        msg.attach(MIMEText(body, "plain"))

        # attach database
        with open(backup_db, "rb") as attachment:

            part = MIMEBase("application", "octet-stream")

            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(backup_db)}"
        )

        msg.attach(part)

        # send mail
        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(EMAIL_ADDRESS, APP_PASSWORD)

        server.send_message(msg)

        server.quit()

        print("Backup email sent successfully")

    except Exception as e:

        print("Backup email failed:", e)


# =========================
# MANUAL BACKUP ROUTE
# =========================

@app.route("/send-backup", methods=["POST"])
def send_backup():

    email = request.form.get("email")

    send_database_backup(custom_email=email)

    flash("Backup email sent successfully")

    return redirect("/")


# =========================
# SCHEDULER
# =========================

scheduler = BackgroundScheduler()
scheduler.add_job(
    send_database_backup,
    'interval',
    minutes=60
    
    )

# scheduler.add_job(
#     send_database_backup,
#     'cron',
#     day_of_week='mon',
#     hour=1,
#     minute=15,

#     # if app opens within 7 days after missed time,
#     # send missed backup automatically
#     misfire_grace_time=604800)

#     scheduler.start()
@app.route("/test-backup")
def test_backup():

    send_database_backup()

    return "Backup email sent"


# =========================
# RUN APP
# =========================

# if __name__ == "__main__":

#     app.run(
#         debug=False,
#         use_reloader=False
#     )
# ---------------------- RUN ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)