from flask import Flask, render_template, redirect, request
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user, login_manager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DB_STRING
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
now = datetime.now()

# DATABASE CONNECTION
db = create_engine(DB_STRING)
conn = db.connect()

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user):
    return User.query.get(user)

# MODELS 
db = SQLAlchemy(app)
db.init_app(app)

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
    post_time = db.Column(db.DateTime, default=now)
    post_date = db.Column(db.DateTime, default=now)

class newComment(db.Model):
    comment_content = db.Column(db.String(512))
    comment_author= db.Column(db.String(32))
    comment_id = db.Column(db.Integer, primary_key=True)
    time_posted = db.Column(db.DateTime, default=now)
    date_posted = db.Column(db.DateTime, default=now)

# PAGES
@app.route('/')
def index():
    posts = conn.execute('SELECT * from blog_post')
    return render_template('index.html', posts=posts)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if current_user.is_authenticated:
        if request.method == 'POST':
            # Get values of the form
            title=request.form['post-title']
            desc=request.form['post-desc']
            author=current_user.name
            global now
            # Add post to the db
            new_post = blogPost(post_title=title, post_content=desc, post_author=author, post_image="null")
            db.session.add(new_post)
            db.session.commit()
            print('New post added successfully.')
            return redirect('/post')
        return render_template('post.html')
    else:
        return redirect('/')

# Needs to be cleaned up and redone. #

@app.route('/posts/<id>', methods=['GET', 'POST'])
def posts(id):
    # Check if post exists, if not, return a error message.
    post = blogPost.query.filter_by(post_id=id).first()
    if post:
        if request.method == 'POST' and current_user.is_authenticated:
            # Add new comment to db
            content = request.form['comment-content']
            author=current_user.name
            new_comment = newComment(comment_content=content, comment_author=author)
            db.session.add(new_comment)
            db.session.commit()
            # Add the id to the post's db
            conn.execute('UPDATE blog_post SET post_comments = array_append(post_comments, %s) WHERE post_id = %s', new_comment.comment_id, id)
            print('Added new comment successfully.')
            return redirect(f'/posts/{id}')
        post = conn.execute('SELECT * FROM blog_post WHERE post_id = %s', id)
        # Get comments.
        comm = conn.execute('SELECT * FROM blog_post WHERE post_id = %s', id)
        comments = []
        pcomment = []
        for p in comm:
            if p['post_comments']:
                pcomment += p['post_comments']
        if pcomment:
            for comment in pcomment:
                comments += conn.execute('SELECT * FROM new_comment WHERE comment_id = %s', comment)
        return render_template('info.html', posts=post, comments=comments)
    return_message = 'Post does not exist.'
    return render_template('info.html', return_message=return_message)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        # To check if either the username or email exists in the database, if so, dont let them register with it.
        email_check = User.query.filter_by(email=email).first()
        username_check = User.query.filter_by(name=name).first()
        if email_check or username_check:
            return_message = 'Email address or username already exists. Try logging in.'
            return render_template('register.html', return_message=return_message)
        # Create new user
        new_user = User(email=email, name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        # Login the new user
        login_user(new_user)
        print("Added user successfully!")
        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check whether or not the user is already logged in:
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        #Login with email
        find_user = User.query.filter_by(email=email).first()
        if find_user:
            if find_user.check_password(password=password):
                login_user(find_user)
                return redirect('/')
            else:
                return_message = 'Invalid credentials, try again.'
                return render_template('login.html', return_message=return_message)
        else:
            return_message = 'Invalid credentials, try again.'
            return render_template('login.html', return_message=return_message)
    return render_template('login.html')

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        user = current_user
        user.logout(user)
    return redirect('/')
app.run()