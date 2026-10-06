"""Grade a model answer two ways: did it get the answer, and did it reason soundly.

parse_output pulls an "Answer:" line and a "Reasoning:" block out of the model
text. The outcome check looks for an acceptable answer string in the answer
line. The reasoning check looks for the expected concepts in the reasoning.
"""
from __future__ import annotations
import re

def parse_output(text):
    """Return (answer_line, reasoning_text) from a model response."""
    text=text or ""
    a=re.search(r"(?im)^\s*answer\s*:\s*(.+?)\s*$", text)
    r=re.search(r"(?is)reasoning\s*:\s*(.+)$", text)
    answer=a.group(1).strip() if a else text.strip().splitlines()[0] if text.strip() else ""
    reasoning=r.group(1).strip() if r else text.strip()
    return answer, reasoning

def outcome_correct(answer_line, acceptable):
    a=answer_line.lower()
    return any(opt.lower() in a for opt in acceptable)

def reasoning_score(reasoning_text, points):
    if not points:
        return 1.0
    t=reasoning_text.lower()
    hit=sum(1 for p in points if all(tok in t for tok in p.lower().split()))
    return hit/len(points)

def grade_item(item, model_output, reasoning_threshold=0.5):
    answer, reasoning = parse_output(model_output)
    correct = outcome_correct(answer, item["acceptable"])
    score = reasoning_score(reasoning, item.get("reasoning_points", []))
    sound = score >= reasoning_threshold
    return {
        "id": item["id"], "topic": item["topic"], "difficulty": item["difficulty"],
        "answer": answer, "correct": correct,
        "reasoning_score": round(score, 3), "sound_reasoning": sound,
        "category": classify(correct, sound),
    }

def classify(correct, sound):
    if correct and sound: return "correct_sound"
    if correct and not sound: return "correct_unsound"
    return "incorrect"
