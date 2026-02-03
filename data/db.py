from time import sleep

import dotenv
import os
import ydb
import json

from tqdm import tqdm

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    credentials=ydb.AuthTokenCredentials(os.getenv("IAM_TOKEN")),
    # credentials=ydb.iam.MetadataUrlCredentials(),
)
driver.wait(fail_fast=True, timeout=16)

pool = ydb.SessionPool(driver)

settings = ydb.BaseRequestSettings().with_timeout(32).with_operation_timeout(24)


def execute(yql):
    def wrapper(session):
        session.transaction().execute(yql, commit_tx=True, settings=settings)

    return pool.retry_operation_sync(wrapper, retry_settings=ydb.RetrySettings())


def save_hash(data_ids):
    src = [f"({hash_id},{data_id})" for hash_id, data_id in data_ids.items()]
    step = 256
    for i in tqdm(range(0, len(src), step)):
        values = ",".join(src[i: i + step])

        execute(f"INSERT INTO hash (id, data_id) VALUES {values};")
        sleep(2)


def save_data(items):
    for item in items:
        if "categories" in item:
            item.pop("categories")

    src = [f"({item.pop('id')},'{json.dumps(item)}')" for item in items]
    step = 64
    for i in tqdm(range(0, len(items), step)):
        values = ",".join(src[i: i + step])
        execute(f"INSERT INTO data (id, data) VALUES {values};")
        sleep(2)
