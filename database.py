from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from SystemSettings import EnvironmentConfigurator
import sys
import os
import subprocess
db = SQLAlchemy()


class User(db.Model):
    """
    User Model class that maps to a User table in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    hashed_password = db.Column(db.LargeBinary, nullable=False)
    salt = db.Column(db.LargeBinary, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} - Phone: {self.phone}>"


class Point(db.Model):
    """
    Point Model class that maps to a Point table in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    color = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    assist = db.Column(db.Integer, nullable=False, default=0)  
    location_hebrew = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', backref=db.backref('points', lazy=True))

    def __repr__(self):
        return f"<Point {self.id} - Lat: {self.latitude}, Lng: {self.longitude}>"

    def delete(self):
        """
        Deletes the Point instance and associated PointItem instances.
        """
        # Delete all associated PointItem instances
        PointItem.query.filter_by(point_id=self.id).delete(synchronize_session=False)

        # Delete the Point instance itself
        db.session.delete(self)
        db.session.commit()

    def update_timestamp(self):
        """
        Updates the timestamp of the Point instance to the current time.
        """
        self.timestamp = datetime.utcnow()
        db.session.commit()

    def update_color(self):
        """
        Updates the color of the Point based on the timestamp.
        """
        # Get the current time
        now = datetime.utcnow()

        # Check if the timestamp is None
        if self.timestamp is None:
            self.timestamp = now  # or assign a different default value if needed

        # Calculate the time since the last update
        time_since_update = now - self.timestamp

        # Load settings
        env_configurator = EnvironmentConfigurator(sys, os, subprocess)
        settings = env_configurator.get_settings('Settings.txt')

        # Define time durations based on the settings
        one_week = timedelta(weeks=settings['orange'])
        one_month = timedelta(weeks=settings['red'])


        if time_since_update <= one_week:
            self.color = "green"
        elif one_week < time_since_update <= one_month:
            self.color = "orange"
        else:
            self.color = "red"


class PointItem(db.Model):
    """
    PointItem Model class that maps to a PointItem table in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey('point.id'), nullable=False)
    item = db.Column(db.String(200), nullable=False)

    point = db.relationship('Point', backref=db.backref('point_items', lazy=True))

    def __repr__(self):
        return f"<PointItem {self.id} - Item: {self.item} for Point: {self.point_id}>"

    @classmethod
    def delete_by_name_and_point(cls, item_name, point_id):
        """
        Deletes a PointItem by name and point_id.
        """
        cls.query.filter_by(item=item_name, point_id=point_id).delete()
        db.session.commit()


class Chat(db.Model):
    """
    Chat Model class that maps to a Chat table in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Chat with room ID: {self.room_id}>"


class Message(db.Model):
    """
    Message Model class that maps to a Message table in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Message from {self.sender.first_name} {self.sender.last_name} in {self.chat}>"


def initialize_database(app):
    """
    Initializes the database and SQLAlchemy for the Flask app.
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
