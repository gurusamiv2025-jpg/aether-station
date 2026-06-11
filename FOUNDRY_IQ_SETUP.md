# Connecting Aether Station to Foundry IQ

This walks you through pointing the app at a real Microsoft Foundry IQ
knowledge-grounded agent in Azure AI Foundry. With this set up, the
**Retrieval** status in the sidebar will read `foundry-iq` instead of
`local-tfidf`, and every reply will be grounded by the Foundry agent.

> **You can submit without this** — the local TF-IDF fallback runs against
> the same `lore/` corpus and produces grounded replies with citations. But
> a live Foundry IQ wiring is the strongest version of the IQ-integration
> requirement.

## Prerequisites

- An Azure subscription (a free trial is fine).
- The Azure CLI installed: <https://learn.microsoft.com/cli/azure/install-azure-cli>
- Logged in: `az login`

## 1. Create an Azure AI Foundry project

1. Open the Azure portal: <https://portal.azure.com>.
2. Search for **Azure AI Foundry** and create a new resource.
3. Inside the resource, **Launch Foundry portal** (<https://ai.azure.com>).
4. Create a new **Project** (any name — e.g. `aether-station-iq`). Note the
   **project endpoint URL** that appears on the project Overview page; it
   looks like
   `https://aether-station-iq.region.api.azureml.ms` or similar — this is
   your `FOUNDRY_PROJECT_ENDPOINT`.

## 2. Upload the lore corpus as a data source

In the Foundry project portal:

1. Go to **Data + indexes** → **Files** (the exact label may vary; the
   feature is "files used by agents").
2. Upload every `.md` file under `aether-station/lore/`, preserving the
   `world/`, `crew/`, `incidents/` subfolder structure if the UI allows it.
3. Wait for indexing to complete (usually a minute or two).

## 3. Create a knowledge-grounded agent

1. In the Foundry portal, go to **Agents** → **Create**.
2. Pick a base model (e.g. `gpt-4o-mini`) — this is the agent's reasoning
   model.
3. Under **Knowledge** (sometimes labelled "Tools" → "Knowledge" → "Files"),
   attach the lore corpus you just uploaded.
4. **System instructions** for the agent (paste this in):

   ```
   You are the knowledge layer for the Aether Station chatbot. When asked
   a question, retrieve the most relevant passages from the lore corpus
   and return them with their file paths. Do not fabricate; if no
   passages match, return an empty result. Each passage should include
   the source file path (e.g. lore/crew/park.md).
   ```

5. **Save** the agent. Copy its **Agent ID** from the agent details page —
   this is your `FOUNDRY_AGENT_ID`.

## 4. Authenticate

The Foundry SDK uses Azure AD via `DefaultAzureCredential`. The easiest path
locally is:

```powershell
az login
```

If you're on a corporate tenant that blocks interactive logins, create a
service principal and set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
`AZURE_CLIENT_SECRET` env vars — `DefaultAzureCredential` picks those up
automatically.

## 5. Point the app at Foundry

Edit `.env` in the project root (copy from `.env.example` first if you
haven't):

```
FOUNDRY_PROJECT_ENDPOINT=https://aether-station-iq.region.api.azureml.ms
FOUNDRY_AGENT_ID=asst_<your-agent-id>
```

## 6. (Recommended) Wire up Azure OpenAI for chat

The Foundry agent grounds retrieval; chat completions still go through
`llm.py`. Use Azure OpenAI for the best demo:

1. In the Azure portal, create an **Azure OpenAI** resource (or use the one
   already in your Foundry hub).
2. Deploy `gpt-4o-mini` (or any chat-capable deployment).
3. Add to `.env`:

   ```
   AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
   AZURE_OPENAI_API_KEY=<key>
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   AZURE_OPENAI_API_VERSION=2024-08-01-preview
   ```

## 7. Verify

Restart the app:

```powershell
python -m streamlit run app.py
```

In the sidebar **Status** panel you should now see:

- **Retrieval:** `foundry-iq`
- **LLM:** `azure-openai`

Ask Cmdr. Park about the Halberd incident. Expand the **Grounding** panel
under her reply — sources should be returned by the live Foundry agent with
realistic relevance scores.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Sidebar still shows `local-tfidf` | One of `FOUNDRY_PROJECT_ENDPOINT` / `FOUNDRY_AGENT_ID` is empty in `.env`. The factory checks both. |
| Auth errors at startup | `az login` not run, or service principal env vars not set. |
| Foundry call raises but app keeps working | Expected — `FoundryAgentRetriever` falls through to `LocalRetriever` on exception so the demo never breaks mid-conversation. Check the terminal for the underlying error. |
| Empty citations panel | Agent's knowledge wasn't attached to the lore files, or the index hasn't finished building. Check the Foundry portal under your agent → Knowledge. |

## What "Foundry IQ" actually means here

Foundry IQ is Microsoft's term for the agentic-knowledge-retrieval layer in
Azure AI Foundry: agents that retrieve grounded, cited passages from an
enterprise corpus with permission-aware filtering. In this app, the lore
bible plays the role of "enterprise corpus" and the agent we created above
is the Foundry IQ knowledge agent. The `FoundryAgentRetriever` in
`foundry_iq.py` is the client that calls it.
