import requests

from app.config import settings


class MoodleClient:

    def __init__(self):

        self.base_url = settings.MOODLE_URL
        self.token = settings.MOODLE_TOKEN

    def call(self, function_name, params=None):

        url = f"{self.base_url}/webservice/rest/server.php"

        payload = {
            "wstoken": self.token,
            "wsfunction": function_name,
            "moodlewsrestformat": "json"
        }

        if params:
            payload.update(params)

        response = requests.post(
            url,
            data=payload
        )

        return response.json()