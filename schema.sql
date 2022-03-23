CREATE DATABASE photoshare8;
USE photoshare8;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT NOT NULL,
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(255),
    last_name varchar(255),
    dob date,
    gender varchar(255),
    hometown varchar(255),
    CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT NOT NULL,
  user_id int4,
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  imgdata longblob ,
  caption varchar(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);


CREATE TABLE Albums
(
	album_id int4 AUTO_INCREMENT NOT NULL,
	name varchar(255),
	user_id int4,
	FOREIGN KEY (user_id) REFERENCES Users(user_id),
	date_started date,
	CONSTRAINT albums_pk PRIMARY KEY (album_id)
);

CREATE TABLE Stored_In
(
	picture_id int4,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
	album_id int4,
	FOREIGN KEY (album_id) REFERENCES Albums(album_id)
);




CREATE TABLE FriCREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
-- Select * From Users;
CREATE TABLE Users(
 user_id INTEGER AUTO_INCREMENT,
 first_name VARCHAR(100),
 last_name VARCHAR(100),
 email VARCHAR(100),
 birth_date DATE,
 hometown VARCHAR(100),
 gender VARCHAR(100),
 password VARCHAR(100) NOT NULL,
 PRIMARY KEY (user_id)
 );

 CREATE TABLE Friends(
 user_id1 INTEGER,
 user_id2 INTEGER,
 PRIMARY KEY (user_id1, user_id2),
 FOREIGN KEY (user_id1)
 REFERENCES Users(user_id),
 FOREIGN KEY (user_id2)
 REFERENCES Users(user_id)
);

CREATE TABLE Albums(
 albums_id INTEGER,
 name VARCHAR(100),
 date DATE,
 user_id INTEGER NOT NULL,
 PRIMARY KEY (albums_id),
 FOREIGN KEY (user_id)
 REFERENCES Users(user_id)
);

CREATE TABLE Tags(
 tag_id INTEGER,
 name VARCHAR(100),
 PRIMARY KEY (tag_id)
);

CREATE TABLE Photos(
 photo_id INTEGER,
 caption VARCHAR(100),
 data LONGBLOB,
 albums_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
 PRIMARY KEY (photo_id),
 FOREIGN KEY (albums_id) REFERENCES Albums (albums_id),
FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Tagged(
 photo_id INTEGER,
 tag_id INTEGER,
 PRIMARY KEY (photo_id, tag_id),
 FOREIGN KEY(photo_id)
 REFERENCES Photos (photo_id),
 FOREIGN KEY(tag_id)
 REFERENCES Tags (tag_id)
);

CREATE TABLE Comments(
 comment_id INTEGER,
 user_id INTEGER NOT NULL,
 photo_id INTEGER NOT NULL,
 text VARCHAR (100),
 date DATE,
 PRIMARY KEY (comment_id),
 FOREIGN KEY (user_id)
 REFERENCES Users (user_id),
 FOREIGN KEY (photo_id)
 REFERENCES Photos (photo_id)
);

CREATE TABLE Likes(
 photo_id INTEGER,
 user_id INTEGER,
 PRIMARY KEY (photo_id,user_id),
 FOREIGN KEY (photo_id)
 REFERENCES Photos (photo_id),
 FOREIGN KEY (user_id)
 REFERENCES Users (user_id)
);
ends_with
(	user_id int4,
	FOREIGN KEY (user_id) REFERENCES Users(user_id),
	friend_uid int4,
	FOREIGN KEY (friend_uid) REFERENCES Users(user_id)
);


CREATE TABLE Tags
(
	tag_id int4 AUTO_INCREMENT NOT NULL,
	tag varchar(255),
	CONSTRAINT tag_pk PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged_Picture
(
	picture_id int4 ,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
	tag_id int4,
	FOREIGN KEY (tag_id) REFERENCES Tags(tag_id)
);

CREATE TABLE Comments
(
	comment_id int4 AUTO_INCREMENT NOT NULL,
	user_id int4,
	FOREIGN KEY (user_id) REFERENCES Users(user_id),
	date_written date,
	words varchar(255),
	CONSTRAINT comments_pk PRIMARY KEY (comment_id)
);

CREATE TABLE Commented_on
(
	comment_id int4,
	FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
	picture_id int4,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Liked_pictures
(
	user_id int4,
	FOREIGN KEY (user_id) REFERENCES Users(user_id),
	picture_id int4,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

