import ydb
import ydb.iam

import os

import dotenv
import json

from utils import add_hash_ids, add_data_ids, get_items, get_data

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
    for k in [
        "time_zone",
        "birthday",
        "height",
        "weight",
        "target_weight",
        "male",
        "activity",
    ]:
        v = params.get(k) or "null"
        updates.append(f"{k}={v}")
    return execute(f"UPDATE user SET {','.join(updates)} WHERE id={user_id};")


def load_site_items(user_id, what):
    res = execute(f"SELECT item FROM site WHERE user_id={user_id} AND what={what};")
    res = [json.loads(q["item"]) for q in res]
    return {q["name"]: q for q in res}


def load_chat_items(user_id):
    res = execute(f"SELECT item FROM chat WHERE user_id={user_id};")
    return [json.loads(q["item"]) for q in res]


def select_site(user_id):
    res = execute(
        f"SELECT created, text, item, what FROM site WHERE user_id={user_id};"
    )
    for q in res:
        q["item"] = json.loads(q["item"])
    return res


def delete_site(id):
    return execute(f"DELETE FROM site WHERE id={id};")


def update_site(id, text, item):
    execute(f"UPDATE site SET text='{text}', item='{json.dumps(item)}' WHERE id={id};")
    return item


def insert_site(id, user_id, what, text, item, created):
    execute(
        f"INSERT INTO site (id, user_id, what, text, item, created) VALUES ({id}, {user_id}, {what}, '{text}', '{json.dumps(item, ensure_ascii=False)}', {created});"
    )
    return item


def where(ids):
    return f"id IN {ids}" if len(ids) > 1 else f"id={ids[0]}"


def load_data_ids(hash_ids):
    res = execute(f"SELECT * FROM hash WHERE {where(hash_ids)};")
    return {q["id"]: q["data_id"] for q in res}


def load_data_items(ids):
    res = execute(f"SELECT * FROM data WHERE {where(ids)};")
    return {q["id"]: json.loads(q["item"]) for q in res}


def add_data(user_id, what, items):
    if not items:
        return

    site_items = load_site_items(user_id, what)
    for item in items:
        name = item["name"]
        if name in site_items:
            item.update(site_items[name])
            item["data_id"] = None

    hash_ids = add_hash_ids(what, items)
    if not hash_ids:
        return

    data_ids = load_data_ids(hash_ids)
    if not data_ids:
        return

    data_ids = add_data_ids(items, data_ids)
    data_items = load_data_items(data_ids)
    if not data_items:
        return

    for item in items:
        data_id = item.pop("data_id", None)
        if data_id and data_id in data_items:
            item.update(data_items[data_id])


def get_item(user_id, what, text):
    name, items = get_items(text)
    add_data(user_id, what, items)
    return get_data(name, items)
