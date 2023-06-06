from datetime import datetime, timedelta
from flask import request, jsonify, render_template, redirect, session, url_for, flash
from database import User, Point, db, PointItem
import requests


class PointService:
    def get_point_form(self):
        """
        Renders the form for adding a new point to the map.
        """
        if "phone" in session:
            return render_template("add_point_form.html")
        else:
            return redirect(url_for("home"))


    def get_add_point(self):
        """
        Adds a new point to the map with the latitude, longitude, and color specified in the form.
        """
        address_hebrew = request.form['address_hebrew']

        try:
            response = requests.post(url_for('geocode', _external=True), data={"address_hebrew": address_hebrew})
            data = response.json()

            latitude = data['latitude']
            longitude = data['longitude']
        except Exception as e:
            error_message = 'Unable to geocode the given address. Please try again with a different address.'
            return render_template("add_point_form.html", error_message=error_message)

        user_id = session['user_id']
        user = User.query.get(user_id)
        color = request.form.get('color')
        if color:
            color = color.lower()

        assist = 0
        if request.form.get('emergency') == '1':
            assist = 1

        # Check if the user has reached the maximum number of points
        max_points = 2
        if Point.query.filter_by(user_id=user.id).count() >= max_points:
            error_message = 'Max number of points reached.'
            return render_template("add_point_form.html", error_message=error_message)

        # Add the location in Hebrew to the new_point creation
        new_point = Point(user_id=user.id, latitude=latitude, longitude=longitude, color=color, assist=assist,
                          location_hebrew=address_hebrew)
        db.session.add(new_point)
        db.session.commit()

        return redirect(url_for('map'))

    def get_points(self):
        """
        Renders the points page, displaying all points made by the current user.
        """
        if "phone" in session:
            user_id = session["user_id"]
            user = User.query.get(user_id)
            if user:
                points = Point.query.filter_by(user_id=user.id).all()
                return render_template("points.html", points=points)
            else:
                return redirect(url_for("home"))
        else:
            return redirect(url_for("login"))

    def update_timestamp(self):
        """
        Updates the timestamp of the Point instance to the current time.
        """
        self.timestamp = datetime.utcnow()
        db.session.commit()

    def add_item_to_point(self):
        """
        Adds an item to a point and updates the point's assist value.
        """
        if 'user_id' not in session:
            return redirect(url_for("login"))

        if request.method == 'POST':
            point_id = request.form.get('point_id')
            item = request.form.get('item')
            assist = request.form.get('assist', 1)

            if point_id and item:
                point_item = PointItem(point_id=point_id, item=item)
                db.session.add(point_item)

                point = Point.query.get(point_id)
                point.assist = int(assist)

                db.session.commit()

        redirect_url = request.referrer or url_for('home')

        return redirect(redirect_url)
