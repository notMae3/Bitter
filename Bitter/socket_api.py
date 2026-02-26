from . import socketio, app
from .utils.misc_utils import login_required, use_only_expected_kwargs
from .utils.socket_utils import (
    add_room_member,
    remove_room_member,
    emit_error_response,
    broadcast_message_to_room
)
from .utils.db_utils import (
    fetch_shared_conversation_id,
    mark_message_as_seen,
    fetch_messages,
    create_message
)
from flask import request
import asyncio, json

@socketio.on("disconnect")
def user_disconnect(_reason) -> None:
    remove_room_member(request.sid)

@socketio.on("register_for_realtime")
@login_required
def register_for_realtime(recipient_username : str, current_user : dict) -> None:
    # ensure proper param types
    recipient_username = str(recipient_username)

    async def respond() -> None:
        shared_conversation = fetch_shared_conversation_id(recipient_username)
        if "error" in shared_conversation:
            log_dict = json.dumps({"recipient_username": recipient_username})
            app.logger.info(f"400: Socket register for realtime - {log_dict} - {shared_conversation['error']}")

            emit_error_response(shared_conversation["error"])
            return

        user_id : int = current_user["user_id"]
        conversation_id = shared_conversation["conversation_id"]

        add_room_member(conversation_id, user_id, request.sid)
    
    asyncio.run(respond())

@socketio.on("request_message_history")
@login_required
@use_only_expected_kwargs
def request_message_history(recipient_username : str, cursor : str | int) -> None:
    # ensure proper param types
    recipient_username = str(recipient_username)
    cursor = str(cursor)

    async def respond() -> None:
        messages = fetch_messages(recipient_username, cursor)
        if "error" in messages:
            log_dict = json.dumps({"recipient_username": recipient_username, "cursor": cursor})
            app.logger.info(f"400: Socket chat request_message_history - {log_dict} - {messages['error']}")

            emit_error_response(messages["error"])
            return

        socketio.emit("send_message_history", messages, to = request.sid)
    
    asyncio.run(respond())

@socketio.on("send_message")
@login_required
@use_only_expected_kwargs
def send_message(recipient_username : str, message_body : str) -> None:
    # ensure proper param types
    recipient_username = str(recipient_username)
    message_body = str(message_body)

    async def respond() -> None:
        new_message = create_message(recipient_username, message_body)
        if "error" in new_message:
            log_dict = json.dumps({"recipient_username": recipient_username, "message_body": message_body})
            app.logger.info(f"400: Socket chat send_message - {log_dict} - {new_message['error']}")

            emit_error_response(new_message["error"])
            return

        recipient_received = broadcast_message_to_room(new_message)
        if recipient_received:
            mark_message_as_seen(new_message["message_id"])
    
    asyncio.run(respond())
