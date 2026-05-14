from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
db = SQLAlchemy()

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

class Invoice(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_id = db.Column(
        db.String(20),
        unique=True
    )

    customer_name = db.Column(
        db.String(100)
    )

    customer_email = db.Column(
        db.String(120)
    )

    subtotal = db.Column(
        db.Float
    )

    tax = db.Column(
        db.Float
    )

    total = db.Column(
        db.Float
    )

    status = db.Column(
        db.String(20),
        default="Paid"
    )

    payment_method = db.Column(
    db.String(100)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoice.id'),
        nullable=False
    )

    item_name = db.Column(db.String(100), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    price = db.Column(db.Float, nullable=False)

    total = db.Column(db.Float, nullable=False)
