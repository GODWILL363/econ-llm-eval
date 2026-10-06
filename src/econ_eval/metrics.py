"""Aggregate graded rows into headline metrics."""
from __future__ import annotations
from collections import defaultdict

def summarize(rows):
    n=len(rows)
    correct=sum(r["correct"] for r in rows)
    sound=sum(r["sound_reasoning"] for r in rows)
    cu=sum(r["category"]=="correct_unsound" for r in rows)
    by_topic=defaultdict(lambda:[0,0])
    by_diff=defaultdict(lambda:[0,0])
    for r in rows:
        by_topic[r["topic"]][0]+=r["correct"]; by_topic[r["topic"]][1]+=1
        by_diff[r["difficulty"]][0]+=r["correct"]; by_diff[r["difficulty"]][1]+=1
    cat=defaultdict(int)
    for r in rows: cat[r["category"]]+=1
    return {
        "n": n,
        "accuracy": round(correct/n, 3) if n else 0.0,
        "sound_reasoning_rate": round(sound/n, 3) if n else 0.0,
        "right_answer_wrong_reasoning": cu,
        "categories": dict(cat),
        "accuracy_by_topic": {k: round(v[0]/v[1],3) for k,v in sorted(by_topic.items())},
        "accuracy_by_difficulty": {k: round(v[0]/v[1],3) for k,v in sorted(by_diff.items())},
    }
