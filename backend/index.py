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

class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.register_blueprint(member)
app.register_blueprint(classification)

from backend.model import *

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.session_protection = None

@login_manager.user_loader
def load_user(user_id):
    return Member.query.get(int(user_id))

app.config['MAX_CONTENT_LENGTH'] = 21 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

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
        return redirect(url_for('index', _scheme='https', _external=True))

    login_user(user, remember=True)
    return redirect(url_for('index', _scheme='https', _external=True))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index', _scheme='https', _external=True))


@app.route("/auth-test")
def auth_test():
    if current_user.is_authenticated:
        return 'Authenticated!'
    else:
        return 'Not authenticated!'


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
