from enum import unique

from sqlalchemy.orm import backref
from forms import LoginForm, RegisterForm, TipForm, SearchForm, CommentForm

from operator import eq, pos
from os import name

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor

from wtforms import StringField, PasswordField, BooleanField, IntegerField, ValidationError
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, InputRequired, Email, Length, EqualTo
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime

# Initializing the flask app
app = Flask(__name__)
ckeditor = CKEditor(app)
# Things for database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'thisisasecretpassword'

Bootstrap(app)


db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Login manager init
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

# Class for USER for database
class Users(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True)
    chapter_letters = db.Column(db.String(120))
    class_year = db.Column(db.Integer())
    date_added = db.Column(db.DateTime, default=datetime.now)
    password_hash = db.Column(db.String(128))

    tips = db.relationship('TipPost', backref="poster")
    comments = db.relationship('Comment', backref='poster', passive_deletes=True)
    likes = db.relationship('Like', backref='poster', passive_deletes=True)


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name


class TipPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    body = db.Column(db.Text(500))
    date_posted = db.Column(db.Date, default=datetime.utcnow)
    topic = db.Column(db.String(255))

    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='tip_post', passive_deletes=True)
    likes = db.relationship('Like', backref='tip_post', passive_deletes=True)



class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.Date, default=datetime.utcnow)

    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tip_id = db.Column(db.Integer, db.ForeignKey('tip_post.id'))

class Like(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tip_id = db.Column(db.Integer, db.ForeignKey('tip_post.id'))


# Landing Page for Website
# Website pages that are public

@app.route('/landing')
def landing():

    return render_template('landing.html')

@app.route('/about')

def about():

    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(username=form.username.data).first()
		if user:
			# Check the hash
			if check_password_hash(user.password_hash, form.password.data):
				login_user(user)
				flash("Login Succesfull!!")
				return redirect(url_for('dashboard'))
			else:
				flash("Wrong Password - Try Again!")
		else:
			flash("That User Doesn't Exist! Try Again...")

	return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():

    name = None
    form = RegisterForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
			# Hash the password!!!
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(username=form.username.data, 
                        name=form.name.data, 
                        email=form.email.data, 
                        chapter_letters=form.chapter_letters.data, 
                        password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()

        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.chapter_letters.data = ''
        form.class_year.data = ''
        form.password_hash.data = ''

        flash("User Added Successfully!")

    our_users = Users.query.order_by(Users.date_added)
    return render_template("register.html", form=form, name=name, our_users=our_users)

# Website Pages that require login
@app.route('/')
@app.route('/home')
def home():

    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():

    tips = TipPost.query.order_by(TipPost.poster_id)
    return render_template('dashboard.html', tips=tips)



@app.context_processor
def base():
    form=SearchForm()
    return dict(form=form)


@app.route('/search', methods=['POST'])
@login_required
def search():

    form = SearchForm()
    tips = TipPost.query
    if form.validate_on_submit():
        tip.searched = form.searched.data

        tips = tips.filter(TipPost.topic.like('%' + tip.searched + '%'))
        tips = tips.order_by(TipPost.title).all()


        return render_template('search.html', form=form, searched=tip.searched, tips=tips)


@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = RegisterForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.username = request.form['username']
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.chapter_letters= request.form['chapter_letters']
        name_to_update.class_year = request.form['class_year']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("edit_profile.html", 
                form=form,
                name_to_update = name_to_update, id=id)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("edit_profile.html", 
                form=form,
                name_to_update = name_to_update,
                id=id)
    else:
        return render_template("edit_profile.html", 
                form=form,
                name_to_update = name_to_update,
                id = id)


@app.route('/tips')
@login_required
def tip_page():

    tips = TipPost.query.order_by(TipPost.date_posted)
    return render_template('tips.html', tips=tips)

@app.route('/add-tip', methods=['GET', 'POST'])
@login_required
def add_tip():
	form = TipForm()

	if form.validate_on_submit():
		poster = current_user.id
		tip_post = TipPost(title=form.title.data, poster_id=poster, body=form.body.data, topic=form.topic.data)
		# Clear The Form
		form.title.data = ''
		form.body.data = ''
		form.topic.data = ''

		# Add post data to database
		db.session.add(tip_post)
		db.session.commit()

		# Return a Message
		flash("Blog Post Submitted Successfully!")

	# Redirect to the webpage
	return render_template("add_tip.html", form=form)

@app.route('/tips/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tip(id):

    tip = TipPost.query.get_or_404(id)
    form = TipForm()

    if form.validate_on_submit():
        tip.title = form.title.data

        tip.topic = form.topic.data
        tip.body = form.body.data

        db.session.add(tip)
        db.session.commit()

        flash("Tip Has Been Updated!")
        return redirect(url_for('tip', id=tip.id))

    form.title.data = tip.title
    form.topic.data = tip.topic
    form.body.data = tip.body

    return render_template('edit_tip.html', form=form)


@app.route('/like/<tip_id>')
@login_required
def like(tip_id):

    tip = TipPost.query.filter_by(id=tip_id)
    like = Like.query.filter_by(poster_id=current_user.id, tip_id=tip_id).first()

    if not tip:
        flash('That tip cannot be liked')
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(poster_id=current_user.id, tip_id=tip_id)
        db.session.add(like)
        db.session.commit()

    return redirect(url_for('tip', id=tip_id))

@app.route('/tips/delete/<int:id>')
@login_required
def delete_tip(id):

	tip_to_delete = TipPost.query.get_or_404(id)
	id = current_user.id
	if id == tip_to_delete.poster.id:
		try:
			db.session.delete(tip_to_delete)
			db.session.commit()

			# Return a message
			flash("Tip Removed!")

			# Grab all the posts from the database
			tips = TipPost.query.order_by(TipPost.date_posted)
			return render_template("tips.html", tips=tips)

		except:
			# Return an error message
			flash("Error, try again")

			# Grab all the posts from the database
			tips = TipPost.query.order_by(TipPost.date_posted)
			return render_template("tips.html", tips=tips)
	else:
		# Return a message
		flash("You Aren't Authorized To Delete That Post!")

		# Grab all the posts from the database
		tips = TipPost.query.order_by(TipPost.date_posted)
		return render_template("tips.html", tips=tips)


@app.route('/profile/<int:id>')
@login_required
def profile(id):

    user = Users.query.get_or_404(id)

    return render_template('profile.html', user=user)


@app.route('/tips/<int:id>')
@login_required
def tip(id): 
    tip = TipPost.query.get_or_404(id)
    return render_template('tip.html', tip=tip)

@app.route('/comment/<tip_id>', methods=['GET','POST'])
def comment(tip_id):

    body = request.form.get('body')

    if not body:
        flash('Comment cannot be empty.', category='error')
    else:
        tip = TipPost.query.filter_by(id=tip_id)
        if tip:
            comment = Comment(
                body=body, poster_id=current_user.id, tip_id=tip_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Tip does not exist.', category='error')

    return redirect(url_for('tip', id=tip_id))


@app.route('/tip/<tip_id>/comment/delete/<int:id>')
@login_required
def delete_comment(tip_id, id):

    comment_to_delete = Comment.query.get_or_404(id)

    db.session.delete(comment_to_delete)
    db.session.commit()

    return redirect(url_for('tip', id=tip_id))    


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("You Have Been Logged Out! ITB")
	return redirect(url_for('login'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
	user_to_delete = Users.query.get_or_404(id)
	name = None
	form = LoginForm()

	try:
		db.session.delete(user_to_delete)
		db.session.commit()
		flash("User Deleted Successfully!!")

		our_users = Users.query.order_by(Users.date_added)
		return render_template("admin.html", 
		form=form,
		name=name,
		our_users=our_users)

	except:
		flash("Whoops! There was a problem deleting user, try again...")
		return render_template("admin.html", 
		form=form, name=name,our_users=our_users)

if __name__ == '__main__':
    app.run(debug=True)
