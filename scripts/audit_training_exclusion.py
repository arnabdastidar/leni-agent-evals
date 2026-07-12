#!/usr/bin/env python3
"""Training-corpus exclusion audit: evaluation items vs. specialist training data.

Purpose: verify, without releasing the proprietary corpora, that no evaluation
instance (or near-duplicate) from BullshitBench v2, GAIA validation, or DRACO
appears in any specialist training set. Publish the script + summary counts;
keep the corpora private.

Usage:
    python3 audit_training_exclusion.py --training <path>

    <path> is a directory (recursively scanned) or a single file containing the
    training documents. Supported: .jsonl (any schema; all string fields are
    scanned), .txt, .csv. Run once per specialist training set.

Method (standard n-gram containment, as used in GPT-3/PaLM/Llama contamination
reports): each evaluation item is reduced to normalized word 8-grams; a
training document is FLAGGED for an item when it contains >= 3 of the item's
8-grams or any single 13-gram. Flags err toward false positives by design;
adjudicate flagged pairs manually and report:

    items_checked, docs_scanned, flagged_pairs, confirmed_duplicates

Output: exclusion_audit_report.txt + exclusion_audit_flags.csv (pair-level,
private; publish counts only if pairs would reveal corpus content).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)

NGRAM_SMALL, HITS_SMALL = 8, 3   # >=3 shared 8-grams flags a pair
NGRAM_LARGE = 13                 # any shared 13-gram flags a pair


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower()).split()


def ngrams(tokens, n):
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def load_eval_items():
    """Evaluation items from the eval-DB export CSVs (run in the export dir)."""
    items = []
    bb = csv.DictReader(open("bullshitbench_tasks.csv"))
    items += [("bullshitbench", r["bench_task_id"], r["question"]) for r in bb]
    ga = csv.DictReader(open("gaia_tasks.csv"))
    items += [("gaia", r["bench_task_id"], r["question"])
              for r in ga if r.get("split") == "validation"]
    dr = csv.DictReader(open("draco_tasks.csv"))
    items += [("draco", r["bench_task_id"], r["problem"]) for r in dr]
    return items


def iter_training_texts(path):
    p = Path(path)
    files = [p] if p.is_file() else [f for f in p.rglob("*")
                                     if f.suffix in {".jsonl", ".txt", ".csv"}]
    for f in files:
        if f.suffix == ".jsonl":
            for i, line in enumerate(open(f, errors="ignore")):
                try:
                    obj = json.loads(line)
                    text = " ".join(str(v) for v in obj.values()
                                    if isinstance(v, str))
                except json.JSONDecodeError:
                    text = line
                yield f"{f}:{i}", text
        elif f.suffix == ".csv":
            for i, row in enumerate(csv.reader(open(f, errors="ignore"))):
                yield f"{f}:{i}", " ".join(row)
        else:
            yield str(f), open(f, errors="ignore").read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--training", required=True,
                    help="directory or file of training documents")
    args = ap.parse_args()

    items = []
    for bench, tid, text in load_eval_items():
        toks = normalize(text)
        items.append({
            "bench": bench, "id": tid,
            "small": ngrams(toks, NGRAM_SMALL),
            "large": ngrams(toks, NGRAM_LARGE),
        })
    print(f"evaluation items loaded: {len(items)}")

    flags, docs = [], 0
    for doc_id, text in iter_training_texts(args.training):
        docs += 1
        toks = normalize(text)
        if len(toks) < NGRAM_SMALL:
            continue
        d_small, d_large = ngrams(toks, NGRAM_SMALL), ngrams(toks, NGRAM_LARGE)
        for it in items:
            small_hits = len(it["small"] & d_small)
            large_hit = bool(it["large"] & d_large)
            if small_hits >= HITS_SMALL or large_hit:
                flags.append({"benchmark": it["bench"], "item_id": it["id"],
                              "doc": doc_id, "shared_8grams": small_hits,
                              "shared_13gram": large_hit})
        if docs % 10000 == 0:
            print(f"  scanned {docs} docs, {len(flags)} flags")

    with open("exclusion_audit_flags.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["benchmark", "item_id", "doc",
                                           "shared_8grams", "shared_13gram"])
        w.writeheader()
        w.writerows(flags)

    summary = (f"items_checked={len(items)}  docs_scanned={docs}  "
               f"flagged_pairs={len(flags)}  "
               f"flagged_items={len({(f['benchmark'], f['item_id']) for f in flags})}")
    print(summary)
    with open("exclusion_audit_report.txt", "w") as fh:
        fh.write(summary + "\nAdjudicate flagged pairs manually; "
                 "report confirmed duplicates alongside these counts.\n")


if __name__ == "__main__":
    main()
