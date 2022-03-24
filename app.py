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
		tags = request.form.get('tags').lower().strip().split()
		album = request.form.get('album')
		photo_data = imgfile.read()

		cursor = conn.cursor()
        #insert tag
		for tag in tags:
			cursor.execute(f"INSERT INTO tags (tag) SELECT '{tag}' FROM DUAL "
						   f"WHERE NOT EXISTS ( SELECT * FROM tags WHERE tags.tag = '{tag}' );")

		# insert album
		cursor.execute(f"INSERT INTO albums (name, user_id) SELECT '{album}', {uid} FROM DUAL "
					   f"WHERE NOT EXISTS ( SELECT * FROM albums WHERE albums.name = '{album}' and albums.user_id={uid});")

		# insert pic
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))

		cursor.execute("SELECT max(picture_id) FROM Pictures")
		picture_id = cursor.fetchone()[0]

		if tags:
			# print(f"-- SELECT tag_id FROM tags WHERE tag in {str(tuple(tags))}")
			if len(tags) == 1:
				cursor.execute(f"SELECT tag_id FROM tags WHERE tag = '{tags[0]}'")
			else:
				cursor.execute(f"SELECT tag_id FROM tags WHERE tag in {str(tuple(tags))}")
			for tag_id in cursor.fetchall():
				# print(f'''INSERT INTO tagged_picture (picture_id, tag_id) VALUES ({picture_id}, {tag_id[0]})''')
				cursor.execute(f'''INSERT INTO tagged_picture (picture_id, tag_id) VALUES({picture_id}, {tag_id[0]})''')

		cursor.execute(f"SELECT album_id FROM albums where name='{album}' and user_id={uid}")
		album_id = cursor.fetchone()[0]
		cursor.execute(f'''INSERT INTO stored_in (picture_id, album_id) VALUES  ({picture_id}, {album_id})''')

		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


# Rank
@app.route('/hot', methods=['GET'])
def hot():
	return """<ul>
		<li><a href="/hot/user">User</a></li>
		<li><a href="/hot/tag">Tag</a></li>
	</ul>"""

@app.route('/hot/<cate>', methods=['GET'])
def hot_cate(cate):
	if cate == "user":
		cursor = conn.cursor()
		cursor.execute("SELECT users.email FROM `pictures` "
					   "LEFT JOIN users ON users.user_id = pictures.user_id "
					   "LEFT JOIN comments ON users.user_id = comments.user_id "
					   "GROUP BY users.user_id ORDER BY COUNT(users.user_id) DESC LIMIT 10")
		emails = [x[0] for x in cursor.fetchall()]
		return render_template("hot.html", emails=emails)
	elif cate == "tag":
		cursor = conn.cursor()
		cursor.execute("SELECT tags.tag_id, tag FROM tags "
					   "JOIN tagged_picture on tags.tag_id=tagged_picture.tag_id "
					   "GROUP BY tags.tag_id ORDER BY count(tags.tag_id) desc")
		tags = [{"tag": tag[1], "tag_id": tag[0]} for tag in cursor.fetchall()]
		return render_template("hot.html", tags=tags)
	else:
		raise

@app.route('/search', methods=["GET"])
def search():
	tags = flask.request.args.get("name")
	if tags:
		tags = tags.lower().split()
		picture_ids = []
		items = dict()
		cursor = conn.cursor()
		for tag in tags:
			cursor.execute(f"SELECT pictures.picture_id, imgdata, caption FROM pictures "
						   f"join tagged_picture on pictures.picture_id=tagged_picture.picture_id "
						   f"join tags on tags.tag_id=tagged_picture.tag_id where "
						   f"tags.tag='{tag}'")
			for picture_id, imgdata, caption in cursor.fetchall():
				imgdata = base64.b64encode(imgdata).decode("ascii")
				items[picture_id] = {
					"picture_id": picture_id,
					"imgdata": imgdata,
					"caption": caption
				}
				picture_ids.append(picture_id)

		pictures = []
		for pic_id, pic_num in Counter(picture_ids).items():
			if pic_num == len(tags):
				pictures.append(items[pic_id])

		message = f"A total of {len(pictures)} images were searched"
		return render_template("browse_by_picture.html", items=pictures, message=message)
	else:
		return """<form action='/search' method='GET'>
						<input type='text' name='name' value=''></input>
						<input type='submit' name='submit' value="search"></input>
					</form><a href='/'>Home</a>"""


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


"""browse"""
@app.route('/create_album', methods=['GET'])
@flask_login.login_required
def create_album():
	album = flask.request.args.get('name')
	if album is None:
		return render_template('create_album.html')
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor.execute(f"INSERT INTO albums (name, user_id) SELECT '{album}', {uid} FROM DUAL "
					   f"WHERE NOT EXISTS ( SELECT * FROM albums WHERE albums.name = '{album}' and albums.user_id={uid});")
		conn.commit()
		return "Successfully create album<br><a href='/'>Home</a>"


@app.route('/my_pictures')
@flask_login.login_required
def my_pictures():
	return """    <ul>
	        <li><a href="browse_by_my/album">By Album</a></li>
	        <li><a href="browse_by_my/tag">By Tag</a></li>
	        <li><a href="browse_by_my/picture">By Pictures</a></li>
	    </ul>
	    <a href='/'>Home</a>"""


@app.route('/browse_by_my/<cate>')
@flask_login.login_required
def browse_by_my(cate):
	cursor = conn.cursor()
	albums = []
	tags = []
	pictures = []
	uid = getUserIdFromEmail(flask_login.current_user.id)

	if cate == "album":
		cursor.execute(f"SELECT album_id, name FROM albums WHERE user_id={uid}")
		for album_id, album_name in cursor.fetchall():
			item = {'name': album_name, "album_id": album_id}
			albums.append(item)
	elif cate == "tag":
		cursor.execute(f"SELECT tags.tag_id, tag FROM tags "
					   f"join tagged_picture on tags.tag_id=tagged_picture.tag_id "
					   f"join pictures on pictures.picture_id=tagged_picture.picture_id "
					   f"WHERE user_id={uid}")
		tags = []
		for tag_id, tag in cursor.fetchall():
			item = {'tag_id': tag_id, "tag": tag}
			tags.append(item)
	elif cate == "picture":
		cursor.execute(f"SELECT picture_id, caption, imgdata FROM pictures WHERE user_id={uid}")
		for picture in cursor.fetchall():
			pictures.append({
				"picture_id": picture[0],
				"caption": picture[1],
				"imgdata": base64.b64encode(picture[2]).decode("ascii")
			})
	else:
		raise
	return render_template("browse_my.html", albums=albums, tags=tags, pictures=pictures)


@app.route('/delete_album', methods=['GET'])
@flask_login.login_required
def delete_album():
	album = flask.request.args.get('name')
	cursor = conn.cursor()

	uid = getUserIdFromEmail(flask_login.current_user.id)
	print(f"-- SELECT album_id FROM albums where name='{album}' and user_id={uid}")
	cursor.execute(f"SELECT album_id FROM albums where name='{album}' and user_id={uid}")
	album_id = cursor.fetchone()[0]

	cursor.execute(f"select picture_id from stored_in where album_id={album_id}")
	picture_ids = [x[0] for x in cursor.fetchall()]

	cursor.execute('SET foreign_key_checks = 0')
	cursor.execute(f'delete from stored_in where album_id={album_id}')
	cursor.execute(f'delete from albums where album_id={album_id}')

	for picture_id in picture_ids:
		cursor.execute(f'delete from pictures where picture_id={picture_id}')
		cursor.execute(f'delete from tagged_picture where picture_id={picture_id}')
	cursor.execute('SET foreign_key_checks = 1')

	return "Successfully delete album<br><a href='/'>Home</a>"


@app.route('/delete_picture', methods=['GET'])
@flask_login.login_required
def delete_picture():
	picture_id = flask.request.args.get('picture_id')
	cursor = conn.cursor()
	cursor.execute('SET foreign_key_checks = 0')
	cursor.execute(f'delete from stored_in where picture_id={picture_id}')
	cursor.execute(f'delete from pictures where picture_id={picture_id}')
	cursor.execute(f'delete from tagged_picture where picture_id={picture_id}')
	cursor.execute('SET foreign_key_checks = 1')
	cursor.close()
	conn.commit()
	return "Successfully delete picture<br><a href='/'>Home</a>"


@app.route('/picture/<picture_id>', methods=['GET'])
# @flask_login.login_required
def show_picture(picture_id):
	# picture_id = flask.request.args.get('picture_id')
	cursor = conn.cursor()
	cursor.execute(f'select imgdata, caption from pictures where picture_id={picture_id}')
	imgdata, captioin = cursor.fetchone()
	imgdata = base64.b64encode(imgdata).decode("ascii")
	cursor.execute(f'select tag from tagged_picture '
				   f'LEFT JOIN tags ON tags.tag_id=tagged_picture.tag_id '
				   f'where picture_id={picture_id}')
	tags = [x[0] for x in cursor.fetchall()]

	cursor.execute(f'select words from comments '
				   f'join commented_on on commented_on.comment_id=comments.comment_id '
				   f'where picture_id={picture_id}')
	comments = [x[0] for x in cursor.fetchall()]

	if flask_login.current_user.is_anonymous:
		is_like = False
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)

		cursor.execute(f'select * from liked_pictures where user_id={uid} and picture_id={picture_id}')
		is_like = True if cursor.fetchone() else False

	cursor.close()
	return render_template("picture.html", captioin=captioin, imgdata=imgdata, tags=tags,
						   picture_id=picture_id, comments=comments, is_like=is_like)


@app.route("/browse_index", methods=["GET"])
def browse_index():
	return """    <ul>
        <li><a href="browse_by_album">By Album</a></li>
        <li><a href="browse_by_tag">By Tag</a></li>
        <li><a href="browse_by_picture">By Pictures</a></li>
    </ul>
    <a href='/'>Home</a>"""


@app.route("/browse_by_tag", methods=["GET"])
def browse_by_tag():
	cursor = conn.cursor()
	cursor.execute("select tag_id, tag from tags")
	items = [{"tag_id": x[0], "tag": x[1]} for x in cursor.fetchall()]
	return render_template("browse_by_tag.html", items=items)

@app.route("/browse_by_album", methods=["GET"])
def browse_by_album():
	cursor = conn.cursor()
	cursor.execute(f"select albums.album_id, name, email from stored_in "
				   f"join pictures on stored_in.picture_id=pictures.picture_id "
				   f"join albums on albums.album_id=stored_in.album_id "
				   f"join users on users.user_id=pictures.user_id")
	albums = [{"album_id": x[0], "album": x[1], "email": x[2]} for x in cursor.fetchall()]
	return render_template("browse_by_album.html", albums=albums)

@app.route("/browse_by_picture", methods=["GET"])
def browse_by_picture():
	cursor = conn.cursor()
	cursor.execute(f"select pictures.picture_id, imgdata, caption from pictures")
	items = [{"picture_id": picture[0],
			  "imgdata": base64.b64encode(picture[1]).decode("ascii"),
			  "caption": picture[2]} for picture in cursor.fetchall()]
	return render_template("browse_by_picture.html", items=items)


@app.route("/browse/<cate>/<cate_id>", methods=["GET"])
def browse(cate, cate_id):
	cursor = conn.cursor()
	if cate == "tag":
		cursor.execute(f"select pictures.picture_id, imgdata, caption from pictures "
					   f"join tagged_picture on pictures.picture_id=tagged_picture.picture_id "
					   f"where tag_id={cate_id}")
	elif cate == "album":
		cursor.execute(f"select pictures.picture_id, imgdata, caption from pictures "
					   f"join stored_in on pictures.picture_id=stored_in.picture_id "
					   f"where album_id={cate_id}")
	else:
		raise ValueError

	items = [{"picture_id": picture[0],
			  "imgdata": base64.b64encode(picture[1]).decode("ascii"),
			  "caption": picture[2]} for picture in cursor.fetchall()]

	return render_template("browse.html", items=items)


@app.route("/submit_comment", methods=["GET"])
def submit_comment():
	cursor = conn.cursor()
	picture_id = flask.request.args.get("picture_id")
	text = flask.request.args.get("text")
	cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
	if not flask_login.current_user.is_anonymous:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor.execute(f"select * from pictures where user_id={uid} and picture_id={picture_id} limit 1")
		value = cursor.fetchone()
		print(value)
		if len(value) != 0:
			return "You can't leave messages for yourself！"
	else:
		uid = -1

	cursor.execute(f'INSERT INTO comments (user_id, words) VALUES({uid}, {text})')
	cursor.execute('select max(comment_id) from comments')
	comment_id = cursor.fetchone()[0]
	cursor.execute(f'INSERT INTO commented_on (comment_id, picture_id) VALUES({comment_id}, {picture_id})')

	cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
	cursor.close()
	conn.commit()
	return redirect(f'/picture/{picture_id}')

@app.route("/like", methods=["GET"])
@flask_login.login_required
def like():
	cursor = conn.cursor()
	picture_id = flask.request.args.get("picture_id")
	uid = getUserIdFromEmail(flask_login.current_user.id)

	cursor.execute(f'INSERT INTO liked_pictures (user_id, picture_id) VALUES({uid}, {picture_id})')

	cursor.close()
	conn.commit()
	return redirect(f'/picture/{picture_id}')



#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
