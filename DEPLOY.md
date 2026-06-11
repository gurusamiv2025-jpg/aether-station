# Deploying Aether Station publicly

Pick the path that matches your taste. All four work; #1 is the fastest.

| Path | Free? | Setup time | Auto-sleep? | Best for |
|---|---|---|---|---|
| 1. Streamlit Community Cloud | ✅ | ~5 min | No | The default. Built for Streamlit. |
| 2. Hugging Face Spaces | ✅ | ~10 min | No (cold start <30s) | ML audience visibility |
| 3. Render | ✅ | ~10 min | Yes, 15 min | Uses your existing Dockerfile |
| 4. Azure Container Apps | ~$5/mo | ~20 min | Configurable | On-brand for the hackathon |

Whichever you pick, **make sure your GitHub repo is public first** (see
`PUBLISH.md`).

---

## 1. Streamlit Community Cloud (recommended)

1. Open <https://share.streamlit.io> and sign in with the GitHub account
   that owns the repo.
2. **New app** → pick your repo → branch `main` → main file `app.py`.
3. **Advanced settings → Secrets** — paste the contents of
   `.streamlit/secrets.toml.example` and fill in any values you have.
   The app runs perfectly with all values blank (offline demo mode).
4. **Deploy.** First build ~2-3 minutes.
5. URL: `https://aether-station-<hash>.streamlit.app`. Paste it into the
   top of your `README.md` under `## Live demo`.

That's it. Streamlit Cloud reads `requirements.txt` automatically, uses
Python 3.12, and picks up `.streamlit/config.toml` for theming.

---

## 2. Hugging Face Spaces

1. <https://huggingface.co/new-space> — SDK: **Streamlit**, license MIT,
   public.
2. Either link the GitHub repo OR clone the new Space's git remote and
   `git push` your code into it.
3. Spaces require a YAML front-matter block at the very top of `README.md`
   to configure the SDK. We've prepared one — copy `HUGGINGFACE_README.md`
   into the Space as `README.md`.
4. Add secrets under **Settings → Variables and secrets**:
   `RETRIEVER_BACKEND`, `AZURE_OPENAI_ENDPOINT`, etc.
5. Space builds, runs `streamlit run app.py`.
6. URL: `https://huggingface.co/spaces/<you>/aether-station`.

---

## 3. Render (Docker)

You already have `Dockerfile` and `render.yaml` in the repo, so this is
mostly point-and-click.

1. <https://dashboard.render.com> → **New + → Blueprint** → pick the repo.
   Render reads `render.yaml` and provisions the service.
2. **Instance type:** Free. **Port:** 8501 (set automatically from the
   blueprint).
3. After deploy, go to **Environment** and fill in the secret env vars.
4. URL: `https://aether-station.onrender.com` (or your chosen name).

Free Render sleeps after 15 min of inactivity and cold-starts in ~30s.
Fine for judging. For continuous uptime, switch to a paid plan.

---

## 4. Azure Container Apps (on-brand for the hackathon)

Bicep template is in `deploy/azure-container-app.bicep`.

```bash
# 1. Login + resource group
az login
az group create -n aether-rg -l eastus

# 2. Container registry + image build
az acr create -g aether-rg -n aetherstationacr --sku Basic --admin-enabled true
az acr build -t aether-station:latest -r aetherstationacr .

# 3. Deploy via Bicep
az deployment group create \
  -g aether-rg \
  -f deploy/azure-container-app.bicep \
  -p image=aetherstationacr.azurecr.io/aether-station:latest \
     azureOpenAiEndpoint=https://YOUR-RESOURCE.openai.azure.com/ \
     azureOpenAiKey=YOUR-KEY \
     azureOpenAiDeployment=gpt-4o-mini
```

Output `appUrl` is your public URL. Cost is roughly $5-10/month at
min-replicas 1; set to 0 to save money but accept a cold-start delay
on the first request.

---

## After it's live

1. **Sanity-check from incognito.** Open the public URL in a private
   window — confirm sidebar status HUD reads sensible backends and no
   errors render in the chat.
2. **Update README.** Add `## Live demo` at the top with the URL and a
   one-line screenshot caption.
3. **Submit to the hackathon.** The Agents League submission form
   typically wants both repo URL and live URL.
4. **Test the demo path.** Click `📜 The Halberd Briefing` scenario,
   make sure the reply renders with citations.

## Troubleshooting

- **"streamlit not recognized"** locally: use `python -m streamlit run app.py`.
- **Hosted build fails on `mcp>=1.0` or Azure deps:** these are
  `[optional-dependencies]` in `pyproject.toml` but are still in
  `requirements.txt`. If the platform pip times out on them, edit
  `requirements.txt` to drop the optional groups for the hosted build.
- **Health check fails:** the path Streamlit serves is `/_stcore/health`;
  use that, not `/`.
- **Foundry IQ env vars set but `RETRIEVER` shows `local-tfidf`:**
  `DefaultAzureCredential` needs identity. On hosted platforms, set a
  service-principal env triple: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
  `AZURE_CLIENT_SECRET`.
