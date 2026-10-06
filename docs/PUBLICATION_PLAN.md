# Trainline publication plan

This document records the read-only branch comparison performed on October 3, 2026. It is a plan, not authorization to commit, merge, push, open a pull request, deploy, or change GitHub settings.

## Confirmed public revisions

| Ref | Commit | Confirmed evidence |
| --- | --- | --- |
| `main` | `ad2591d36c9114cce748fe93696b38d463eb86ec` | GitHub Actions run [35893319473](https://github.com/hs14235/Trainline/actions/runs/35893319473) completed successfully for this exact push; main also contains the tiered membership-card change. |
| `revamp-trainline` | `1c17e6610987ec6bc8114c184cdf2b5a61f7add9` | Local October 3 verification: 73 fast backend tests, 94.96% coverage, 2 PostgreSQL concurrency tests, and 26 frontend tests. No hosted CI run or live deployment is claimed for this ref. |

The branches share `b9e9ae3` and each has four unique commits. `main` contains the merged frontend-review skill and later membership-card work. `revamp-trainline` contains temporary-demo and Render hardening, but its `fbb4641` commit also bundled `.codex-worktree-compose.yml` and six resume-review PNGs under `tmp/pdfs/`.

## Recommended publication target

Create a short-lived integration branch from current `main`, not from the revamp head. Preserve the membership UI and apply only the reviewed hardening changes:

1. Start from `main@ad2591d` after rechecking the remote head.
2. Apply `1f02949` (temporary deployment demo safeguards).
3. Apply `80b620f` (proxy, authentication/logout, API-origin, booking-journey, and Render Blueprint hardening).
4. Apply `1c17e66` (Render startup flag correction and Blueprint regression test).
5. Apply the reviewer-facing documentation corrections prepared after this comparison.
6. Resolve documentation conflicts deliberately; do not overwrite main's membership-card source or tests.
7. Exclude `fbb4641`, `.codex-worktree-compose.yml`, and `tmp/pdfs/**` from the publication candidate. Main already contains the repository skill files through its own history.

Before publication, inspect `git diff main...<candidate>`, run the complete fast verification plus the isolated PostgreSQL tier, scan the staged diff for secrets and machine-local artifacts, and obtain explicit approval for the exact commit/push/PR scope.

## GitHub About replacement

The current About description says MySQL, while the implemented database is PostgreSQL. A truthful replacement is:

> Full-stack rail booking demo with Django REST Framework, React, PostgreSQL, Docker, transaction-safe seat assignment, and authorization tests.

Changing the repository description is an external GitHub settings action and has not been performed.

## Deployment boundary

`render.yaml` is deployment configuration, not deployment evidence. No Render service, public URL, hosted booking flow, public TLS/proxy behavior, backup/restore path, or monitoring result was verified during this review.
