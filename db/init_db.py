import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("database.db")

with open("schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("password")))

recipes = [
    ("Biryani", "Indian", "Rice, Spices, Meat", "Cook slowly"),
    ("Paneer Butter Masala", "Indian", "Paneer, Tomato", "Simmer gravy"),
    ("Fish and Chips", "UK", "Fish, Potato", "Deep fry"),
    ("Jollof Rice", "Nigerian", "Rice, Tomato", "Cook together"),
    ("Sarmale", "Romanian", "Cabbage, Meat", "Roll & cook"),
    ("Borscht", "Ukrainian", "Beetroot", "Boil slowly")
]

for r in recipes:
    cur.execute(
        "INSERT INTO recipes (title, cuisine, ingredients, steps) VALUES (?, ?, ?, ?)",
        r
    )

connection.commit()
connection.close()
