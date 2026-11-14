# New Mac setup

Steps to move the regulation watcher and the AI Audit BOK to a new MacBook.

## 0. On the old Mac (before retiring it)
Stop the daily run so two Macs never write to the vault:
```bash
~/Documents/_git/ai-reg-watch-bok/bootstrap.sh --unschedule
```
Copy these local-only files somewhere safe (they are not in any git repo):
- `~/Documents/_git/ai-reg-watch-bok.local/secrets/anthropic_api_key`
- `~/Documents/vaults/ai-audit-bok/Reference/` (two files, listed in step 2)

Change history (`ai-reg-watch-bok.local/state/`) does not need to move: the first run on
the new Mac records a fresh baseline.

## 1. Base tools
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git gh python
brew install --cask obsidian
gh auth login
```

## 2. Restore the BOK vault (private repo)
```bash
mkdir -p ~/Documents/vaults
gh repo clone maxStephen/ai-audit-bok ~/Documents/vaults/ai-audit-bok
```
Then in Obsidian: **Open folder as vault** → `~/Documents/vaults/ai-audit-bok`.

**Local-only files (not in git, copy manually from the old Mac or a backup):**
- `Reference/100.12_ARTIFICIAL_INTELLIGENCE_USAGE_POLICY.pdf`
- `Reference/PCI-DSS-v4-0-1-AOC-for-SAQ-A-r1.dotx`

## 3. Restore the regulation watcher (this repo)
```bash
mkdir -p ~/Documents/_git
gh repo clone maxStephen/ai-reg-watch-bok ~/Documents/_git/ai-reg-watch-bok
```
Then run the bootstrap script:
```bash
~/Documents/_git/ai-reg-watch-bok/bootstrap.sh
```
It is safe to re-run. It:
- installs `python`, `git`, `gh`, and `terminal-notifier` with Homebrew
- clones the vault (step 2) if it isn't there yet
- creates the Python environment and the local data folder `~/Documents/_git/ai-reg-watch-bok.local/`
  (`logs/`, `state/`, `secrets/`)
- asks for the Anthropic API key and saves it to `secrets/anthropic_api_key`, readable only by you.
  Keep ~/Documents out of iCloud's "Desktop & Documents Folders" sync so the key stays local.
- warns if the Mac's time zone isn't Eastern
- installs the daily 07:00 run (`~/Library/LaunchAgents/com.maxstephen.regwatch.plist`)
- finishes with a dry run

## 4. Restore the ops register (private repo)
```bash
brew install age
gh repo clone maxStephen/ops ~/Documents/_git/ops
mkdir -p ~/.config/age
```
Restore the age private key from your password manager to `~/.config/age/ops.key`
(`chmod 600` it). Without this key, the encrypted config backups can't be decrypted.

## 5. Restore Claude Code configuration
Global `CLAUDE.md` and `settings.json` live in the private `dotfiles` repo and are symlinked into `~/.claude/`:
```bash
gh repo clone maxStephen/dotfiles ~/Documents/_git/dotfiles
~/Documents/_git/dotfiles/install.sh
```
Install Claude Code (CLI and/or desktop app) and sign in; it picks up the linked files on the next session.

## 6. Verify
```bash
~/Documents/_git/ai-reg-watch-bok/.venv/bin/regwatch run
```
The first run records baselines and sends a "No AI regulation changes" notification.
To see a digest without waiting for a Monday, run with `--date` set to a Monday
(e.g. `--date 2026-11-16`): the digest in `Regulation Watch/Digests/` lists the manual ISO check.
Logs are in `~/Documents/_git/ai-reg-watch-bok.local/logs/`.
