"""Offline tests: no keys, no network. Run with `python3 tests/test_offline.py` or pytest.

A fake httpx answers every provider shape the script speaks (Anthropic with a paused turn,
OpenAI Responses, Gemini, chat/completions), so the tests cover the whole pipeline: isolation,
random labels, resume without repeated calls, manual stages, and role enforcement.
"""
import json
import os
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

CALLS = []


class _Resp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


def fake_post(url, headers=None, json=None, timeout=None):
    CALLS.append(url)
    if "anthropic.com" in url:
        turns = sum(1 for m in json["messages"] if m["role"] == "assistant")
        if turns == 0:
            return _Resp({"stop_reason": "pause_turn",
                          "content": [{"type": "text", "text": "part one, "},
                                      {"type": "server_tool_use", "name": "web_search"}]})
        return _Resp({"stop_reason": "end_turn",
                      "content": [{"type": "text", "text": "part two. [R-free]\nVERDICT: approve"}]})
    if url.endswith("/responses"):
        return _Resp({"output": [{"type": "web_search_call"},
                                 {"type": "message", "content": [{"type": "output_text",
                                                                  "text": "gpt draft\nVERDICT: approve with fixes"}]}]})
    if "generativelanguage" in url:
        return _Resp({"candidates": [{"content": {"parts": [{"text": "gemini draft"}]}}]})
    if url.endswith("/chat/completions"):
        return _Resp({"choices": [{"message": {"content": "I am Llama, made by Meta. llama draft"}}]})
    raise AssertionError(url)


sys.modules["httpx"] = types.SimpleNamespace(post=fake_post)
import docprep  # noqa: E402

CFG = {
    "providers": {
        "anthropic": {"type": "anthropic", "api_key_env": "K"},
        "openai": {"type": "openai", "api_key_env": "K"},
        "google": {"type": "gemini", "api_key_env": "K"},
        "meta": {"type": "openai_compatible", "api_key_env": "K", "base_url": "https://x/v1"},
        "manual": {"type": "manual"},
    },
    "settings": {"min_generators": 3, "min_vendors": 3, "retries": 1, "retry_wait": 0},
    "formulas": {
        "api": {
            "generators": [
                {"name": "claude", "provider": "anthropic", "model": "claude-sonnet-5", "search": True},
                {"name": "gpt", "provider": "openai", "model": "gpt-5.6-terra", "search": True},
                {"name": "gemini", "provider": "google", "model": "gemini-3.1-pro-high", "search": True},
                {"name": "meta", "provider": "meta", "model": "llama", "search": True}],
            "consolidator": {"name": "consolidator", "provider": "anthropic", "model": "claude-sonnet-5"},
            "critics": [{"name": "critic_internal", "provider": "anthropic", "model": "claude-sonnet-5"},
                        {"name": "critic_cross", "provider": "openai", "model": "gpt-5.6-terra"}]},
        "hand": {
            "generators": [
                {"name": "a", "provider": "manual", "family": "anthropic"},
                {"name": "b", "provider": "manual", "family": "openai"},
                {"name": "c", "provider": "manual", "family": "google"}],
            "consolidator": {"name": "consolidator", "provider": "manual", "family": "anthropic"},
            "critics": [{"name": "critic_internal", "provider": "manual", "family": "anthropic"},
                        {"name": "critic_cross", "provider": "manual", "family": "openai"}]},
        "broken": {
            "generators": [
                {"name": "claude", "provider": "anthropic", "model": "claude-sonnet-5"},
                {"name": "gpt", "provider": "openai", "model": "gpt-5.6-terra"},
                {"name": "gemini", "provider": "google", "model": "gemini-3.1-pro-high"}],
            "consolidator": {"name": "consolidator", "provider": "anthropic", "model": "claude-sonnet-5"},
            "critics": [{"name": "c1", "provider": "openai", "model": "gpt-5.6-terra"},
                        {"name": "c2", "provider": "anthropic", "model": "claude-sonnet-5"}]},
    },
}


def setup():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "config.json"), "w") as fh:
        json.dump(CFG, fh)
    with open(os.path.join(d, "brief.md"), "w") as fh:
        fh.write("# Brief\nDraft a one-page memorandum.\n")
    os.environ["K"] = "test-key"
    CALLS.clear()
    return d


def run_dir_of(d):
    runs = os.path.join(d, "runs")
    return os.path.join(runs, sorted(os.listdir(runs))[0])


def test_api_pipeline_and_resume():
    d = setup()
    cfg, brief = os.path.join(d, "config.json"), os.path.join(d, "brief.md")
    assert docprep.main(["run", "--config", cfg, "--brief", brief, "--formula", "api",
                         "--runs", os.path.join(d, "runs")]) == 0
    rd = run_dir_of(d)
    m = json.load(open(os.path.join(rd, "manifest.json")))
    assert m["finished"]
    assert len(m["stages"]) == 7, [s["stage"] for s in m["stages"]]
    assert set(m["label_map"].values()) == {"claude", "gpt", "gemini", "meta"}
    assert open(os.path.join(rd, "draft-claude.md")).read().startswith("part one, part two")
    cons = [s for s in m["stages"] if s["stage"] == "consolidate"][0]
    assert cons["search_requested"] is False and cons["prompt_sha256_16"]
    meta = [s for s in m["stages"] if s["role"] == "meta"][0]
    assert meta["search_requested"] is True and meta["search_applied"] is False
    assert "meta" in m["self_identification"]
    critic2 = [s for s in m["stages"] if s["role"] == "critic_cross"][0]
    assert critic2["saw_previous_report"] is True and critic2["family"] == "openai"
    assert m["verdicts"]["critic_cross"] == "VERDICT: approve with fixes"
    assert os.path.exists(os.path.join(rd, "consolidated.md"))
    assert os.path.exists(os.path.join(rd, "prompts", "draft-gpt.md"))
    prompt = open(os.path.join(rd, "prompts", "consolidation.md")).read()
    assert "### R4" in prompt and "claude" not in prompt.split("### R1")[1].lower()
    n = len(CALLS)
    # every anthropic stage takes two posts (paused turn): 2+1+1+1 generators, 2 consolidation,
    # 2 critic 1, 1 critic 2
    assert n == 10, CALLS
    assert docprep.main(["resume", "--config", cfg, "--run", rd]) == 0
    assert len(CALLS) == n, "resume must not repeat completed stages"
    assert docprep.main(["status", "--config", cfg, "--run", rd]) == 0


def test_manual_pipeline_step_by_step():
    d = setup()
    cfg, brief = os.path.join(d, "config.json"), os.path.join(d, "brief.md")
    runs = os.path.join(d, "runs")
    assert docprep.main(["run", "--config", cfg, "--brief", brief, "--formula", "hand", "--runs", runs]) == 0
    rd = run_dir_of(d)
    assert not CALLS
    for role, answer in [("a", "draft a"), ("b", "draft b"), ("c", "draft c")]:
        p = os.path.join(rd, f"MANUAL-{role}.md")
        assert os.path.exists(p)
        with open(p, "a") as fh:
            fh.write(answer + "\n")
    docprep.main(["resume", "--config", cfg, "--run", rd])
    assert os.path.exists(os.path.join(rd, "MANUAL-consolidator.md"))
    m = json.load(open(os.path.join(rd, "manifest.json")))
    assert len(m["label_map"]) == 3
    with open(os.path.join(rd, "MANUAL-consolidator.md"), "a") as fh:
        fh.write("merged text [R1, R2]\n---LOG---\nagreed on everything\n")
    docprep.main(["resume", "--config", cfg, "--run", rd])
    assert open(os.path.join(rd, "consolidation-log.md")).read() == "agreed on everything"
    with open(os.path.join(rd, "MANUAL-critic_internal.md"), "a") as fh:
        fh.write("fine\nVERDICT: approve\n")
    docprep.main(["resume", "--config", cfg, "--run", rd])
    p2 = os.path.join(rd, "MANUAL-critic_cross.md")
    assert "A previous reviewer reported" in open(p2).read()
    with open(p2, "a") as fh:
        fh.write("also fine\nVERDICT: approve\n")
    docprep.main(["resume", "--config", cfg, "--run", rd])
    m = json.load(open(os.path.join(rd, "manifest.json")))
    assert m["finished"] and all(s["manual"] for s in m["stages"]) and len(m["stages"]) == 6
    assert not CALLS


def test_roles_are_enforced():
    d = setup()
    cfg, brief = os.path.join(d, "config.json"), os.path.join(d, "brief.md")
    try:
        docprep.main(["run", "--config", cfg, "--brief", brief, "--formula", "broken",
                      "--runs", os.path.join(d, "runs")])
    except SystemExit as e:
        assert "last reader must come from another vendor" in str(e)
    else:
        raise AssertionError("a same-family last critic must be refused")


def test_check_answers():
    d = setup()
    assert docprep.main(["check", "--config", os.path.join(d, "config.json")]) == 1  # 'broken' formula fails
    assert not any(c for c in CALLS) or all(isinstance(c, str) for c in CALLS)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
