# The protocol

_This is the text that appears as a worked example in the paper, written so that it can be read without the code and reproduced without this repository._

# One Assistance Architecture, Specified So It Can Be Run

The argument of this article is that "AI assistance" names a family of architectures with different failure properties. The claim is easier to test once at least one architecture is stated precisely enough to be run and criticized. The protocol below is such a statement. It is one example among many possible ones, it uses only public models, and anyone with consumer or API access to three vendors can reproduce it.

## The problem it addresses

A self-represented litigant can reach several frontier models at no cost. The common practice is to ask one, read the answer and file it. The documented failure is a confident model producing a citation that does not exist, with nothing in the process positioned to catch it. The protocol replaces the single ask with a common task statement and four stages that follow it. It leaves each model exactly as accurate as it was; it arranges several so that one system's error has to survive contact with systems trained by other organizations, and it records what each of them said.

## Roles

The protocol is defined by what each role is allowed to see. Three rules fix it:

1. Generators see the task statement and nothing else. None sees another generator's draft.
2. The consolidator sees every draft under neutral labels R1 to Rn, in a random order. It never learns which vendor produced which draft.
3. The last reader is a critic from a different vendor than the consolidator. It sees the consolidated document and the first critic's report, and its verdict closes the run.

Any set of frontier models from different vendors that satisfies the three rules runs the protocol. As an illustration, these are public models that were available in September 2026 and could fill the roles:

| Role | Routine documents | High-stakes documents |
|---|---|---|
| Generators, isolated | `claude-sonnet-5` with search; `gpt-5.6-terra` with search; `gemini-3.1-pro-high` with search; an open-weight model | `claude-opus-5` with search; `gpt-6-astra` with search; `gemini-3.1-pro-high` with search; Grok (xAI); an open-weight model |
| Consolidator, blind | `claude-sonnet-5` | `claude-fable-5-1` |
| Critic 1, consolidator's family, fresh context | `claude-sonnet-5` | `claude-fable-5-1` |
| Critic 2, different vendor, reads last | `gpt-5.6-terra` | `gpt-6-astra` |

The table is an illustration of what was available, and the identifiers will age. The roles will not. Grok and the open-weight model are named by vendor because their hosted identifiers vary from host to host. The high-stakes column adds a fifth generator, and its consolidator is a model that wrote no draft, so it never judges its own text under a label.

## Stages

**Stage 0. One task statement.** A single written statement sets out the objective, the jurisdiction, the required format, what counts as a source, and what to do with a claim that cannot be verified. Every model receives it unchanged, so that differences between drafts come from the models.

**Stage 1. Isolated generation.** Each generator produces a complete draft in parallel, each with web search enabled, and with deep research where the task calls for depth. Each is required to cite a verifiable source for every factual and legal proposition, to mark what it could not verify as unverified, and to close with its open questions. Isolation is the mechanism. Models built by different organizations on different corpora invent different things, and a claim that several of them produce independently, each with its own citation, stands in a different evidential position from a claim one of them produced alone. A drafter that sees another draft agrees with it for reasons unrelated to whether the claim is true.

**Stage 2. Blind consolidation.** One model receives the drafts as R1 to Rn, in an order chosen at random and recorded only in the run manifest, and merges them under explicit rules. Claims supported by several drafts or by a verifiable citation are preferred. Material found in a single draft is kept when it carries a verifiable citation. Conflicts are resolved with evidence or flagged in the text. Agreement between drafts is recorded as agreement and never promoted to proof. New material enters only if the consolidator verifies it itself, and is marked as added. Each substantive claim carries a tag naming the drafts that support it. The consolidator also writes a log: what the drafts agreed on, what they disagreed on and how each conflict was resolved, and what was dropped and why. The log is where the disagreement survives. Because the label map is kept, a later reader can set the tags against it and measure how often the consolidator preferred its own vendor's draft.

**Stage 3. Internal verification.** A critic from the consolidator's family reads the merged document in a fresh context, with no memory of the consolidation. Its task is verification, and it returns no improved document. It checks every citation for existence and accuracy, tests the reasoning for gaps and overstatement, confirms the task statement was met, and reports findings ranked Critical, Major and Minor with a verdict: approve, approve with fixes, or reject.

**Stage 4. Cross-vendor verification.** A critic from a different vendor reads the same document and the first report. It confirms, disputes or extends each finding, adds its own, and gives the closing verdict. The stage exists because of the weakness of the two before it: a consolidator checked by its own family shares that family's blind spots, and a reader trained elsewhere is the most direct route to them.

## What leaves the pipeline

The deliverable is the consolidated document, the consolidation log, both verification reports and a manifest. No stage overwrites the document with a critic's output. A person reads the reports and decides which fixes to apply. In litigation the person signing the filing is accountable for its contents, and a pipeline that silently rewrote the text would obscure who decided what.

The manifest records, for every stage, the model identifier, the prompt hash, the output hash, the start time and the duration, together with the label map. Without it, a document prepared this way is indistinguishable from one produced by asking a single model twice. With it, a reader who was not present can verify that the generators were independent, that the consolidator was blind, and that the last reader came from another vendor.

```
INPUT:  task statement B; generators G[1..n]; consolidator C; critics K1, K2

1. drafts   <- PARALLEL for g in G: g.generate(B)          # no cross-visibility
2. labelled <- shuffle(drafts) as R1..Rn                    # map kept in the manifest only
3. D, log   <- C.consolidate(B, labelled)                   # claims tagged [R1, R3]
4. V1       <- K1.verify(B, D)                              # C's family, fresh context
5. V2       <- K2.verify(B, D, V1)                          # other vendor; closing verdict

OUTPUT: D, log, V1, V2, manifest(identifiers, prompt and output hashes, timestamps, label map)
```

## Limits

The deep-research modes of the consumer interfaces have no exact equivalent in the vendor APIs. A stage that needs one is run by hand: the prompt is written to a file, the operator runs it in the interface and pastes the answer back, and the manifest records that the stage was run that way. That fallback is manual, and a protocol that depends on it inherits the accessibility limit it creates.

Agreement between models is evidence of correlation as much as of truth. Models trained on overlapping corpora share errors, and a unanimous set of drafts can be wrong together. The protocol lowers the correlation it can reach and records the rest.

The protocol has not been compared with single-model prompting. The comparison that would settle its value is a blind assessment: the same tasks prepared both ways, the resulting documents scored by readers who do not know which is which, on citation accuracy, completeness against the task statement, and errors a court would notice. The protocol is stated here so that this comparison can be run.

A reference implementation of the protocol, with the configuration above and the manifest format, is published under an open license at https://github.com/vadimchernets/docprep, so that the comparison can be run by anyone. The repository contains the runnable pipeline, the configuration, the offline tests that check the role constraints, and this appendix as a standalone specification.
