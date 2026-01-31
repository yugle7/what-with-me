import db

from utils import load_items, get_data_ids


def main(what):
    items = load_items(what)
    data_ids = get_data_ids(what, items)

    db.save_hash(data_ids)
    db.save_data(what, items)


if __name__ == "__main__":
    main("food")
