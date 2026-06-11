"""Sanity tests for the deployment artifacts so they don't silently
break the hosted build path."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_streamlit_config_exists_and_has_dark_theme():
    p = ROOT / ".streamlit" / "config.toml"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    assert 'base = "dark"' in body
    assert "headless = true" in body


def test_secrets_template_lists_all_known_env_vars():
    p = ROOT / ".streamlit" / "secrets.toml.example"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_DEPLOYMENT", "FOUNDRY_PROJECT_ENDPOINT",
                "FOUNDRY_AGENT_ID", "RETRIEVER_BACKEND"):
        assert key in body, f"missing {key} in secrets template"


def test_render_yaml_has_healthcheck_and_port():
    p = ROOT / "render.yaml"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    assert "/_stcore/health" in body
    assert "runtime: docker" in body


def test_huggingface_readme_has_streamlit_sdk_header():
    p = ROOT / "HUGGINGFACE_README.md"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    assert body.startswith("---")
    assert "sdk: streamlit" in body
    assert "app_file: app.py" in body


def test_azure_bicep_targets_port_8501():
    p = ROOT / "deploy" / "azure-container-app.bicep"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    assert "targetPort: 8501" in body
    assert "external: true" in body


def test_deploy_md_lists_all_four_paths():
    p = ROOT / "DEPLOY.md"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    for needle in ("Streamlit Community Cloud", "Hugging Face Spaces",
                   "Render", "Azure Container Apps"):
        assert needle in body, f"missing path: {needle}"


def test_dockerfile_exposes_8501():
    p = ROOT / "Dockerfile"
    assert p.exists()
    assert "EXPOSE 8501" in p.read_text(encoding="utf-8")
