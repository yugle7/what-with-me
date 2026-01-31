import json
import db
import tg

from utils import get_id


def handler(event, context):
    try:
        res = handle(event)
    except Exception as err:
        print(err)
        res = str(err)
    return {"statusCode": 200, "body": res}


def handle(event):
    body = json.loads(event["body"])
    print("body:", body)

    user_id = tg.get_user_id(body)
    if not user_id:
        return "not user"

    user = db.load_user(user_id) or db.create_user(user_id)
    print("user:", user)

    message = body.get("message") or body.get("edited_message")
    if not message:
        return "no message"

    if "text" not in message:
        return "no text"

    text = message["text"]
    if text == "/start":
        tg.send_message(user, "Привет!")
        return "start"

    edited = "edit_date" in message
    message_id = message["message_id"]
    created = message["date"]

    id = get_id(user_id, message_id)
    note = edited and db.load_note(id)
    print("note:", note)

    if note and note["text"] == text:
        return "the same text"

    answer = db.get_answer(user, created, text)
    print("answer:", answer)
    if not note:
        answer_id = tg.send_message(user_id, answer)
        db.create_note(id, text, created, user_id, message_id, answer_id)
        return "note created"

    db.update_note(id, text)
    answer_id = note["answer_id"]
    tg.edit_message(user_id, answer_id, answer)
    return "note edited"


if __name__ == "__main__":
    body = {
        "update_id": 204610942,
        "message": {
            "message_id": 777,
            "from": {
                "id": 164671585,
                "is_bot": False,
                "first_name": "Gleb",
                "last_name": "Yuzhakov",
                "username": "yugle7",
                "language_code": "ru",
            },
            "chat": {
                "id": 164671585,
                "first_name": "Gleb",
                "last_name": "Yuzhakov",
                "username": "yugle7",
                "type": "private",
            },
            "date": 1769629716,
            "text": "15 минут назад съел\nщи 200 г\nхлеб 2 \nсметану 2",
        },
    }
    event = {"body": json.dumps(body)}
    handler(event, None)
