import csv
from cs50 import SQL
from datetime import datetime, date
import sqlite3
import pytz
import io
import qrcode
import requests
import urllib
import uuid
import re
import base64

from flask import flash, redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

#decorate route to restrict access to service client
def service_client_only(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if session.get("username") != "Service Client":
            flash("Access denied: You do not have permission to view this page.", "warning")
            return redirect("/")  # Redirect unauthorized users
        return f(*args, **kwargs)
    return decorated_function
    

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def is_valid_email(email):
    # Define a regular expression for a valid email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # Return True if the email matches the regex, else False
    return re.match(email_regex, email) is not None


def generator_qr(number_sender,number_receiver):
    #setting time zone
    belgium_tz = pytz.timezone('Europe/Brussels')

    #setting db
    db = SQL("sqlite:///sorted.db")

    #defining the current date
    
    dt_now_belgium = datetime.now(belgium_tz)
    only_date_belgium = dt_now_belgium.date()


    # Check if there is already an order for the current date and sort the last order_number
    row = db.execute("SELECT order_number FROM orders WHERE order_date = ? ORDER BY order_number DESC LIMIT 1", (only_date_belgium,))
    
    #initialize or increment number order

    if row:
        #if a number exist for today increment it
        number_order = int(row[0]["order_number"]) + 1
    else:
        #if no order number for today start at 1
        number_order = 1

    #generate qr code (with only the date not the time)
    order_info = str(only_date_belgium) + "#" + str(number_order) + "#" + str(number_sender) + "#" + str(number_receiver)
    order_qr = qrcode.make(order_info)

    #convert the image to binary (BytesIO)
    img_byte_array = io.BytesIO()
    order_qr.save(img_byte_array, format ="PNG")
    img_data = img_byte_array.getvalue()




     
    return number_order, only_date_belgium, dt_now_belgium, order_info, img_data, number_sender, number_receiver