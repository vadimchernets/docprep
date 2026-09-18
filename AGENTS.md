# Instructions for an agent running this repository

Start here, and do not invent a different workflow.

1. `python3 docprep.py check --config config.yaml` confirms the roles are valid and every
   configured model answers. If it fails, fix the identifier, the key or the formula first.
2. Write the brief as a single file under `briefs/`: objective, jurisdiction, output format,
   what counts as a source, what to do with a claim that cannot be verified. Every model
   receives it unchanged. Supporting files go in `--materials`, and they too reach every model.
3. `python3 docprep.py run --brief briefs/<file>.md --formula enhanced`
4. `python3 docprep.py status --run runs/<id>` shows which stages are done, waiting or missing.

## Rules you may not relax

- **Generators never see each other.** If one fails, resume; do not paste another draft into it.
- **The consolidator never learns which vendor wrote which draft.** The labels R1..Rn are
  shuffled at random and the map lives only in `manifest.json`. Do not decode it for the model.
- **The last critic comes from a different vendor than the consolidator.** The script refuses
  any other configuration. Do not set `enforce_roles: false` to get around it.
- **Do not apply the critics' fixes.** The deliverable is the document plus both reports.
  A person decides.
- **Do not invent a model identifier.** If you cannot verify one, set the role to `manual`
  and give it a `family:`.
- **Do not edit anything inside `runs/`.** It is the audit trail. The one exception is pasting
  an answer under the marker line of a `MANUAL-<role>.md` file.

## When a stage says it is waiting

A role with provider `manual` writes `MANUAL-<role>.md` and stops. Tell the operator which
file to run in which interface, in a fresh session. Do not write the answer yourself. When the
answer is pasted under the marker line: `python3 docprep.py resume --run runs/<id>`. Resume
loads every stage that already has a file and runs only what is missing.

## What to report back

The run directory, the `verdicts` from `manifest.json`, any finding ranked Critical in either
report, and any `self_identification` entry (a draft that named its own maker weakens the
blinding). Do not summarise the document itself: the point of the run is that a person reads it.
