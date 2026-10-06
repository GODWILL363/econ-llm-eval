"""Load the economics question set."""
from __future__ import annotations
import json

def load_questions(path):
    items=[]
    with open(path, encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                items.append(json.loads(line))
    return items
