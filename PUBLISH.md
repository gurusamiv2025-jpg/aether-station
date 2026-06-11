# Publishing this project

The PowerShell commands below take a fresh checkout to a public GitHub repo
that's ready to submit to Agents League. Run them from inside the
`aether-station` folder.

## 1. Clean any half-initialized git state

If `.git/` is already in this folder (e.g. from an earlier failed attempt),
delete it first:

```powershell
Remove-Item -Recurse -Force .git
```

## 2. Initialize a fresh repo

```powershell
git init -b main
git config user.email "gurusamivelmurugan@gmail.com"
git config user.name "gv"
```

## 3. Double-check no secrets will be committed

```powershell
git status
type .gitignore
# .env should NOT appear in `git status`. If it does, ensure your
# secrets file is named exactly `.env` and that `.gitignore` lists it.
```

## 4. First commit

```powershell
git add -A
git commit -m "Initial commit: Aether Station multi-character chatbot"
```

## 5. Create the GitHub repo and push

Easiest path with the GitHub CLI (`gh`):

```powershell
gh auth login           # one-time, if not already
gh repo create aether-station --public --source=. --remote=origin --push
```

Or, manually:

1. Create a new **public** repo on github.com named `aether-station` (no
   README, no .gitignore, no license — we already have those).
2. Then:

   ```powershell
   git remote add origin https://github.com/<your-username>/aether-station.git
   git push -u origin main
   ```

## 6. Verify before submitting

- Visit the repo URL in a browser and confirm:
  - README renders
  - LICENSE is present
  - `lore/` shows all 11 markdown files
  - `.env` is NOT visible (only `.env.example` should be)
- Click around to confirm the repo is truly public (open it in an incognito
  window).

You're ready to submit.
