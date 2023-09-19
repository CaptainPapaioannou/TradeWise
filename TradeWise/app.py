import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute(
        "SELECT stock, sum(shares) as sum_of_shares FROM purchases WHERE user_id = ? GROUP BY user_id, stock HAVING sum_of_shares > 0",
        session["user_id"],
    )

    for row in rows:
        row.update({"price": lookup(row["stock"])["price"]})
        row.update({"total": row["price"] * row["sum_of_shares"]})

    cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
    cash_balance = cash[0]["cash"]

    ground_total = cash_balance + sum([x["total"] for x in rows])

    return render_template(
        "index.html", rows=rows, cash_balance=cash_balance, ground_total=ground_total
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # check to see if symbol form left blank
        if not request.form.get("symbol"):
            return apology("must choose a stock")

        # check to see if shares form left blank
        if not request.form.get("shares"):
            return apology("must choose number of shares")

        # assign shares into a variable
        shares = request.form.get("shares")

        # check to see that shares is a valid integer
        try:
            shares = int(shares)
        except ValueError:
            return apology("Invalid number of shares")

        # check if given shares are a positive int
        if shares < 1:
            return apology("Enter a positive number of shares")

        # lookup symbol
        if not (symbol := lookup(request.form.get("symbol"))):
            return apology("INVALID SYMBOL")

        # set cost of transaction
        cost = symbol["price"] * float(shares)

        # query for users wallet
        wallet = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # check if user can afford purchase
        if cost <= wallet[0]["cash"]:
            db.execute(
                "INSERT INTO purchases(user_id, stock, price, shares) VALUES(?, ?, ?, ?)",
                session["user_id"],
                symbol["symbol"],
                symbol["price"],
                shares,
            )
            db.execute(
                "UPDATE users SET cash = ? WHERE id = ?",
                (wallet[0]["cash"] - cost),
                session["user_id"],
            )

            flash("Bought!")

            return redirect("/")
        else:
            return apology("Couldn't complete transaction")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT * FROM purchases WHERE user_id=?", session["user_id"]
    )

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password")

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # check to see if form left blank
        if not request.form.get("symbol"):
            return apology("must enter symbol")

        # lookup symbol
        symbol = lookup(request.form.get("symbol"))

        if symbol is None:
            return apology("Couldn't find what you are looking for")

        else:
            return render_template(
                "quoted.html", name=symbol["name"], price=usd(symbol["price"])
            )

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password")

        # check if we allready have a user with the same username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) != 0:
            return apology("username allready taken")

        # check if the passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match")

        # store username and password hash and insert into database
        new_username = request.form.get("username")
        new_password = generate_password_hash(
            request.form.get("password"), method="pbkdf2", salt_length=16
        )
        db.execute(
            "INSERT INTO users(username, hash) VALUES(?,?);", new_username, new_password
        )

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    owned_stocks = db.execute(
        "SELECT stock, sum(shares) as sum_of_shares FROM purchases WHERE user_id = ? GROUP BY user_id, stock HAVING sum_of_shares > 0",
        session["user_id"],
    )

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing stock symbol")

        if not request.form.get("shares"):
            return apology("Choose number of shares")

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        try:
            shares = int(shares)
        except ValueError:
            return apology("Invalid Shares")

        if shares < 1:
            return apology("Invalid Shares")

        symbols_dict = {d["stock"]: d["sum_of_shares"] for d in owned_stocks}

        if symbol not in symbols_dict:
            return apology("you do not own this stock")

        if symbols_dict[symbol] < shares:
            return apology("you do not own this many shares")

        query = lookup(symbol)

        cash_balance = db.execute(
            "SELECT cash FROM users WHERE id=?", session["user_id"]
        )

        db.execute(
            "INSERT INTO purchases(user_id, stock, price, shares) VALUES(?, ?, ?, ?)",
            session["user_id"],
            symbol,
            query["price"],
            -(shares),
        )

        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            (cash_balance[0]["cash"] + (query["price"] * shares)),
            session["user_id"],
        )

        flash("Sold!")

        return redirect("/")

    else:
        return render_template("sell.html", stocks=owned_stocks)


@app.route("/reset", methods=["GET", "POST"])
@login_required
def reset():
    """Reset password"""
    if request.method == "POST":
        if (
            not request.form.get("password")
            or not request.form.get("new_password")
            or not request.form.get("confirmation")
        ):
            return apology("Must fill the form")

        password = request.form.get("password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        row = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])

        if not check_password_hash(row[0]["hash"], password):
            return apology("INVALID CURRENT PASSWORD")

        if new_password != confirmation:
            return apology("New password and confirmation do not match")

        new_password = generate_password_hash(
            new_password, method="pbkdf2", salt_length=16
        )

        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?", new_password, session["user_id"]
        )

        flash("Password Changed!")

        return redirect("/")

    else:
        return render_template("reset.html")
