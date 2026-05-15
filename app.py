from flask import Flask, render_template, request, redirect
from config import Config
from flask import flash
from datetime import datetime
import uuid
from flask_migrate import Migrate
from flask import jsonify
from sqlalchemy import extract, func
from flask import send_file
from weasyprint import HTML
import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from flask import send_from_directory
import warnings
warnings.filterwarnings("ignore")

INVOICE_FOLDER = "invoices"
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from models import (
    db,
    User,
    Customer,
    Invoice,
    InvoiceItem
)
if not os.path.exists(INVOICE_FOLDER):
    os.makedirs(INVOICE_FOLDER)

app = Flask(__name__)
login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db.init_app(app)

migrate = Migrate(app, db)
@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register",
           methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        existing_user = User.query.filter_by(
            email=email
        ).first()
        if existing_user:
            flash("Email already exists", "error")
            return redirect("/register")
        hashed_password = generate_password_hash(
            password
        )
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")
@app.route("/login",
           methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(
            email=email
        ).first()
        if not user:
            flash("Invalid email", "error")
            return redirect("/login")
        if not check_password_hash(
            user.password,
            password
        ):
            flash("Wrong password", "error")
            return redirect("/login")
        login_user(user)
        return redirect("/dashboard")
    return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")

@app.route("/download/<invoice_id>")
@login_required
def download_invoice(invoice_id):
    invoice = Invoice.query.filter_by(

        invoice_id=invoice_id,

        user_id=current_user.id

    ).first()

    items_db = InvoiceItem.query.filter_by(
        invoice_id=invoice.id
    ).all()

    items = []

    for item in items_db:
        items.append({
            "name": item.item_name,
            "qty": item.quantity,
            "price": item.price,
            "total": item.total
        })

    rendered_html = render_template(
        "invoice.html",
        customer_name=invoice.customer_name,
        customer_email=invoice.customer_email,
        items=items,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        grand_total=invoice.total,
        invoice_id=invoice.invoice_id,
        payment_method=invoice.payment_method,
        date=invoice.created_at.strftime("%d-%m-%Y"),
        show_download = False
    )

    pdf_path = f"invoices/invoice_{invoice_id}.pdf"

    HTML(
        string=rendered_html,
        base_url=request.host_url
    ).write_pdf(pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True
    )


@app.route("/generate", methods=["POST"])
@login_required
def generate_invoice():
    status = request.form.get("status")
    customer_name = request.form.get("customer_name")
    payment_method = request.form.get("payment_method")
    customer_email = request.form.get("customer_email")

    item_names = request.form.getlist("item_name")
    quantities = request.form.getlist("quantity")
    prices = request.form.getlist("price")

    items = []

    subtotal = 0

    for i in range(len(item_names)):

        qty = int(quantities[i])

        price = float(prices[i])

        total = qty * price

        subtotal += total

        items.append({
            "name": item_names[i],
            "qty": qty,
            "price": price,
            "total": total
        })

    tax = subtotal * 0.18

    grand_total = subtotal + tax

    invoice_unique_id = str(uuid.uuid4())[:8].upper()
    
    existing_customer = Customer.query.filter_by(
    email=customer_email,
    user_id=current_user.id
).first()

if existing_customer:

    customer = existing_customer

else:

    customer = Customer(
        name=customer_name,
        email=customer_email,
        user_id=current_user.id
    )

    db.session.add(customer)

    db.session.commit()
    
    invoice = Invoice(
        invoice_id=invoice_unique_id,
        customer_name=customer_name,
        customer_email=customer_email,
        subtotal=subtotal,
        tax=tax,
        total=grand_total,
        status=status,
        payment_method=payment_method,
        user_id=current_user.id
    )

    db.session.add(invoice)

    db.session.commit()

    for item in items:

        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            item_name=item["name"],
            quantity=item["qty"],
            price=item["price"],
            total=item["total"]
        )

        db.session.add(invoice_item)

    db.session.commit()
    return render_template(
        "invoice.html",
        customer_name=customer_name,
        customer_email=customer_email,
        items=items,
        subtotal=subtotal,
        tax=tax,
        grand_total=grand_total,
        invoice_id=invoice_unique_id,
        payment_method=request.form.get("payment_method"),
        date=datetime.now().strftime("%d-%m-%Y"),
        show_download = True
    )

@app.route("/dashboard")
@login_required
def dashboard():
    invoices = Invoice.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Invoice.created_at.desc()
    ).all()

    paid_revenue = sum(

        invoice.total

        for invoice in invoices

        if invoice.status == "Paid"

    )

    outstanding_amount = sum(

        invoice.total

        for invoice in invoices

        if invoice.status in ["Pending", "Overdue"]

    )

    total_invoiced = sum(

        invoice.total

        for invoice in invoices

    )

    return render_template(

        "dashboard.html",

        invoices=invoices,

        paid_revenue=paid_revenue,

        outstanding_amount=outstanding_amount,

        total_invoiced=total_invoiced

    )

@app.route("/update-status/<int:invoice_id>",
           methods=["POST"])
@login_required
def update_status(invoice_id):

    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user.id
    ).first_or_404()

    new_status = request.form.get("status")

    invoice.status = new_status

    db.session.commit()

    return redirect("/dashboard")
@app.route("/revenue-data")
@login_required
def revenue_data():
    invoices = Invoice.query.filter_by(
        user_id=current_user.id
    ).all()

    revenue_by_month = {}

    for invoice in invoices:

        if invoice.status != "Paid":
            continue

        month = invoice.created_at.strftime("%b")

        revenue_by_month[month] = (

            revenue_by_month.get(month, 0)

            + invoice.total

        )

    return jsonify({

        "labels": list(revenue_by_month.keys()),

        "revenue": list(revenue_by_month.values())

    })
if __name__ == "__main__":
    app.run(debug=True)
