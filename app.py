from flask import Flask, render_template, url_for, request, flash, redirect

from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf


app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Required for CSRF protection
csrf = CSRFProtect(app)  # This automatically protects all POST routes

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())




# @app.context_processor
# def inject_site_name():
#     return dict()



@app.route("/", methods=['GET','post'])
def index():
    if request.method == 'post':
        email=request.form['useremail']
        password=request.form['userpassword']

        error = None
        if not email:
            error = 'Username is Required!'
        elif not password:
            error = 'Password is Required!'

        if error is none:
            flash(category='success', message=f"The Form Was Posted Successfully! Well Done {username}")
            return redirect (url_for("home"))
        else:
            flash(category='danger', message=f"Login failed: {error}")

     return render_template("index.html")


@app.route("/home/")
def home():
    return render_template("home.html")


@app.route("/registration/" , methods=('GET', 'POST'))
def registration():
    if request.method=="POST":
        USERNAME = request.form['username']
        PASSWORD = request.form['password']
        REPASSWORD = request.form['repassword']

        # Simple validation checks
        error = None
        if not USERNAME:
            error = 'Username is required!'
        elif not PASSWORD or not REPASSWORD:
            error = 'Password is required!'
        elif PASSWORD != REPASSWORD:
            error = 'Passwords do not match!'

        if error is None:
            flash(category='success', message=f"The Form Was Posted Successfully! Well Done {username}")
        else:
            flash(category='danger', message=error)

    return render_template("registration.html")

@app.route("/loginproblemlog/")
def loginerrors():
    return render_template("loginerrors.html")





if __name__ == '__main__':
    app.run(debug=True)