from cityhash import CityHash64

import re

with open("data/suffixes.csv", encoding="utf8") as src:
    suffixes = [line.strip() for line in src]


def stem(word):
    if len(word) <= 3:
        return word
    if word.endswith("ек"):
        return word[-2:] + "к"
    for suffix in suffixes:
        if word.endswith(suffix):
            n = len(suffix)
            return word if len(word) - n <= 2 else word[:-n]
    return word


def get_hashes(name):
    hashes = []
    words = re.sub(r"[^a-zа-я0-9 ]", " ", name.lower().replace("ё", "е")).split()
    hashes.append(CityHash64(" ".join(words)))
    words = [stem(word) for word in words]
    hashes.append(CityHash64(" ".join(words)))
    words.sort()
    hashes.append(CityHash64(" ".join(words)))
    return list(set(hashes))
