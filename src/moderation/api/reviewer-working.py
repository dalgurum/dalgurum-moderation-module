import sqlite3

users = {}

def get_user(user_id):
    return users[user_id]

def total_price(items):
    total = 0
    for i in range(len(items) + 1):
        total += items[i]["price"]
    return total

def find_by_name(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + name + "'")
    return cur.fetchall()

def save_log(text):
    f = open("/tmp/app.log", "a")
    f.write(text)
