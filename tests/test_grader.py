import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from econ_eval.data import load_questions
from econ_eval.grader import parse_output, grade_item
from econ_eval.metrics import summarize
from econ_eval.providers import MockProvider

DATA=os.path.join(os.path.dirname(__file__),"..","data","questions.jsonl")

def test_parse_output():
    a,r=parse_output("Answer: lower.\nReasoning: deadweight loss and no terms-of-trade gain.")
    assert a.lower().startswith("lower")
    assert "deadweight" in r.lower()

def test_right_answer_wrong_reasoning_is_flagged():
    item={"id":"x","topic":"t","difficulty":"easy","acceptable":["lower"],
          "reasoning_points":["deadweight loss","terms of trade"]}
    g=grade_item(item,"Answer: lower.\nReasoning: it just is.")
    assert g["correct"] and not g["sound_reasoning"]
    assert g["category"]=="correct_unsound"

def test_wrong_answer_is_incorrect():
    item={"id":"x","topic":"t","difficulty":"easy","acceptable":["lower"],"reasoning_points":[]}
    g=grade_item(item,"Answer: higher.\nReasoning: whatever.")
    assert not g["correct"] and g["category"]=="incorrect"

def test_mock_run_distribution():
    items=load_questions(DATA)
    p=MockProvider()
    rows=[grade_item(it, p.answer(it)) for it in items]
    s=summarize(rows)
    assert s["n"]==24
    # 5 wrong, 4 shallow, 15 sound by construction of the mock
    assert s["categories"].get("incorrect")==5
    assert s["categories"].get("correct_unsound")==4
    assert s["categories"].get("correct_sound")==15

if __name__=="__main__":
    for k,v in list(globals().items()):
        if k.startswith("test_") and callable(v):
            v(); print("ok", k)
    print("all tests passed")
