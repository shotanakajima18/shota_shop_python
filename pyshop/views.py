from flask import request, redirect, url_for, render_template, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, TextAreaField, FloatField, FileField, RadioField
from wtforms.validators import InputRequired, Email, Length
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from pyshop import app, db
from pyshop.models import User, Item, Order
from urllib.request import Request, urlopen
import json
import base64
import os

app.config["IMAGE_UPLOADS"] = 'pyshop/static/images'

bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class LoginForm(FlaskForm):
    screen_name = StringField('Username', validators=[InputRequired(), Length(min=1, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=1, max=80)])

    remember = BooleanField('Remember me')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    screen_name = StringField('Username', validators=[InputRequired(), Length(min=1, max=15)])
    address = StringField('Address',validators=[Length(min=1,max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=1, max=80)])

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=50)])
    price = FloatField('Price', validators=[InputRequired()])
    quantity = IntegerField('Quantity',validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    size = RadioField('Size', choices=[('S','S'),('M','M'),('L','L')])
    image = FileField('Image', validators=[InputRequired()])

class Item2Form(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=50)])
    price = FloatField('Price', validators=[InputRequired()])
    quantity = IntegerField('Quantity',validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])

class OrderForm(FlaskForm):
    quantity = IntegerField('Quantity',validators=[InputRequired()])


class SearchForm(FlaskForm):
    keyword = StringField('keyword', validators=[InputRequired(), Length(min=1, max=100)])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def first():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(screen_name=form.screen_name.data).first()
            if user:
                if user.is_active == False:
                    flash('Invalid user')
                    return redirect('/login')
                elif check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    if user.is_admin:
                        flash('Welcome admin!')
                        return redirect('/admin_add')
                    else:
                        flash('Welcome user!')
                        return redirect('/home')
                    
                flash('Invalid Password')
                return redirect('/login')
            flash('Invalid screen_name or password')
            return redirect('/login')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(screen_name=form.screen_name.data,
                        email=form.email.data,
                        password=hashed_password,
                        address=form.address.data)
        db.session.add(new_user)
        db.session.commit()
        
        flash('New User was successfully created')
        return redirect('/login')
    
    return render_template('register.html', form=form)

@app.route('/admin_add', methods=['GET', 'POST'])
@login_required
def add():

    form = ItemForm()
    if form.validate_on_submit():
        images = request.files['image']
        pic_name = images.filename
        images.save(os.path.join(app.config["IMAGE_UPLOADS"], images.filename))
        # images.save(os.path.join(app.config["IMAGE_UPLOADS"], pic_name))

        new_item = Item(name=form.name.data,
                        price=form.price.data,
                        quantity=form.quantity.data,
                        description=form.description.data,
                        size=form.size.data,
                        image=pic_name)
        try:
            db.session.add(new_item)
            db.session.commit()
            flash('New Item was successfully added')
            return redirect('admin_add')
        except:
            return 'Error'
    return render_template('admin/add.html',form=form)

@app.route('/admin/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        item.name=request.form['name']
        item.price=request.form['price']
        item.quantity=request.form['quantity']
        item.description=request.form['description']
        
        try:
            db.session.commit()
            flash('Item was successfully updated')
            return redirect('/home')
        except:
            return 'Error'
    return render_template('admin/edit.html',item=item)

@app.route('/admin/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = Item.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('The item was successfully deleted')
    return redirect('/home')


@app.route('/item/show/<int:item_id>', methods=['GET', 'POST'])
@login_required
def show_item(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        if quantity > item.quantity:
            flash('Sorry! No stock.')
            return redirect('/item/show/{}'.format(item_id))
        else:
            return redirect('/item/receipt/{}/{}'.format(item_id,quantity))
        
    return render_template('item/show.html', item=item)

@app.route('/item/receipt/<int:item_id>/<int:quantity>', methods=['GET', 'POST'])
@login_required
def receipt(item_id,quantity):
    item = Item.query.get(item_id)
    if request.method == 'POST':

        new_order = Order(users=current_user, items=item, quantity=quantity,price=item.price)
        item.quantity -= quantity
        db.session.add(new_order)
        db.session.commit()
        flash('New Order was successfully created')
        return redirect('/home')
    return render_template('item/receipt.html',item=item,quantity=quantity)

@app.route('/item/search', methods=['GET','POST'])
@login_required
def search_item():
    form = SearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            keyword = form.keyword.data
            results = Item.search_item(keyword)
            if results:
                return render_template('item/search.html', form = form, results = results)
    return render_template('item/search.html', form = form)


@app.route('/users/me')
@login_required
def show_me():
    return render_template('user/show.html', user=current_user)

@app.route('/user/history/<int:user_id>')
@login_required
def history(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.updated_at.desc()).all()
    user = User.query.get(user_id)

    return render_template('user/history.html',orders=orders,user=user)

@app.route('/user/index/')
@login_required
def user_index():
    users = User.query.all()

    return render_template('user/index.html',users=users)


@app.route('/users/me/edit', methods=['GET', 'POST'])
@login_required
def edit_me():
    if request.method == 'POST':
        current_user.screen_name = request.form['screen_name']
        current_user.email = request.form['email']
        current_user.address = request.form['address']
        current_user.bio = request.form['bio']
        db.session.commit()
        return redirect(url_for('show_me'))
    return render_template('user/edit.html', user=current_user)


@app.route('/user/me/delete', methods=['POST'])
@login_required
def delete_me():
    current_user.is_active = False
    db.session.commit()
    flash('Your data was successfully deleted')
    return redirect('login')

@app.route('/admin/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_user(user_id):
    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    flash('The user was successfully deactivated')
    return redirect('user/index')

@app.route('/admin/<int:user_id>/activate', methods=['POST'])
@login_required
def activate_user(user_id):
    user = User.query.get(user_id)
    user.is_active = True
    db.session.commit()
    flash('The user was successfully activated')
    return redirect('user/index')

@app.route('/user/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    return render_template('user/profile.html', user=user)

@app.route('/home')
@login_required
def home():
    items = Item.query.all()
    return render_template('home.html',user=current_user,items=items)

@app.route('/item/show/<int:item_id>', methods =['GET','POST'])
@login_required
def show(item_id):
    item = Item.query.filter_by(id=item_id)
    return render_template('/item/show.html',item=item)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logout')

    return redirect('/')



@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')
