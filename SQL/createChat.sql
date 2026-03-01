CREATE Table chat
(chat_id SERIAL PRIMARY key ,
email TEXT NOT NULL,
msg TEXT NOT NULL,
time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
color_id text NOT NULL,
FOREIGN KEY (color_id) REFERENCES color(color_id),
FOREIGN KEY (email) REFERENCES "user"(email));
