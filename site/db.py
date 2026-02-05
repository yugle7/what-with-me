import ydb
import ydb.iam

import os

import dotenv
import json

from utils import add_hash_ids, add_data_ids, to_item, as_item

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    # credentials=ydb.AuthTokenCredentials(os.getenv("IAM_TOKEN")),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

driver.wait(fail_fast=True, timeout=5)

pool = ydb.SessionPool(driver)

settings = ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)


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


def select_user(user_id):
    res = execute(f"SELECT * FROM user WHERE id={user_id};")
    return res[0] if res else {}


def update_user(user_id, params):
    updates = []
    for k in ["time_zone", "birthday", "height", "weight", "target_weight", "male"]:
        v = params.get(k) or "null"
        updates.append(f"{k}={v}")
    return execute(f"UPDATE user SET {','.join(updates)} WHERE id={user_id};")


def select_user_what_data(user_id, what):
    res = execute(
        f"SELECT item FROM user_data WHERE user_id={user_id} AND what={what};"
    )
    res = [json.loads(q["item"]) for q in res]
    return {q["name"]: q for q in res}


def select_user_data(user_id):
    res = execute(
        f"SELECT created, text, item, what FROM user_data WHERE user_id={user_id};"
    )
    for q in res:
        q["item"] = json.loads(q["item"])
    return res


def delete_user_data(id):
    return execute(f"DELETE FROM user_data WHERE id={id};")


def update_user_data(id, text, item):
    execute(f"UPDATE user_data SET text='{text}', item='{json.dumps(item)}' WHERE id={id};")
    return item


def insert_user_data(id, user_id, what, text, item, created):
    execute(
        f"INSERT INTO user_data (id, user_id, what, text, item, created) VALUES ({id}, {user_id}, {what}, '{text}', '{json.dumps(item, ensure_ascii=False)}', {created});"
    )
    return item


def where(ids):
    return f"id IN {ids}" if len(ids) > 1 else f"id={ids[0]}"


def select_data_ids(hash_ids):
    res = execute(f"SELECT * FROM hash WHERE {where(hash_ids)};")
    return {q["id"]: q["data_id"] for q in res}


def select_data(ids):
    res = execute(f"SELECT * FROM data WHERE {where(ids)};")
    return {q["id"]: json.loads(q["data"]) for q in res}


def add_data(user_id, what, items):
    if not items:
        return

    data = select_user_what_data(user_id, what)
    for item in items:
        if item['name'] in data:
            item['data'] = data[item['name']]

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
            item['data'] = data[item["data_id"]]


def main(user_id, what, text):
    item = to_item(text)
    add_data(user_id, what, item["items"])
    item["items"] = list(map(as_item, item["items"]))
    return item
