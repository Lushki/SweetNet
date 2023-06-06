import sys
import os
import subprocess
from SystemSettings import EnvironmentConfigurator
# config the env from the root directory requirements.txt
configurator = EnvironmentConfigurator(sys, os, subprocess)
configurator.config()

# my module imports
from time_datetime import time_delta, date_current_Get, time_current_Get
from database import initialize_database, User, Point, db, PointItem, Message, Chat
from map import get_map, get_geocode
from points import PointService
from HashPassword import PasswordManager
from chat import chat_route, on_join, on_leave, handle_message, general_chat_route, get_users_chats
from BotHelpr import initialise, load_bot_chat


from flask import Flask, request, render_template, url_for, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from functools import wraps
import openai
import requests


# flask
app = Flask(__name__)
# encryption
app.secret_key = "SUSYBAKA"
# session length - the time the session will last
app.permanent_session_lifetime = time_delta()
# database
initialize_database(app)
# socket
socketio = SocketIO(app)
# setup for the point service class
point_service = PointService()



def login_required(f):
    """
    Checks if logged in
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "phone" not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/manager")
@login_required
def manager():
    """
    Renders the manager page for user_id = 1.
    """
    if session['user_id'] == 1:
            users = User.query.all()
            points = Point.query.all()
            chats = Chat.query.all()
            return render_template('manager.html', users=users, points=points, chats=chats)
    else:
        redirect(url_for(""))


@app.route("/")
def base():
    """
    Renders the home page.
    """
    try:
        return redirect(url_for("home"))
    except:
        return render_template("home.html")


@app.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    """
    Renders the user profile page for a given user ID.
    """
    user = User.query.get(user_id)
    if user is None:
        return "User not found", 404
    else:
        return render_template('user.html', user=user)


@app.route("/home")
def home():
    """
    Renders the home page. If the user is already logged in, redirects them to the map page.
    """
    if "phone" in session:
        return redirect(url_for("map"))
    else:
        return render_template("home.html")


@app.route('/Info')
def info():
    """
    Renders the info page.
    """
    return render_template('info.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Logs a user in and saves their user ID to the session if their phone number and password match.
    """
    error_message = None

    if request.method == "POST":
        session.permanent = True
        phone = request.form["pn"]
        entered_password = request.form["ps"]

        if len(phone) != 10:
            error_message = "Phone number should be exactly 10 digits long."
            return render_template("login.html", error_message=error_message)

        user = User.query.filter_by(phone=phone).first()
        if user:
            if PasswordManager.verify_password(entered_password, user.salt, user.hashed_password):
                session["phone"] = phone
                session["user_id"] = user.id  # Save the user ID to the session

                points = Point.query.filter_by(user_id=user.id).all()
                for point in points:
                    point.update_timestamp()

                return redirect(url_for("map"))
            else:
                error_message = "Invalid password. Please try again."
        else:
            error_message = "User not found."
        return render_template("login.html", error_message=error_message)
    else:
        if "phone" in session:
            return redirect(url_for("map"))
        return render_template("login.html", error_message=error_message)


@app.route("/register", methods=["POST", "GET"])
def register():
    """
    Registers a new user.
    """
    if request.method == "POST":
        session.permanent = True
        password = request.form["ps"]
        password_confirmation = request.form["psC"]
        phone = request.form["ph"]
        first_name = request.form["fn"]
        last_name = request.form["ln"]

        if len(phone) != 10:
            error_message = 'Phone number must be 10 digits.'
            return render_template("register.html", error_message=error_message)

        if password != password_confirmation:
            error_message = 'Passwords do not match.'
            return render_template("register.html", error_message=error_message)

        salt, hashed_password = PasswordManager.hash_password(password)

        user = User(phone=phone, hashed_password=hashed_password, salt=salt, first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()
        session["phone"] = phone
        return render_template("map.html")
    else:
        if "phone" in session:
            return redirect(url_for("user"))
        return render_template("register.html")


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Renders the settings page, allowing the user to change their password but not their name.
    """
    if "phone" in session:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            phone = session['phone']
            user = User.query.filter_by(phone=phone).first()

            if PasswordManager.verify_password(current_password, user.salt, user.hashed_password):
                if new_password != confirm_password:
                    return render_template("settings.html", message="New password and confirm password do not match")

                salt, hashed_new_password = PasswordManager.hash_new_password(new_password)
                user.hashed_password = hashed_new_password
                user.salt = salt
                db.session.commit()

                return render_template("settings.html", message="Password successfully changed")
            else:
                return render_template("settings.html", message="Incorrect current password")

        else:
            return render_template("settings.html")
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """
    Logs the user out by removing their phone number from the session.
    """
    session.pop("phone", None)
    return redirect(url_for("home"))


@app.route('/delete_point/<int:point_id>', methods=['POST'])
@login_required
def delete_point(point_id):
    """
    Deletes a point with the given point ID.
    """
    point = Point.query.get(point_id)
    if point is not None:
        point.delete()
        return redirect(url_for('user_profile', user_id=session['user_id']))
    else:
        return "Point not found", 404


@app.route('/delete_item/<int:point_item_id>', methods=['POST'])
@login_required
def delete_item(point_item_id):
    """
    Deletes a point item with the given point item ID.
    """
    item = PointItem.query.get(point_item_id)
    if item is not None:
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('user_profile', user_id=session['user_id']))
    else:
        return "Item not found", 404


@app.route('/map')
@login_required
def map():
    """
    Renders the map page with all the points.
    """
    points = Point.query.all()
    for point in points:
        point.update_color()
    db.session.commit()
    return get_map()


@app.route('/add_point_form')
@login_required
def add_point_form():
    """
    Renders the form for adding a new point to the map.
    """
    return point_service.get_point_form()


@app.route('/add_point', methods=['POST'])
@login_required
def add_point():
    """
    Adds a new point to the map with the latitude, longitude, and color specified in the form.
    """
    return point_service.get_add_point()


@app.route('/geocode', methods=['POST'])
def geocode():
    """
    Geocodes an address and returns the latitude and longitude.
    """
    return get_geocode()


@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    """
    Adds an item to a point.
    """
    return point_service.add_item_to_point()


@app.route('/general_chat')
@login_required
def general_chat():
    """
    Renders the general chat page.
    """
    if "phone" in session:
        return general_chat_route()
    else:
        return redirect(url_for("login"))


@app.route('/chat/<int:partner_id>')
@login_required
def chat(partner_id):
    """
    Renders the chat page with the given partner ID.
    """
    return chat_route(partner_id)


@socketio.on('join')
def join(data):
    """
    Handles a user joining a chat room.
    """
    on_join(data)


@socketio.on('leave')
def leave(data):
    """
    Handles a user leaving a chat room.
    """
    on_leave(data)


@socketio.on('message')
def message(data):
    """
    Handles a new message in a chat room.
    """
    handle_message(data)


@app.route("/chat_list")
@login_required
def user_chats():
    """
    Renders a page displaying all chats a user has been a part of.
    """
    if "phone" in session:
        return get_users_chats()
    else:
        return redirect(url_for("login"))


@app.route("/bot_helper", methods=["GET", "POST"])
@login_required
def bot_chat():
    """
    Handles the interaction with the AI chatbot.
    """
    initialise()
    return load_bot_chat()


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")
