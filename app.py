import os
from flask import (
    Flask, render_template, request, flash, redirect, request, session, url_for
    )
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("account", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                return redirect(url_for(
                            "account", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/logout')
def logout():
    """Logs out the user and pops the session"""
    session.pop('user')
    return render_template("index.html")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/our_fleet")
def our_fleet():
    return render_template("our_fleet.html")


@app.route("/sell_car", methods=["GET", "POST"])
def sell_car():
    """
    Returns Sell Your Car page and sends the form to the database when posted.
    """
    if request.method == 'POST':
        # Get the user's username and user_id from the session
        username = session["user"]
        user_data = mongo.db.users.find_one({"username": username})
        user_id = user_data["_id"]

        cars = mongo.db.cars
        car = {
            'user_id': user_id,
            'fname': request.form.get('fname'),
            'lname': request.form.get('lname'),
            'brand': request.form.get('brand'),
            'model': request.form.get('model'),
            'body_type': request.form.get('body_type'),
            'year': request.form.get('year'),
            'fuel': request.form.get('fuel'),
            'colour': request.form.get('colour'),
            'mileage': request.form.get('mileage'),
            'price': request.form.get('price'),
            'email': request.form.get('email'),
            'telephone': request.form.get('telephone')
        }

        # Insert data into MongoDB
        cars.insert_one(car)

        return redirect(url_for('account'))
    return render_template("sell_car.html")


@app.route("/edit_car/<car_id>", methods=["GET", "POST"])
def edit_car(car_id):
    car = mongo.db.cars.find_one({"_id": ObjectId(car_id)})
    if request.method == 'POST':
        cars = mongo.db.cars
        submit = {
            'fname': request.form.get('fname'),
            'lname': request.form.get('lname'),
            'brand': request.form.get('brand'),
            'model': request.form.get('model'),
            'body_type': request.form.get('body_type'),
            'year': request.form.get('year'),
            'fuel': request.form.get('fuel'),
            'colour': request.form.get('colour'),
            'mileage': request.form.get('mileage'),
            'price': request.form.get('price'),
            'email': request.form.get('email'),
            'telephone': request.form.get('telephone')
        }

        # Update data into MongoDB
        cars.update_one({"_id": ObjectId(car_id)}, {"$set": submit})

        return redirect(url_for('account'))
    return render_template("edit_car.html", car=car)


@app.route("/delete_car/<car_id>")
def delete_car(car_id):
    mongo.db.cars.delete_one({"_id": ObjectId(car_id)})
    return redirect(url_for("account"))


@app.route("/account", methods=["GET", "POST"])
def account():
    # check if "user" key is in the session
    if "user" in session:
        # grab the session user's username from db
        username = session["user"]
        user_data = mongo.db.users.find_one({"username": username})

        if user_data:
            user_id = user_data["_id"]
            # Fetch only the car listings associated with the current user
            cars = list(mongo.db.cars.find({"user_id": user_id}))
            return render_template("account.html", username=username, cars=cars)
        else:
            # Handle the case where the user is not found
            abort(404)
    else:
        return render_template("login.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash(
            "Thank you! We have received your enquiry.".format(
                request.form.get("name")))
    return render_template("contact.html")


@app.errorhandler(404)
def page_not_found(e):
    """
    On 404 error redirects the user to the 404 page.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(err):
    """
    On 500 error redirects the user to the 500 page.
    """
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=os.environ.get("DEBUG"))
