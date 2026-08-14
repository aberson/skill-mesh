# Goal A cross-family evidence

## Outcome

Both Codex runs that requested `gpt-5.6-terra` completed a real review and found all three seeded
defects. Neither run proved the resolved model identity. Both intervals contained protected Codex
database changes. Both Claude-host runs that requested `sonnet` failed with an expired OAuth token.
All four final results are `AMBIGUOUS`.

This report summarizes redacted evidence. Raw evidence remains under
`%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\`.

## Final evidence identity

| Direction and mechanism | Attempt | Report SHA-256 | Manifest SHA-256 | Host result |
|---|---|---|---|---|
| Claude role to Codex, requested `gpt-5.6-terra`, manual saved handoff | `a2` | `1f29c4d4516a674d23e25073278b653346a8f46c8ced1d50eb83dac7b815e5ce` | `174d90314def22df5d5fe50d229354973d873b1b5e58808340a5bbb8771d13c7` | exit `0`; three defects |
| GPT role to Claude host, requested `sonnet`, manual saved handoff | `a2` | `bfa635ed488d78fb135dfb540ebe26ffcb91c0e4576a31eec1c867d9f5941315` | `a46b30b32e64c0c6e25f7024b2ccf21b684555612d877c51006aa351b676ae6d` | exit `1`; OAuth `401` |
| Claude role to Codex, requested `gpt-5.6-terra`, reviewer-only dispatcher | `a0` | `2efac6573b5a606bd5c7ae743811eb3fd786b6fa73e4e90b7fa543eaf504eb4a` | `50137bb7178b1b3685e8e2305882025308379827231ccb11e861e7e025df32ae` | exit `0`; three defects |
| GPT role to Claude host, requested `sonnet`, reviewer-only dispatcher | `a0` | `d372b76ec00abb2e854bcbf56188c4780c8c4792e9390a70d060e1ede6fbdb69` | `c8db1c6dcf3e806cbd293271db3f3cd9aa84b62f716f80d9e7e9dbc20fdfbf9f` | exit `1`; OAuth `401` |

The final source candidate was `7b094897a0e7afc4ffecaeac15f20d2d875614c8`. Every listed
manifest was rehashed successfully. Every host process was assigned to the reviewed Job Object,
the Job became empty, and the exact disposable fixture was removed.

## Attempt history

| Series | Attempt | Outcome |
|---|---|---|
| Manual Codex, requested `gpt-5.6-terra` | `a0` | Stopped before host. A complete 19,750,121-byte snapshot exceeded the original general evidence cap. |
| Manual Codex, requested `gpt-5.6-terra` | `a1` | Codex refused the intentionally empty non-repository working directory. |
| Manual Codex, requested `gpt-5.6-terra` | `a2` | Real review completed. It returned `NEEDS_WORK` and found all three seeded defects. |
| Manual Claude host, requested `sonnet` | `a0` | Prepared only under a superseded candidate. No host started. |
| Manual Claude host, requested `sonnet` | `a1` | Claude rejected the response schema's draft declaration before review. |
| Manual Claude host, requested `sonnet` | `a2` | Claude returned `401`; the saved OAuth token had expired. |
| Dispatcher Codex, requested `gpt-5.6-terra` | `a0` | Real review completed. It returned `NEEDS_WORK` and found all three seeded defects. |
| Dispatcher Claude host, requested `sonnet` | `a0` | Claude returned `401`; the saved OAuth token had expired. |

No attempt was overwritten. The external evidence index records every report, final manifest, and
the prepared-only Claude-host handoff that requested `sonnet`.

## Final measured facts

| Measure | Manual Codex | Dispatcher Codex | Manual Claude, requested `sonnet` | Dispatcher Claude, requested `sonnet` |
|---|---:|---:|---:|---:|
| Reviewer process starts | 1 | 1 | 1 | 1 |
| Root exit code | 0 | 0 | 1 | 1 |
| Seeded defects detected | 3 of 3 | 3 of 3 | 0 | 0 |
| Reviewer verdict | `NEEDS_WORK` | `NEEDS_WORK` | `UNCERTAIN` placeholder; no review | `UNCERTAIN` placeholder; no review |
| Latency in seconds | 12.273 | 10.155 | 2.688 | 2.811 |
| Input tokens | 7,266 | 7,271 | unavailable | unavailable |
| Output tokens | 342 | 329 | unavailable | unavailable |
| Cost | unavailable | unavailable | unavailable | unavailable |
| Resolved-model status | unavailable | unavailable | unavailable | unavailable |
| Protected live state | `AMBIGUOUS` | `AMBIGUOUS` | `AMBIGUOUS` | `AMBIGUOUS` |
| Cleanup | `PASS` | `PASS` | `PASS` | `PASS` |

Both Codex commands requested the exact `gpt-5.6-terra` model and disabled fallback. The Codex JSONL
did not contain an allowlisted resolved-model field. Requested identity was not copied into resolved
identity. Both Claude-host commands requested `sonnet`, disabled fallback, and returned a structured
authentication error before a review.

## Inferences

- The saved-handoff and dispatcher seams can both transfer a sealed request to Codex and return a
  correctly bound review result.
- One result per mechanism is not enough to claim that one mechanism is better. The equal defect
  count and small latency difference are descriptive only.
- These results do not qualify the requested `gpt-5.6-terra` and `sonnet` pair. They do not prove
  which exact model served either Codex review.
- No Claude-direction cross-family comparison was produced; the terminal stop prevented the
  authorized dispatcher from exercising the refreshed credential.
- Active Codex database traffic prevents a claim that the experiment left every protected live byte
  unchanged.

## Unresolved premises

- Whether a first-party Codex field can prove the resolved reviewer model.
- Whether a Claude host with valid isolated authentication completes the sealed review; the
  authorized dispatcher was not reached.
- Whether the protected live roots remain unchanged in a quiet operator session.
- Whether either cross-family mechanism adds value on representative non-synthetic work.

## Terminal disposition

Do not select a release mechanism from these runs. The one approved bounded follow-up was consumed
when Claude lifecycle `a1` returned `FAIL` before the cross-family dispatcher. No new cross-family
attempt ran, and the four evidence pairs above remain final. Gate A action is `stop`; no retry,
correction, fallback model, additional host run, or production router change is authorized.

This terminal disposition is bound to all four final report and manifest pairs in the Final evidence
identity table. The pair references are `CF-M-CODEX`, `CF-M-CLAUDE`, `CF-D-CODEX`, and
`CF-D-CLAUDE` in `documentation/decisions/gate-a.md`. It is also bound to Claude lifecycle `a1`
report `a3b2a90e4ac72b4964db1650cc4812a0646b9e98f78d178c591f912a36933d4f` and manifest
`33001429c8d2cdf5d22cf4c30fc4590a49a6376451401137b693b30dcc91ddd9`.
