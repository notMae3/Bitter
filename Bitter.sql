/* Create the database */
CREATE DATABASE IF NOT EXISTS Bitter;

USE Bitter;

DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Posts;
DROP TABLE IF EXISTS Replies;
DROP TABLE IF EXISTS Conversations;
DROP TABLE IF EXISTS Messages;

-- Users related
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(24) UNIQUE NOT NULL,
    display_name VARCHAR(24) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT False
);

-- Posts related
CREATE TABLE Posts (
    post_id INT PRIMARY KEY AUTO_INCREMENT,
    author_id INT NOT NULL,
    date_created BIGINT NOT NULL,
    body VARCHAR(120) NOT NULL,
    contains_image BOOLEAN NOT NULL,
    view_count MEDIUMINT NOT NULL DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Replies (
    reply_id MEDIUMINT PRIMARY KEY AUTO_INCREMENT,
    parent_post_id INT NOT NULL,
    author_id INT NOT NULL,
    date_created BIGINT NOT NULL,
    body VARCHAR(120) NOT NULL,
    FOREIGN KEY (parent_post_id) REFERENCES Posts(post_id),
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Likes (
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    date_created BIGINT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES Posts(post_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    CONSTRAINT UC_singular_like_per_post UNIQUE(post_id, user_id)
);

-- Chat related
CREATE TABLE Conversations (
    conversation_id INT PRIMARY KEY AUTO_INCREMENT,
    user_1_id INT NOT NULL,
    user_2_id INT NOT NULL,
    date_created BIGINT NOT NULL,
    FOREIGN KEY (user_1_id) REFERENCES Users(user_id),
    FOREIGN KEY (user_2_id) REFERENCES Users(user_id),
    CONSTRAINT UC_one_conversation_per_user_pair UNIQUE(user_1_id, user_2_id),
    CONSTRAINT CC_cannot_converse_with_self CHECK (user_1_id <> user_2_id)
);

CREATE TABLE Messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    author_id INT NOT NULL,
    body VARCHAR(120) NOT NULL,
    date_created BIGINT NOT NULL,
    conversation_id INT NOT NULL,
    seen BOOLEAN DEFAULT False,
    FOREIGN KEY (author_id) REFERENCES Users(user_id),
    FOREIGN KEY (conversation_id) REFERENCES Conversations(conversation_id)
);
