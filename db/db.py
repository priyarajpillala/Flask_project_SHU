import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)    #connects to database
    conn.row_factory = sqlite3.Row  
    conn.execute("PRAGMA foreign_keys = ON")   #comments will auto delete now
    return conn


def create_user(username, password):
    hashed = generate_password_hash(password)  #converts plain text into encrypted password
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()            #creates new row into the table named "users"


def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone() #gets first row that matches in users table
    conn.close()
    return user

def get_admin_by_username(username):
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone() #gets first row that matches in admins table
    conn.close()
    return admin

def validate_login(username, password):  #verifies username and password
    user = get_user_by_username(username) # searches for user name
    if user and check_password_hash(user["password"], password): #checks the hashed password if user name matches 
        return user #returns user's data

    admin = get_admin_by_username(username)      # if not a user then it chekcs if it is an admin
    if admin and check_password_hash(admin["password"], password): #checks the hashed password if admin name matches
        return admin  #returns admin's data

    return None  #if there is no matching found, it returns nothing

def get_all_recipes(): #gets all recipes from "recipes table"
    conn = get_db_connection()
    recipes = conn.execute("SELECT * FROM recipes ORDER BY created DESC").fetchall() #fetches all the results and gives in descending order
    conn.close()
    return recipes


def get_latest_recipes(limit):
    conn = get_db_connection()
    recipes = conn.execute(
        "SELECT * FROM recipes ORDER BY created DESC LIMIT ?", (limit,) # gets the latest recipes with limit (5)
    ).fetchall()
    conn.close()
    return recipes


def get_recipe_by_id(id):
    conn = get_db_connection()     # searches and return backs the recipes by id in recipes table
    recipe = conn.execute("SELECT * FROM recipes WHERE id=?", (id,)).fetchone()
    conn.close()
    return recipe


def create_recipe(title, cuisine, ingredients, steps, user_id, recipe_photo='default_recipe.jpg'):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO recipes (title, cuisine, ingredients, steps, user_id, recipe_photo) VALUES (?, ?, ?, ?, ?, ?)",
        (title, cuisine, ingredients, steps, user_id, recipe_photo)
    )
    conn.commit()             #creates new recipes
    conn.close()

def search_recipes_by_title(query):
    conn = get_db_connection()

    recipes = conn.execute("""SELECT * FROM recipes WHERE LOWER(title) = LOWER(?)""",(query,)).fetchall()   #searches for the recipe by exact word if not found then checks similar (like) words.
    if not recipes:
        recipes = conn.execute("""SELECT * FROM recipes WHERE LOWER(title) LIKE LOWER(?)""",(f"%{query}%",)).fetchall()
    conn.close()
    return recipes



def update_recipe(id, title, cuisine, ingredients, steps, recipe_photo=None):
    conn = get_db_connection()
    if recipe_photo:
        conn.execute(
            "UPDATE recipes SET title=?, cuisine=?, ingredients=?, steps=?, recipe_photo=? WHERE id=?",
            (title, cuisine, ingredients, steps, recipe_photo, id)      #updates all fields
        )
    else:
        conn.execute(
            "UPDATE recipes SET title=?, cuisine=?, ingredients=?, steps=? WHERE id=?",  # updates other fields except photo(if user did not upload) 
            (title, cuisine, ingredients, steps, id)
        )
    conn.commit()
    conn.close()


def delete_recipe(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM recipes WHERE id=?", (id,))
    conn.commit()
    conn.close()        # removes the recipe row that matches the given id



def get_all_users():  # for admin use
    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, username FROM users"  # gets id and username columns from users table 
    ).fetchall()    #fetches all matching rows
    conn.close()
    return users


def delete_user_by_id(user_id):   # for admin use
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))   # deletes the username that matches the id
    conn.commit()
    conn.close()


def add_comment(recipe_id, user_id, content):
    conn = get_db_connection()
    conn.execute("INSERT INTO comments (recipe_id, user_id, content) VALUES (?, ?, ?)", (recipe_id, user_id, content))
    conn.commit()          # insert comment into comments table
    conn.close()

def get_comments_by_recipe(recipe_id):
    conn = get_db_connection()
    comments = conn.execute("""
        SELECT c.*, u.username FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.recipe_id = ?
        ORDER BY c.created ASC           
    """, (recipe_id,)).fetchall()      # gets  comments for recipes
    conn.close()
    return comments

def delete_comment(comment_id): # for admin
    conn = get_db_connection()
    conn.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()       # deletes the comment that matches the comment id
    conn.close()


def save_recipe(user_id, recipe_id):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO saved_recipes (user_id, recipe_id) VALUES (?, ?)", (user_id, recipe_id))
        conn.commit()        #inserts into saved_recipes a recipe
    except sqlite3.IntegrityError:   # if already saved throws an error
        pass
    conn.close()

def unsave_recipe(user_id, recipe_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM saved_recipes WHERE user_id=? AND recipe_id=?", (user_id, recipe_id))
    conn.commit()
    conn.close()      # deletes/unsaves a recipe from saved_recipes


def get_saved_recipes_by_user(user_id): # for admin
    conn = get_db_connection()
    recipes = conn.execute("""
        SELECT r.* FROM recipes r
        JOIN saved_recipes s ON r.id = s.recipe_id
        WHERE s.user_id = ?
        ORDER BY r.created DESC
    """, (user_id,)).fetchall()   #gets saved recipes that users had saved
    conn.close()
    return recipes

def get_all_saved_recipes(): #for admin
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT sr.recipe_id, r.title, r.cuisine, u.username
        FROM saved_recipes sr
        JOIN users u ON sr.user_id = u.id
        JOIN recipes r ON sr.recipe_id = r.id
        ORDER BY u.username, r.title
    """).fetchall()
    conn.close()       #admin can actually see all the saved recipes by the users

    saved = {}
    for row in rows:
        username = row["username"]
        saved.setdefault(username, []).append({
            "recipe_id": row["recipe_id"],
            "title": row["title"],
            "cuisine": row["cuisine"]
        })
    return saved


def delete_comment_by_user(comment_id, user_id): #for user
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id)
    )                          #Deletes a comment if it belongs to the user
    conn.commit()
    conn.close()


