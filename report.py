"""Build a self-contained HTML report for an evaluation run.

Runs the eval (mock by default, or a real model), then writes method, metrics,
both plots, a per-question table, a worked example, and interpretation to
outputs/report.html.

Usage:
    python report.py
    OPENAI_API_KEY=... python report.py --provider openai --model gpt-4o-mini
    python report.py --provider hf --model Qwen/Qwen2.5-0.5B-Instruct
"""
from __future__ import annotations
import argparse, base64, os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from econ_eval.data import load_questions
from econ_eval.grader import parse_output, grade_item
from econ_eval.metrics import summarize
from econ_eval.providers import get_provider
from econ_eval.plotting import plot_accuracy_by_topic, plot_categories

def _img(p):
    with open(p,"rb") as f: return base64.b64encode(f.read()).decode()

def _missing_points(item, reasoning):
    t=reasoning.lower()
    return [p for p in item.get("reasoning_points",[]) if not all(tok in t for tok in p.lower().split())]

def build(provider, items, threshold):
    rows=[]
    by_id={it["id"]:it for it in items}
    for it in items:
        out=provider.answer(it)
        g=grade_item(it, out, threshold)
        ans, reasoning = parse_output(out)
        g["reasoning_text"]=reasoning
        g["missing"]=_missing_points(it, reasoning)
        rows.append(g)
    summary=summarize(rows)

    tmp=tempfile.mkdtemp()
    p1=os.path.join(tmp,"a.png"); p2=os.path.join(tmp,"b.png")
    plot_accuracy_by_topic(summary,p1); plot_categories(summary,p2)
    img1,img2=_img(p1),_img(p2)

    # pick a worked example: a correct-but-weak-reasoning case, else an incorrect one
    ex=next((r for r in rows if r["category"]=="correct_unsound"),
            next((r for r in rows if r["category"]=="incorrect"), rows[0]))
    exi=by_id[ex["id"]]

    color={"correct_sound":"#1e7e34","correct_unsound":"#b8860b","incorrect":"#b02a37"}
    label={"correct_sound":"correct, sound","correct_unsound":"correct, weak reasoning","incorrect":"incorrect"}
    trows=""
    for r in rows:
        trows+=(f"<tr><td>{r['id']}</td><td>{r['topic']}</td><td>{r['difficulty']}</td>"
                f"<td class='c' style='text-align:center'>{'yes' if r['correct'] else 'no'}</td>"
                f"<td class='c' style='text-align:right'>{r['reasoning_score']:.2f}</td>"
                f"<td style='color:{color[r['category']]}'>{label[r['category']]}</td></tr>")
    topt="".join(f"<tr><td>{k}</td><td style='text-align:right'>{v*100:.0f}%</td></tr>"
                 for k,v in summary["accuracy_by_topic"].items())
    difft="".join(f"<tr><td>{k}</td><td style='text-align:right'>{v*100:.0f}%</td></tr>"
                  for k,v in summary["accuracy_by_difficulty"].items())
    miss=", ".join(ex["missing"]) if ex["missing"] else "none"

    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Econ LLM Eval Report</title>
<style>
 :root{{--ink:#1a1a1a;--muted:#555;--line:#e2e2e2;--accent:#1f3864;--panel:#f7f8fa;}}
 *{{box-sizing:border-box;}}
 body{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);
  max-width:880px;margin:0 auto;padding:2.2rem 1.2rem 4rem;line-height:1.55;}}
 h1{{font-size:1.7rem;color:var(--accent);margin:0 0 .2rem;}}
 h2{{font-size:1.2rem;color:var(--accent);margin:2rem 0 .5rem;border-bottom:2px solid var(--accent);padding-bottom:.25rem;}}
 .sub{{color:var(--muted);margin:0 0 1.2rem;}}
 p{{margin:.6rem 0;}}
 table{{border-collapse:collapse;margin:.8rem 0;font-size:.92rem;width:100%;}}
 th,td{{border:1px solid var(--line);padding:.35rem .6rem;text-align:left;}}
 th{{background:var(--panel);}}
 .kpi{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0;}}
 .kpi div{{flex:1;min-width:150px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:.8rem 1rem;}}
 .kpi b{{display:block;font-size:1.5rem;color:var(--accent);}}
 .small{{font-size:.85rem;color:var(--muted);}}
 img{{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;margin:.5rem 0;}}
 .cols{{display:flex;gap:1.2rem;flex-wrap:wrap;}} .cols>div{{flex:1;min-width:260px;}}
 .panel{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:.8rem 1rem;margin:1rem 0;}}
 .note{{border-left:4px solid var(--accent);padding:.3rem 0 .3rem 1rem;color:var(--muted);}}
 code{{background:var(--panel);padding:.05rem .3rem;border-radius:4px;}}
 footer{{margin-top:2rem;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:1rem;}}
</style></head><body>

<h1>Economics LLM Evaluation Report</h1>
<p class="sub">Provider: {provider.name}. Questions: {summary['n']}. Reasoning threshold: {threshold}.</p>

<div class="panel"><strong>What this measures.</strong> How a language model does on a set of
economics questions, graded two ways: did it get the answer, and did it reason soundly. The
gap between the two is the point.</div>

<div class="kpi">
 <div><b>{summary['accuracy']*100:.0f}%</b>answer accuracy</div>
 <div><b>{summary['sound_reasoning_rate']*100:.0f}%</b>sound-reasoning rate</div>
 <div><b>{summary['right_answer_wrong_reasoning']}</b>right answer, weak reasoning</div>
</div>

<h2>Method</h2>
<p>Each question ships with an acceptable-answer set and the reasoning points the explanation
should contain. The outcome grade checks whether an acceptable answer appears in the model's
answer line. The reasoning grade is the share of expected reasoning points found in the
explanation, passed if it clears the threshold. Each answer lands in one of three categories:
correct with sound reasoning, correct answer with weak reasoning, or incorrect.</p>

<h2>Results</h2>
<div class="cols">
 <div><img alt="accuracy by topic" src="data:image/png;base64,{img1}"></div>
 <div><img alt="categories" src="data:image/png;base64,{img2}"></div>
</div>
<div class="cols">
 <div><h3>Accuracy by topic</h3><table><tr><th>Topic</th><th>Accuracy</th></tr>{topt}</table></div>
 <div><h3>Accuracy by difficulty</h3><table><tr><th>Difficulty</th><th>Accuracy</th></tr>{difft}</table></div>
</div>

<h2>A worked example: {label[ex['category']]}</h2>
<div class="panel">
<p><strong>Question ({ex['id']}, {ex['topic']}).</strong> {exi['question']}</p>
<p><strong>Reference answer.</strong> {exi['answer_summary']}</p>
<p><strong>Model answer.</strong> {ex['answer']}</p>
<p><strong>Grade.</strong> Outcome {'correct' if ex['correct'] else 'incorrect'}, reasoning score
{ex['reasoning_score']:.2f}. Missing reasoning points: {miss}.</p>
</div>
<p class="small">This is the case the evaluation is built to catch. Grading only the final answer
would mark it as fine, hiding that the model did not give the reasoning that makes the answer correct.</p>

<h2>Every question</h2>
<table>
<tr><th>ID</th><th>Topic</th><th>Difficulty</th><th>Correct</th><th>Reasoning</th><th>Category</th></tr>
{trows}
</table>

<h2>Interpretation</h2>
<p>Answer accuracy was {summary['accuracy']*100:.0f}%, but the sound-reasoning rate was
{summary['sound_reasoning_rate']*100:.0f}%, and {summary['right_answer_wrong_reasoning']} answers
were right for weak reasons. A single accuracy number would have hidden that gap. For training,
the gap matters: a reward signal built on final answers alone would reward those weak-reasoning
cases, pushing a model toward answers that look right rather than reasoning that is right.</p>

<h2>Limitations</h2>
<p class="note">The reasoning grade is keyword-based, a simple proxy for whether an explanation
contains the right ideas. It can miss a correct explanation worded differently, or credit one
that name-drops a term without using it. A stronger version would grade against a rubric using a
stronger model or a human. The question set is small by design, meant to be read and trusted
rather than to be comprehensive.</p>

<footer>Generated by <code>report.py</code>. Regenerate with <code>python report.py</code>
(add <code>--provider openai</code> or <code>--provider hf</code> for a real model).</footer>
</body></html>"""

def main():
    here=os.path.dirname(__file__)
    ap=argparse.ArgumentParser()
    ap.add_argument("--provider", default="mock", choices=["mock","openai","hf"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--data", default=os.path.join(here,"data","questions.jsonl"))
    ap.add_argument("--reasoning-threshold", type=float, default=0.5)
    ap.add_argument("--out", default=os.path.join(here,"outputs","report.html"))
    args=ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    items=load_questions(args.data)
    provider=get_provider(args.provider, args.model)
    html=build(provider, items, args.reasoning_threshold)
    open(args.out,"w",encoding="utf-8").write(html)
    print(f"Wrote {os.path.abspath(args.out)}")

if __name__=="__main__":
    main()
