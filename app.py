######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

from collections import Counter

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'jarki'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


# User activity
@app.route('/user_hot', methods=['GET'])
@flask_login.login_required
def user_hot():
	cursor = conn.cursor()
	cursor.execute("SELECT users.email FROM `pictures` "
				   "LEFT JOIN users ON users.user_id = pictures.user_id "
				   "LEFT JOIN comments ON users.user_id = comments.user_id "
				   "GROUP BY users.user_id ORDER BY COUNT(users.user_id) DESC LIMIT 10")
	emails = [x[0] for x in cursor.fetchall()]
	return render_template("hot.html", emails=emails)



"""Friends start"""
# Friend home page, including my friends, friend recommendation, user search
@app.route('/friend', methods=['GET'])
@flask_login.login_required
def friend_index():
	cursor = conn.cursor()
	# my friends
	cursor.execute(f"SELECT t2.email AS friend_eamil FROM users "
				   f"INNER JOIN friends_with AS t1 ON users.user_id = t1.user_id "
				   f"INNER JOIN users AS t2 ON t1.friend_uid = t2.user_id "
				   f"WHERE users.email='{flask_login.current_user.id}'")

	friend_emails = [x[0] for x in cursor.fetchall()]

	# you like
	recommend = []
	for email in friend_emails:
		cursor.execute(f"SELECT t2.email AS friend_eamil FROM users "
					   f"INNER JOIN friends_with AS t1 ON users.user_id = t1.user_id "
					   f"INNER JOIN users AS t2 ON t1.friend_uid = t2.user_id "
					   f"WHERE users.email='{email}'")
		recommend.extend([x[0] for x in cursor.fetchall()])

	if recommend:
		recommend_emails = [x[0] for x in sorted(dict(Counter(recommend)).items(), key=lambda x: x[1], reverse=True)[:15]]
	else:
		recommend_emails = None

	return render_template("friend.html", name=flask_login.current_user.id, friend_emails=friend_emails, recommend_emails=recommend_emails)


@app.route('/find_friend', methods=['GET'])
@flask_login.login_required
def find_friend():
	email = flask.request.args.get('email')
	cursor = conn.cursor()
	cursor.execute(f"select email from users where email like '%{email}%'")

	search_emails = [x[0] for x in cursor.fetchall() if x[0] != flask_login.current_user.id]
	message = f"A total of {len(search_emails)} other users were found"
	return render_template("find_friend.html", search_emails=search_emails, message=message)


@app.route('/add_friend_api', methods=['GET'])
@flask_login.login_required
def add_friend_api():
	email = flask.request.args.get('email')
	cursor = conn.cursor()
	cursor.execute(f"select user_id from users where email = '{flask_login.current_user.id}'")
	user_id = cursor.fetchone()[0]

	cursor.execute(f"select user_id from users where email = '{email}'")
	friend_uid = cursor.fetchone()[0]

	cursor.execute(f"INSERT INTO friends_with VALUES({user_id}, {friend_uid})")
	cursor.close()
	return "Successfully add a friend<br><a href='/'>Home</a>"


"""Friends end"""


"""Albums start"""
def getAlbums():
    user = User()
    user.id = flask_login.current_user.id
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()


@app.route("/albums/", methods=['POST'])
@flask_login.login_required
def create_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    a_name = request.form.get('a_name')
    if a_name in str(users):
        return render_template('albums.html', name=flask_login.current_user.id, message='Repeated album name!')
    doc = calcCurrent()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Albums (a_name, doc, user_id) VALUES ('{0}', '{1}', '{2}')".format(a_name, doc, uid))
    conn.commit()
    return render_template('albums.html', name=flask_login.current_user.id, message='New album created!',
                           albums=getUserAlbums(uid))


@app.route("/albums/", methods=['DELETE'])
@flask_login.login_required
def delete_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    del_name = request.form.get('del_name')
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Albums WHERE user_id = '{0}' AND a_name = '{1}'".format(uid, del_name))
    conn.commit()
    return render_template('albums.html', name=flask_login.current_user.id, message='Album deleted!',
                           albums=getUserAlbums(uid))


"""Friends end"""

"""Users start"""
@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user

"""Users end"""

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)