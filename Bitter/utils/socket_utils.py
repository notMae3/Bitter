from .. import socket_rooms

def add_room_member(conversation_id, user_id, sid) -> None:
    if not conversation_id in socket_rooms:
        socket_rooms[conversation_id] = []
    
    socket_rooms[conversation_id].append({
        "user_id": user_id,
        "sid": sid
    })

def get_room_members(conversation_id) -> list:
    return socket_rooms.get(conversation_id, [])

def remove_room_member(sid) -> None:
    def remove_member() -> int | None:
        # remove this socket id from its socket room
        for conversation_id, room in socket_rooms.items():
            for member in room:
                if member["sid"] == sid:
                    room.remove(member)
                    return conversation_id

    # delete rooms with 0 members
    conversation_id = remove_member()
    if conversation_id and not len(socket_rooms[conversation_id]):
        socket_rooms.pop(conversation_id)

