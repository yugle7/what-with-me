from cityhash import CityHash64
import json
import re

from const import *


def stem(word):
    if len(word) <= 3:
        return word
    if word.endswith("ек"):
        return word[-2:] + "к"
    for suffix in SUFFIX:
        if word.endswith(suffix):
            n = len(suffix)
            return word if len(word) - n <= 2 else word[:-n]
    return word


def get_hash_ids(what, name):
    name = name.lower().replace("ё", "е").strip()
    names = [name]

    words = re.sub(r"[^a-zа-я0-9 ]", " ", name).split()
    names.append(" ".join(words))
    words = [stem(word) for word in words]
    names.append(" ".join(words))
    names.append(" ".join(sorted(words)))

    return [CityHash64(f"{what} {name}") for name in names]


def load_items(what):
    with open(f"{ROOT}/src/{what}.jsonl", encoding="utf8") as src:
        items = [json.loads(q) for q in src]
        src = set()
        for item in items:
            item["id"] = CityHash64(f"{what} {item['name']}")
            if item["id"] in src:
                exit(item)
            src.add(item["id"])

        for name in item.get("names", []):
            src.add(CityHash64(f"{what} {name}"))

        dst = set()
        for item in items:
            if "items" in item:
                for name in item["items"]:
                    if CityHash64(f"{what} {name}") not in src:
                        dst.add(name)

        print("\n".join(dst))
        return items


def get_data_ids(what, items):
    dst = {}

    for item in items:
        for h in get_hash_ids(what, item["name"]):
            if h not in dst:
                dst[h] = item["id"]

    for item in items:
        for name in item.get("names", []):
            for h in get_hash_ids(what, name):
                if h not in dst:
                    dst[h] = item["id"]

    for item in items:
        for name in [item["name"]] + item.get("names", []):
            if "(" in name:
                name = re.sub(r" ?\(.*?\) ?", " ", name)
                for h in get_hash_ids(what, name):
                    if h not in dst:
                        dst[h] = item["id"]

    return dst
