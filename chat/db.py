import json

import ydb.iam

import os

import dotenv
from utils import add_hash_ids, get_weights, add_data_ids, to_item, as_item, to_text
from datetime import datetime

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    # credentials=ydb.AuthTokenCredentials(os.getenv("IAM_TOKEN")),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

driver.wait(fail_fast=True, timeout=10)

pool = ydb.SessionPool(driver)

settings = ydb.BaseRequestSettings().with_timeout(10).with_operation_timeout(8)


def execute(yql):
    def wrapper(session):
        try:
            res = session.transaction().execute(yql, commit_tx=True, settings=settings)
            return res[0].rows if len(res) else []

        except Exception as e:
            print(e)
            return []

    print(yql)
    return pool.retry_operation_sync(wrapper)


def load_user(id):
    res = execute(f"SELECT * FROM user WHERE id={id};")
    return res and res[0]


def create_user(id):
    res = execute(f"INSERT INTO user (id, time_zone) VALUES ({id}, 3) RETURNING id;")
    return res and res[0]


def load_note(id):
    res = execute(f"SELECT * FROM note WHERE id={id};")
    return res and res[0]


def create_note(id, text, item, created, user_id, message_id, answer_id):
    values = f"({id}, '{text}', '{json.dumps(item, ensure_ascii=False)}', {created}, {user_id}, {message_id}, {answer_id})"
    execute(
        f"INSERT INTO note (id, text, item, created, user_id, message_id, answer_id) VALUES {values};"
    )


def update_note(id, text, item):
    execute(f'UPDATE note SET text="{text}", item="{json.dumps(item)}" WHERE id={id};')


def get_where(ids):
    return f"id IN {ids}" if len(ids) > 1 else f"id={ids[0]}"


def get_data_ids(hash_ids):
    res = execute(f"SELECT * FROM hash WHERE {get_where(hash_ids)};")
    return {q["id"]: q["data_id"] for q in res}


def get_data(data_ids):
    res = execute(f"SELECT * FROM data WHERE {get_where(data_ids)};")
    return {q["id"]: json.loads(q["data"]) for q in res}


def add_data(user_id, whats, items):
    if not items:
        return

    hash_ids = add_hash_ids(user_id, whats, items)
    data_ids = get_data_ids(hash_ids)
    if not data_ids:
        return

    weights = get_weights(whats, items, data_ids)
    data_ids = add_data_ids(weights, items)

    data = get_data(data_ids)
    if not data:
        return

    for item in items:
        if 'data_id' in item:
            item.update(data[item["data_id"]])


def get_item(user_id, created, text):
    item = to_item(created, text)
    add_data(user_id, item["whats"], item["items"])
    item["items"] = list(map(as_item, item["items"]))
    return item


def get_answer(user, created, text):
    created = datetime.fromtimestamp(created + user["time_zone"] * 3600)
    item = get_item(user["id"], created, text)
    answer = to_text(item)
    item['when'] = int(item['when'].timestamp())
    return answer, item
