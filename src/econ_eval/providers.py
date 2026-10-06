"""Model providers. Mock runs offline; openai and hf call a real model.

The mock provider is a stand-in that lets the whole pipeline run without a
model, so the repo works out of the box. Real signal comes from running a real
model with the openai or hf provider.
"""
from __future__ import annotations

PROMPT = (
 "You are answering an economics question. Respond in exactly this format:\n"
 "Answer: <one short line, the direct answer>\n"
 "Reasoning: <2 to 4 sentences explaining why>\n\n"
 "Question: {q}"
)

# Mock behavior sets, chosen to produce a realistic, non-perfect run.
_WRONG   = {"t02","a04","f03","m07","a02"}          # model gets the answer wrong
_SHALLOW = {"t01","m01","f01","a06"}                # right answer, weak reasoning
_WRONG_ANSWER = {
 "t02":"it lowers welfare", "a04":"the trade balance always worsens",
 "f03":"duration predicts the gain exactly", "m07":"quantity demanded falls",
 "a02":"real output rises permanently",
}

class MockProvider:
    name="mock"
    def answer(self, item):
        i=item["id"]
        if i in _WRONG:
            return f"Answer: {_WRONG_ANSWER.get(i,'no significant effect')}.\nReasoning: This follows from a quick reading of the question."
        if i in _SHALLOW:
            return f"Answer: {item['acceptable'][0]}.\nReasoning: It follows from basic economics."
        pts="; ".join(item.get("reasoning_points", []))
        return f"Answer: {item['acceptable'][0]}.\nReasoning: {pts}."

class OpenAIProvider:
    name="openai"
    def __init__(self, model="gpt-4o-mini", base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY"):
        import os, requests
        self.requests=requests; self.model=model; self.base=base_url
        self.key=os.environ.get(api_key_env)
        if not self.key:
            raise RuntimeError(f"Set {api_key_env} in your environment to use the openai provider.")
    def answer(self, item):
        r=self.requests.post(f"{self.base}/chat/completions",
            headers={"Authorization":f"Bearer {self.key}"},
            json={"model":self.model,"temperature":0,
                  "messages":[{"role":"user","content":PROMPT.format(q=item['question'])}]},
            timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

class HFProvider:
    name="hf"
    def __init__(self, model="Qwen/Qwen2.5-0.5B-Instruct"):
        from transformers import pipeline
        self.pipe=pipeline("text-generation", model=model)
    def answer(self, item):
        out=self.pipe(PROMPT.format(q=item['question']), max_new_tokens=160, do_sample=False)
        return out[0]["generated_text"]

def get_provider(name, model=None):
    if name=="mock": return MockProvider()
    if name=="openai": return OpenAIProvider(model=model or "gpt-4o-mini")
    if name=="hf": return HFProvider(model=model or "Qwen/Qwen2.5-0.5B-Instruct")
    raise ValueError(f"unknown provider: {name}")
