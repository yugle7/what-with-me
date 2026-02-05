import os

from cityhash import CityHash64

import db
import dotenv

dotenv.load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")


def handle(params):
    action = params.get("action")
    if action not in ("create", "update", "remove", "load", "write", "read"):
        return "unknown action"

    user_id = params.get("user_id")

    if action == "read":
        return db.select_user(user_id)

    if action == "write":
        return db.update_user(user_id, params)

    if action == "load":
        return db.select_user_data(user_id)

    created = int(params.get("created"))
    id = CityHash64(f"{user_id} {created}")

    if action == "remove":
        return db.delete_user_data(id)

    text = params.get("text")
    what = int(params.get("what"))
    item = db.main(user_id, what, text)

    if action == "update":
        return db.update_user_data(id, text, item)

    if action == "create":
        return db.insert_user_data(id, user_id, text, item, created)

    return action


def handler(event, context):
    params = event["queryStringParameters"]

    # secret_key = hmac.new(
    #     key=b'WebAppData',
    #     msg=TG_BOT_TOKEN.encode(),
    #     digestmod=hashlib.sha256
    # ).digest()

    # calculated_hash = hmac.new(
    #     key=secret_key,
    #     msg=params['checkDataString'].encode(),
    #     digestmod=hashlib.sha256
    # ).hexdigest()

    # if calculated_hash != params['hash']:
    #     return {'statusCode': 200, 'body': []}

    print(params)
    return {"statusCode": 200, "body": handle(params)}


if __name__ == "__main__":
    event = {
        "queryStringParameters": {
            "user_id": 164671585,
            "action": "update",
            "created": 1769629716001,
            "what": 0,
            "text": "Мой завтрак\nборщ со свининой 10000 г\nхлеб 200 г \nсметана 200 гр",
        }
    }
    handler(event, None)
