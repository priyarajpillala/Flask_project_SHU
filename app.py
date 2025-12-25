from flask import Flask, render_template, request, redirect, url_for, flash, session
from db.db import *
import random

app = Flask(__name__)
app.secret_key = "royal_red_secret_key"


@app.route("/")
def index():
    if "user_id" in session:
        recipes = get_all_recipes()
    else:
        recipes = get_latest_recipes(5)

    return render_template("index.html", recipes=recipes)


@app.route("/recipes/")
def recipes():
    if "user_id" not in session:
        flash("Login required to view all recipes", "warning")
        return redirect(url_for("login"))

    recipes = get_all_recipes()
    return render_template("recipes.html", recipes=recipes)


@app.route("/recipe/<int:id>/")
def recipe(id):
    recipe = get_recipe_by_id(id)
    return render_template("recipe.html", recipe=recipe)


@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user already exists
        if get_user_by_username(username):
            flash("Username already exists", "danger")
            return render_template("register.html")

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Store temporary registration data in session
        session["reg_username"] = username
        session["reg_password"] = password
        session["reg_otp"] = otp

        print("REGISTRATION OTP:", otp)  # Simulated OTP send

        return redirect(url_for("verify_otp"))

    return render_template("register.html")



@app.route("/verify-otp/", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        # Compare OTP
        if str(session.get("reg_otp")) == entered_otp:
            # Create user only after OTP verification
            create_user(
                session["reg_username"],
                session["reg_password"]
            )

            # Log the user in
            user = get_user_by_username(session["reg_username"])
            session["user_id"] = user["id"]

            # Clear temporary session data
            session.pop("reg_username")
            session.pop("reg_password")
            session.pop("reg_otp")

            flash("Registration successful", "success")
            return redirect(url_for("recipes"))
        else:
            flash("Invalid OTP", "danger")

    return render_template("verify_otp.html")



@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = validate_login(username, password)

        if user is None:
            flash("Invalid credentials", "danger")
        else:
            session["user_id"] = user["id"]
            flash("Login successful", "success")
            return redirect(url_for("recipes"))

    return render_template("login.html")



@app.route("/logout/")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("index"))


@app.route("/create/", methods=["GET", "POST"])
def create():
    if "user_id" not in session:
        flash("Login required", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        cuisine = request.form["cuisine"]
        ingredients = request.form["ingredients"]
        steps = request.form["steps"]

        create_recipe(title, cuisine, ingredients, steps)
        flash("Recipe created", "success")
        return redirect(url_for("recipes"))

    return render_template("create.html")


@app.route("/update/<int:id>/", methods=["GET", "POST"])
def update(id):
    recipe = get_recipe_by_id(id)

    if request.method == "POST":
        update_recipe(
            id,
            request.form["title"],
            request.form["cuisine"],
            request.form["ingredients"],
            request.form["steps"]
        )
        flash("Recipe updated", "success")
        return redirect(url_for("recipe", id=id))

    return render_template("update.html", recipe=recipe)


@app.route("/delete/<int:id>/", methods=["GET", "POST"])
def delete(id):
    recipe = get_recipe_by_id(id)

    if request.method == "POST":
        delete_recipe(id)
        flash("Recipe deleted", "info")
        return redirect(url_for("recipes"))

    return render_template("delete.html", recipe=recipe)












if __name__ == "__main__":
    app.run(debug=True)
