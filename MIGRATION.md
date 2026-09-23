# New Mac setup

Steps to move the regulation watcher and the AI Audit BOK to a new MacBook.
Sections marked **TBD** will be filled in as the implementation is built.

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
- **TBD:** `bootstrap.sh` (Python environment, `launchd` schedule, vault path)
- **TBD:** Anthropic API key storage (macOS Keychain; never committed)

## 4. Restore Claude Code configuration
- **TBD:** private dotfiles repo for `~/.claude/CLAUDE.md` and `~/.claude/settings.json`

## 5. Verify
- **TBD:** run the watcher once manually and confirm a digest note appears in the vault.
