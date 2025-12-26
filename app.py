from flask import Flask, render_template, request, redirect, url_for, flash, session
from db.db import *
from email.message import EmailMessage
import smtplib
import random
# from flask_wtf import CSRFProtect
# from flask_wtf.csrf import generate_csrf

app = Flask(__name__)
app.secret_key = "royal_red_secret_key"


# csrf = CSRFProtect(app)  
# @app.context_processor
# def inject_csrf_token():
#     return dict(csrf_token=generate_csrf())


OTP = ""
for i in range(6):
    OTP += str(random.randint(0,9))


server = smtplib.SMTP('smtp.gmail.com',587)
server.starttls()
from_mail = "priyarajpillala1999@gmail.com"
server.login(from_mail,'fbky qdtm ippg nupj')

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

    username = session.get("username")
    is_admin = False

    if username:
        admin_record = get_admin_by_username(username)
        if admin_record:
            is_admin = True

    return render_template("recipe.html", recipe=recipe, user_id=session.get("user_id"), is_admin=is_admin)



@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if get_user_by_username(username):
            flash("Username already exists", "danger")
            return render_template("register.html")
        
        msg=EmailMessage()
        msg["subject"] = "OTP verification"
        msg["from"] = from_mail
        msg["to"] = username
        msg.set_content('your OTP is :' + OTP )
        server.send_message(msg)


        session["reg_username"] = username
        session["reg_password"] = password
        session["reg_otp"] = OTP

        print("REGISTRATION OTP:", OTP) 

        return redirect(url_for("verify_otp"))

    return render_template("register.html")



@app.route("/verify-otp/", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if str(session.get("reg_otp")) == entered_otp:
            create_user(
                session["reg_username"],
                session["reg_password"]
            )

            user = get_user_by_username(session["reg_username"])
            session["user_id"] = user["id"]

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
            session["username"] = user["username"]
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


    user_id = session["user_id"]


    if request.method == "POST":
        title = request.form["title"]
        cuisine = request.form["cuisine"]
        ingredients = request.form["ingredients"]
        steps = request.form["steps"]
        
        

        create_recipe(title, cuisine, ingredients, steps, user_id)
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



@app.route("/admin/dashboard/")
def admin_dashboard():
    username = session.get("username")

    if not username or not get_admin_by_username(username):
        return "Access denied", 403

    users = get_all_users()

    recipes = get_all_recipes()

    user_recipes = {}
    for recipe in recipes:
        if recipe["user_id"] not in user_recipes:
            user_recipes[recipe["user_id"]] = []
        user_recipes[recipe["user_id"]].append(recipe)

    return render_template(
        "admin_dashboard.html",
        users=users,
        user_recipes=user_recipes
    )




@app.route("/admin/delete-user/<int:user_id>/", methods=["POST"])
def admin_delete_user(user_id):
    username = session.get("username")

    if not username or not get_admin_by_username(username):
        return "Access denied", 403

    delete_user_by_id(user_id)
    return redirect("/admin/dashboard/")



@app.route("/admin/delete-recipe/<int:recipe_id>/", methods=["POST"])
def admin_delete_recipe(recipe_id):
    username = session.get("username")
    if not username or not get_admin_by_username(username):
        return "Access denied", 403

    delete_recipe(recipe_id)
    return redirect("/admin/dashboard/")






if __name__ == "__main__":
    app.run(debug=True)
