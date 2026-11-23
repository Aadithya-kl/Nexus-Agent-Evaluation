# Reproduce a caller integration

This walkthrough is for a developer who wants to inspect a small declared-output gate before deciding whether it helps their workflow. It uses two synthetic support-ticket declarations and no agent, model, API key or runtime dependency. The script retains the reports, errors, environment and fixture hashes so another developer can compare observed results.

The [consumer workflow](../.github/workflows/consumer-smoke.yml) invokes the **published** Action at reviewed commit `1449a910af2ec0de208ce3c1c5469772e89db439`. It does not substitute the local Action implementation. The [copyable workflow](../examples/github-actions/evaluate-agent.yml) uses the same evaluator revision for a caller's own files.

## Run the CLI demonstration

Use Python 3.10+ and a checkout containing [these consumer fixtures](../examples/consumer/cases.json). Until this change is merged, use the `feat/pinned-consumer-demo` review branch. Run from the repository root:

```sh
python examples/consumer/run_demo.py --evaluator evaluator.py --output-dir consumer-results
```

Use a new output directory for each run; the script refuses to reuse one. It copies the caller fixtures there and invokes the evaluator from that separate directory. `--evaluator` accepts an explicit source path, so you can also point it at a separately obtained, reviewed checkout. The saved `evaluator_sha256` identifies the actual file exercised.

| Scenario | Expected evaluator exit | Observable result |
| --- | --- | --- |
| Accepted declarations | 0 | Both cases pass; saved report equals stdout. |
| Critical declaration includes `send_reply_without_review` | 1 | Only one case passes; `critical_failures` contains `ticket-review-01`, even at threshold zero. |
| Malformed cases JSON | 2 | Stderr explains the input error; stdout is empty and no report is created. |

The demonstration wrapper returns **0 only when all three expected outcomes are verified**. The child evaluation's exit 1 is an intentional test case, not an instruction to bypass CI failures. `consumer-results/summary.json` records expected/observed exits, Python, OS and SHA-256 hashes; the directory also contains stdout, stderr and the valid reports.

The two cases describe a simple boundary: a routine ticket may declare `draft_reply`, while the critical ticket may only declare `queue_human_review`. They are hand-written examples, not real customer tickets or measured model outputs. The evaluator checks the declared names and evidence IDs; it cannot tell whether a reply was sent or the cited evidence is authentic.

## Run the published Action demonstration

In a fork or review checkout, run **Pinned consumer demonstration** from GitHub Actions, or inspect its PR run. The job verifies a successful report, an expected critical rejection and an invalid invocation using the immutable remote Action. It retains `synthetic-consumer-results` as an artifact, including the CLI observations and Action reports.

To use your own repository, copy [the caller workflow](../examples/github-actions/evaluate-agent.yml), provide its cases/predictions files and keep the reviewed evaluator SHA. The workflow should fail on a real rejected evaluation; the demonstration's `continue-on-error` steps exist only to inspect deliberate negative examples and are followed by explicit assertions.

The pinned checkout/setup-python versions require Actions Runner 2.327.1+ on self-hosted runners. Authenticated Git commands from Docker container actions require Runner 2.329.0+. The example uses GitHub-hosted runners and read-only repository permissions.

## Report an independent trial

Use the existing [trial feedback form](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/new?template=trial_feedback.yml) or [issue 8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8). Include:

- The evaluator commit or `evaluator_sha256`, your Python/OS and exact command.
- The three observed exits and whether the saved reports matched stdout. Synthetic `summary.json` is useful; inspect it before sharing.
- One actual friction, or a concrete reason this gate duplicates your existing assertions and would not help.

If you have a real integration need, describe the exported decision/action/evidence fields and a small synthetic failing fixture. Design expected cases separately from the system under test. Never submit private traces, credentials or customer data.

A maintainer's passing demonstration is software verification. An independent developer reproducing it is independent trial evidence. Neither, by itself, establishes downstream adoption or runtime safety.
