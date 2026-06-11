"""Small i18n stub.

The Welcome monologue + a handful of sidebar labels are translated into
three languages: English (en), Spanish (es), and Hindi (hi). Adding a
new language is a matter of adding another entry to `STRINGS`.

Keys are stable; values can change without breaking call sites.
"""

from __future__ import annotations

from typing import Dict

DEFAULT_LANG = "en"
LANGUAGES = {"en": "English", "es": "Español", "hi": "हिन्दी", "fr": "Français", "de": "Deutsch"}


STRINGS: Dict[str, Dict[str, str]] = {
    "welcome_par1": {
        "en": (
            "Welcome aboard Aether Station. I'm Mira-7, your seventh-generation "
            "station AI — alto voice, deliberate manner. You can speak with any "
            "of the crew via the sidebar."
        ),
        "es": (
            "Bienvenido a bordo de la Estación Aether. Soy Mira-7, su IA de séptima "
            "generación — voz contralto, modales pausados. Puede hablar con cualquier "
            "miembro de la tripulación desde la barra lateral."
        ),
        "hi": (
            "एथर स्टेशन पर स्वागत है। मैं Mira-7 हूँ, आपकी सातवीं पीढ़ी की "
            "स्टेशन AI — आल्टो आवाज़, संयत व्यवहार। आप साइडबार से किसी भी "
            "क्रू सदस्य से बात कर सकते हैं।"
        ),
    
        "fr": (
            "Bienvenue à bord de la station Aether. Je suis Mira-7, votre IA "
            "de septième génération — voix d'alto, manière délibérée. Vous "
            "pouvez parler à n'importe quel membre de l'équipage via la barre "
            "latérale."),
        "de": (
            "Willkommen an Bord der Aether-Station. Ich bin Mira-7, Ihre KI "
            "der siebten Generation — Alt-Stimme, bedächtige Art. Sie können "
            "über die Seitenleiste mit jedem Crewmitglied sprechen."),
    },
    "welcome_par2": {
        "en": (
            "Cmdr. Park runs the place. Dr. Okafor is in Ring 3 with sample "
            "HB-441 and will tell you more about it than you asked. Chief Volkov "
            "is in engineering and will mention the eleven-second isolation delay "
            "I owe him from February. Junior medic Lin Hua is on her first "
            "rotation and is, in my opinion, the most observant person on this "
            "rotation."
        ),
        "es": (
            "La Cmdte. Park dirige el lugar. El Dr. Okafor está en el Anillo 3 "
            "con la muestra HB-441 y le contará más de lo que pidió. El Jefe "
            "Volkov está en ingeniería y mencionará el retraso de aislamiento "
            "de once segundos que le debo desde febrero. La médica junior Lin "
            "Hua está en su primera rotación y es, en mi opinión, la persona "
            "más observadora a bordo."
        ),
        "hi": (
            "Cmdr. Park यहाँ कमान सँभालती हैं। Dr. Okafor Ring 3 में HB-441 नमूने "
            "के साथ हैं और आपके पूछे से ज़्यादा बताएँगे। Chief Volkov इंजीनियरिंग "
            "में हैं और फ़रवरी से उनके बकाया ग्यारह-सेकंड के विलंब का ज़िक्र "
            "करेंगे। Junior medic Lin Hua अपनी पहली रोटेशन पर हैं और मेरी राय में "
            "इस रोटेशन की सबसे सतर्क सदस्य हैं।"
        ),
    
        "fr": (
            "Cmdte Park dirige le lieu. Le Dr Okafor est dans l'Anneau 3 avec "
            "l'échantillon HB-441 et vous en dira plus que vous n'avez demandé. "
            "Chef Volkov est en ingénierie et mentionnera le retard d'isolement "
            "de onze secondes que je lui dois depuis février. La médecin junior "
            "Lin Hua est dans sa première rotation et, à mon avis, la personne "
            "la plus observatrice à bord."),
        "de": (
            "Cmdr. Park leitet den Laden. Dr. Okafor ist in Ring 3 mit Probe "
            "HB-441 und wird Ihnen mehr darüber erzählen, als Sie wissen wollten. "
            "Chefingenieur Volkov ist im Maschinenraum und wird die elf Sekunden "
            "Isolationsverzögerung erwähnen, die ich ihm seit Februar schulde. "
            "Junior-Ärztin Lin Hua ist auf ihrer ersten Rotation und meiner "
            "Meinung nach die aufmerksamste Person an Bord."),
    },
    "welcome_par3": {
        "en": (
            "Click any crew member on the left to start, or pick a Scenario for "
            "a one-tap guided demo. If you want two of us to talk to each other, "
            "the Dialogue panel below sets that up. Every reply is grounded in "
            "our station logs — open the Grounding expander on any answer to "
            "see what we cited."
        ),
        "es": (
            "Haga clic en cualquier miembro a la izquierda para comenzar, o "
            "elija un Escenario para una demostración guiada. Si quiere que dos "
            "de nosotros hablemos, el panel de Diálogo lo configura. Cada "
            "respuesta está fundamentada en los registros de la estación — abra "
            "el panel de Anclaje para ver las citas."
        ),
        "hi": (
            "शुरू करने के लिए बाईं ओर किसी भी क्रू सदस्य पर क्लिक करें, या "
            "एक-टैप गाइडेड डेमो के लिए कोई Scenario चुनें। यदि आप चाहते हैं कि "
            "हम में से दो आपस में बात करें, नीचे का Dialogue पैनल इसे सेट करता "
            "है। हर उत्तर स्टेशन लॉग पर आधारित है — किसी भी उत्तर पर Grounding "
            "विस्तार खोलकर देखें कि हमने क्या उद्धृत किया।"
        ),
    
        "fr": (
            "Cliquez sur un membre d'équipage à gauche pour commencer, ou "
            "choisissez un Scénario pour une démo guidée en un clic. Si vous "
            "voulez que deux d'entre nous se parlent, le panneau Dialogue le "
            "configure. Chaque réponse est ancrée dans nos registres de "
            "station — ouvrez le panneau Ancrage pour voir nos citations."),
        "de": (
            "Klicken Sie links auf ein Crewmitglied, um zu beginnen, oder "
            "wählen Sie ein Szenario für eine geführte Demo. Wenn Sie wollen, "
            "dass zwei von uns miteinander reden, das Dialog-Panel richtet "
            "das ein. Jede Antwort ist in unseren Stationsprotokollen "
            "verankert — öffnen Sie das Grounding-Panel für die Zitate."),
    },
    "welcome_par4": {
        "en": "Logged.",
        "es": "Registrado.",
        "hi": "लॉग किया गया।",
    
        "fr": ("Enregistré."),
        "de": ("Protokolliert."),
    },
    "ui_language": {"en": "Language", "es": "Idioma", "hi": "भाषा",
        "fr": ("Langue"),
        "de": ("Sprache"),
    },
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    if key not in STRINGS:
        return key
    bag = STRINGS[key]
    return bag.get(lang, bag.get(DEFAULT_LANG, key))
