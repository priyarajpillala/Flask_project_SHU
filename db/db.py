import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_user(username, password):
    hashed = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()


def validate_login(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user["password"], password):
        return user 

    admin = get_admin_by_username(username)
    if admin and check_password_hash(admin["password"], password):
        return admin

    return None



def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user

def get_admin_by_username(username):
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
    conn.close()
    return admin


def get_all_recipes():
    conn = get_db_connection()
    recipes = conn.execute("SELECT * FROM recipes ORDER BY created DESC").fetchall()
    conn.close()
    return recipes


def get_latest_recipes(limit):
    conn = get_db_connection()
    recipes = conn.execute(
        "SELECT * FROM recipes ORDER BY created DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return recipes


def get_recipe_by_id(id):
    conn = get_db_connection()
    recipe = conn.execute("SELECT * FROM recipes WHERE id=?", (id,)).fetchone()
    conn.close()
    return recipe


def create_recipe(title, cuisine, ingredients, steps, user_id):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO recipes (title, cuisine, ingredients, steps, user_id) VALUES (?, ?, ?, ?,?)",
        (title, cuisine, ingredients, steps, user_id)
    )
    conn.commit()
    conn.close()

def search_recipes_by_title(query):
    conn = get_db_connection()

    recipes = conn.execute("""SELECT * FROM recipes WHERE LOWER(title) = LOWER(?)""",(query,)).fetchall()
    if not recipes:
        recipes = conn.execute("""SELECT * FROM recipes WHERE LOWER(title) LIKE LOWER(?)""",(f"%{query}%",)).fetchall()
    conn.close()
    return recipes



def update_recipe(id, title, cuisine, ingredients, steps):
    conn = get_db_connection()
    conn.execute(
        "UPDATE recipes SET title=?, cuisine=?, ingredients=?, steps=? WHERE id=?",
        (title, cuisine, ingredients, steps, id)
    )
    conn.commit()
    conn.close()


def delete_recipe(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM recipes WHERE id=?", (id,))
    conn.commit()
    conn.close()



def get_all_users():
    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, username FROM users"
    ).fetchall()
    conn.close()
    return users


def delete_user_by_id(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
