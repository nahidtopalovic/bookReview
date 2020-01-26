import os
import requests

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from helpers import login_required, apology


# LOAD ENV VARIABLES
load_dotenv() 
# GOODREADS API KEY
key = os.getenv("KEY")

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    """Index page"""

    return render_template("index.html")

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    isbn = request.args.get("isbn")
    title = request.args.get("title")
    author = request.args.get("author")

    if isbn:
        query = db.execute("SELECT bookid, isbn FROM imbooks WHERE isbn LIKE :isbn LIMIT 10", {"isbn": '%'+isbn+'%'}).fetchall()
        db.commit()
        results = [isbn[1] for isbn in query]
        id_results = [id[0] for id in query]
        return jsonify({
            "results": results,
            "bookids": id_results
        })
    elif title:
        query = db.execute("SELECT bookid, title FROM imbooks WHERE UPPER(title) LIKE UPPER(:title) LIMIT 10", {"title": '%'+title+'%'}).fetchall()
        db.commit()
        results = [title[1] for title in query]
        id_results = [id[0] for id in query]
        print(results)
        return jsonify({
            "results": results,
            "bookids": id_results
        })
    elif author:
        query = db.execute("SELECT bookid, author FROM imbooks WHERE UPPER(author) LIKE UPPER(:author) LIMIT 10", {"author": '%'+author+'%'}).fetchall()
        db.commit()
        results = [author[1] for author in query]
        id_results = [id[0] for id in query]
        return jsonify({
            "results": results,
            "bookids": id_results
        })

@app.route("/books", methods=["GET"])
def books():
    # To do: update anchor link with bookid using JS 

    # Book Page: When users click on a book from the results of 
    # the search page, they should be taken to a book page, 
    # with details about the book: its title, author, publication year, ISBN number,
    #  and any reviews that users have left for the book on your website.
    isbn = request.args.get("isbn")
    title = request.args.get("title")
    author = request.args.get("author")
    print(f"Request string is: {request.query_string}")

    if not isbn and not title and not author:
        return apology("You need to enter isbn, book title or author''s name", 403)

    if isbn:
        query = db.execute("SELECT * FROM imbooks WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        db.commit()
        result = query

    elif title:
        query = db.execute("SELECT * FROM imbooks WHERE UPPER(title) = UPPER(:title)", {"title": title}).fetchone()
        db.commit()
        result = query

    elif author:
        query = db.execute("SELECT * FROM imbooks WHERE UPPER(author) = UPPER(:author)", {"author": author}).fetchone()
        db.commit()
        result = query
    
    if result:
        return render_template("books.html", result=result)
    else:
        flash("No such a book")
        return render_template("books.html")


@app.route("/comment", methods=["GET","POST"])
def comment():
    comment_submission = request.form.get("comment")
    print(comment_submission)
    print(request.url)
    return redirect(request.url)
    



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()
        db.commit()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        #Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                         {"username": request.form.get("username")}).fetchall()
        db.commit()

        if len(rows) != 0:
            return apology("username already exists")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was repeated correctly
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must repeat the same password", 403)

        db.execute("INSERT INTO users (username,hash) VALUES (:username,:hash)",
        {"username": request.form.get("username"),"hash": generate_password_hash(request.form.get("password"),method='pbkdf2:sha256', salt_length=8)})
    

        #Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                         {"username": request.form.get("username")}).fetchall()
        db.commit()

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash('You were successfully registered')

        # Redirect user to home page
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

