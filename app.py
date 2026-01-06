from flask import Flask, render_template, request, redirect, url_for, flash, session
from db.db import *
from email.message import EmailMessage
import smtplib
import random
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.utils import secure_filename
import os
import time

UPLOAD_FOLDER = 'static/uploads/recipes'        # where recipe images are stored
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}    # image formats

app = Flask(__name__)
app.secret_key = "royal_red_secret_key" # secret key for session to run with encryption 

csrf = CSRFProtect(app)   # csrf protection for forms
 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

@app.route("/")
def index():
    if "user_id" in session:
        recipes = get_all_recipes()
    else:                                  # if user is logged in, it shows all recipes else it shows only the latest 5 recipes
        recipes = get_latest_recipes(5)

    return render_template("index.html", recipes=recipes)

@app.route("/about/")
def about():                            #about page
    return render_template("about.html")

@app.route("/recipes/")
def recipes():
    if "user_id" not in session:     # user need to get logged in to get access to all the recipes
        flash("Login required to view all recipes", "warning")
        return redirect(url_for("login"))

    recipes = get_all_recipes()   # gets all recipes from database
    return render_template("recipes.html", recipes=recipes)


@app.route("/search/", methods=["GET", "POST"])
@csrf.exempt  # skip CSRF check
def search():
    recipes = []
    query = ""

    # Gets query from POST or GET
    if request.method == "POST":
        query = request.form.get("query", "").strip()  #from form
    elif request.method == "GET":
        query = request.args.get("query", "").strip()   #from url

    if query:
        recipes = search_recipes_by_title(query)   # search database that matching the query 

    return render_template("search.html", recipes=recipes, query=query)


@app.route("/register/", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        repassword = request.form["repassword"]

        if get_user_by_username(username):
            flash("Username already exists", "danger")   # checks if user already exists
            return render_template("register.html")

        if password != repassword:
            flash("Passwords do not match", "danger")   # checks if the password matches with repassword
            return render_template("register.html")

        if password == username:
            flash("Password cannot be the same as username", "danger")  # password and username should not be same
            return render_template("register.html")

        # Generate NEW OTP for THIS registration
        OTP = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Create email
        msg = EmailMessage()
        msg["subject"] = "OTP verification"
        msg["from"] = "priyarajpillala1999@gmail.com"
        msg["to"] = username
        msg.set_content("Your OTP is: " + OTP)
        
        # Send email with NEW connection each time
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('priyarajpillala1999@gmail.com', 'fdzv jnvz enla mqwm')
            server.send_message(msg)
            server.quit()  # Close connection after sending
        except Exception as e:
            flash(f"Email sending failed: {str(e)}", "danger")
            return render_template("register.html")

        session["reg_username"] = username
        session["reg_password"] = password   #stores registration data temporarily in session
        session["reg_otp"] = OTP

        print("REGISTRATION OTP:", OTP)

        return redirect(url_for("verify_otp"))  # redirects to verification page for OTP

    return render_template("register.html")

@app.route("/verify-otp/", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]   #gets entered OTP by user

        if str(session.get("reg_otp")) == entered_otp:    #checks if the entered OTP is similar to the OTP that's sent via email
            create_user(
                session["reg_username"],
                session["reg_password"]          # if OTP matches this creates a user with the username and password he git registered with
            )

            user = get_user_by_username(session["reg_username"])
            session["user_id"] = user["id"]

            session.pop("reg_username")
            session.pop("reg_password")   #creates temporary registration data from session
            session.pop("reg_otp")

            flash("Registration successful", "success")
            return redirect(url_for("recipes"))    #redirects to recipes page
        else:
            flash("Invalid OTP", "danger")   #when otp is incorrect

    return render_template("verify_otp.html")

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        #  user login
        user = get_user_by_username(username)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = False   #  IMPORTANT
            flash("User login successful", "success")
            return redirect(url_for("recipes"))

        #  admin login
        admin = get_admin_by_username(username)
        if admin and check_password_hash(admin["password"], password):
            session["user_id"] = admin["id"]
            session["username"] = admin["username"]
            session["is_admin"] = True    #  IMPORTANT
            flash("Admin login successful", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid credentials", "danger")   # if not user or admin

    return render_template("login.html")

@app.route("/logout/")
def logout():
    session.clear()   # removes all session data
    flash("Logged out", "info")
    return redirect(url_for("index"))

@app.route("/create/", methods=["GET", "POST"])
def create():
    if "user_id" not in session:
        flash("Login required", "danger")   #you can not create a recipe until you get logged in
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":          # gets form data
        title = request.form["title"]
        cuisine = request.form["cuisine"]
        ingredients = request.form["ingredients"]
        steps = request.form["steps"]
        recipe_photo = 'default_recipe.jpg'

        if 'recipe_photo' in request.files:     #recipe photos
            file = request.files['recipe_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{user_id}_{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))   # saves file to uploads folder
                recipe_photo = filename
        
        create_recipe(title, cuisine, ingredients, steps, user_id, recipe_photo)
        flash("Recipe created", "success")
        return redirect(url_for("recipes"))    # saves recipe to database

    return render_template("create.html")

@app.route("/update/<int:id>/", methods=["GET", "POST"])
def update(id):
    recipe = get_recipe_by_id(id)       # gets current recipe data

    if request.method == "POST":    
        recipe_photo = None     # no new photos by default 
        
        if 'recipe_photo' in request.files:       #optional to add new photo
            file = request.files['recipe_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{session['user_id']}_{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                recipe_photo = filename
        
        update_recipe(
            id,
            request.form["title"],
            request.form["cuisine"],
            request.form["ingredients"],
            request.form["steps"],
            recipe_photo
        )
        flash("Recipe updated", "success")
        return redirect(url_for("recipe", id=id))

    return render_template("update.html", recipe=recipe)   # shows update form with current recipes

@app.route("/delete/<int:id>/", methods=["GET", "POST"])
def delete(id):
    recipe = get_recipe_by_id(id) #gets recipe to delete

    if request.method == "POST":
        delete_recipe(id)
        flash("Recipe deleted", "info") #deletes from database
        return redirect(url_for("recipes"))

    return render_template("delete.html", recipe=recipe)

@app.route("/admin/dashboard/")
def admin_dashboard():
    username = session.get("username")

    if not username or not get_admin_by_username(username):     #checks if user is admin
        return "Access denied", 403    # if not then you are not allowed to access this option

    all_users = get_all_users() #gets all users
    all_recipes = get_all_recipes()  # gets all recipes

    latest_users = all_users[:3]
    latest_recipes = all_recipes[:3]    #gets only the latest 3

    user_recipes = {}      #organises recipes by users on the page
    for recipe in latest_recipes:
        user_recipes.setdefault(recipe["user_id"], []).append(recipe)

    return render_template("admin_dashboard.html",users=latest_users,user_recipes=user_recipes)

@app.route("/admin/delete-user/<int:user_id>/", methods=["POST"])
def admin_delete_user(user_id):
    username = session.get("username")

    if not username or not get_admin_by_username(username):    #checks if user is admin and if not then the option is not allowed
        return "Access denied", 403

    delete_user_by_id(user_id)     # user will be deleted from database
    return redirect("/admin/dashboard/")

@app.route("/admin/delete-recipe/<int:recipe_id>/", methods=["POST"])
def admin_delete_recipe(recipe_id):
    username = session.get("username")
    if not username or not get_admin_by_username(username): #checks if user is admin
        return "Access denied", 403

    delete_recipe(recipe_id)     # deletes recipe from database
    return redirect("/admin/dashboard/")

@app.route("/admin/users/")
def admin_users():
    username = session.get("username")

    if not username or not get_admin_by_username(username):   # checks if user is admin
        return "Access denied", 403

    users = get_all_users()
    return render_template("users_list.html", users=users)

@app.route("/admin/recipes/")
def admin_recipes():
    username = session.get("username")

    if not username or not get_admin_by_username(username):
        return "Access denied", 403

    users = get_all_users() #gets all the users
    recipes = get_all_recipes()    # gets all the recipes       

    user_recipes = {}                              # to get recipes by user id
    for recipe in recipes:
        user_recipes.setdefault(recipe["user_id"], []).append(recipe)

    return render_template(
        "recipes_by_users.html",
        users=users,
        user_recipes=user_recipes
    )

@app.route("/recipe/<int:id>/", methods=["GET", "POST"])
def recipe(id):
    recipe = get_recipe_by_id(id)
    user_id = session.get("user_id")
    is_admin = False
    username = session.get("username")         
    if username and get_admin_by_username(username):    # checks if current user is an admin
        is_admin = True

    if request.method == "POST" and "comment" in request.form and user_id:
        content = request.form["comment"].strip()
        if content:
            add_comment(id, user_id, content)         # commenting on a recipe
            flash("Comment added!", "success")
            return redirect(url_for("recipe", id=id))

    comments = get_comments_by_recipe(id)   # gets all comments from the recipe

    saved = False
    if user_id:
        saved_recipes = get_saved_recipes_by_user(user_id)    #checks if the current recipe is saved by the current user or not
        saved = any(r["id"] == id for r in saved_recipes)

    return render_template("recipe.html",recipe=recipe,user_id=user_id,is_admin=is_admin,comments=comments,saved=saved)

@app.route("/save-recipe/<int:id>/", methods=["POST"])
def save_recipe_route(id):
    if "user_id" not in session:
        flash("Login to save recipes", "danger")
        return redirect(url_for("login"))            #you can only save a recipe if you are a user and logged in
    save_recipe(session["user_id"], id)
    flash("Recipe saved!", "success")
    return redirect(url_for("recipe", id=id))

@app.route("/unsave-recipe/<int:id>/", methods=["POST"])
def unsave_recipe_route(id):
    if "user_id" not in session:
        flash("Login to unsave recipes", "danger")
        return redirect(url_for("login"))
    unsave_recipe(session["user_id"], id)
    flash("Recipe unsaved!", "info")                     #you can only unsave a recipe if you are a user and logged in
    return redirect(url_for("recipe", id=id))

@app.route("/saved-recipes/")
def saved_recipes_route():
    if "user_id" not in session:
        return redirect(url_for("login"))    #only logged in users can be able to see the saved recipes 
    recipes = get_saved_recipes_by_user(session["user_id"])         # gets all saved recipes from the current user
    return render_template("saved_recipes.html", recipes=recipes)

@app.route("/admin/saved-recipes/")
def admin_saved_recipes():
    if not session.get("username") or not get_admin_by_username(session.get("username")):
        return "Access denied", 403

    saved = get_all_saved_recipes()         # admin can see saved recipes by individual user
    return render_template("admin_saved_recipes.html", saved=saved)

@app.route("/admin/delete-comment/<int:id>/", methods=["POST"])
def admin_delete_comment(id):
    if not session.get("username") or not get_admin_by_username(session.get("username")):
        return "Access denied", 403
    delete_comment(id)                              # admin can delete any comment
    flash("Comment deleted", "info")
    return redirect(request.referrer or url_for("admin_dashboard"))

@app.route("/delete-comment/<int:id>/", methods=["POST"])
def delete_own_comment(id):
    if "user_id" not in session:
        flash("You must be logged in to delete comments", "danger")      # user can delete their own comment
        return redirect(url_for("login"))

    user_id = session["user_id"]
    delete_comment_by_user(id, user_id)
    flash("Comment deleted", "info")
    return redirect(request.referrer or url_for("recipes"))

if __name__ == "__main__":
    app.run(debug=True)
