from .. import socket_rooms, socketio
from flask import request

def add_room_member(conversation_id : int, user_id : str, sid : str) -> None:
    """Adds a socket session-id to the room with the given conversation id

    Args:
        conversation_id (int): The conversation id of the room to add a new member to
        user_id (str): user id
        sid (str): socket session-id
    """
    if not conversation_id in socket_rooms:
        socket_rooms[conversation_id] = []
    
    socket_rooms[conversation_id].append({
        "user_id": user_id,
        "sid": sid
    })

def get_room_members(conversation_id) -> list:
    return socket_rooms.get(conversation_id, [])

def remove_room_member(sid) -> None:
    # go through each room and remove the member with the current sid once found. also delete the socket room if there
    # are no members left after removing the member with the current sid
    for conversation_id, room in socket_rooms.items():
        for member in room:
            if member["sid"] == sid:
                # remove the member with the current sid
                room.remove(member)

                # delete the room if it is now empty
                if not len(socket_rooms[conversation_id]):
                    socket_rooms.pop(conversation_id)
                
                return


def emit_error_response(message : str) -> None:
    socketio.emit(
        "error_response",
        message,
        to = request.sid
    )

def broadcast_message_to_room(message : str) -> bool:
    """Sent a message to every member of a socket-room. Return a bool whether the
    message recipient received the message

    Args:
        message (str): The message

    Returns:
        bool: Did the message recipient see the message?
    """
    recipient_saw_message = False

    # send the new message to each member of this conversation's socket_room
    conversation_id = message["conversation_id"]
    for room_member in get_room_members(conversation_id):
        unique_message = message.copy()
        
        # note that the message recipient saw the message if the message is being sent to them
        if unique_message["author_id"] != room_member["user_id"]:
            recipient_saw_message = True

        # add whether the message originated from the user the message is being sent to
        from_current_user = unique_message["author_id"] == room_member["user_id"]
        unique_message["origin"] = "sent" if from_current_user else "received"

        # send the new message
        socketio.emit(
            "new_message_created",
            unique_message,
            to = room_member["sid"]
        )
    
    return recipient_saw_message
