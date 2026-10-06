# Econ LLM Eval

A small, honest evaluation harness for language models on economics questions.
It runs a model on a set of micro, macro, trade, and fixed-income questions,
then grades each answer two ways: did the model get the answer, and did it
reason soundly. The point is to separate a right answer from right reasoning,
and to show that an evaluation is only as good as the reference key behind it.

Built with Python (matplotlib; optional requests or transformers for a real model).

## Why two grades

A model can reach the right answer with the wrong logic, or the right logic
with a slip at the end. Grading only the final answer hides both. Each question
here ships with an acceptable-answer set and the reasoning points the
explanation should contain, so the grader reports three outcomes: correct with
sound reasoning, correct answer with weak reasoning, and incorrect.

## Quick start (no setup)

```bash
pip install -r requirements.txt
python run_eval.py        # metrics, tables, plots
python report.py          # full HTML report with analysis
```

This runs the offline mock provider so the pipeline works out of the box, and
writes results, metrics, and two plots to `outputs/`. The mock is a stand-in,
not a model. It exists so the repo runs anywhere and so the grader and metrics
are demonstrably correct (see the sample run in `results/`).

## Evaluate a real model

With an API key (OpenAI-compatible endpoint):

```bash
pip install requests
export OPENAI_API_KEY=your_key
python run_eval.py --provider openai --model gpt-4o-mini
```

Fully local and free, with a small open model:

```bash
pip install transformers torch
python run_eval.py --provider hf --model Qwen/Qwen2.5-0.5B-Instruct
```

## The question set

`data/questions.jsonl`, 24 items across trade, micro, macro, and fixed income.
Each item has the question, a one-line reference answer summary, the key
assumption that fixes the answer, an acceptable-answer set for the outcome
check, and the reasoning points for the process check. All questions are
standard, textbook-level economics.

## Method

- Outcome grade: an acceptable answer string appears in the model's Answer line.
- Reasoning grade: the fraction of expected reasoning points found in the
  model's explanation, passed if it clears a threshold (default 0.5).
- Category: correct and sound, correct but weak reasoning, or incorrect.
- Metrics: accuracy, sound-reasoning rate, the count of right-answer
  wrong-reasoning cases, and accuracy by topic and difficulty.

## Sample run

`results/` holds a committed mock run so the output is visible without running
anything: `sample_results.csv`, `sample_metrics.json`, two plots, and
`sample_report.html`.

## Tests

```bash
python tests/test_grader.py
```

Checks the parser, the right-answer-wrong-reasoning flag, and the full mock
distribution.

## Layout

```
src/econ_eval/   data.py, providers.py, grader.py, metrics.py, plotting.py
data/            questions.jsonl
results/         committed sample run
tests/           test_grader.py
run_eval.py
report.py
```

## Limitations

The reasoning check is keyword-based, which is a deliberately simple proxy for
whether an explanation contains the right ideas. It can miss a correct
explanation worded differently, or credit one that name-drops a term without
using it. A stronger version would use a rubric graded by a stronger model or a
human, which is the direction real evaluation work takes. The question set is
small by design, meant to be read and trusted rather than to be comprehensive.

## License

MIT. See LICENSE.
