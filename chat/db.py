import ydb.iam

import os

import dotenv

dotenv.load_dotenv()

driver = ydb.Driver(
    endpoint=os.getenv("YDB_ENDPOINT"),
    database=os.getenv("YDB_DATABASE"),
    credentials=ydb.AuthTokenCredentials(os.getenv("IAM_TOKEN")),
    # credentials=ydb.iam.MetadataUrlCredentials()
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
    res = execute(f"SELECT * FROM users WHERE id={id};")
    return res and res[0]


def create_user(id):
    res = execute(f"INSERT INTO users (id, time_zone) VALUES ({id}, 3) RETURNING id;")
    return res and res[0]


def load_note(id):
    res = execute(f"SELECT * FROM note WHERE id={id};")
    return res and res[0]


def create_note(id, text, created, user_id, message_id, answer_id):
    values = f'({id}, "{text}", {created}, {user_id}, {message_id}, {answer_id})'
    execute(
        f"INSERT INTO note (id, text, created, user_id, message_id, answer_id) VALUES {values};"
    )


def update_note(id, text):
    execute(f'UPDATE note SET text="{text}" WHERE id={id};')
