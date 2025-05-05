import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, make_response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime, timedelta
from weasyprint import HTML
import base64


from helpers import apology, is_valid_email, login_required, generator_qr,service_client_only

#config the app

app = Flask(__name__)

#config the session to store data serverside (instead of cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#config db

db = SQL("sqlite:///sorted.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
@login_required
def index():
    # Check if the user is "Service Client"
    if session.get("username") == "Service Client":
        return render_template("scan.html")
    else:
        return render_template("index.html")
    
@app.route("/sending", methods=["GET"])
@login_required
def sending():
    # Restrict access if the user is "Service Client"
    if session.get("username") == "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/scan")  # Redirect unauthorized users
    exchanges = []
    user_id = session["user_id"]
    id_client = db.execute ("SELECT us_id_client FROM users WHERE us_id_users = ?", (user_id))
    id_client = id_client[0]["us_id_client"]
    try:
        #Querry db for all order with id_client as sender
        rows = db.execute("""SELECT name, order_datetime, processing, order_number FROM orders
                        JOIN client ON client.id_client = orders.receiver  
                        WHERE sender = ? ORDER BY order_datetime DESC""", id_client)
        #for each querry's row put the value in a list 
        for row in rows:
            receiver = row["name"]
            order_datetime = row["order_datetime"]
            processing = row["processing"]
            order_number = row["order_number"]

            exchanges.append({"receiver" : receiver, "order_datetime" : order_datetime, "processing" : processing, "order_number" : order_number })
        return render_template("sending.html", exchanges = exchanges)
    except:
        return apology ("No valid client")
    
@app.route("/reception", methods=["GET"])
@login_required
def reception():
    # Restrict access if the user is "Service Client"
    if session.get("username") == "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/scan")  # Redirect unauthorized users
    exchanges = []
    user_id = session["user_id"]
    id_client = db.execute ("SELECT us_id_client FROM users WHERE us_id_users = ?", (user_id))
    id_client = id_client[0]["us_id_client"]
    #Querry db for all order with id_client as receiver
    try:
        rows = db.execute("""SELECT name, order_datetime, processing, order_number FROM orders 
                          JOIN client ON client.id_client = orders.sender
                          WHERE receiver = ? ORDER BY order_datetime DESC""", id_client)
        #for each querry's row put the value in a list 
        for row in rows:
            sender = row["name"]
            order_datetime = row["order_datetime"]
            processing = row["processing"]
            order_number = row["order_number"]

            exchanges.append({"sender" : sender, "order_datetime" : order_datetime, "processing" : processing, "order_number" : order_number })
        return render_template("reception.html", exchanges = exchanges)
    except:
        return apology ("No valid client")
    
@app.route("/history", methods=["GET"])
@login_required
def history():
    # Restrict access if the user is "Service Client"
    if session.get("username") == "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/scan")  # Redirect unauthorized users
    exchanges = []
    user_id = session["user_id"]
    id_client = db.execute ("SELECT us_id_client FROM users WHERE us_id_users = ?", (user_id))
    id_client = id_client[0]["us_id_client"]
    #Querry db for all order with id_client as receiver and sender
    try:
        rows = db.execute("""SELECT r.name as receiver, s.name as sender, order_datetime, processing, order_number 
                        FROM orders
                        JOIN client r ON r.id_client = orders.receiver 
                        JOIN client s ON s.id_client = orders.sender
                        WHERE receiver = ? OR sender = ? ORDER BY order_datetime DESC""", id_client, id_client)
        #for each querry's row put the value in a list
        for row in rows:
            sender = row["sender"]
            receiver = row["receiver"]
            order_datetime = row["order_datetime"]
            processing = row["processing"]
            order_number = row["order_number"]

            exchanges.append({"sender" : sender, "receiver" : receiver, "order_datetime" : order_datetime, "processing" : processing, "order_number" : order_number })
        return render_template("history.html", exchanges = exchanges)
    except:
        return apology ("No valid client")

@app.route("/scan", methods=["GET", "POST"])
@login_required
@service_client_only
def scan():
    # Restrict access if the user is "Service Client"
    if session.get("username") != "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/")  # Redirect unauthorized users
    if request.method == "POST":
        #ensure qr_code was submited
        if not request.form.get("qrcode_scanning"):
            return apology("Scan QR-code")
        #querry db and update the orders status (processing)
        try:
            qr_code = request.form.get("qrcode_scanning")
            rows = db.execute("SELECT processing FROM orders WHERE order_info = ?", qr_code)
            #ensure there is only one qr_code who's matching
            if len(rows) != 1:
                flash("invalid Qr_code", "danger")
                return render_template("scan.html")
            #update processing value if it's value was 0
            if rows[0]["processing"] == 0:
                db.execute("UPDATE orders SET processing = 1 WHERE order_info = ?", qr_code)
                flash("QR-code scanned successfully", 'success')
            else:
                flash("QR-code already scanned", "danger")
                return render_template("scan.html")
            
            return render_template("scan.html")
        except:
            return apology ("Invalid QR-code")     

    else:
        return render_template("scan.html")
    
@app.route("/research", methods=["GET", "POST"])
@login_required
@service_client_only
def research():
    # Restrict access if the user is "Service Client"
    if session.get("username") != "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/")  # Redirect unauthorized users
    if request.method == "GET":
         #create a datalist for the input of pharmacie
        client_names = []
        rows = db.execute("SELECT name FROM client")
        for row in rows:
            name = row["name"]
            client_names.append(name)       
        return render_template("research.html",client_names = client_names)
    
    else:
        client_name = request.form.get ("name")
        try:
            client_number = db.execute("SELECT id_client FROM client WHERE number_client = ?",request.form.get ("number_client"))
        except:
            return apology("This client number does not exist")
        exchange_date = request.form.get("exchange_date")
        research_order = []
        # Start building the query
        query = """SELECT order_date, s.name as sender, r.name as receiver, processing, order_number 
                FROM orders
                JOIN client r ON r.id_client = orders.receiver 
                JOIN client s ON s.id_client = orders.sender
                WHERE 1=1"""
        
        query_values = []

        # Add condition for exchange_date if provided
        if exchange_date:
            query += " AND order_date = ?"
            query_values.append(exchange_date)

        # Add condition for client_number if provided
        if client_number:
            query += " AND (sender = ? OR receiver = ?)"
            query_values.append(client_number)
            query_values.append(client_number)


        # Add condition for client_name if provided
        if client_name:
            query += " AND (r.name = ? OR s.name = ?)"
            query_values.append(client_name)
            query_values.append(client_name)
        query += " ORDER BY order_datetime DESC "
        print(query, query_values)
        try:
            #SQLITE have issue with passing list or tupple as a value in sql query so we need to unpack them
            # Unpack the query_values list so each item is passed as an individual argument with *query_values which will select each element 1 by 1
            rows = db.execute(query, *query_values)
            for row in rows:
                date = row ["order_date"]
                sender = row["sender"]
                receiver = row["receiver"]
                processing = row["processing"]
                order_number = row["order_number"]

                research_order.append({"order_date": date, "sender": sender, "receiver": receiver, "processing": processing, "order_number": order_number})
                
            return render_template("/research_table.html", research_order = research_order)
        except Exception as e:
            print(f"Error during insert: {e}")
            return apology("can't check db in db")
        
        
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure user_mail was submitted
        if not request.form.get("user_mail"):
            return apology("must provide user_mail", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for user_mail
        rows = db.execute(
            "SELECT * FROM users WHERE us_user_mail = ?", request.form.get("user_mail")
        )

        # Check if the user exists
        if not rows:
            flash("Invalid user mail", "danger")
            return render_template("login.html")
        
        # Check if the account is locked
        if rows[0]['lockout_until'] and datetime.now() < datetime.strptime(rows[0]['lockout_until'], "%Y-%m-%d %H:%M:%S"):
            flash("Account locked. Try again later.", "danger")
            return render_template("login.html")
        
        # Ensure  password is correct
        if check_password_hash(rows[0]["us_hash"], request.form.get("password")):
             # Successful login: reset failed_attempts and lockout_until
            db.execute("UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE us_id_users = ?", (rows[0]['us_id_users'],))
            # Remember which user has logged in
            session["user_id"] = rows[0]["us_id_users"]
            session["username"] = rows[0]["us_name"]
            return redirect("/")

        #invalid password
        else:
            failed_attempts = rows[0]['failed_attempts'] + 1
            if failed_attempts >= 3:
                # Lock the account for 5 minutes (or desired duration)
                lockout_until = datetime.now() + timedelta(minutes=5)
                my_list = [failed_attempts, lockout_until.strftime("%Y-%m-%d %H:%M:%S"), rows[0]['us_id_users']]
                db.execute("UPDATE users SET failed_attempts = ?, lockout_until = ? WHERE us_id_users = ?",
                           *my_list)
                flash("Too many failed attempts. Account locked for 5 minutes.", "danger")
            else:
                # Create a list to put inside the querry (i've still the same issue with the number of placeholders and the values so i've to put them in a list)
                my_list = [failed_attempts, rows[0]['us_id_users'] ]
                # Increment failed_attempts
                print(failed_attempts, rows[0]['us_id_users'])
                db.execute("UPDATE users SET failed_attempts = ? WHERE us_id_users = ?", *my_list)
                flash("Invalid username or password", "danger")
            return render_template("login.html")
        

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

    # user route via POST
    if request.method == "POST":

        # full submission
        mail = request.form.get("user_mail") # Todo mettre en lower case pour la case sensitive car pour sqlite QsQ est différent de qsq
        password = request.form.get("password")
        confpass = request.form.get("confirmation")
        hashpass = generate_password_hash(password)
        name = request.form.get("pharmacie")
        number_client = int(request.form.get("number_client")) 

        # ensure user_mail was submitted
        if not request.form.get("user_mail"):
            return apology("Enter an email")
        
        # ensure name was submitted
        elif not request.form.get("pharmacie"):
            return apology("Enter a pharmacy name")
        
        #ensure number_client was submited
        elif not request.form.get("number_client"):
            return apology("Enter a customer number")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("No password")

        # ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("No confirmation")

        # ensure confirmation match with password
        elif password != confpass:
            return apology("password and confirmation don't match")
        
        elif  not is_valid_email(mail):
            return apology("invalid e-mail ")

        #ensure pharmacie exist and id match with pharmacie
        try:
            rows = db.execute("SELECT number_client, id_client FROM client WHERE name = ?", name)
            print (rows)
            #check if the query returned any rows
            if len(rows) == 0:
                return apology ("The pharmacy name does not match")
            
            #extract the id_client from the first row
            matching_number = int(rows[0]["number_client"])
            matching_id = int(rows[0]["id_client"])
            print(matching_id)

            #ensure the id submited matches the correspond id_client 
            if matching_number != number_client:
                return apology("The customer number does not match")

        except Exception as e:
            print(f"Error during insert: {e}")
            return apology("Unexpected error checking pharmacy name")


        # querry db
        try:
            db.execute("INSERT INTO users (us_user_mail, us_hash, us_id_client, us_name) VALUES (?, ?, ?, ?)", mail, hashpass, matching_id, name)     
            rows = db.execute("SELECT us_id_users FROM users WHERE us_user_mail = ?", mail)
            
            if rows:
                new_id = rows[0]
                session["user_id"] = new_id["us_id_users"]
                return redirect("/")
            else:
                return apology("id_user not found")
        except Exception as e:
            print(f"Error during insert: {e}")
            return apology("user_mail or password invalid")

    # user route via get
    elif request.method == "GET":
        #create a datalist for the input of pharmacie
        client_names = []
        rows = db.execute("SELECT name FROM client")
        for row in rows:
            name = row["name"]
            client_names.append(name)       
        return render_template("register.html",client_names = client_names)
    
@app.route("/exchange", methods=["POST", "GET"])
@login_required
def exchange():
    # Restrict access if the user is "Service Client"
    if session.get("username") == "Service Client":
        flash("You do not have permission to access this page.","danger")
        return redirect("/scan")  # Redirect unauthorized users
    
    if request.method == "GET":  
        #create a datalist for the input of pharmacie
        client_names = []
        rows = db.execute("SELECT name FROM client")
        for row in rows:
            name = row["name"]
            client_names.append(name)       
        return render_template("exchange.html",client_names = client_names)
    
    elif request.method == "POST":
        recipient = request.form.get("recipient")
        sender = session["user_id"]
        #querry db for info about recipent and sender
        try:
            recipient_info = db.execute("""SELECT name, address, GROUP_CONCAT(number_round, ' | ') AS rounds
                                    FROM client
                                    LEFT OUTER JOIN delivery ON delivery.id_client = client.id_client
                                    LEFT OUTER JOIN round ON delivery.id_round = round.id_round
                                    WHERE client.name = ?
                                    GROUP BY name, address;""",recipient)
            sender_info = db.execute("""SELECT name,address
                                     FROM client
                                     JOIN users ON users.us_id_client = client.id_client
                                     WHERE users.us_id_users = ?
                                     """,(sender,))
            number_sender = db.execute ("SELECT us_id_client FROM users WHERE us_id_users = ?", (sender))
            number_receiver = db.execute ("SELECT id_client FROM client WHERE name = ?", recipient)
            # Extract actual values from the query results 
            number_sender = number_sender[0]["us_id_client"]
            number_receiver = number_receiver[0]["id_client"]

        except:
            return apology("recipient doesn't exist")

        # Generate QR code and number order
        number_order, only_date_belgium, dt_now_belgium, order_info, img_data, number_sender, number_receiver = generator_qr(number_sender, number_receiver)

        # Directly use number_sender and number_receiver as they are integers
        number_sender_id = number_sender if isinstance(number_sender, int) else number_sender[0]["us_id_client"]
        number_receiver_id = number_receiver if isinstance(number_receiver, int) else number_receiver[0]["id_client"]

        # Ensure both sender and receiver IDs are valid
        if number_sender_id is None or number_receiver_id is None:
            return apology("Invalid sender or receiver ID")

        try:
            # Insert data into the orders table
            db.execute(
                "INSERT INTO orders (order_number, order_date, order_datetime, order_info, sender, receiver) VALUES ( ?, ?, ?, ?, ?, ?)",
                number_order, only_date_belgium, dt_now_belgium, order_info, number_sender, number_receiver
            )
            
        
        except Exception as e:
            print(number_sender, number_receiver)
            print(f"Error inserting into database: {e}")
            return apology("can't insert info_qr in db")
        
        # Convert the binary (BLOB) data to base64 for embedding in html
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        
        #render ab HTML template
        html = render_template("pdf_template.html", recipient = recipient, recipient_info = recipient_info, sender_info = sender_info, img_base64 = img_base64 )

        #convert HTML to PDF
        pdf = HTML(string=html,base_url=request.host_url).write_pdf()
        
        #create a response object with the pdf
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = 'inline; filename = "form_data.pdf"' 
        
        return response
    
    return redirect ("/")



#ToDo
#full check les options client/service  bug recherche avec le n°pharmacie
#ajouter commande recues
#check les dernieres differences fp50t22
#faire une fonction pour generer une datalist
#possibilité d'annuler l'echange si time < 10min


