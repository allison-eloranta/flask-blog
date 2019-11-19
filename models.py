from flask import Flask
from flask_login import UserMixin, LoginManager, logout_user, login_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from config import *
from main import app

db = SQLAlchemy(app)

db.init_app(app)
# LOGIN MANAGER
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(32))
    def check_password(self, password):
        return check_password_hash(self.password, password)
    def logout(self, user):
        logout_user()


class blogPost(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(128))
    post_content = db.Column(db.String(2048))
    post_author = db.Column(db.String(32))
    post_image = db.Column(db.String(256))

