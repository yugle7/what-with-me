import re
from time import sleep

import dotenv
import os
import ydb
import json

from tqdm import tqdm

from stem import get_hashes

dotenv.load_dotenv()

if __name__ == "__main__":
    driver_config = ydb.DriverConfig(
        os.getenv("YDB_ENDPOINT"),
        os.getenv("YDB_DATABASE"),
        credentials=ydb.AuthTokenCredentials(os.getenv("IAM_TOKEN")),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    with ydb.Driver(driver_config) as driver:
        try:
            driver.wait(fail_fast=True, timeout=5)
        except TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(driver.discovery_debug_details())
            exit(1)

        pool = ydb.SessionPool(driver)

        settings = ydb.BaseRequestSettings().with_timeout(20).with_operation_timeout(16)

        def insert(yql):
            def wrapper(session):
                session.transaction().execute(yql, commit_tx=True, settings=settings)

            pool.retry_operation_sync(wrapper)

        items = []
        with open("data/food.jsonl", encoding="utf8") as src:
            for q in src:
                items.append(json.loads(q))

        hashes = {}
        for i, q in enumerate(items, 1):
            for h in get_hashes(q["name"]):
                if h not in hashes:
                    hashes[h] = i

        for i, q in enumerate(items):
            name = re.sub(r"\(.*?\)", " ", q["name"])
            name = re.sub(r"(, )?м\.д\.ж\..*", "", name)
            name = re.sub(r"  +", " ", name.strip())
            if name != q["name"]:
                for h in get_hashes(name):
                    if h not in hashes:
                        hashes[h] = i

        hashes = [f"({h},{i})" for h, i in hashes.items()]

        step = 1024
        for i in tqdm(range(0, len(hashes), step)):
            values = ",".join(hashes[i : i + step])
            # print(values)
            # break
            insert(f"INSERT INTO hash_food (id, food_id) VALUES {values};")
            sleep(1)

        step = 128
        for i in tqdm(range(0, len(items), step)):
            values = ",".join(
                [
                    "('" + json.dumps(item, ensure_ascii=False) + "')"
                    for item in items[i : i + step]
                ]
            )
            # print(values)
            # break
            try:
                insert(f"INSERT INTO data_food (data) VALUES {values};")
                sleep(1)
            except Exception as e:
                print(e)
                print(values)
                break
