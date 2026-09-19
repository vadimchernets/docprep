# docprep: one assistance architecture, stated so it can be run

Four stages: isolated generation, blind consolidation, internal verification, cross-vendor
verification. Several frontier models draft the same brief without seeing each other, one merges
the drafts without knowing who wrote which, and two critics from different vendors check the
result. Every run leaves a manifest of model identifiers, prompt and output hashes, timestamps
and the label map.

This is the reference implementation of the protocol described in **[PROTOCOL.md](PROTOCOL.md)**,
the same text that appears as a worked example in:

> Vadym Chernets, *The Missing Variable in AI-Assisted Litigation: Architecture and the Quality
> of Pro Se Access to Justice*, [SSRN 7120940](https://ssrn.com/abstract=7120940).

The protocol is one example of an assistance architecture, offered because a claim that
architecture is a variable is worth little until someone states an architecture precisely enough
to be checked, run and criticized. The models in `config.example.yaml` illustrate what was
publicly available in September 2026. They are not a requirement.

## How this relates to work you may already know

This design belongs to a family the machine-learning literature calls **multi-agent debate**,
**LLM council**, **mixture-of-agents** and **LLM ensemble**, and the checking step is an instance
of **LLM-as-a-judge**. Four things distinguish the protocol implemented here, and each is enforced
by `validate()` rather than left to the operator:

1. **The generators never read one another.** There is no debate round. Independent evaluations of
   debate structures report that extending discussion can make agents reinforce each other's
   mistakes, so the drafts are produced in isolation and meet only at consolidation.
2. **The consolidating model does not know which vendor wrote which draft.** Drafts arrive under
   labels R1…Rn and a label map is written to the manifest afterwards. The established name for the
   effect this addresses is **self-preference bias**: a model rates its own output higher when it
   can tell which output is its own. Keeping the map makes that bias measurable after the fact
   instead of merely hoped away.
3. **Two critics in sequence, and the second is from a different vendor.** A same-family critic
   catches what the family knows to look for; a cross-vendor critic catches what the family shares.
4. **Every run leaves a manifest**: model identifiers, prompt and output hashes, timestamps, the
   label map. A run that produces no log writes its manifest and exits rather than reporting success.

Agreement among models is not proof. Where their errors are correlated, several answers carry less
independent evidence than their number suggests; that argument is made separately in
*Agreement Is Not Independent Evidence* ([SSRN 7390698](https://ssrn.com/abstract=7390698)).
The manifest exists so that a reader can check what happened, not so that the output can be trusted
because a machine produced it.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml      # set the identifiers your accounts expose
export ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GEMINI_API_KEY=...

python3 docprep.py check                # roles valid, every model answers?
python3 docprep.py run --brief briefs/example_brief.md --formula enhanced
python3 docprep.py status --run runs/<id>
```

A run writes `runs/<timestamp>-<formula>/` containing the brief as sent, every prompt, every
draft, the consolidated document, the consolidation log, both verification reports and
`manifest.json`. The deliverable is the document **plus both reports**. The pipeline never
applies a critic's fixes. A person decides which to apply and stays accountable for the text
that leaves the room.

## Roles, not brands

The protocol is defined by what each stage is allowed to see, and `check` refuses a
configuration that breaks it:

- generators cannot see each other;
- the consolidator receives the drafts as R1..Rn in a random order; the map lives only in the manifest;
- the last critic comes from a different vendor family than the consolidator;
- generators span at least three vendor families.

## Manual stages

Set a role's provider to `manual` when the interface has no API equivalent, as with the
deep-research modes, and give the role a `family:`. The pipeline writes `MANUAL-<role>.md`,
stops, and continues with `resume` once the answer is pasted under the marker line. A completed
stage is a file on disk: `resume` never repeats a stage that already has one, so a manual step
or a failed call never repeats paid calls. The manifest records manual stages as manual.

## Tests

`python3 tests/test_offline.py` runs the whole pipeline against a fake `httpx`, without keys or
network: API path with a paused Anthropic turn, manual path stage by stage, resume without
repeated calls, and refusal of a same-family last critic.

## Licence

MIT for the code. `PROTOCOL.md` is CC BY 4.0, matching the paper.
