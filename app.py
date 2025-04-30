from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from extensions import db, login_manager
from models import User, Product
from forms import RegisterForm, LoginForm, ProductForm
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
# from flask_sqlalchemy import SQLAlchemy  # Remove this import since db is already initialized

# Create the Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)  # This initializes the db with the Flask app
migrate = Migrate(app, db)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data,
                        password=hashed_pw, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Failed. Please check email and password', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()
    return render_template('dashboard.html', products=products)

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash('You do not have permission to add products.', 'danger')
        return redirect(url_for('home'))
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(name=form.name.data, description=form.description.data,
                              price=form.price.data, stock=form.stock.data)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('product/add.html', form=form)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit products.', 'danger')
        return redirect(url_for('home'))
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('product/edit.html', form=form, product=product)

@app.route('/product/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete products.', 'danger')
        return redirect(url_for('home'))
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product/detail.html', product=product)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
