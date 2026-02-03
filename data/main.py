import db
from utils import load_items, get_data_ids


def main(what):
    items = load_items(what)
    print("data:", len(items))
    data_ids = get_data_ids(what, items)
    print("hash:", len(data_ids))

    # db.save_hash(data_ids)
    db.save_data(items)


if __name__ == "__main__":
    main(0)
