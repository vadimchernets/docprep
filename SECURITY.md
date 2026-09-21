# Security

docprep reads API keys and sends text to several model providers, so safety problems matter.

## Reporting a vulnerability

Please do not open a public issue. Open a private security advisory instead: repository page, then "Security",
then "Report a vulnerability". Describe what you found, how to reproduce it, and what it lets someone do. You will
get a reply as soon as possible.

## In scope

- How API keys are read, stored or written anywhere, including the run folder and `manifest.json`.
- Text reaching a provider that the brief or the configuration did not send there.
- A way around the role checks, for example a drafter that sees another drafter's text or the consolidator that
  learns which model wrote which draft.

Supported version: the latest commit on `main`.
