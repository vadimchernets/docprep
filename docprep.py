#!/usr/bin/env python3
"""docprep: one assistance architecture, stated so it can be run.

Four stages: isolated generation, blind consolidation, internal verification, cross-vendor
verification. The protocol is defined by roles, and the code enforces them before a run starts:

  - generators never see each other;
  - the consolidator receives the drafts as R1..Rn in a random order and never learns the vendors;
  - the last critic comes from a different vendor than the consolidator.

Every run leaves a manifest: model identifiers, prompt and output hashes, timestamps, durations
and the label map. A completed stage is a file in the run directory. `resume` loads what exists
and runs only what is missing, so a manual stage or a failure never repeats a paid call.

    python3 docprep.py check                                    # every configured model answers
    python3 docprep.py run --brief briefs/example_brief.md --formula enhanced
    python3 docprep.py resume --run runs/<id>                   # after a manual stage or a failure
    python3 docprep.py status --run runs/<id>

A role whose provider is "manual" writes MANUAL-<role>.md and stops. Run the prompt in the web
interface in a fresh session, paste the answer under the marker line, resume. The deep-research
modes of the consumer interfaces have no API equivalent, and the manifest records such stages
as manual.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

RUNS = "runs"
TIMEOUT = 1800
MARKER = "<!-- paste the answer below this line -->"
# Drafts reach the consolidator without vendor names. This does not redact anything; it flags a
# draft that names its own maker so the reader knows the blinding was weakened.
SELF_ID = re.compile(r"\b(?:I am|I'm|this is) (?:Claude|ChatGPT|GPT-[\d.]+\w*|Gemini|Grok|Llama)\b"
                     r"|\b(?:made|trained|developed) by (?:Anthropic|OpenAI|Google|xAI|Meta)\b", re.I)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_config(path):
    if not os.path.exists(path):
        sys.exit(f"no config at {path}. Copy config.example.yaml to config.yaml and set your identifiers.")
    if path.endswith(".json"):
        return json.loads(read(path))
    try:
        import yaml
    except ImportError:
        sys.exit("pip install pyyaml")
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------- roles

def family(cfg, role):
    """The vendor family a role belongs to. Manual roles must declare it."""
    prov = cfg["providers"][role["provider"]]
    fam = role.get("family") or prov.get("family")
    if not fam and prov["type"] != "manual":
        fam = role["provider"]
    if not fam:
        raise SystemExit(f"{role['name']}: a manual role needs 'family:' naming the vendor you will use")
    return fam


def validate(cfg, formula_name, enforce=None):
    """Check that a formula satisfies the protocol. Returns the list of problems found, and
    stops the program when roles are enforced (the default) and a problem exists."""
    f = cfg["formulas"][formula_name]
    s = cfg.get("settings", {})
    if enforce is None:
        enforce = s.get("enforce_roles", True)
    gens, cons, critics = f["generators"], f["consolidator"], f["critics"]
    problems = []
    if len(critics) != 2:
        problems.append("a formula has exactly two critics")
    fams = {family(cfg, g) for g in gens}
    if len(fams) < s.get("min_vendors", 3):
        problems.append(f"generators span {len(fams)} vendor families; min_vendors is {s.get('min_vendors', 3)}")
    if critics and family(cfg, critics[-1]) == family(cfg, cons):
        problems.append(f"the last critic ({critics[-1]['name']}) is from the consolidator's family "
                        f"({family(cfg, cons)}); the last reader must come from another vendor")
    names = [r["name"] for r in gens + [cons] + critics]
    if len(set(names)) != len(names):
        problems.append("role names must be unique")
    for r in gens + [cons] + critics:
        if cfg["providers"][r["provider"]]["type"] != "manual" and str(r.get("model", "")).startswith("SET-"):
            problems.append(f"{r['name']}: model identifier not set ({r.get('model')})")
    if problems and enforce:
        sys.exit(f"formula '{formula_name}' breaks the protocol:\n  - " + "\n  - ".join(problems))
    return problems


# ---------------------------------------------------------------- providers
# Each caller returns (text, search_applied). search_applied says whether the request actually
# carried a search tool, so the manifest never claims a search that did not happen.

def call_anthropic(prov, role, prompt, key):
    import httpx
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": role["model"], "max_tokens": role.get("max_tokens", 16000),
            "messages": [{"role": "user", "content": prompt}]}
    if role.get("search"):
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search",
                          "max_uses": role.get("max_searches", 20)}]
    texts = []
    for _ in range(12):  # a long search run pauses the turn; continue it until the model stops
        r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        texts += [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        if data.get("stop_reason") != "pause_turn":
            break
        body["messages"].append({"role": "assistant", "content": data["content"]})
    return "".join(texts), bool(role.get("search"))


def call_openai(prov, role, prompt, key):
    """Responses API: the endpoint that carries OpenAI's web_search tool."""
    import httpx
    base = prov.get("base_url", "https://api.openai.com/v1").rstrip("/")
    body = {"model": role["model"], "input": prompt}
    if role.get("search"):
        body["tools"] = [{"type": "web_search"}]
    if role.get("reasoning_effort"):
        body["reasoning"] = {"effort": role["reasoning_effort"]}
    r = httpx.post(f"{base}/responses", headers={"Authorization": f"Bearer {key}",
                                                 "content-type": "application/json"},
                   json=body, timeout=TIMEOUT)
    r.raise_for_status()
    text = "".join(part.get("text", "") for item in r.json().get("output", [])
                   if item.get("type") == "message"
                   for part in item.get("content", []) if part.get("type") == "output_text")
    return text, bool(role.get("search"))


def call_openai_compatible(prov, role, prompt, key):
    """chat/completions for hosts such as xAI or a Llama provider. No search tool is sent."""
    import httpx
    r = httpx.post(f"{prov['base_url'].rstrip('/')}/chat/completions",
                   headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
                   json={"model": role["model"], "messages": [{"role": "user", "content": prompt}]},
                   timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], False


def call_gemini(prov, role, prompt, key):
    import httpx
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if role.get("search"):
        body["tools"] = [{"google_search": {}}]
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{role['model']}:generateContent",
                   headers={"x-goog-api-key": key, "content-type": "application/json"},
                   json=body, timeout=TIMEOUT)
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought")), bool(role.get("search"))


CALLERS = {"anthropic": call_anthropic, "openai": call_openai,
           "openai_compatible": call_openai_compatible, "gemini": call_gemini}


def manual(role, prompt, run_dir):
    """Write the prompt for the operator, or read the pasted answer. None means still waiting."""
    path = os.path.join(run_dir, f"MANUAL-{role['name']}.md")
    if os.path.exists(path):
        text = read(path)
        answer = text.split(MARKER, 1)[1].strip() if MARKER in text else ""
        if answer:
            return {"text": answer, "seconds": None, "search_applied": None, "manual": True}
        return None
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# Manual stage: {role['name']}\n\n"
                 f"Model to use: {role.get('model', '(your choice)')}, in a fresh session with no prior context.\n"
                 f"Run the prompt below in the web interface, paste the full answer under the marker line,\n"
                 f"then: python3 docprep.py resume --run {run_dir}\n\n## Prompt\n\n{prompt}\n\n{MARKER}\n")
    return None


def ask(cfg, role, prompt, run_dir):
    """Run one role once, with retries. Returns a result dict, or None when a manual stage waits."""
    prov = cfg["providers"][role["provider"]]
    if prov["type"] == "manual":
        return manual(role, prompt, run_dir)
    if prov["type"] not in CALLERS:
        raise RuntimeError(f"unknown provider type {prov['type']}")
    key = os.environ.get(prov.get("api_key_env", ""), "")
    if not key:
        raise RuntimeError(f"{role['name']}: {prov.get('api_key_env')} is not set")
    retries = cfg.get("settings", {}).get("retries", 2)
    for attempt in range(retries + 1):
        try:
            t0 = time.time()
            text, applied = CALLERS[prov["type"]](prov, role, prompt, key)
            if not text.strip():
                raise RuntimeError("empty response")
            return {"text": text, "seconds": round(time.time() - t0, 1), "search_applied": applied}
        except Exception as e:                                        # noqa: BLE001
            if attempt == retries:
                raise
            print(f"  {role['name']}: attempt {attempt + 1} failed ({str(e)[:100]}); retrying")
            time.sleep(cfg.get("settings", {}).get("retry_wait", 10) * (attempt + 1))


# ---------------------------------------------------------------- prompts

GENERATE = """{brief}

Produce a complete draft that answers the brief.

Rules that apply to every claim you make:
- cite a verifiable source for every factual and legal proposition;
- mark anything you could not verify as "unverified" rather than omitting it or softening it;
- end with the open questions a professional would still need to resolve.

You are one of several drafters working independently. Do not hedge toward a middle position:
write what you actually conclude, so that a later stage can see where the drafts disagree.
"""

CONSOLIDATE = """{brief}

Below are {n} independent drafts, labelled R1 to R{n}. The labels carry no information about
which system produced which draft, and you should not speculate.

{drafts}

Merge them into one document, under these rules:
1. Prefer claims that several drafts support, or that carry a verifiable citation.
2. Keep material found in a single draft when it carries a verifiable citation.
3. Where drafts conflict, resolve it with evidence or flag the conflict in the text. Agreement
   between drafts is agreement, not proof: several drafts repeating an unsourced claim do not
   make it a citation.
4. Add new material only if you can verify it yourself, and mark what you added.
5. Tag each substantive claim with the drafts that support it, as [R1, R3].

Then write a consolidation log with three sections: what the drafts agreed on, what they
disagreed on and how each conflict was resolved, and what you dropped and why.

Return the document, then the line ---LOG--- , then the log.
"""

VERIFY = """{brief}

Below is a consolidated document. Your task is verification, not rewriting. Do not return an
improved document.

{document}
{prior}
Check, in this order:
1. Every citation: does the source exist, and does it say what the document says it says?
2. The reasoning: gaps, overstatement, claims stronger than the evidence behind them.
3. The brief: is anything it asked for missing?

Report findings ranked Critical, Major, Minor. For each: what is wrong, where, and what would
fix it. End with one line: VERDICT: approve | approve with fixes | reject.
"""

PRIOR = """
A previous reviewer reported the following. Confirm, dispute or extend each finding; you are
not bound by it, and a finding you cannot substantiate should be marked as such.

{v1}
"""


# ---------------------------------------------------------------- pipeline

def write(run_dir, name, text):
    path = os.path.join(run_dir, name)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return {"file": name, "sha256_16": sha(text), "chars": len(text), "written": now()}


def save_manifest(run_dir, manifest):
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)


def stage(cfg, run_dir, manifest, name, role, filename, prompt, **extra):
    """Run one role once. A completed stage is its file on disk: it is loaded, never re-run."""
    path = os.path.join(run_dir, filename)
    if os.path.exists(path):
        return read(path)
    write(run_dir, f"prompts/{filename}", prompt)
    started = now()
    res = ask(cfg, role, prompt, run_dir)
    if res is None:
        return None
    rec = write(run_dir, filename, res["text"])
    rec.update({"stage": name, "role": role["name"], "provider": role["provider"],
                "family": family(cfg, role), "model": role.get("model"), "started": started,
                "seconds": res["seconds"], "manual": res.get("manual", False),
                "search_requested": bool(role.get("search")), "search_applied": res["search_applied"],
                "prompt_file": f"prompts/{filename}", "prompt_sha256_16": sha(prompt)})
    rec.update(extra)
    manifest["stages"].append(rec)
    return res["text"]


def run_pipeline(cfg, run_dir, manifest):
    formula_name = manifest["formula"]
    formula = cfg["formulas"][formula_name]
    settings = cfg.get("settings", {})
    manifest["role_problems"] = validate(cfg, formula_name)
    manifest["roles_enforced"] = settings.get("enforce_roles", True)
    brief = read(os.path.join(run_dir, "brief.md"))

    # Stage 1: isolated generation. Each generator receives the brief and nothing else.
    gens = formula["generators"]
    print(f"stage 1: {len(gens)} generators, in parallel, no cross-visibility")

    def one(g):
        try:
            text = stage(cfg, run_dir, manifest, "generate", g, f"draft-{g['name']}.md",
                         GENERATE.format(brief=brief))
            return g, text, None
        except Exception as e:                                        # noqa: BLE001
            return g, None, str(e)[:200]

    drafts, waiting = {}, []
    with ThreadPoolExecutor(max_workers=max(1, len(gens))) as pool:
        for g, text, err in pool.map(one, gens):
            if err:
                print(f"  {g['name']}: failed: {err}")
                manifest["failures"].append({"stage": "generate", "role": g["name"], "error": err, "at": now()})
            elif text is None:
                print(f"  {g['name']}: manual stage waiting, see MANUAL-{g['name']}.md")
                waiting.append(g["name"])
            else:
                drafts[g["name"]] = text
                hits = sorted(set(m.group(0) for m in SELF_ID.finditer(text)))
                if hits:
                    print(f"  {g['name']}: names its maker ({hits[0]}); blinding weakened, recorded")
                    manifest.setdefault("self_identification", {})[g["name"]] = hits
                print(f"  {g['name']}: {len(text)} chars")

    if waiting:
        save_manifest(run_dir, manifest)
        print(f"\nwaiting on manual stages: {', '.join(waiting)}. Fill them in, then resume.")
        return manifest
    minimum = settings.get("min_generators", 3)
    if len(drafts) < minimum:
        save_manifest(run_dir, manifest)
        sys.exit(f"only {len(drafts)} drafts succeeded; min_generators is {minimum}. "
                 f"Fix the failed generators and resume; a council of two is not a council.")

    # Stage 2: blind consolidation. Order is random, and the map lives only in the manifest.
    if not os.path.exists(os.path.join(run_dir, "consolidation.md")) and \
            set(manifest.get("label_map", {}).values()) != set(drafts):
        names = sorted(drafts)
        seed = random.SystemRandom().randrange(10 ** 9)
        random.Random(seed).shuffle(names)
        manifest["label_map"] = {f"R{i}": n for i, n in enumerate(names, 1)}
        manifest["label_seed"] = seed
    order = [manifest["label_map"][f"R{i}"] for i in range(1, len(manifest["label_map"]) + 1)]
    print(f"stage 2: consolidation, {len(order)} drafts anonymised as R1..R{len(order)}")
    blocks = "\n\n".join(f"### R{i}\n\n{drafts[n]}" for i, n in enumerate(order, 1))
    cons = formula["consolidator"]
    merged = stage(cfg, run_dir, manifest, "consolidate", cons, "consolidation.md",
                   CONSOLIDATE.format(brief=brief, n=len(order), drafts=blocks))
    if merged is None:
        save_manifest(run_dir, manifest)
        print("manual consolidation waiting, see MANUAL-consolidator.md")
        return manifest
    document, _, log = merged.partition("---LOG---")
    document = document.strip()
    if not os.path.exists(os.path.join(run_dir, "consolidated.md")):
        manifest["derived"] = [write(run_dir, "consolidated.md", document)]
        if log.strip():
            manifest["derived"].append(write(run_dir, "consolidation-log.md", log.strip()))
        else:
            print("  consolidator wrote no ---LOG--- section; recorded")
            manifest["derived"].append({"file": "consolidation-log.md", "missing": True})

    # Stages 3 and 4: two critics. The second reads the first's report and comes from another vendor.
    reports = []
    for i, k in enumerate(formula["critics"], 1):
        print(f"stage {2 + i}: {k['name']} ({family(cfg, k)})")
        prior = PRIOR.format(v1=reports[-1]) if (i > 1 and settings.get("critic2_sees_critic1", True)) else ""
        report = stage(cfg, run_dir, manifest, "verify", k, f"verification-{i}-{k['name']}.md",
                       VERIFY.format(brief=brief, document=document, prior=prior),
                       position=i, saw_previous_report=bool(prior))
        if report is None:
            save_manifest(run_dir, manifest)
            print(f"manual critic stage waiting, see MANUAL-{k['name']}.md")
            return manifest
        reports.append(report)
        lines = [ln.strip() for ln in report.splitlines() if ln.strip().upper().startswith("VERDICT")]
        manifest.setdefault("verdicts", {})[k["name"]] = lines[-1] if lines else "(no verdict line)"
        print(f"  {manifest['verdicts'][k['name']]}")

    manifest["finished"] = now()
    save_manifest(run_dir, manifest)
    print("\ndone. The deliverable is consolidated.md plus both verification reports.")
    print("The pipeline does not apply the critics' fixes. A person decides which to apply,")
    print("and remains accountable for the text that leaves the room.")
    return manifest


# ---------------------------------------------------------------- commands

def cmd_run(cfg, a):
    if a.formula not in cfg["formulas"]:
        sys.exit(f"no formula '{a.formula}' in config; have: {', '.join(cfg['formulas'])}")
    validate(cfg, a.formula)
    brief = read(a.brief)
    for p in a.materials or []:
        brief += f"\n\n--- ATTACHED MATERIAL: {os.path.basename(p)} ---\n{read(p)}"
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(a.runs, f"{stamp}-{a.formula}")
    os.makedirs(run_dir, exist_ok=True)
    write(run_dir, "brief.md", brief)
    shutil.copy(a.config, os.path.join(run_dir, "config-used" + os.path.splitext(a.config)[1]))
    manifest = {"started": now(), "formula": a.formula, "brief_source": a.brief,
                "materials": a.materials or [], "brief_sha256_16": sha(brief),
                "config_sha256_16": sha(read(a.config)), "stages": [], "failures": []}
    save_manifest(run_dir, manifest)
    run_pipeline(cfg, run_dir, manifest)
    print(f"run directory: {run_dir}")
    return 0


def cmd_resume(cfg, a):
    if not a.run:
        sys.exit("resume needs --run runs/<id>")
    manifest = json.loads(read(os.path.join(a.run, "manifest.json")))
    if manifest.get("finished"):
        print("this run is already finished; nothing to do")
        return 0
    run_pipeline(cfg, a.run, manifest)
    return 0


def cmd_status(cfg, a):
    if not a.run:
        sys.exit("status needs --run runs/<id>")
    manifest = json.loads(read(os.path.join(a.run, "manifest.json")))
    f = cfg["formulas"][manifest["formula"]]
    expected = [f"draft-{g['name']}.md" for g in f["generators"]] + ["consolidation.md"] + \
               [f"verification-{i}-{k['name']}.md" for i, k in enumerate(f["critics"], 1)]
    for name in expected:
        present = os.path.exists(os.path.join(a.run, name))
        waiting = os.path.exists(os.path.join(a.run, "MANUAL-" + name.split("-", 1)[1].rsplit(".", 1)[0] + ".md")) \
            if name.startswith(("draft-", "verification-")) else False
        print(f"  {'done   ' if present else ('manual ' if waiting else 'todo   ')} {name}")
    print(f"  {'finished ' + manifest['finished'] if manifest.get('finished') else 'not finished'}")
    return 0


def cmd_check(cfg, a):
    """Validate every formula and ask every configured model one trivial question."""
    bad = 0
    for fname in cfg["formulas"]:
        problems = validate(cfg, fname, enforce=False)
        for p in problems:
            print(f"  formula {fname}: {p}")
        bad += len(problems)
    seen = set()
    for f in cfg["formulas"].values():
        for r in list(f["generators"]) + [f["consolidator"]] + list(f["critics"]):
            kid = (r["provider"], r.get("model"))
            if kid in seen:
                continue
            seen.add(kid)
            if cfg["providers"][r["provider"]]["type"] == "manual":
                print(f"  manual   {r['name']} ({family(cfg, r)})")
                continue
            try:
                out = ask(dict(cfg, settings=dict(cfg.get("settings", {}), retries=0)),
                          dict(r, search=False), "Reply with the single word: ready", ".")
                ok = bool(out) and "ready" in out["text"].lower()
                print(f"  {'ok  ' if ok else 'odd '}     {r.get('model')} ({r['provider']})")
                bad += 0 if ok else 1
            except Exception as e:                                    # noqa: BLE001
                print(f"  FAILED   {r.get('model')} ({r['provider']}): {str(e)[:120]}")
                bad += 1
    print("\nall formulas valid and all configured models answered." if not bad else f"\n{bad} problem(s).")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "resume", "status", "check"])
    ap.add_argument("--brief", default="briefs/example_brief.md")
    ap.add_argument("--materials", nargs="*", help="text files appended to the brief, identical for every model")
    ap.add_argument("--formula", default="basic")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--runs", default=RUNS, help="directory that holds run directories")
    ap.add_argument("--run", default=None, help="run directory, for resume and status")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    return {"run": cmd_run, "resume": cmd_resume, "status": cmd_status, "check": cmd_check}[a.command](cfg, a)


if __name__ == "__main__":
    sys.exit(main())
