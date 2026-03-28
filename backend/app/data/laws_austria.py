"""
Austrian criminal law definitions relevant to digital harassment and cybercrime.
Based on the Austrian Strafgesetzbuch (StGB).
"""

from app.models.evidence import GermanLaw


# § 107 StGB (AT) — Gefährliche Drohung
AT_LAW_107 = GermanLaw(
    paragraph="§ 107 StGB (AT)",
    title="Dangerous Threat (Gefährliche Drohung)",
    title_de="Gefährliche Drohung",
    description="Threatening a person in a way that causes justified fear, including threats to life, health, physical integrity, freedom, or property.",
    description_de="Bedrohung einer Person in einer Weise, die begründete Furcht hervorruft, einschließlich Drohungen gegen Leben, Gesundheit, körperliche Unversehrtheit, Freiheit oder Vermögen.",
    max_penalty="Up to 1 year imprisonment (up to 3 years if threat involves death or severe violence)",
    applies_because="The content contains a threat that is likely to cause justified fear for the victim's safety or well-being.",
    applies_because_de="Der Inhalt enthält eine Drohung, die geeignet ist, begründete Furcht um die Sicherheit oder das Wohlergehen des Opfers auszulösen."
)

# § 107a StGB (AT) — Beharrliche Verfolgung (Stalking)
AT_LAW_107A = GermanLaw(
    paragraph="§ 107a StGB (AT)",
    title="Persistent Pursuit / Stalking (Beharrliche Verfolgung)",
    title_de="Beharrliche Verfolgung (Stalking)",
    description="Persistently pursuing or surveilling a person over an extended period in a way that unreasonably impairs their lifestyle, including repeated unwanted contact via telecommunications.",
    description_de="Beharrliches Verfolgen oder Überwachen einer Person über einen längeren Zeitraum in einer Weise, die deren Lebensführung unzumutbar beeinträchtigt, einschließlich wiederholter unerwünschter Kontaktaufnahme über Telekommunikation.",
    max_penalty="Up to 1 year imprisonment",
    applies_because="The offender is persistently contacting or pursuing the victim through digital channels in a way that impairs their daily life.",
    applies_because_de="Der Täter kontaktiert oder verfolgt das Opfer beharrlich über digitale Kanäle in einer Weise, die deren Alltag beeinträchtigt."
)

# § 107c StGB (AT) — Fortgesetzte Belästigung im Wege einer Telekommunikation oder eines Computersystems (Cybermobbing)
AT_LAW_107C = GermanLaw(
    paragraph="§ 107c StGB (AT)",
    title="Continued Harassment via Cyberbullying (Fortgesetzte Belästigung durch Cybermobbing)",
    title_de="Fortgesetzte Belästigung durch Cybermobbing",
    description="Continued harassment of a person via telecommunications or computer systems in a way that is likely to unreasonably impair their lifestyle, including publishing defamatory or intimate content online.",
    description_de="Fortgesetzte Belästigung einer Person über Telekommunikation oder Computersysteme in einer Weise, die geeignet ist, deren Lebensführung unzumutbar zu beeinträchtigen, einschließlich der Veröffentlichung diffamierender oder intimer Inhalte im Internet.",
    max_penalty="Up to 1 year imprisonment",
    applies_because="The victim is being repeatedly harassed via digital platforms in a sustained pattern that impacts their quality of life.",
    applies_because_de="Das Opfer wird wiederholt über digitale Plattformen in einem anhaltenden Muster belästigt, das seine Lebensqualität beeinträchtigt."
)

# § 111 StGB (AT) — Üble Nachrede
AT_LAW_111 = GermanLaw(
    paragraph="§ 111 StGB (AT)",
    title="Defamation (Üble Nachrede)",
    title_de="Üble Nachrede",
    description="Accusing a person of having a contemptible character trait or a dishonorable behavior, or of acting against public morality, in a way perceivable by a third party.",
    description_de="Beschuldigung einer Person, eine verächtliche Eigenschaft oder ein unehrenhaftes Verhalten zu haben oder gegen die öffentliche Moral zu handeln, in einer für Dritte wahrnehmbaren Weise.",
    max_penalty="Up to 6 months imprisonment or fine of up to 360 daily rates",
    applies_because="False factual claims or accusations about the victim were made that are likely to damage their reputation in the eyes of third parties.",
    applies_because_de="Es wurden falsche Tatsachenbehauptungen oder Beschuldigungen über das Opfer aufgestellt, die geeignet sind, dessen Ruf in den Augen Dritter zu schädigen."
)

# § 115 StGB (AT) — Beleidigung
AT_LAW_115 = GermanLaw(
    paragraph="§ 115 StGB (AT)",
    title="Insult (Beleidigung)",
    title_de="Beleidigung",
    description="Publicly insulting, mocking, or threatening another person with bodily harm, in the presence of others or in a manner accessible to a wider audience.",
    description_de="Öffentliches Beschimpfen, Verspotten oder Androhen von Misshandlungen gegenüber einer anderen Person in Gegenwart anderer oder auf eine einem breiteren Publikum zugängliche Weise.",
    max_penalty="Up to 3 months imprisonment or fine of up to 180 daily rates",
    applies_because="The content publicly insults or degrades the victim in a way accessible to a wider audience on social media.",
    applies_because_de="Der Inhalt beleidigt oder erniedrigt das Opfer öffentlich auf eine in sozialen Medien einem breiteren Publikum zugängliche Weise."
)

# § 105 StGB (AT) — Nötigung
AT_LAW_105 = GermanLaw(
    paragraph="§ 105 StGB (AT)",
    title="Coercion (Nötigung)",
    title_de="Nötigung",
    description="Compelling another person to do, tolerate, or refrain from doing something by means of force or dangerous threat.",
    description_de="Nötigung einer anderen Person zu einem Tun, Dulden oder Unterlassen durch Gewalt oder gefährliche Drohung.",
    max_penalty="Up to 1 year imprisonment",
    applies_because="The offender uses threats or intimidation to coerce the victim into a specific action or behavior.",
    applies_because_de="Der Täter verwendet Drohungen oder Einschüchterung, um das Opfer zu einer bestimmten Handlung oder einem bestimmten Verhalten zu nötigen."
)

# Combined export for convenience
AUSTRIAN_LAWS = {
    "threat": [AT_LAW_107],
    "death_threat": [AT_LAW_107],
    "stalking": [AT_LAW_107A, AT_LAW_107C],
    "cyberbullying": [AT_LAW_107C],
    "harassment": [AT_LAW_115, AT_LAW_107C],
    "defamation": [AT_LAW_111],
    "false_facts": [AT_LAW_111],
    "insult": [AT_LAW_115],
    "coercion": [AT_LAW_105],
    "misogyny": [AT_LAW_115],
    "body_shaming": [AT_LAW_115],
    "sexual_harassment": [AT_LAW_105, AT_LAW_107C],
}
