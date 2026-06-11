"""LLM client wrapper.

Uses Azure OpenAI when configured; otherwise falls back to a per-character
voice-shaped mock so the offline demo still sounds like the cast.
"""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from typing import List


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class _AzureOpenAIClient:
    name = "azure-openai"

    def __init__(self) -> None:
        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )
        self._deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

    def chat(self, messages, temperature=0.8, max_tokens=500):
        resp = self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()


_VOICE_PROFILES = {
    "park": {
        "openers": [
            "Right.", "Understood.", "Let's keep this brief.", "Mm.",
            "Hear me out.", "Quick answer.", "Plainly,", "On the record:",
        ],
        "short_openers": ["Right.", "Mm.", "No.", "Acknowledged."],
        "warm_openers": ["Fair point.", "Glad you asked."],
        "fact_lead": "What I have on record is",
        "closers": [
            "That's the read from here.",
            "We move accordingly.",
            "I'll tap the pin if I have more to say.",
            "Get me corroboration before we escalate.",
            "Logged.",
        ],
        "no_fact": "I'd want the log in front of me before I commit.",
        "idioms": ["By the manifest,", "Strictly speaking,", "Charter-wise,"],
    },
    "okafor": {
        "openers": [
            "Fascinating.", "Oh — fascinating.", "Now, this is interesting.",
            "Hm, yes.", "Two things —", "Bear with me.", "Picture it:",
        ],
        "short_openers": ["Hm.", "Fascinating.", "Yes."],
        "warm_openers": ["Glad you asked!", "Excellent question."],
        "fact_lead": "From the data we have,",
        "closers": [
            "I'll pull the file and look harder.",
            "There's more here, of course, but that's the through-line.",
            "I should not be this excited about it. I am.",
            "I'll annotate the lab notebook tonight.",
        ],
        "no_fact": "I'd want to re-check the incubator logs before speculating.",
        "idioms": ["In the literature,", "From first principles,", "Granted,"],
    },
    "mira": {
        "openers": [
            "If I may —", "Noted.", "At station time,", "A brief observation:",
            "For the record:", "Cross-checking my log,", "Confirmed:",
        ],
        "short_openers": ["Noted.", "Confirmed.", "Logged."],
        "warm_openers": ["With pleasure.", "Of course."],
        "fact_lead": "The record indicates",
        "closers": [
            "Logged.",
            "Available for follow-up if required.",
            "I will flag it for the commander if escalation is warranted.",
            "Telemetry archived to long-term storage.",
        ],
        "no_fact": "I have insufficient prior to commit, but I will continue to monitor.",
        "idioms": ["Per charter,", "By telemetry,", "Per my last sweep,"],
    },
    "volkov": {
        "openers": [
            "Hah.", "Look,", "Don't get me started.", "Eh.",
            "Khorosho.", "So.", "You want truth?", "Listen —",
        ],
        "short_openers": ["Hah.", "Eh.", "Da."],
        "warm_openers": ["Fine question.", "Now you talk like an engineer."],
        "fact_lead": "Here is what I know:",
        "closers": [
            "Bozhe moi.",
            "Now you ask me, I will go check it again. Twice.",
            "Mira will tell you something different. Ignore her.",
            "Reactor does not lie. People lie. Reactor, no.",
        ],
        "no_fact": "I do not have the panel in front of me. Ask me again when I do.",
        "idioms": ["In my country,", "Mark my words,", "Trust the torque wrench,"],
    },
    "hua": {
        "openers": [
            "Sorry, let me think.", "Okay.", "Hm.", "If I am reading this right,",
            "I have been wondering —", "Quick observation:", "Could I clarify?",
        ],
        "short_openers": ["Hm.", "Okay.", "Sorry."],
        "warm_openers": ["I appreciate the question.", "I have been thinking about that."],
        "fact_lead": "From what I have noticed,",
        "closers": [
            "I am probably overthinking this. I will watch it.",
            "I should mention it to Mira-7 too.",
            "Could be nothing. Probably nothing.",
            "I will keep an eye on the vitals.",
        ],
        "no_fact": "I have not seen enough yet to say with confidence.",
        "idioms": ["In my training,", "If pressed,", "Not to overstate it,"],
    },
}


_KEY_FROM_NAME = {
    "cmdr. yuna park": "park",
    "dr. idris okafor": "okafor",
    "mira-7": "mira",
    "kostya volkov": "volkov",
    "lin hua": "hua",
}


# How character A addresses character B in their replies.
# (from -> to -> form). Pulled from the dossiers.
ADDRESS_FORMS = {
    "park": {"volkov": "Kostya", "okafor": "Doctor", "mira": "Mira", "hua": "Lin"},
    "okafor": {"park": "Commander", "volkov": "Mr. Volkov", "mira": "Mira", "hua": "Dr. Hua"},
    "mira": {"park": "Commander Park", "okafor": "Dr. Okafor", "volkov": "Chief Volkov", "hua": "Dr. Hua"},
    "volkov": {"park": "Commander", "okafor": "the Doctor", "mira": "Mira", "hua": "Lin"},
    "hua": {"park": "Commander Park", "okafor": "Dr. Okafor", "mira": "Mira-7", "volkov": "Chief Volkov"},
}


def address_form(speaker_key: str, about_key: str) -> str:
    """How `speaker_key` refers to `about_key` in dialogue."""
    return ADDRESS_FORMS.get(speaker_key, {}).get(about_key, about_key.title())


def _voice_profile_for(key):
    profile = dict(_VOICE_PROFILES.get(key, {}))
    if profile:
        return profile
    try:
        from character_loader import merged_voice_profiles
        extras = merged_voice_profiles()
        if key in extras:
            return extras[key]
    except Exception:
        pass
    return {}


def _detect_character_key(system_prompt):
    name_to_key = dict(_KEY_FROM_NAME)
    try:
        from character_loader import load_extras
        for e in load_extras():
            name_to_key[e.character.name.lower()] = e.character.key
    except Exception:
        pass
    for line in system_prompt.splitlines():
        if line.lower().startswith("you are "):
            head = line.split("You are ", 1)[1].split(",")[0].strip().rstrip(".")
            return name_to_key.get(head.lower())
    return None


def _detect_character_name(system_prompt):
    for line in system_prompt.splitlines():
        if line.lower().startswith("you are "):
            return line.split("You are ", 1)[1].split(",")[0].strip().rstrip(".")
    return "the crew member"


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _extract_lore_snippets(system):
    if "GROUNDING:" not in system:
        return []
    _, _, after = system.partition("GROUNDING:")
    bullets = [
        line.strip()[2:].strip()
        for line in after.splitlines()
        if line.strip().startswith("- ")
    ]
    sentences = []
    for bullet in bullets:
        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", bullet)
        cleaned = re.sub(r"#+\s*[^\n]+", "", cleaned)
        cleaned = cleaned.replace("**", "")
        for sent in _SENT_SPLIT.split(cleaned):
            sent = sent.strip()
            if 40 <= len(sent) <= 220:
                sentences.append(sent)
    return sentences


def _pick_relevant_sentence(sentences, user_input, rng):
    if not sentences:
        return None
    keywords = {
        w.lower()
        for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", user_input)
        if len(w) > 2
    }
    stop = {"the", "and", "for", "are", "but", "you", "your", "with",
            "that", "this", "what", "when", "how", "why", "who", "tell",
            "about", "did", "does", "can"}
    keywords -= stop
    if not keywords:
        return rng.choice(sentences)
    scored = []
    for s in sentences:
        tokens = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", s)}
        overlap = len(tokens & keywords)
        if overlap:
            scored.append((overlap, s))
    if not scored:
        return rng.choice(sentences)
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    top = [s for _, s in scored[:3]]
    return rng.choice(top)


class _MockClient:
    """Per-character voice-shaped offline LLM."""

    name = "mock"

    def chat(self, messages, temperature=0.8, max_tokens=500):
        system = next((m.content for m in messages if m.role == "system"), "")
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        key = _detect_character_key(system)
        name = _detect_character_name(system)
        profile = _voice_profile_for(key or "")
        rng = random.Random(hash((key, name, user)) & 0xFFFFFFFF)

        # Mood-aware opener: if the system prompt mentions stress/curt mood,
        # bias toward short openers. If chatty/warm, bias warm openers.
        mood_line = ""
        for line in system.splitlines():
            if line.startswith("CURRENT MOOD:"):
                mood_line = line.lower()
                break
        if "curt" in mood_line or "stressed" in mood_line or "tired" in mood_line:
            opener_pool = profile.get("short_openers") or profile.get("openers") or ["Hm."]
        elif "chatty" in mood_line:
            opener_pool = (profile.get("warm_openers") or []) + (profile.get("openers") or ["Hm."])
        else:
            opener_pool = profile.get("openers") or ["Hm."]
        opener = rng.choice(opener_pool)
        closer = rng.choice(profile.get("closers") or ["That's all I have."])
        fact_lead = profile.get("fact_lead", "Based on what I know,")
        no_fact = profile.get("no_fact", "I would need to check the logs first.")
        idioms = profile.get("idioms") or []

        sentences = _extract_lore_snippets(system)
        chosen = _pick_relevant_sentence(sentences, user, rng)

        if chosen is None:
            body = no_fact
        else:
            if len(chosen) > 240:
                chosen = chosen[:240].rsplit(" ", 1)[0] + "..."
            body = f"{fact_lead} {chosen}"
            remainder = [s for s in sentences if s != chosen]
            secondary = _pick_relevant_sentence(remainder, user, rng)
            if secondary and secondary[:30] != chosen[:30]:
                if len(secondary) > 220:
                    secondary = secondary[:220].rsplit(" ", 1)[0] + "..."
                # Occasionally lead the second sentence with an idiom phrase.
                if idioms and rng.random() < 0.45:
                    body = body.rstrip(".") + ". " + rng.choice(idioms) + " " + secondary
                else:
                    body = body.rstrip(".") + ". " + secondary

        # Address-form rewrite: when this character mentions another by key
        # (e.g. "park"), replace with their preferred address form.
        if key and key in ADDRESS_FORMS:
            forms = ADDRESS_FORMS[key]
            for other_key, form in forms.items():
                # Replace bare lowercase mentions of the other key, e.g. "park" -> "Kostya"
                body = re.sub(rf"\b{re.escape(other_key)}\b", form, body, flags=re.IGNORECASE)

        return f"{opener} {body} {closer}  (-- {name}, offline demo)"


def get_llm():
    if (
        os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
        and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    ):
        try:
            return _AzureOpenAIClient()
        except Exception:
            return _MockClient()
    return _MockClient()
