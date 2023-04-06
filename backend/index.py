import functools
import json
import os
import re

from flask import Flask, request, redirect, abort, render_template, url_for, flash
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.security import generate_password_hash, check_password_hash

from backend.member import member
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

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Member.query.filter_by(id=user_id).first()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('classification.html', user=current_user)
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


def add_user(username, password):
    with app.app_context():
        user = Member.query.filter_by(username=username).first() # if this returns a user, then the email already exists in database

        if user:
            return

        new_user = Member(username=username, password=generate_password_hash(password, method='sha256'))

        db.session.add(new_user)
        db.session.commit()

add_user('jameshball', 'n6Fj82vEtkC7i$LF4h')


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
