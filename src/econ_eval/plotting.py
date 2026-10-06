"""Two plots: accuracy by topic, and a count of outcome-reasoning categories."""
from __future__ import annotations
import matplotlib.pyplot as plt

def plot_accuracy_by_topic(summary, path):
    d=summary["accuracy_by_topic"]
    fig,ax=plt.subplots(figsize=(7,4))
    ax.bar(list(d.keys()), [v*100 for v in d.values()], color="#1f3864")
    ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0,100)
    ax.set_title("Answer accuracy by topic"); ax.grid(axis="y",alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=140); return fig

def plot_categories(summary, path):
    order=["correct_sound","correct_unsound","incorrect"]
    labels={"correct_sound":"Correct, sound\nreasoning",
            "correct_unsound":"Correct answer,\nweak reasoning","incorrect":"Incorrect"}
    cats=summary["categories"]; vals=[cats.get(k,0) for k in order]
    colors=["#27ae60","#e1a500","#c0392b"]
    fig,ax=plt.subplots(figsize=(7,4))
    ax.bar([labels[k] for k in order], vals, color=colors)
    ax.set_ylabel("Number of questions")
    ax.set_title("Outcome vs reasoning"); ax.grid(axis="y",alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=140); return fig
