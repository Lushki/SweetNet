from flask import request, jsonify, render_template, redirect, session, url_for
from database import User, Point, db
import requests
import sys
import os
import subprocess
from SystemSettings import EnvironmentConfigurator

configurator = EnvironmentConfigurator(sys, os, subprocess)
google_maps_api_key = configurator.get_google_maps_api_key()


def get_map():
    """
    Renders the map page, displaying all registered points.
    """
    if "phone" in session:
        phone = session["phone"]
        points = Point.query.all()
        return render_template("map.html", points=points, google_maps_api_key=google_maps_api_key)
    else:
        return redirect(url_for("home"))


def get_geocode():
    """
    Geocodes a given address in Hebrew and returns its latitude and longitude.
    """
    address_hebrew = request.form['address_hebrew']
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address_hebrew,
        "key": google_maps_api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == "OK":
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return jsonify({"latitude": lat, "longitude": lng})
