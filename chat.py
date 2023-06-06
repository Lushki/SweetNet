from flask import session, redirect, url_for, render_template, request
from flask_socketio import join_room, leave_room, send, emit
from datetime import datetime
from database import User, Chat, db, Message
from time_datetime import time_current_Get


def general_chat_route():
    """
    Renders the general chat page.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('home')) 

    room_id = "general_chat_room"

    chat = Chat.query.filter_by(room_id=room_id).first()
    if not chat:
        # If chat doesn't exist, create it
        chat = Chat(room_id=room_id)
        db.session.add(chat)
        db.session.commit()

    return render_template('general_chat.html', user=user, user_id=user_id)


def chat_route(partner_id):
    """
    Renders the chat page for a specific partner.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    partner = User.query.get(partner_id)
    if not user or not partner:
        return redirect(url_for('home'))

    room_id = f"{user_id}-{partner_id}" if user_id < partner_id else f"{partner_id}-{user_id}"

    chat = Chat.query.filter_by(room_id=room_id).first()
    if not chat:
        # If chat doesn't exist, create it
        chat = Chat(room_id=room_id)
        db.session.add(chat)
        db.session.commit()

    return render_template('chat.html', user=user, partner=partner, user_id=user_id, partner_id=partner_id)


def on_join(data):
    """
    Handles the join event when a user joins a chat room.
    """
    username = data['username']
    room = data['room']
    join_room(room)

    # Retrieve the chat based on the room name
    chat = Chat.query.filter_by(room_id=room).first()

    if chat:
        # Get all the messages for this chat
        messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()

        # Format and send each message to the user
        for message in messages:
            sender = User.query.get(message.sender_id)
            message_content = f"<p><strong>{sender.first_name} {sender.last_name}: </strong>{message.content}<br><small>{message.timestamp}</small></p>"
            emit('message', message_content, room=request.sid)

    send(f'<br>{username} has entered the room.', room=room)


def on_leave(data):
    """
    Handles the leave event when a user leaves a chat room.
    """
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f'{username} has left the room.', room=room)


def handle_message(data):
    """
    Handles the message event when a user sends a message in a chat room.
    """
    timestamp_str = time_current_Get()
    # Convert the string to a datetime object
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')

    message_content = f"<p><strong>{data['username']}: </strong>{data['message']}<br><small>{timestamp_str}</small></p>"
    send(message_content, room=data['room'])

    # Retrieve the chat based on the room name
    chat = Chat.query.filter_by(room_id=data['room']).first()

    if chat:
        # Retrieve the sender based on the username
        sender = User.query.filter_by(first_name=data['username'].split()[0], last_name=data['username'].split()[1]).first()

        if sender:
            # Create a new message object
            message = Message(content=data['message'], timestamp=timestamp, sender_id=sender.id, chat_id=chat.id)

            # Add the message to the session and commit
            db.session.add(message)
            db.session.commit()


def get_users_chats():
    """
    Renders a page displaying all chats a user has been a part of.
    """
    if "user_id" in session:
        user_id = session["user_id"]
        # Fetch all chats where user_id is a participant
        user_chats = Chat.query.filter(Chat.room_id.contains(str(user_id))).all()

        chats = []
        for chat in user_chats:
            if chat.room_id == 'general_chat_room':
                # If it's the general chat, just add the chat to the list without users
                chats.append({
                    'chat': chat,
                    'users': ['General Chat']
                })
            else:
                # assuming the room_id is a string composed of two user_ids with a '-' separator
                user_ids = [int(id) for id in chat.room_id.split('-') if int(id) != user_id]
                users = [User.query.get(id) for id in user_ids]
                # Add chat and corresponding users to the list
                chats.append({
                    'chat': chat,
                    'users': users
                })
        return render_template("chat_list.html", chats=chats)
    else:
        return redirect(url_for("login"))
