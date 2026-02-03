from . import socketio, app
from .utils.socket_utils import add_room_member, remove_room_member, get_room_members
from .db_api import fetch_messages, create_message, fetch_shared_conversation_id, mark_message_seen
from flask import session, request
import asyncio, json

@socketio.on("connect")
def user_connect():
    pass

@socketio.on("disconnect")
def user_disconnect(_reason):
    remove_room_member(request.sid)

@socketio.on("register_for_realtime")
def register_for_realtime(recipient_username):
    async def respond():
        fetch_result = fetch_shared_conversation_id(recipient_username)
        if "error" in fetch_result:
            log_dict = json.dumps({"recipient_username": recipient_username})
            app.logger.info(f"400: Socket register for realtime - {log_dict} - {fetch_result['error']}")
            emit_error_response(fetch_result["error"])
            return

        user_id = session.get("user_id")    
        conversation_id = fetch_result["conversation_id"]

        add_room_member(conversation_id, user_id, request.sid)
    
    asyncio.run(respond())


@socketio.on("request_message_history")
def request_message_history(recipient_username, cursor):
    async def respond():
        messages = fetch_messages(str(recipient_username), str(cursor))
        socketio.emit("send_message_history", messages, to = request.sid)
    
    asyncio.run(respond())

@socketio.on("send_message")
def send_message(recipient_username, message_body):
    async def respond():
        # create the message
        message_result = create_message(recipient_username, message_body)
        if "error" in message_result:
            log_dict = json.dumps({"recipient_username": recipient_username, "message_body": message_body})
            app.logger.info(f"400: Socket chat send_message - {log_dict} - {message_result['error']}")
            emit_error_response(message_result["error"])
            return

        broadcast_message_to_room(message_result)
    
    asyncio.run(respond())

def emit_error_response(message):
    socketio.emit(
        "error_response",
        message,
        to = request.sid
    )

def broadcast_message_to_room(message):
    recipient_saw_message = False

    # send the new message to each member of this conversation's socket_room
    conversation_id = message["conversation_id"]
    for room_member in get_room_members(conversation_id):
        unique_message = message.copy()
        
        # if the message is being sent to the message recipient
        if unique_message["author_id"] != room_member["user_id"]:
            recipient_saw_message = True

        # add wether the message originated from the current user
        from_current_user = unique_message["author_id"] == room_member["user_id"]
        unique_message["origin"] = "sent" if from_current_user else "received"

        # send the new message
        socketio.emit(
            "new_message_created",
            unique_message,
            to = room_member["sid"]
        )
    
    if recipient_saw_message:
        mark_message_seen(message["message_id"])