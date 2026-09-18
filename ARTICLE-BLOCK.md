# A Worked Example: One Assistance Architecture, Stated So It Can Be Run

The argument of this article is that "AI assistance" names a family of architectures with different failure properties. The claim is easier to test once at least one architecture is stated precisely enough to be run and criticised. The protocol below is such a statement. It is one example among many possible ones, it uses only public models, and anyone with consumer or API access to three vendors can reproduce it.

## The problem it addresses

A self-represented litigant can reach several frontier models at no cost. The common practice is to ask one, read the answer and file it. The documented failure is a confident model producing a citation that does not exist, with nothing in the process positioned to catch it. The protocol replaces the single ask with four stages. It leaves each model exactly as accurate as it was; it arranges several so that one system's error has to survive contact with systems trained by other organisations, and it records what each of them said.

## Roles

The protocol is defined by what each role is allowed to see. Three rules fix it:

1. Generators see the brief and nothing else. None sees another generator's draft.
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

**Stage 0. One brief.** A single written brief states the objective, the jurisdiction, the required format, what counts as a source, and what to do with a claim that cannot be verified. Every model receives it unchanged, so that differences between drafts come from the models.

**Stage 1. Isolated generation.** Each generator produces a complete draft in parallel, with web search or deep research where the interface offers it. Each is required to cite a verifiable source for every factual and legal proposition, to mark what it could not verify as unverified, and to close with its open questions. Isolation is the mechanism. Models built by different organisations on different corpora invent different things, and a claim that several of them produce independently, each with its own citation, stands in a different evidential position from a claim one of them produced alone. A drafter that sees another draft agrees with it for reasons unrelated to whether the claim is true.

**Stage 2. Blind consolidation.** One model receives the drafts as R1 to Rn, in an order chosen at random and recorded only in the run manifest, and merges them under explicit rules. Claims supported by several drafts or by a verifiable citation are preferred. Material found in a single draft is kept when it carries a verifiable citation. Conflicts are resolved with evidence or flagged in the text. Agreement between drafts is recorded as agreement and never promoted to proof. New material enters only if the consolidator verifies it itself, and is marked as added. Each substantive claim carries a tag naming the drafts that support it. The consolidator also writes a log: what the drafts agreed on, what they disagreed on and how each conflict was resolved, and what was dropped and why. The log is where the disagreement survives. Because the label map is kept, a later reader can set the tags against it and measure how often the consolidator preferred its own vendor's draft.

**Stage 3. Internal verification.** A critic from the consolidator's family reads the merged document in a fresh context, with no memory of the consolidation. Its task is verification, and it returns no improved document. It checks every citation for existence and accuracy, tests the reasoning for gaps and overstatement, confirms the brief was met, and reports findings ranked Critical, Major and Minor with a verdict: approve, approve with fixes, or reject.

**Stage 4. Cross-vendor verification.** A critic from a different vendor reads the same document and the first report. It confirms, disputes or extends each finding, adds its own, and gives the closing verdict. The stage exists because of the weakness of the two before it: a consolidator checked by its own family shares that family's blind spots, and a reader trained elsewhere is the most direct route to them.

## What leaves the pipeline

The deliverable is the consolidated document, the consolidation log, both verification reports and a manifest. No stage overwrites the document with a critic's output. A person reads the reports and decides which fixes to apply. In litigation the person signing the filing is accountable for its contents, and a pipeline that silently rewrote the text would obscure who decided what.

The manifest records, for every stage, the model identifier, the prompt hash, the output hash, the start time and the duration, together with the label map. Without it, a document prepared this way is indistinguishable from one produced by asking a single model twice. With it, a reader who was not present can verify that the generators were independent, that the consolidator was blind, and that the last reader came from another vendor.

```
INPUT:  brief B; generators G[1..n]; consolidator C; critics K1, K2

1. drafts   <- PARALLEL for g in G: g.generate(B)          # no cross-visibility
2. labelled <- shuffle(drafts) as R1..Rn                    # map kept in the manifest only
3. D, log   <- C.consolidate(B, labelled)                   # claims tagged [R1, R3]
4. V1       <- K1.verify(B, D)                              # C's family, fresh context
5. V2       <- K2.verify(B, D, V1)                          # other vendor; closing verdict

OUTPUT: D, log, V1, V2, manifest(identifiers, prompt and output hashes, timestamps, label map)
```

## The legal envelope

An architecture that lowers error correlation by adding vendors raises, by the same act, the
number of places where the material leaves. For a self-represented litigant in a United States
court that trade is not abstract, and the position as of September 2026 is this.

No federal rule requires a filer to disclose the use of AI or to name a model. The Advisory
Committee on Civil Rules took a Rule 11 amendment off its agenda in April 2026, finding that
rulemaking would not be appropriate at that time, and proposed Federal Rule of Evidence 707,
which governs the admissibility of machine-generated evidence rather than disclosure, had not
been adopted. Individual judges have filled the gap: the Ropes & Gray tracker recorded 145
standing orders and local rules requiring disclosure or verification as of June 2026, and the
requirements differ. The Northern District of Texas asks for the fact of AI use on the first
page of a brief and does not ask which model. Judge Vaden of the Court of International Trade
asks for the program used and the specific portions of text it produced.

Material under a protective order is the harder case, and it reaches this architecture directly.
In *Morgan v. V2X, Inc.*, No. 25-cv-01991 (D. Colo., 30 March 2026), the court allowed a
self-represented plaintiff to put confidential discovery material into an AI service only where
the provider is contractually bound not to train on the input, not to disclose it, and to delete
it on request, and it ordered the plaintiff to identify the tool used. The court observed that
this condition excludes most mainstream low-to-no-cost AI, which is the tier this architecture
is designed to run on. Five free consumer accounts are five disclosures.

Whether the work survives as work product is unsettled. *Warner v. Gilbarco Inc.* (E.D. Mich.,
10 February 2026) treated a self-represented litigant's AI-assisted preparation as work product.
*United States v. Heppner* (S.D.N.Y., 17 February 2026) held that material produced through a
public consumer AI tool, without an attorney's direction, was not protected. A litigant choosing
between these architectures is also choosing between two lines of authority.

Three requirements follow, and they belong with the architecture rather than after it.

1. Public filings and one's own material may go to the generators. Sealed material, material
   under a protective order, and another party's confidential discovery do not, unless the order
   permits it and the provider's terms meet the *Morgan* condition. The manifest makes the
   exposure auditable; it does not make it lawful.
2. The manifest is the disclosure. It records which model identifier produced which artefact and
   when, which is what a court asking for the program used will want, and is worth keeping
   whether or not the presiding judge asks.
3. Verification of every citation against its source is done by a person. In the database of
   decisions recording fabricated citations, self-represented litigants account for 1,174 of
   2,041 cases as of 17 September 2026, more than the 811 attributed to lawyers. Rule 11(b)
   reaches an unrepresented party by its terms, and courts have said there is no pro se exception
   to it. Agreement among models and approval by two critics are not verification.

This is a description of the legal position and not legal advice. Requirements vary by district
and by judge, and the standing order of the presiding judge governs.

## Limits

The deep-research modes of the consumer interfaces have no exact equivalent in the vendor APIs. A stage that needs one is run by hand: the prompt is written to a file, the operator runs it in the interface and pastes the answer back, and the manifest records the stage as manual. This is slower, and it is a truthful record of what was done.

Agreement between models is evidence of correlation as much as of truth. Models trained on overlapping corpora share errors, and a unanimous set of drafts can be wrong together. The protocol lowers the correlation it can reach and records the rest.

The protocol has not been compared with the single-model practice it replaces. The comparison that would settle its value is a blind assessment: the same briefs prepared both ways, the resulting documents scored by readers who do not know which is which, on citation accuracy, completeness against the brief, and errors a court would notice. The protocol is stated here so that this comparison can be run.

A reference implementation of the protocol, with the configuration above and the manifest format, is published under an open licence at the repository cited in the references, so that the comparison can be run by anyone.

---

**Figure caption (for the SVG in `figure-protocol.svg`):**

Figure N. One assistance architecture, drawn by role. Stage 0: one brief, identical for every model. Stage 1: generators draft in isolation, four for routine documents and five for high-stakes ones. Drafts are shuffled and relabelled R1 to Rn; the map is kept only in the manifest. Stage 2: the consolidator merges the drafts blind and writes a log. Stage 3: a critic from the consolidator's family verifies the document in a fresh context and returns report V1. Stage 4: a critic from a different vendor reads the document and V1 and returns the closing verdict V2. Critics report and never rewrite; a person decides which fixes to apply. Public models available in September 2026 that could fill the roles: `claude-sonnet-5` or `claude-fable-5-1` (consolidator and critic 1), `gpt-5.6-terra` or `gpt-6-astra` (critic 2), and generators from Anthropic, OpenAI, Google, xAI and an open-weight model.
