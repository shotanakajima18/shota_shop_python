from pyshop.database import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    screen_name = db.Column(db.String(21), unique=True)
    email = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean, default=False)
    address = db.Column(db.Text(240))
    bio = db.Column(db.Text(240))
    is_active = db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", order_by = "desc(Order.updated_at)", back_populates = 'users')

    def __init__(self, screen_name, email, password, address):
        self.screen_name = screen_name
        self.email = email
        self.password = password
        self.address = address

    def __repr__(self):
        return '<User %r>' % (self.screen_name)

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.Text(21), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text(240), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(5), nullable=False)


    orders = db.relationship("Order", order_by = "desc(Order.updated_at)", back_populates = 'items')

    @staticmethod
    def search_item(keyword):
        searchresult = db.session.query(Item).filter(Item.name.like('%\\' + keyword + '%', escape='\\')).all()
        return searchresult


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    users = db.relationship("User", back_populates = 'orders')
    items = db.relationship("Item", back_populates = 'orders')

