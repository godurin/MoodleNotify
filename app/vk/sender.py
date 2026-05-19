import random
import vk_api

from app.config import settings


vk_session = vk_api.VkApi(
    token=settings.VK_TOKEN
)

vk = vk_session.get_api()


def send_message(user_id, message):

    try:

        response = vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 1000000)
        )

        print("VK RESPONSE:", response)

    except Exception as e:

        print("VK ERROR:")
        print(e)