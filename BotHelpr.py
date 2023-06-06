from flask import Flask, request, render_template, jsonify
import openai
from SystemSettings import EnvironmentConfigurator
import sys
import os
import subprocess

configurator = EnvironmentConfigurator(sys, os, subprocess)
openai_api_key = configurator.get_openai_api_key()


def initialise():
    """
    Initializes the OpenAI API by setting the API key.
    """
    openai.api_key = openai_api_key


def load_bot_chat():
    """
    Handles the bot chat functionality.
    """
    if request.method == 'POST':
        message = request.form.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        if len(message) > 500:
            return jsonify({'error': 'Message is too long. It must be less than 500 characters.'}), 400

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly and knowledgeable AI assistant trained to help people manage diabetes. Give short, clear answers to questions and provide useful advice."
                },
                {
                    "role": "user",
                    "content": message,
                }
            ]
        )

        assistant_message = response['choices'][0]['message']['content']

        return jsonify({'message': assistant_message})
    else:
        return render_template('bot_helper.html')
