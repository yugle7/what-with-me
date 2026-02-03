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

    for name in names:
        yield CityHash64(f"{what} {name}")


def get_weights(whats, items, data_ids):
    weights = {what: 0 for what in whats}
    for item in items:
        item["results"] = []
        for what, hash_ids in item.pop("hash_ids"):
            for i, hash_id in enumerate(hash_ids):
                if hash_id in data_ids:
                    weight = 1 - i / len(hash_ids)
                    item["results"].append((weight, what, data_ids[hash_id]))
                    weights[what] += weight
                    break

    return {what: weight / len(data_ids) for what, weight in weights.items()}


def add_data_ids(weights, items):
    dst = []
    for item in items:
        results = item.pop("results")
        if results:
            results = [
                (weight + weights[what], what, result_id)
                for weight, what, result_id in results
            ]
            item["weight"], item["what"], item["data_id"] = max(results)
            dst.append(item["data_id"])
    return dst



def load_items(what):
    with open(
        f"/Users/gleb/Projects/bots/what_with_me/src/{what}.jsonl", encoding="utf8"
    ) as src:
        items = [json.loads(q) for q in src]
        src = set()
        for item in items:
            item['id'] = CityHash64(f"{what} {item['names'][0]}")
            if item['id'] in src:
                exit(item)
            src.add(item['id'])

        for name in item["names"]:
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
        for h in get_hash_ids(what, item["names"][0]):
            if h not in dst:
                dst[h] = item['id']

    for item in items:
        for name in item["names"][1:]:
            for h in get_hash_ids(what, name):
                if h not in dst:
                    dst[h] = item['id']

    for item in items:
        for name in item["names"]:
            if "(" in name:
                name = re.sub(r" ?\(.*?\) ?", " ", name)
                for h in get_hash_ids(what, name):
                    if h not in dst:
                        dst[h] = item['id']

    return dst
