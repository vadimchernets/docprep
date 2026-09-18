# The protocol

_This is the text of the appendix to the paper “The Missing Variable in AI-Assisted Litigation: Architecture and the Quality of Pro Se Access to Justice” (SSRN 7120940), reproduced here so the specification can be read and run without the paper. It is kept identical to the published appendix; where it says “Part II”, “Part IV”, “Part VI.A” or “note 24” it is pointing into that paper. The figure is `figure-protocol.svg`._

# One Assistance Architecture, Specified So It Can Be Run

The argument of this article is that "AI assistance" names a family of architectures with different failure properties. The claim is easier to test once at least one architecture is stated precisely enough to be run and criticized. The protocol below is such a statement. It is one example among many possible ones, it uses only public models, and anyone with consumer or API access to three vendors can reproduce it.

## The problem it addresses

A self-represented litigant can reach several frontier models through free consumer tiers, and cost, digital access and technical fluency remain barriers: the high-stakes column below is paid API access, and the confidentiality condition set out later excludes most free tiers for the material that most needs protection. The common practice is to ask one, read the answer and file it. The documented failure is a confident model producing a citation that does not exist, with nothing in the process positioned to catch it. The protocol replaces the single ask with a common task statement and four stages that follow it. It leaves each model exactly as accurate as it was; it arranges several so that one system's error has to survive contact with systems trained by other organizations, and it records what each of them said.

## Roles

The protocol is defined by what each role is allowed to see. Four rules fix it:

1. Generators see the task statement and nothing else. None sees another generator's draft.
2. The consolidator sees every draft under neutral labels R1 to Rn, in a random order. It never learns which vendor produced which draft.
3. The first critic reads inside the consolidator's own family, in a fresh context. It sees the task statement and the consolidated document, and nothing of the consolidation that produced it.
4. The last reader is a critic from a different vendor than the consolidator. It sees the consolidated document and the first critic's report, and its verdict closes the run.

Any set of frontier models from different vendors that satisfies the four rules runs the protocol. As an illustration, these are public models that were available in September 2026 and could fill the roles:

| Role | Routine documents | High-stakes documents |
|---|---|---|
| Generators, isolated | `claude-sonnet-5` with search; `gpt-5.6-terra` with search; `gemini-3.1-pro-high` with search; an open-weight model | `claude-opus-5` with search; `gpt-6-astra` with search; `gemini-3.1-pro-high` with search; Grok (xAI); an open-weight model |
| Consolidator, blind | `claude-sonnet-5` | `claude-fable-5-1` |
| Critic 1, consolidator's family, fresh context | `claude-sonnet-5` | `claude-fable-5-1` |
| Critic 2, different vendor, reads last | `gpt-5.6-terra` | `gpt-6-astra` |

The table is an illustration of what was available, and the identifiers will age. The roles will not. Grok and the open-weight model are named by vendor because their hosted identifiers vary from host to host, and `gemini-3.1-pro-high` is the alias of a hosted interface rather than the model code in the vendor's API documentation. The high-stakes column adds a fifth generator, and its consolidator is a model that wrote no draft, so it never judges its own text under a label.

The assignment of families to roles is the author's, and it rests on his own use rather than on a measurement. Across roughly two thousand hours of work with these systems in 2025 and 2026, a model placed in a fresh context as a blind critic returned the strictest and most useful verification when it came from the same family as the consolidator, and it did so even where the text under review had been produced by that family. Critics from other vendors were not weaker readers; they found different things, which is why the protocol keeps one of them and gives it the closing verdict. This is a self-reported observation, not a result, and it is marked off here so that a reader can discount it and still have the protocol. Nothing in the protocol depends on it: the three rules are about what each role may see, not about which vendor fills it, and a reader who prefers a different family at the consolidator or at the first critic can substitute one and still be running the protocol.

## Stages

**Stage 0. One task statement.** A single written statement sets out the objective, the jurisdiction, the required format, what counts as a source, and what to do with a claim that cannot be verified. Every model receives it unchanged, so that differences between drafts come from the models.

**Stage 1. Isolated generation.** **Stage 1. Isolated generation.** Each generator produces a complete draft in parallel, with web search enabled wherever the interface or the API carries it, and with deep research where the task calls for depth. The consumer interfaces of these vendors search by default; some programmatic endpoints carry no search tool, and a generator running on one of those is drafting from weights, which the run record must show. Each is required to cite a verifiable source for every factual and legal proposition, to mark what it could not verify as unverified, and to close with its open questions. Isolation is the mechanism. Models built by different organizations on different corpora invent different things, and a claim that several of them produce independently, each with its own citation, stands in a different evidential position from a claim one of them produced alone. A drafter that sees another draft agrees with it for reasons unrelated to whether the claim is true.

**Stage 2. Blind consolidation.** One model receives the drafts as R1 to Rn, in an order chosen at random and recorded only in the run manifest, and merges them under explicit rules. Claims supported by several drafts or by a verifiable citation are preferred for inclusion, which is a rule about what enters the draft and not a finding that they are true. Material found in a single draft is kept when it carries a verifiable citation. Conflicts are resolved with evidence or flagged in the text. Agreement between drafts is recorded as agreement and never promoted to proof. New material enters only if the consolidator verifies it itself, and is marked as added. Each substantive claim carries a tag naming the drafts that support it. The consolidator also writes a log: what the drafts agreed on, what they disagreed on and how each conflict was resolved, and what was dropped and why. The log is where the disagreement survives. Because the label map is kept, a later reader can set the tags against it and measure how often the consolidator preferred its own vendor's draft.

**Stage 3. Internal verification.** A critic from the consolidator's family reads the merged document in a fresh context, with no memory of the consolidation. Its task is verification, and it returns no improved document. It checks every citation for existence and accuracy, tests the reasoning for gaps and overstatement, confirms the task statement was met, and reports findings ranked Critical, Major and Minor with a verdict: approve, approve with fixes, or reject.

**Stage 4. Cross-vendor verification.** A critic from a different vendor reads the same document and the first report. It confirms, disputes or extends each finding, adds its own, and gives the closing verdict. The stage exists because of the weakness of the two before it: a consolidator checked by its own family shares that family's blind spots, and a reader trained elsewhere is the most direct route to them.

## What leaves the pipeline

The deliverable is the consolidated document, the consolidation log, both verification reports and a manifest. No stage overwrites the document with a critic's output. A person reads the reports and decides which fixes to apply. In litigation the person signing the filing is accountable for its contents, and a pipeline that silently rewrote the text would obscure who decided what.

The manifest records, for every stage, the model identifier, the prompt hash, the output hash, the start time and the duration, together with the label map. Without it, a document prepared this way is indistinguishable from one produced by asking a single model twice. With it, a reader who was not present can audit the operator's record of the run: which identifier was configured for which role, in what order the drafts were labeled, what each stage received and returned. It is a structured self-report, not a proof. The identifiers come from the configuration rather than from an authenticated response, a stage run by hand carries the operator's word for what happened in the interface, and a record of a search tool being offered is not a record of a source being checked. Making the variable observed rather than reported takes third-party custody of the run, which a file format cannot supply.


## The legal envelope

An architecture that lowers error correlation by adding vendors raises, by the same act, the
number of places where the material leaves. For a self-represented litigant in a United States
court that trade is not abstract.

The position in the United States as of September 2026 has three parts: what a filer must disclose, what may be sent to a provider at all, and whether the work survives as work product. Part II and Table 1 of the article carry the disclosure regime; Part VI.A carries the work-product analysis and its authorities. No generally applicable federal procedural rule requires a filer to disclose the use of AI or to name a model: in April 2026 the Advisory Committee on Civil Rules dropped from its agenda two proposals directed at fabricated authority, agreeing that rulemaking would not be appropriate at that time. Local rules and individual standing orders do require it, and they differ. The Northern District of Texas asks for the fact of AI use on the first page of a brief and does not ask which model. Judge Vaden of the Court of International Trade asks for the program used, for the specific portions of text it produced, and for a certification that the use disclosed no confidential or business proprietary information to an unauthorized party.

Two rulemaking actions of spring 2026 are easy to conflate, and the conflation changes the answer. The Advisory Committee on Civil Rules took up two proposals to amend Rule 11 to address citations of authority that do not exist, agreed that rulemaking would not be appropriate at that time, and dropped the item on April 14, 2026. Three weeks later the Advisory Committee on Evidence Rules took up proposed Federal Rule of Evidence 707, which governs the admissibility of machine-generated evidence rather than the disclosure of AI use; it revised the draft and kept it under study rather than advancing it. The first action concerns what a filer certifies, the second what a court may admit, and neither created a duty to disclose. The two are linked in the record itself, which is why they are read as one: the April memorandum of the Civil Rules committee quotes the draft of Rule 707, and its minutes note that the Evidence Rules committee had that rule under study.

Material another party has designated confidential is the harder case, and it reaches this architecture directly. In *Morgan* the court allowed a self-represented plaintiff to put such material into an AI service only where the provider is contractually bound not to store or use the input to train or improve its model, not to disclose it to third parties except where disclosure is essential to delivering the service and the recipient is bound by equivalent protections, and to remove or delete it on request; it required the plaintiff to name any tool used in connection with that material and to keep written documentation of those safeguards. The court observed that the condition excludes most mainstream low-to-no-cost AI. Those are the terms of one protective order rather than a national rule, and they are the most restrictive the author has located; the protocol adopts them as its own design policy.

Whether AI-assisted preparation survives as work product, and on what facts, is the subject of Part VI.A of the article, which reads the same decisions and explains why *Warner* and *Heppner* do not conflict. Nothing in this Appendix adds to that analysis.

Three constraints follow. They are design rules of this protocol, not statements of what the law requires of a litigant.

1. Public filings and material the operator is free to transmit may go to the models. Sealed material, material under a protective order, and another party's confidential discovery do not, unless the order permits it and the provider's terms meet the condition *Morgan* imposed. The restriction covers every stage and every recipient, not the generators alone: the consolidator and both critics receive the merged draft, and the retained artifacts travel with it. Ownership of a document does not by itself discharge an obligation of confidentiality attached to it. The manifest makes the exposure auditable; it does not make it lawful.

This states operating constraints for the protocol and is not legal advice. Requirements vary by district
and by judge, and the standing order of the presiding judge governs.

## Limits

The deep-research modes of the consumer interfaces have no exact equivalent in the vendor APIs. A stage that needs one is run by hand: the prompt is written to a file, the operator runs it in the interface and pastes the answer back, and the manifest records that the stage was run that way. That fallback is manual, and a protocol that depends on it inherits the accessibility limit it creates.

Agreement between models is evidence of correlation as much as of truth. Models trained on overlapping corpora share errors, and a unanimous set of drafts can be wrong together. The protocol lowers the correlation it can reach and records the rest.

The protocol has not been compared with single-model prompting. The comparison that would settle its value is a blind assessment: the same tasks prepared both ways, the resulting documents scored by readers who do not know which is which, on citation accuracy, completeness against the task statement, and errors a court would notice. The protocol is stated here so that this comparison can be run.

A reference implementation of the protocol, with the configuration above and the manifest format, is published under an open license at https://github.com/vadimchernets/docprep, so that the comparison can be run by anyone. The repository contains the runnable pipeline, the configuration, the offline tests that check the role constraints, and this appendix as a standalone specification.
