#!/usr/bin/env python3
"""Read the board data out of an interactive HTML BOM (InteractiveHtmlBom, which KiBot's ibom
output runs).

    python3 labs/lab-05-fab-outputs-in-ci/src/ibom.py out/kibot/pmod-ibom.html

The page carries the board as one JSON object, `pcbdata`. By default it's compressed with
LZString and stored as Base64 (`var pcbdata = JSON.parse(LZString.decompressFromBase64("..."))`);
with the ibom option `no_compression` it's plain JSON (`var pcbdata = {...}`). read() returns
that object; Lab 05's check uses its `bom` and `footprints`:

  bom["both"]      the BOM's rows, each a list of [reference, footprint index] pairs
  bom["skipped"]   the indexes of footprints left out of the BOM (blacklisted or not fitted)
  footprints[i]    each footprint on the board, with its "ref"

Run on its own, it prints the BOM's rows and the skipped parts.
"""
import json
import re
import sys

_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_B64_VALUE = {c: i for i, c in enumerate(_B64)}


def lzstring_from_base64(data):
    """LZString.decompressFromBase64, as in lz-string 1.4 (which the ibom page carries)."""
    if not data:
        return ""
    n = len(data)

    def value(i):
        return _B64_VALUE.get(data[i], 0) if i < n else 0

    state = {"val": value(0), "pos": 32, "index": 1}

    def bits(count):
        out, power = 0, 1
        for _ in range(count):
            bit = state["val"] & state["pos"]
            state["pos"] >>= 1
            if state["pos"] == 0:
                state["pos"] = 32
                state["val"] = value(state["index"])
                state["index"] += 1
            if bit:
                out |= power
            power <<= 1
        return out

    dictionary = {0: 0, 1: 1, 2: 2}
    size, enlarge_in, num_bits = 4, 4, 3
    first = bits(2)
    if first == 2:
        return ""
    c = chr(bits(8 if first == 0 else 16))
    dictionary[3] = c
    w = c
    result = [c]
    while True:
        if state["index"] > n:
            return ""
        code = bits(num_bits)
        if code in (0, 1):
            dictionary[size] = chr(bits(8 if code == 0 else 16))
            size += 1
            code = size - 1
            enlarge_in -= 1
        elif code == 2:
            text = "".join(result)
            # JavaScript strings are UTF-16, so characters outside the BMP arrive as pairs.
            return text.encode("utf-16", "surrogatepass").decode("utf-16")
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1
        if code in dictionary:
            entry = dictionary[code]
        elif code == size:
            entry = w + w[0]
        else:
            raise ValueError("the compressed board data is damaged")
        result.append(entry)
        dictionary[size] = w + entry[0]
        size += 1
        enlarge_in -= 1
        w = entry
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1


def is_ibom(text):
    return "var pcbdata" in text


def read(path):
    """The page's pcbdata as a dict. Raises ValueError if the page has none we can read."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r'var pcbdata\s*=\s*JSON\.parse\(LZString\.decompressFromBase64\("([A-Za-z0-9+/=]*)"\)\)', text)
    if m:
        return json.loads(lzstring_from_base64(m.group(1)))
    m = re.search(r"var pcbdata\s*=\s*", text)
    if m:
        data, _ = json.JSONDecoder().raw_decode(text, m.end())
        return data
    raise ValueError("no board data (var pcbdata) in the page")


def bom_refs(data):
    """References in the BOM's rows, and the references of the footprints it skipped."""
    rows = data["bom"]["both"]
    listed = [ref for row in rows for ref, _ in row]
    skipped = [data["footprints"][i]["ref"] for i in data["bom"].get("skipped", [])]
    return rows, listed, skipped


if __name__ == "__main__":
    d = read(sys.argv[1])
    rows, listed, skipped = bom_refs(d)
    for row in rows:
        print(" ".join(ref for ref, _ in row))
    print(f"{len(listed)} parts in {len(rows)} rows; skipped: {', '.join(skipped) or 'none'}")
