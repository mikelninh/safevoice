"""
Swiss criminal law definitions relevant to digital harassment and cybercrime.
Based on the Swiss Strafgesetzbuch (StGB).
"""

from app.models.evidence import GermanLaw


# Art. 173 StGB (CH) — Üble Nachrede
CH_LAW_173 = GermanLaw(
    paragraph="Art. 173 StGB (CH)",
    title="Defamation (Üble Nachrede)",
    title_de="Üble Nachrede",
    description="Accusing or casting suspicion on a person of dishonorable conduct, or of other facts likely to damage their reputation, before a third party.",
    description_de="Beschuldigung oder Verdächtigung einer Person eines unehrenhaften Verhaltens oder anderer Tatsachen, die geeignet sind, ihren Ruf zu schädigen, gegenüber einem Dritten.",
    max_penalty="Up to 3 years imprisonment or monetary penalty (Geldstrafe)",
    applies_because="The content spreads factual claims about the victim before third parties that are likely to damage their reputation.",
    applies_because_de="Der Inhalt verbreitet Tatsachenbehauptungen über das Opfer gegenüber Dritten, die geeignet sind, dessen Ruf zu schädigen."
)

# Art. 174 StGB (CH) — Verleumdung
CH_LAW_174 = GermanLaw(
    paragraph="Art. 174 StGB (CH)",
    title="Slander (Verleumdung)",
    title_de="Verleumdung",
    description="Knowingly making false accusations against a person of dishonorable conduct, or spreading other false facts likely to damage their reputation.",
    description_de="Wissentliches Aufstellen falscher Beschuldigungen gegen eine Person wegen unehrenhaften Verhaltens oder Verbreitung anderer falscher Tatsachen, die geeignet sind, deren Ruf zu schädigen.",
    max_penalty="Up to 3 years imprisonment or monetary penalty (Geldstrafe)",
    applies_because="Knowingly false factual claims about the victim were deliberately spread to damage their reputation.",
    applies_because_de="Wissentlich falsche Tatsachenbehauptungen über das Opfer wurden vorsätzlich verbreitet, um dessen Ruf zu schädigen."
)

# Art. 177 StGB (CH) — Beschimpfung
CH_LAW_177 = GermanLaw(
    paragraph="Art. 177 StGB (CH)",
    title="Verbal Abuse (Beschimpfung)",
    title_de="Beschimpfung",
    description="Insulting another person through words, writing, images, gestures, or physical actions.",
    description_de="Beschimpfung einer anderen Person durch Worte, Schrift, Bilder, Gebärden oder Tätlichkeiten.",
    max_penalty="Monetary penalty (Geldstrafe) of up to 180 daily rates",
    applies_because="The content directly insults and degrades the victim's personal dignity through abusive language.",
    applies_because_de="Der Inhalt beleidigt und erniedrigt die persönliche Würde des Opfers direkt durch beleidigende Sprache."
)

# Art. 180 StGB (CH) — Drohung
CH_LAW_180 = GermanLaw(
    paragraph="Art. 180 StGB (CH)",
    title="Threat (Drohung)",
    title_de="Drohung",
    description="Alarming or frightening a person by threatening a serious detriment (felony or misdemeanor against them or a person close to them).",
    description_de="In Schrecken oder Angst versetzen einer Person durch Androhung eines schwerwiegenden Nachteils (Verbrechen oder Vergehen gegen sie oder eine ihr nahestehende Person).",
    max_penalty="Up to 3 years imprisonment or monetary penalty (Geldstrafe)",
    applies_because="The content contains threats that are likely to alarm or frighten the victim regarding their safety.",
    applies_because_de="Der Inhalt enthält Drohungen, die geeignet sind, das Opfer hinsichtlich seiner Sicherheit in Schrecken oder Angst zu versetzen."
)

# Art. 181 StGB (CH) — Nötigung
CH_LAW_181 = GermanLaw(
    paragraph="Art. 181 StGB (CH)",
    title="Coercion (Nötigung)",
    title_de="Nötigung",
    description="Compelling a person by force, threat of serious detriment, or other restriction of their freedom of action to do, tolerate, or refrain from doing something.",
    description_de="Nötigung einer Person durch Gewalt, Androhung eines ernstlichen Nachteils oder andere Beschränkung ihrer Handlungsfreiheit zu einem Tun, Dulden oder Unterlassen.",
    max_penalty="Up to 3 years imprisonment or monetary penalty (Geldstrafe)",
    applies_because="The offender uses threats or pressure to coerce the victim into a specific action or to suppress their freedom of expression.",
    applies_because_de="Der Täter verwendet Drohungen oder Druck, um das Opfer zu einer bestimmten Handlung zu nötigen oder seine Meinungsfreiheit zu unterdrücken."
)

# Art. 179septies StGB (CH) — Missbrauch einer Fernmeldeanlage
CH_LAW_179SEPTIES = GermanLaw(
    paragraph="Art. 179septies StGB (CH)",
    title="Misuse of Telecommunications Equipment (Missbrauch einer Fernmeldeanlage)",
    title_de="Missbrauch einer Fernmeldeanlage",
    description="Using a telecommunications device to alarm, harass, or otherwise disturb another person through misuse.",
    description_de="Verwendung einer Fernmeldeanlage zur Beunruhigung, Belästigung oder sonstigen Störung einer anderen Person durch Missbrauch.",
    max_penalty="Prosecution upon complaint; monetary penalty (Geldstrafe) or custodial sentence",
    applies_because="The offender uses digital communication platforms (social media, messaging) to repeatedly harass or disturb the victim.",
    applies_because_de="Der Täter nutzt digitale Kommunikationsplattformen (soziale Medien, Messaging) zur wiederholten Belästigung oder Störung des Opfers."
)

# Combined export for convenience
SWISS_LAWS = {
    "threat": [CH_LAW_180],
    "death_threat": [CH_LAW_180, CH_LAW_181],
    "harassment": [CH_LAW_177, CH_LAW_179SEPTIES],
    "defamation": [CH_LAW_173, CH_LAW_174],
    "false_facts": [CH_LAW_173, CH_LAW_174],
    "insult": [CH_LAW_177],
    "coercion": [CH_LAW_181],
    "misogyny": [CH_LAW_177],
    "body_shaming": [CH_LAW_177],
    "sexual_harassment": [CH_LAW_181, CH_LAW_179SEPTIES],
    "stalking": [CH_LAW_179SEPTIES],
    "cyberbullying": [CH_LAW_179SEPTIES, CH_LAW_177],
}
