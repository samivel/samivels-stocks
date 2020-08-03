import os


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")



# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")



@app.route("/")
@login_required
def index():
    return render_template('index.html')



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    # Find users current balance
    balance = db.execute('SELECT cash FROM users WHERE id = :id', id=session["user_id"])
    
    if request.method == "POST":

        # Assigns users input to variables
        symbol = lookup(request.form.get("symbol"))
        shares = request.form.get("shares")
        

        # Ensures valid symbol
        if not symbol:
            flash('Invalid symbol', 'danger')
            return redirect('/buy')
        # Ensures shares != 0
        elif shares == '':
            flash('Shares required', 'danger')
            return redirect('/buy')
        

        # Ensures user has enough money
        elif balance[0]['cash'] < (float(symbol["price"]) * int(shares)):
            flash("Insuffeciant funds", "warning")
            return redirect('/buy')
        
        # Add purchase log to 'transactions' table
        # Update users cash
        # redirect home
        else:
            db.execute("INSERT INTO transactions (user_id, symbol, quantity, price) VALUES(:user_id, :symbol, :quantity, :price)", user_id=session["user_id"], symbol=symbol['symbol'], quantity=int(shares), price=symbol["price"])
            db.execute("UPDATE users SET cash = cash - :price WHERE id = :user_id", price=(float(symbol["price"]) * int(shares)), user_id=session["user_id"])
            return redirect("/")

        

        



    else:
        # Shows buy page with users curent account balance
        return render_template('buy.html', balance=usd(balance[0]['cash']))


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        if request.args.get('success') == "yes":
            flash('Account created successfully', 'success')
            return render_template("login.html")
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

    # If method is post, search for stock and return the price
    if request.method == "POST":
        symbol = lookup(request.form.get("symbol"))

        # Ensures symbol exists and returns its info
        if symbol == None:
            flash('Symbol does not exist', 'danger')
            return redirect('/quote')
        else:
            return render_template("quoted.html", name=symbol['name'], symbol=symbol['symbol'], price=usd(symbol['price']))

    else:
        return render_template("/quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Gets values of register form and saves as variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks if user is in table already
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Ensures all fields have input
        if not username or not password or not confirmation:
            return apology('all fields are required', 403)

        # Ensures passwords match
        elif password != confirmation:
            flash('Passwords do not match!', 'danger')
            return redirect("/register")
        
        # Ensures user doesnt already exist
        elif len(rows) == 1:
            flash('Username already exists!', 'danger')
            return redirect("/register")

        # Hash password and insert user to db
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=generate_password_hash(password))
            return redirect('/login?success=yes')

            

    else:
        return render_template('register.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run()