"""Run the economics evaluation and write results, metrics, and plots.

Examples:
    python run_eval.py                         # offline mock run, no setup
    OPENAI_API_KEY=... python run_eval.py --provider openai --model gpt-4o-mini
    python run_eval.py --provider hf --model Qwen/Qwen2.5-0.5B-Instruct
"""
from __future__ import annotations
import argparse, csv, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from econ_eval.data import load_questions
from econ_eval.grader import grade_item
from econ_eval.metrics import summarize
from econ_eval.providers import get_provider
from econ_eval.plotting import plot_accuracy_by_topic, plot_categories

def main():
    here=os.path.dirname(__file__)
    ap=argparse.ArgumentParser()
    ap.add_argument("--provider", default="mock", choices=["mock","openai","hf"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--data", default=os.path.join(here,"data","questions.jsonl"))
    ap.add_argument("--reasoning-threshold", type=float, default=0.5)
    ap.add_argument("--outdir", default=os.path.join(here,"outputs"))
    args=ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    items=load_questions(args.data)
    provider=get_provider(args.provider, args.model)

    rows=[]
    for it in items:
        out=provider.answer(it)
        g=grade_item(it, out, args.reasoning_threshold)
        g["question"]=it["question"]; g["model_answer"]=out.replace("\n"," / ")
        rows.append(g)

    cols=["id","topic","difficulty","correct","reasoning_score","sound_reasoning","category","answer"]
    with open(os.path.join(args.outdir,"results.csv"),"w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f, fieldnames=cols); wr.writeheader()
        for r in rows: wr.writerow({k:r[k] for k in cols})

    summary=summarize(rows)
    with open(os.path.join(args.outdir,"metrics.json"),"w") as f:
        json.dump(summary, f, indent=2)

    plot_accuracy_by_topic(summary, os.path.join(args.outdir,"accuracy_by_topic.png"))
    plot_categories(summary, os.path.join(args.outdir,"categories.png"))

    print(f"Provider: {provider.name}   Questions: {summary['n']}")
    print(f"Accuracy: {summary['accuracy']*100:.1f}%   "
          f"Sound-reasoning rate: {summary['sound_reasoning_rate']*100:.1f}%")
    print(f"Right answer, wrong reasoning: {summary['right_answer_wrong_reasoning']}")
    print("By topic:", summary["accuracy_by_topic"])
    print(f"Wrote results, metrics, and plots to {args.outdir}")
    if provider.name=="mock":
        print("\nNote: mock provider is an offline stand-in. Use --provider openai "
              "or --provider hf to evaluate a real model.")

if __name__=="__main__":
    main()
