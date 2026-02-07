import json

import ydb.iam

import os

import dotenv
from utils import add_hash_ids, add_data_ids, to_item, as_item, to_text, get_what
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


def select_user(id):
    res = execute(f"SELECT * FROM user WHERE id={id};")
    return res and res[0]


def insert_user(id):
    res = execute(f"INSERT INTO user (id, time_zone) VALUES ({id}, 3) RETURNING id;")
    return res and res[0]


def select_note(id):
    res = execute(f"SELECT * FROM note WHERE id={id};")
    return res and res[0]


def insert_note(id, text, item, created, user_id, message_id, answer_id):
    values = f"({id}, '{text}', '{json.dumps(item, ensure_ascii=False)}', {created}, {user_id}, {message_id}, {answer_id})"
    execute(
        f"INSERT INTO note (id, text, item, created, user_id, message_id, answer_id) VALUES {values};"
    )


def update_note(id, text, item):
    execute(f'UPDATE note SET text="{text}", item="{json.dumps(item)}" WHERE id={id};')


def where(ids):
    return f"id IN {ids}" if len(ids) > 1 else f"id={ids[0]}"


def select_data_ids(hash_ids):
    res = execute(f"SELECT * FROM hash WHERE {where(hash_ids)};")
    return {q["id"]: q["data_id"] for q in res}


def select_data(data_ids):
    res = execute(f"SELECT * FROM data WHERE {where(data_ids)};")
    return {q["id"]: json.loads(q["item"]) for q in res}


def select_user_what_data(user_id, what):
    res = execute(
        f"SELECT item FROM user_data WHERE user_id={user_id} AND what={what};"
    )
    res = [json.loads(q["item"]) for q in res]
    return {q["name"]: q for q in res}


def add_data(user_id, what, items):
    if not items:
        return

    data = select_user_what_data(user_id, what)
    for item in items:
        if item["name"] in data:
            item["data"] = data[item["name"]]

    hash_ids = add_hash_ids(what, items)
    if not hash_ids:
        return

    data_ids = select_data_ids(hash_ids)
    if not data_ids:
        return

    data_ids = add_data_ids(items, data_ids)
    data = select_data(data_ids)
    if not data:
        return

    for item in items:
        if "data_id" in item:
            item["data"] = data[item["data_id"]]


def get_item(user_id, created, text):
    item = to_item(created, text)
    what = get_what(item["items"])
    add_data(user_id, what, item["items"])
    item["items"] = list(map(as_item, item["items"]))
    return item


def get_answer(user, created, text):
    created = datetime.fromtimestamp(created + user["time_zone"] * 3600)
    item = get_item(user["id"], created, text)
    answer = to_text(item)
    item["when"] = int(item["when"].timestamp())
    return answer, item
