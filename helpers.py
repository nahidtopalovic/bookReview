import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def lookup(isbn):
    """Look up book on Goodreads."""


    # Contact API
    try:
        api_key = os.environ.get("KEY")
        response = requests.get(f"https://www.goodreads.com/book/review_counts.json?isbns={isbn}&key={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        data = response.json()
        return data
    except (KeyError, TypeError, ValueError):
        return None

def lookupGoogleBooks(bookname):
    """Look up book on Google Books."""

    # Contact API
    try:
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote_plus(bookname)}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        data = response.json()
        # print(f"Data from api is: {data}")
        data1 = data["items"][0]["volumeInfo"]["description"]
        data2 = data["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]

        print(f"Data 1 and 2 is {data1}")

        return {
            "description": data["items"][0]["volumeInfo"]["description"],
            "thumbnail": data["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
        }
    except (KeyError, TypeError, ValueError):
        return None

        