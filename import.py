import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

# LOAD ENV VARIABLES
load_dotenv() 


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    with open("books.csv") as file:
        reader = csv.reader(file)

        for isbn, title, author, year in reader:
            if not isbn.isnumeric():
                continue
            
            db.execute("INSERT INTO imbooks(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
            {"isbn":isbn, "title":title, "author":author, "year":year})

        db.commit()

if __name__ == "__main__":
    main()



