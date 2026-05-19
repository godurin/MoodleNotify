from app.moodle.client import MoodleClient


client = MoodleClient()


def find_user_by_username(username):

    data = client.call(
        "core_user_get_users",
        {
            "criteria[0][key]": "username",
            "criteria[0][value]": username
        }
    )

    users = data.get("users", [])

    if not users:
        return None

    return users[0]