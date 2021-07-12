
from unicodedata import name
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import bcrypt
from dotenv import load_dotenv
from os import environ

def get_database_client(flask_app):
    # Database
    client = pymongo.MongoClient(flask_app.config['DB_URI'], flask_app.config['DB_PORT'])
    return client

def create_app():
    load_dotenv('.env')
    app = Flask(__name__)
    app.secret_key = environ.get("SECRET_KEY")
    app.config['DB_URI'] = environ.get('DB_URI')
    app.config['DB_PORT'] = int(environ.get('DB_PORT'))
    return app

app = create_app()
# db = client["database_name"]
# collection = db["first_collection"]
client = get_database_client(app)
db = client.get_database('Restaurant_Rater_Users')
records = db.register
groups = db.groups


@app.route("/", methods=['post', 'get'])
def index():
    message = ''
    if "email" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")

        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('index.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('index.html', message=message)
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('index.html', message=message)
        else:
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            user_input = {'name': user, 'email': email, 'password': hashed}
            records.insert_one(user_input)

            user_data = records.find_one({"email": email})
            new_email = user_data['email']

            session["email"] = new_email
            return render_template('logged_in.html', email=new_email)
    return render_template('index.html')


@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('logged_in.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")


        email_found = records.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']

            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('index.html')


@app.route("/groups", methods=["POST", "GET"])
def create_group():
    message = ''
    if "email" in session:
        email = session["email"]
        if request.method == "POST":
            group = request.form.get("groupname")
            group_found = groups.find_one({"groupname": group})
            if group_found:
                message = 'There already is a group by that name'
                return render_template('groups.html', message=message, email=email)
            else:
                new_group = {'groupname': group, 'groupadmin': email, 'memebers': [email]}
                groups.insert_one(new_group)

                new_group = groups.find_one({"groupname": group})
                session["group"] = group
            return render_template('index.html', email=email)
        return render_template('groups.html', email=email)
    else:
        message = 'You must log in first'
        return render_template('login.html', message=message)

@app.route("/mygroups", methods=["POST", "GET"])
def my_group():
    message = ''
    if "email" in session:
        email = session["email"]
        user_groups = list(groups.find({"groupadmin": email}, {"groupname"}))
        print(user_groups)
    return render_template("my_groups.html", email=email, user_groups=user_groups)


#end of code to run it

if __name__ == "__main__":
  app.run()
