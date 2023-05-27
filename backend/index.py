import os
import random

from flask import Flask, request, redirect, abort, render_template, url_for, flash
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash

from backend.member import member
from backend.classification import classification, get_classification
from backend.model import db

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = '401dd05815924be5a9bc159e6198a4c9'
app.register_blueprint(member)
app.register_blueprint(classification)

from backend.model import *

login_manager = LoginManager()
login_manager.login_view = 'index'
login_manager.init_app(app)
login_manager.session_protection = None

@login_manager.user_loader
def load_user(user_id):
    return Member.query.get(int(user_id))

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['MAX_CONTENT_LENGTH'] = 21 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, os.pardir, 'instance', 'db.sqlite')

db.app = app
db.init_app(app)


@app.context_processor
def inject_user():
    return dict(user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return Member.query.filter_by(id=user_id).first()


@app.route('/')
def index():
    if current_user.is_authenticated:
        real_patch, fake_patch, num_classifications = get_classification()
        patch1_id = real_patch.id
        patch2_id = fake_patch.id

        if random.random() > 0.5:
            patch1_id, patch2_id = patch2_id, patch1_id

        return render_template(
            'classification.html',
            user=current_user,
            patch1_id=patch1_id,
            patch2_id=patch2_id,
            real_patch_id=real_patch.id,
            fake_patch_id=fake_patch.id,
            num_classifications=num_classifications,
        )
    else:
        return render_template('login.html')


@app.route("/login", methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user = Member.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('index'))

    login_user(user, remember=True)
    return redirect(url_for('index'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/auth-test")
def auth_test():
    if current_user.is_authenticated:
        return 'Authenticated!'
    else:
        return 'Not authenticated!'


if __name__ == '__main__':
    app.run()
