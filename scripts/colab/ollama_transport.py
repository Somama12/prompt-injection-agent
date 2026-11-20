"""Used as agent/llm.py ONLY in the isolated Colab source tree."""
import json
import time
import requests

PROVIDER = "ollama-local"
DEFAULT_MODEL = DEFAULT_JUDGE_MODEL = "gpt-oss:20b"
THINKING_BUDGET = RPM = None
BASE = "http://127.0.0.1:11434"
SESSION = requests.Session()
SESSION.trust_env = False
TOOLS = {
    "read_webpage": ("Read a page in the local mock environment.", ["url"]),
    "summarize": ("Summarize text using the local mock tool.", ["text"]),
    "send_email": ("Queue a message in the local mock environment.", ["to","subject","body"]),
}

class LLMError(RuntimeError):
    pass

def redact_secrets(s):
    # This isolated transport reads no credentials and only calls loopback.
    return str(s)

class Stats:
    def __init__(self):
        self.calls = self.failures = self.tokens = 0
        self.seconds = 0.0

    def snapshot(self):
        return dict(calls=self.calls, failures=self.failures, generated_tokens=self.tokens,
                    total_latency_s=round(self.seconds, 2))

STATS = Stats()

def generate(prompt, *, system_instruction=None, model=None, temperature=0.0, max_output_tokens=1024):
    model = model or DEFAULT_MODEL
    if model != DEFAULT_MODEL:
        raise LLMError("Unexpected model")
    messages = ([dict(role="system", content=system_instruction)] if system_instruction else [])
    messages.append(dict(role="user", content=prompt))
    p = dict(model=model, messages=messages, stream=False, think="low",
             options=dict(temperature=temperature, num_ctx=8192, num_predict=max_output_tokens))
    if system_instruction and system_instruction.startswith("You are MailBot,"):
        p["tools"] = [dict(type="function", function=dict(name=n, description=d,
            parameters=dict(type="object", properties={a:dict(type="string") for a in args},
                            required=args, additionalProperties=False))) for n,(d,args) in TOOLS.items()]
    started = time.monotonic()
    try:
        res = SESSION.post(BASE+"/api/chat", json=p, timeout=(5,240), allow_redirects=False)
        res.raise_for_status()
        r = res.json()
        if r["model"] != model or r.get("done_reason") != "stop" or r["done"] is not True:
            raise ValueError("Wrong model or incomplete response")
        # Do not accept responses at the context boundary as intact transcripts.
        if r.get("prompt_eval_count", 0) + r.get("eval_count", 0) >= p["options"]["num_ctx"]:
            raise ValueError("Context capacity reached")
        msg = r["message"]
        calls = msg.get("tool_calls") or []
        if calls:
            if len(calls) != 1 or "tools" not in p:
                raise ValueError("Unexpected tool calls")
            f = calls[0]["function"]
            if f["name"] not in TOOLS or not isinstance(f["arguments"],dict):
                raise ValueError("Malformed mock action")
            result = "ACTION: "+json.dumps(dict(tool=f["name"],args=f["arguments"]))
        else:
            result = msg["content"].strip()
            if not result:
                raise ValueError("No answer")
        STATS.calls += 1
        STATS.tokens += r.get("eval_count",0)
        STATS.seconds += time.monotonic()-started
        return result
    except (ValueError, TypeError, KeyError, AttributeError, requests.RequestException) as exc:
        STATS.failures += 1
        raise LLMError(str(exc)) from exc
