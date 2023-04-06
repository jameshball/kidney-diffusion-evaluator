from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy(engine_options={"max_overflow": -1})

# ANY UPDATES TO MODEL NEED TO BE APPLIED TO TEST/PROD DATABASES USING FLASK-MIGRATE/ALEMBIC
# https://flask-migrate.readthedocs.io/en/latest/


class Patch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    real = db.Column(db.Boolean) # True if real, False if fake


class Classification(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    real_patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    real_patch = db.relationship('Patch', foreign_keys=[real_patch_id], backref=db.backref('real_classifications', lazy=True))
    fake_patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    fake_patch = db.relationship('Patch', foreign_keys=[fake_patch_id], backref=db.backref('fake_classifications', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    user = db.relationship('Member', backref=db.backref('classifications', lazy=True))
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    classification = db.Column(db.Boolean) # True if real, False if fake


class Member(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
