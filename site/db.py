import ydb
import ydb.iam

from cityhash import CityHash64

import os

import dotenv
import json

from utils import add_hash_ids, get_weights, add_data_ids, to_item, as_item

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    credentials=ydb.AuthTokenCredentials(os.getenv('IAM_TOKEN')),
    # credentials=ydb.iam.MetadataUrlCredentials(),
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


def read(user_id):
    res = execute(f"SELECT * FROM user WHERE id={user_id};")
    return res[0] if res else {}


def write(user_id, params):
    updates = []
    for k in ["time_zone", "birthday", "height", "weight", "target_weight", "male"]:
        v = params.get(k) or "null"
        updates.append(f"{k}={v}")
    return execute(f"UPDATE user SET {','.join(updates)} WHERE id={user_id};")


def load(user_id):
    return execute(f"SELECT created, text, what FROM what WHERE user_id={user_id};")


def remove(id):
    return execute(f"DELETE FROM what WHERE id={id};")


def update(id, text, item):
    execute(
        f"UPDATE what SET text='{text}', item='{json.dumps(item)}' WHERE id={id};"
    )
    return item


def create(id, user_id, text, item, created, what):
    execute(
        f"INSERT INTO what (id, user_id, text, item, created, what) VALUES ({id}, {user_id}, '{text}', '{json.dumps(item)}', {created}, '{what}');"
    )
    return item


def get_where(ids):
    return f"id IN {ids}" if len(ids) > 1 else f"id={ids[0]}"


def get_data_ids(hash_ids):
    res = execute(f"SELECT * FROM hash WHERE {get_where(hash_ids)};")
    return {q["id"]: q["data_id"] for q in res}


def get_results(data_ids):
    res = execute(f"SELECT * FROM data WHERE {get_where(data_ids)};")
    return {q["id"]: json.loads(q["result"]) for q in res}


def add_results(user_id, whats, items):
    if not items:
        return

    hash_ids = add_hash_ids(user_id, whats, items)
    data_ids = get_data_ids(hash_ids)
    if not data_ids:
        return

    weights = get_weights(whats, items, data_ids)
    data_ids = add_data_ids(weights, items)

    results = get_results(data_ids)
    if not results:
        return

    for item in items:
        if 'data_id' in item:
            item["result"] = results[item["data_id"]]


def get_item(user_id, what, text):
    item = to_item(text)
    add_results(user_id, [what], item["items"])
    item["items"] = list(map(as_item, item["items"]))
    return item
