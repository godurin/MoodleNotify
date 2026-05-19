from app.storage.users import LINKED_USERS

from app.services.moodle_users import (
    find_user_by_username
)


def link_vk_user(vk_user_id, username):

    user = find_user_by_username(
        username
    )

    if not user:
        return None

    LINKED_USERS[vk_user_id] = {
        "moodle_id": user["id"],
        "fullname": user["fullname"],
        "username": user["username"]
    }

    return LINKED_USERS[vk_user_id]