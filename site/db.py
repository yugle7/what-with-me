import ydb
import ydb.iam

from cityhash import CityHash64

import os

import dotenv

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    # credentials=ydb.AuthTokenCredentials(os.getenv('IAM_TOKEN')),
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


def get_id(a, b):
    return CityHash64(str(a) + " " + str(b).lower().strip())


def handle(params):
    action = params.get("action")
    if action not in ("create", "update", "remove", "load", "write", "read"):
        return "unknown action"

    user_id = params.get("user_id")
    table = params.get("table")

    if action == "read":
        res = execute(f"SELECT * FROM {table} WHERE id={user_id};")
        return res[0] if res else {}

    if action == "write":
        updates = []
        for k in ["time_zone", "birthday", "height", "weight", "target_weight", "male"]:
            v = params.get(k) or "null"
            updates.append(f"{k}={v}")
        return execute(f"UPDATE {table} SET {','.join(updates)} WHERE id={user_id};")

    table = "user_" + table
    if action == "load":
        items = execute(f"SELECT created, text FROM {table} WHERE user_id={user_id};")
        return [
            {"created": str(i.get("created")), "text": i.get("text")} for i in items
        ]

    created = int(params.get("created"))
    id = get_id(user_id, created)

    if action == "remove":
        return execute(f"DELETE FROM {table} WHERE id={id};")

    text = params.get("text")
    if action == "create":
        return execute(
            f"INSERT INTO {table} (id, user_id, text, created) VALUES ({id}, {user_id}, '{text}', {created});"
        )
    if action == "update":
        return execute(f"UPDATE {table} SET text='{text}' WHERE id={id};")
