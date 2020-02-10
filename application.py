import os
import requests

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from helpers import login_required, apology, lookup, lookupGoogleBooks


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
    # Make it work like goodreads search
    # change it from autocomplete to something else
    search = request.args.get("title")

    if search:
        query = db.execute("(SELECT bookid, title, author FROM imbooks WHERE UPPER(title) LIKE UPPER(:search)) UNION (SELECT bookid, title, author FROM imbooks WHERE UPPER(author) LIKE UPPER(:search)) UNION (SELECT bookid, title, author FROM imbooks WHERE UPPER(isbn) LIKE UPPER(:search)) LIMIT 5", {"search": '%'+search+'%'}).fetchall()
        db.commit()
        # saving id , title + author in a list 
        results = [[row[0],row[1] + " by "  + row[2]]  for row in query]
        return jsonify({
            "results": results,
        })

@app.route("/books/<int:book_id>", methods=["GET"])
def books(book_id):

    # TODO:
    # 1. On your book page, you should also display (if available) the average rating and number of ratings the work has received
    #    from Goodreads.
    # 2. Add book cover and description instead of default ones


    if book_id:
        user_id = session["user_id"]
        query = db.execute("SELECT * FROM imbooks WHERE bookid = :book_id", {"book_id": book_id}).fetchone()
        reviews_query = db.execute("SELECT * FROM reviews WHERE related_book = :book_id", {"book_id": book_id}).fetchall()
        userHasReviewed = db.execute("SELECT * FROM reviews WHERE author_id = :author AND related_book = :bookid",{"author": user_id, "bookid": book_id}).fetchall()
        db.commit()

        if userHasReviewed:
            userReviewed = True
        else:
            userReviewed = False

        reviews = [row for row in reviews_query]
        result = query

        # Getting data from Goodreads API
        book_isbn = result[1]
        data = lookup(book_isbn)
        book_data = {
            "average_rating": data["books"][0]["average_rating"],
            "ratings_count": data["books"][0]["ratings_count"]
             }

        # Receiving data from GoogleBooks API
        # Book description and thumbnail
        bookname = result[2]
        google_data = lookupGoogleBooks(bookname)
        print(f"GOogle data is: {google_data}")      
    
    if result:
        return render_template("books.html", result=result, bookid=book_id, reviews=reviews, userReviewed = userReviewed, book_data = book_data, google_data = google_data)
    else:
        flash("No such a book")
        result = False
        return render_template("books.html", result = result, bookid=book_id)


@app.route("/books/<int:book_id>", methods=["POST"])
@login_required
def comment(book_id):
    user_id = session["user_id"]
    comment = request.form.get("comment")
    # if user forgot to add rating
    star_rating = request.form.get("star")

    if star_rating == None:
        star_rating = 0

    query = db.execute("SELECT * FROM reviews WHERE author_id = :author AND related_book = :bookid",{"author": user_id, "bookid": book_id}).fetchall()
    username_query = db.execute("SELECT username FROM users WHERE id = :user_id", {"user_id": session["user_id"]}).fetchone()
    db.commit()
    
    if query:
        flash("You have already posted review!")
        return redirect("/books/" + str(book_id))
    else: 
        db.execute("INSERT INTO reviews (related_book, comment, author_id, username, star_rating) VALUES(:book_id, :comment, :author_id, :username, :star_rating)", {"book_id": book_id, "comment": comment, "author_id": user_id, "username": username_query[0], "star_rating": star_rating})
        db.commit()

        flash("Your review has been added!")
        return redirect("/books/" + str(book_id))
    
    



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

