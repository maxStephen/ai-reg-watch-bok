# ai-reg-watch-bok

Monitors AI regulation and standards sources for changes and delivers curated
updates into an Obsidian-based AI Audit Body of Knowledge (BOK).

> **Status:** scaffolding. Implementation in progress.

## Planned design
- **Runs locally** on macOS once a day via `launchd`.
- **Detects changes** in configured sources (NIST AI RMF, ISO/IEC 42001 to start).
- **Summarizes** substantive changes with Claude, except for sources whose terms
  restrict AI use (e.g. ISO): those are hash-compared only and flagged for manual review.
  No ISO text is stored or committed.
- **Delivers into the vault:** one note per change in `Regulation Watch/Inbox/`,
  a dated digest note with `diff` blocks, and a macOS notification that opens the digest.

## Setup
See [MIGRATION.md](MIGRATION.md) for setting up a new Mac.

## Credits
Design inspired by [solomonkbuilds/ai-regulation-watch](https://github.com/solomonkbuilds/ai-regulation-watch).
No code is copied from that project (it has no license); this is an independent implementation.

## License
MIT
