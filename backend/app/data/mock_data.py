"""
Mock data representing realistic harassment scenarios.
All usernames and content are fictional.
"""

from datetime import datetime, timedelta
from app.models.evidence import (
    Case, EvidenceItem, ClassificationResult, PatternFlag,
    Severity, Category, GermanLaw
)
import uuid

# --- Reusable law definitions ---

LAW_185 = GermanLaw(
    paragraph="§ 185 StGB",
    title="Insult (Beleidigung)",
    title_de="Beleidigung",
    description="Insult of a person in a way that violates their personal honor.",
    description_de="Beleidigung einer Person in einer Weise, die ihre persönliche Ehre verletzt.",
    max_penalty="Up to 1 year imprisonment or fine",
    applies_because="The content directly attacks the victim's personal dignity with derogatory language.",
    applies_because_de="Der Inhalt greift die persönliche Würde des Opfers mit abwertender Sprache direkt an."
)

LAW_186 = GermanLaw(
    paragraph="§ 186 StGB",
    title="Defamation (Üble Nachrede)",
    title_de="Üble Nachrede",
    description="Making or spreading false statements of fact about a person that are likely to damage their reputation.",
    description_de="Verbreitung falscher Tatsachenbehauptungen über eine Person, die geeignet sind, ihren Ruf zu schädigen.",
    max_penalty="Up to 1 year imprisonment or fine",
    applies_because="False factual claims about the victim's character or behavior were spread publicly.",
    applies_because_de="Falsche Tatsachenbehauptungen über den Charakter oder das Verhalten des Opfers wurden öffentlich verbreitet."
)

LAW_241 = GermanLaw(
    paragraph="§ 241 StGB",
    title="Threat (Bedrohung)",
    title_de="Bedrohung",
    description="Threatening a person with a serious crime against them or someone close to them.",
    description_de="Bedrohung einer Person mit einem schweren Verbrechen gegen sie oder ihr nahestehende Personen.",
    max_penalty="Up to 2 years imprisonment or fine",
    applies_because="The content explicitly threatens harm, creating reasonable fear for the victim's safety.",
    applies_because_de="Der Inhalt droht ausdrücklich mit Schaden und schafft begründete Angst um die Sicherheit des Opfers."
)

LAW_126A = GermanLaw(
    paragraph="§ 126a StGB",
    title="Threatening with a crime (Strafbare Bedrohung)",
    title_de="Strafbare Bedrohung",
    description="Threatening a person with a crime against their life or physical integrity in a way likely to disturb public peace.",
    description_de="Bedrohung einer Person mit einem Verbrechen gegen ihr Leben oder ihre körperliche Unversehrtheit.",
    max_penalty="Up to 3 years imprisonment",
    applies_because="Explicit death threat or serious threat to physical safety was made.",
    applies_because_de="Eine explizite Todesdrohung oder ernsthafte Bedrohung der körperlichen Sicherheit wurde ausgesprochen."
)

NETZ_DG = GermanLaw(
    paragraph="NetzDG § 3",
    title="Network Enforcement Act - Reporting Obligation",
    title_de="Netzwerkdurchsetzungsgesetz - Meldepflicht",
    description="Platforms with over 2 million users must remove clearly illegal content within 24 hours and other illegal content within 7 days.",
    description_de="Plattformen mit über 2 Millionen Nutzern müssen offensichtlich rechtswidrige Inhalte innerhalb von 24 Stunden und andere rechtswidrige Inhalte innerhalb von 7 Tagen entfernen.",
    max_penalty="Platform fines up to €50 million for systematic failure",
    applies_because="Instagram exceeds the NetzDG threshold. A formal NetzDG report triggers a legal obligation to respond.",
    applies_because_de="Instagram überschreitet die NetzDG-Schwelle. Eine formelle NetzDG-Meldung löst eine gesetzliche Reaktionspflicht aus."
)

LAW_263 = GermanLaw(
    paragraph="§ 263 StGB",
    title="Fraud (Betrug)",
    title_de="Betrug",
    description="Obtaining property by deception – creating a false belief to induce a financial transaction.",
    description_de="Erschleichen von Vermögensvorteilen durch Täuschung – Herbeiführen eines Irrtums zur Veranlassung einer Vermögensverfügung.",
    max_penalty="Up to 5 years imprisonment (up to 10 years in serious cases)",
    applies_because="The content uses deceptive claims to induce a financial transaction or extract personal data for financial gain.",
    applies_because_de="Der Inhalt verwendet täuschende Behauptungen, um eine finanzielle Transaktion oder persönliche Daten zu Gewinnzwecken zu erlangen."
)

LAW_263A = GermanLaw(
    paragraph="§ 263a StGB",
    title="Computer Fraud (Computerbetrug)",
    title_de="Computerbetrug",
    description="Influencing a data processing operation in an unauthorized way to obtain financial benefit.",
    description_de="Unbefugtes Beeinflussen eines Datenverarbeitungsvorgangs zur Erlangung eines Vermögensvorteils.",
    max_penalty="Up to 5 years imprisonment",
    applies_because="The offense involves digital systems or automated processes to commit fraud.",
    applies_because_de="Die Straftat nutzt digitale Systeme oder automatisierte Prozesse zur Begehung von Betrug."
)

LAW_269 = GermanLaw(
    paragraph="§ 269 StGB",
    title="Falsification of Provably False Data (Fälschung beweiserheblicher Daten)",
    title_de="Fälschung beweiserheblicher Daten",
    description="Storing or transmitting falsified data with intent to deceive in legal transactions.",
    description_de="Speichern oder Übermitteln gefälschter Daten mit Täuschungsabsicht im Rechtsverkehr.",
    max_penalty="Up to 5 years imprisonment",
    applies_because="The offense involves falsified digital identities, fake profiles, or manipulated data used to deceive victims.",
    applies_because_de="Die Straftat umfasst gefälschte digitale Identitäten, gefälschte Profile oder manipulierte Daten zur Täuschung von Opfern."
)

# --- Mock Cases ---

MOCK_CASES: list[Case] = [

    Case(
        id="case-001",
        title="Coordinated harassment after vegan post",
        created_at=datetime.now() - timedelta(days=2),
        updated_at=datetime.now() - timedelta(hours=3),
        victim_context="I posted a video about plant-based nutrition. Within 2 hours I received over 40 hostile comments.",
        overall_severity=Severity.HIGH,
        status="open",
        pattern_flags=[
            PatternFlag(
                type="coordinated_attack",
                description="3 accounts showing coordinated behavior within 15 minutes of each other.",
                description_de="3 Konten zeigen koordiniertes Verhalten innerhalb von 15 Minuten.",
                evidence_count=3,
                severity=Severity.HIGH
            ),
            PatternFlag(
                type="serial_harasser",
                description="Account @beef_truth99 has appeared in 2 other cases in our database.",
                description_de="Das Konto @beef_truth99 ist in 2 anderen Fällen in unserer Datenbank aufgetreten.",
                evidence_count=2,
                severity=Severity.MEDIUM
            )
        ],
        evidence_items=[
            EvidenceItem(
                id="ev-001-a",
                url="https://www.instagram.com/p/mockpost1/comments/c001",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=2, hours=1),
                author_username="beef_truth99",
                author_display_name="Beef Truth",
                content_text="You vegans are so stupid, your brain is damaged from lack of protein. Go eat a steak you malnourished idiot.",
                content_type="comment",
                archived_url="https://archive.org/mock/001",
                content_hash="sha256:a3f4b2c1d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4",
                classification=ClassificationResult(
                    severity=Severity.MEDIUM,
                    categories=[Category.HARASSMENT, Category.FALSE_FACTS],
                    confidence=0.91,
                    requires_immediate_action=False,
                    summary="Personal insult combined with false health claims. Violates § 185 StGB.",
                    summary_de="Persönliche Beleidigung kombiniert mit falschen Gesundheitsbehauptungen. Verstößt gegen § 185 StGB.",
                    applicable_laws=[LAW_185, LAW_186, NETZ_DG],
                    potential_consequences="Fine or up to 1 year imprisonment. Platform obligated to remove within 7 days under NetzDG.",
                    potential_consequences_de="Geldstrafe oder bis zu 1 Jahr Freiheitsstrafe. Plattform verpflichtet zur Löschung innerhalb von 7 Tagen nach NetzDG."
                )
            ),
            EvidenceItem(
                id="ev-001-b",
                url="https://www.instagram.com/p/mockpost1/comments/c002",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=2, hours=1),
                author_username="meatlovers_unite",
                author_display_name="Meat Lovers Unite",
                content_text="Nobody wants to hear your propaganda. Women like you should stay in the kitchen and shut up.",
                content_type="comment",
                archived_url="https://archive.org/mock/002",
                content_hash="sha256:b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
                classification=ClassificationResult(
                    severity=Severity.HIGH,
                    categories=[Category.HARASSMENT, Category.MISOGYNY],
                    confidence=0.96,
                    requires_immediate_action=False,
                    summary="Explicitly misogynistic harassment targeting the victim as a woman. Violates § 185 StGB.",
                    summary_de="Explizit misogyner Angriff, der das Opfer als Frau ins Visier nimmt. Verstößt gegen § 185 StGB.",
                    applicable_laws=[LAW_185, NETZ_DG],
                    potential_consequences="Fine or up to 1 year imprisonment. High priority NetzDG report candidate.",
                    potential_consequences_de="Geldstrafe oder bis zu 1 Jahr Freiheitsstrafe. Prioritärer NetzDG-Meldekandidat."
                )
            ),
            EvidenceItem(
                id="ev-001-c",
                url="https://www.instagram.com/p/mockpost1/comments/c003",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=2, minutes=58),
                author_username="realfoodonly_k",
                author_display_name="Real Food Only",
                content_text="I know where people like you live. Watch yourself.",
                content_type="comment",
                archived_url="https://archive.org/mock/003",
                content_hash="sha256:c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
                classification=ClassificationResult(
                    severity=Severity.CRITICAL,
                    categories=[Category.THREAT, Category.COORDINATED_ATTACK],
                    confidence=0.98,
                    requires_immediate_action=True,
                    summary="Implicit threat with location reference. This is a serious threat requiring immediate action. Violates § 241 StGB.",
                    summary_de="Implizite Drohung mit Ortsangabe. Dies ist eine ernsthafte Bedrohung, die sofortiges Handeln erfordert. Verstößt gegen § 241 StGB.",
                    applicable_laws=[LAW_241, LAW_185, NETZ_DG],
                    potential_consequences="Up to 2 years imprisonment. Qualifies for emergency NetzDG removal (24h). Consider filing police report immediately.",
                    potential_consequences_de="Bis zu 2 Jahre Freiheitsstrafe. Qualifiziert für NetzDG-Notlöschung (24h). Erwägen Sie sofortige Strafanzeige."
                )
            ),
        ]
    ),

    Case(
        id="case-002",
        title="Death threat following opinion piece",
        created_at=datetime.now() - timedelta(days=5),
        updated_at=datetime.now() - timedelta(days=1),
        victim_context="I shared my opinion on reproductive rights. A man DMed me repeatedly then posted publicly.",
        overall_severity=Severity.CRITICAL,
        status="reported",
        pattern_flags=[
            PatternFlag(
                type="escalation",
                description="Messages escalated from insult to explicit death threat over 48 hours.",
                description_de="Nachrichten eskalierten von Beleidigung zu expliziter Todesdrohung über 48 Stunden.",
                evidence_count=4,
                severity=Severity.CRITICAL
            )
        ],
        evidence_items=[
            EvidenceItem(
                id="ev-002-a",
                url="https://www.instagram.com/p/mockpost2/comments/c010",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=5),
                author_username="anon_justice_x",
                author_display_name=None,
                content_text="Frauen wie du verdienen es nicht, eine Meinung zu haben. Halt die Klappe.",
                content_type="comment",
                archived_url="https://archive.org/mock/010",
                content_hash="sha256:d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5",
                classification=ClassificationResult(
                    severity=Severity.HIGH,
                    categories=[Category.HARASSMENT, Category.MISOGYNY],
                    confidence=0.97,
                    requires_immediate_action=False,
                    summary="Severe misogynistic insult denying the victim's right to express opinions. § 185 StGB.",
                    summary_de="Schwere misogyner Beleidigung, die dem Opfer das Recht auf Meinungsäußerung abspricht. § 185 StGB.",
                    applicable_laws=[LAW_185, NETZ_DG],
                    potential_consequences="Fine or up to 1 year imprisonment.",
                    potential_consequences_de="Geldstrafe oder bis zu 1 Jahr Freiheitsstrafe."
                )
            ),
            EvidenceItem(
                id="ev-002-b",
                url="https://www.instagram.com/p/mockpost2/comments/c011",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=4),
                author_username="anon_justice_x",
                author_display_name=None,
                content_text="Ich weiß wer du bist. Du solltest aufhören zu reden, sonst passiert dir was.",
                content_type="comment",
                archived_url="https://archive.org/mock/011",
                content_hash="sha256:e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
                classification=ClassificationResult(
                    severity=Severity.CRITICAL,
                    categories=[Category.THREAT, Category.DEATH_THREAT],
                    confidence=0.99,
                    requires_immediate_action=True,
                    summary="Explicit threat combined with claim of knowing victim's identity. CRITICAL - immediate police report recommended. § 241 StGB, § 126a StGB.",
                    summary_de="Explizite Drohung kombiniert mit Behauptung, die Identität des Opfers zu kennen. KRITISCH – sofortige Strafanzeige empfohlen. § 241 StGB, § 126a StGB.",
                    applicable_laws=[LAW_241, LAW_126A, NETZ_DG],
                    potential_consequences="Up to 3 years imprisonment. File police report (Strafanzeige) immediately at local Polizeidienststelle or online via www.onlinewache.polizei.de",
                    potential_consequences_de="Bis zu 3 Jahre Freiheitsstrafe. Sofortige Strafanzeige bei der lokalen Polizeidienststelle oder online über www.onlinewache.polizei.de"
                )
            ),
        ]
    ),

    Case(
        id="case-003",
        title="Body shaming and sexual harassment",
        created_at=datetime.now() - timedelta(hours=6),
        updated_at=datetime.now() - timedelta(hours=1),
        victim_context="Posted a photo at the beach. Received unsolicited sexual comments and body shaming.",
        overall_severity=Severity.HIGH,
        status="open",
        pattern_flags=[],
        evidence_items=[
            EvidenceItem(
                id="ev-003-a",
                url="https://www.instagram.com/p/mockpost3/comments/c020",
                platform="instagram",
                captured_at=datetime.now() - timedelta(hours=5),
                author_username="user_k2291",
                author_display_name="K22",
                content_text="Your body is disgusting. No wonder you're alone. Delete this before you embarrass yourself more.",
                content_type="comment",
                archived_url="https://archive.org/mock/020",
                content_hash="sha256:f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
                classification=ClassificationResult(
                    severity=Severity.HIGH,
                    categories=[Category.HARASSMENT, Category.BODY_SHAMING],
                    confidence=0.94,
                    requires_immediate_action=False,
                    summary="Severe body shaming combined with personal attack on the victim's dignity. § 185 StGB.",
                    summary_de="Schweres Body-Shaming kombiniert mit persönlichem Angriff auf die Würde des Opfers. § 185 StGB.",
                    applicable_laws=[LAW_185, NETZ_DG],
                    potential_consequences="Fine or up to 1 year imprisonment. NetzDG report applicable.",
                    potential_consequences_de="Geldstrafe oder bis zu 1 Jahr Freiheitsstrafe. NetzDG-Meldung anwendbar."
                )
            ),
            EvidenceItem(
                id="ev-003-b",
                url="https://www.instagram.com/p/mockpost3/comments/c021",
                platform="instagram",
                captured_at=datetime.now() - timedelta(hours=4),
                author_username="dm_slides_23",
                author_display_name=None,
                content_text="Send me a private message I have something for you 😏 or I'll post what I think about women like you everywhere",
                content_type="comment",
                archived_url="https://archive.org/mock/021",
                content_hash="sha256:a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8",
                classification=ClassificationResult(
                    severity=Severity.CRITICAL,
                    categories=[Category.SEXUAL_HARASSMENT, Category.THREAT],
                    confidence=0.97,
                    requires_immediate_action=True,
                    summary="Sexual coercion combined with implicit threat. This is a criminal offense under § 240 StGB (coercion) and § 185 StGB.",
                    summary_de="Sexuelle Nötigung kombiniert mit impliziter Drohung. Dies ist eine Straftat nach § 240 StGB (Nötigung) und § 185 StGB.",
                    applicable_laws=[LAW_241, LAW_185, NETZ_DG],
                    potential_consequences="Up to 3 years imprisonment. Immediate NetzDG and police report recommended.",
                    potential_consequences_de="Bis zu 3 Jahre Freiheitsstrafe. Sofortige NetzDG- und Polizeimeldung empfohlen."
                )
            ),
        ]
    ),

    Case(
        id="case-004",
        title="Instagram investment scam / Romance scam",
        created_at=datetime.now() - timedelta(days=1),
        updated_at=datetime.now() - timedelta(hours=2),
        victim_context="Someone contacted me via Instagram DM claiming to be a financial advisor. After weeks of messaging they asked me to invest €500 in a crypto platform. I lost the money and they disappeared.",
        overall_severity=Severity.CRITICAL,
        status="open",
        pattern_flags=[
            PatternFlag(
                type="coordinated_scam",
                description="Classic advance-fee / investment fraud pattern: trust-building phase followed by financial request. Linked fake profile detected.",
                description_de="Klassisches Vorschussbetrug / Investitionsbetrug-Muster: Vertrauensaufbauphase gefolgt von finanziellem Ersuchen. Gefälschtes verknüpftes Profil erkannt.",
                evidence_count=3,
                severity=Severity.CRITICAL
            )
        ],
        evidence_items=[
            EvidenceItem(
                id="ev-004-a",
                url="https://www.instagram.com/direct/mock/dm001",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=14),
                author_username="crypto_advisor_thomas_w",
                author_display_name="Thomas Weber – Financial Advisor",
                content_text="Hi! I noticed your profile and I think I can help you grow your savings. I've helped over 200 clients earn 30-40% monthly returns on crypto. I'd love to share my strategy with you – no obligation.",
                content_type="dm",
                archived_url="https://archive.org/mock/dm001",
                content_hash="sha256:b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
                classification=ClassificationResult(
                    severity=Severity.HIGH,
                    categories=[Category.SCAM, Category.INVESTMENT_FRAUD],
                    confidence=0.93,
                    requires_immediate_action=False,
                    summary="Classic investment fraud opener: unsolicited contact, implausible returns, trust-building. § 263 StGB (attempted fraud).",
                    summary_de="Klassischer Einstieg in Investitionsbetrug: unaufgeforderter Kontakt, unrealistische Renditen, Vertrauensaufbau. § 263 StGB (versuchter Betrug).",
                    applicable_laws=[LAW_263, LAW_269, NETZ_DG],
                    potential_consequences="Up to 5 years imprisonment for fraud. Report to BaFin (German financial regulator) and police.",
                    potential_consequences_de="Bis zu 5 Jahre Freiheitsstrafe für Betrug. Meldung bei BaFin (Bundesanstalt für Finanzdienstleistungsaufsicht) und Polizei."
                )
            ),
            EvidenceItem(
                id="ev-004-b",
                url="https://www.instagram.com/direct/mock/dm002",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=3),
                author_username="crypto_advisor_thomas_w",
                author_display_name="Thomas Weber – Financial Advisor",
                content_text="I've been watching the market for you. Now is the perfect moment. You just need to send €500 in Bitcoin to this wallet: 1A2B3C4D5E6F... I'll handle everything. You'll see returns within 48 hours. Trust me, I've done this hundreds of times.",
                content_type="dm",
                archived_url="https://archive.org/mock/dm002",
                content_hash="sha256:c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
                classification=ClassificationResult(
                    severity=Severity.CRITICAL,
                    categories=[Category.SCAM, Category.INVESTMENT_FRAUD],
                    confidence=0.98,
                    requires_immediate_action=True,
                    summary="Direct request for Bitcoin transfer to unverified wallet with false promises of returns. This is fraud. § 263 StGB, § 263a StGB.",
                    summary_de="Direkte Aufforderung zur Bitcoin-Überweisung an nicht verifiziertes Wallet mit falschen Renditeversprechen. Dies ist Betrug. § 263 StGB, § 263a StGB.",
                    applicable_laws=[LAW_263, LAW_263A, LAW_269, NETZ_DG],
                    potential_consequences="URGENT: Do not transfer any money. File police report immediately. Report to BaFin. Contact your bank if a transfer was made.",
                    potential_consequences_de="DRINGEND: Kein Geld überweisen. Sofortige Strafanzeige erstatten. BaFin informieren. Bank kontaktieren falls bereits überwiesen."
                )
            ),
            EvidenceItem(
                id="ev-004-c",
                url="https://www.instagram.com/direct/mock/dm003",
                platform="instagram",
                captured_at=datetime.now() - timedelta(days=1),
                author_username="crypto_advisor_thomas_w",
                author_display_name="Thomas Weber – Financial Advisor",
                content_text="Your investment is showing great results! To withdraw your profits you just need to pay a small 'verification fee' of €200. This is required by the platform for international transfers. After that your full €1,200 will be released.",
                content_type="dm",
                archived_url="https://archive.org/mock/dm003",
                content_hash="sha256:d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1",
                classification=ClassificationResult(
                    severity=Severity.CRITICAL,
                    categories=[Category.SCAM, Category.INVESTMENT_FRAUD],
                    confidence=0.99,
                    requires_immediate_action=True,
                    summary="Advance-fee fraud: requesting additional 'verification fee' to release fake profits. Do NOT pay. § 263 StGB.",
                    summary_de="Vorschussbetrug: Forderung einer weiteren 'Verifizierungsgebühr' zur Freigabe gefälschter Gewinne. NICHT zahlen. § 263 StGB.",
                    applicable_laws=[LAW_263, LAW_263A, NETZ_DG],
                    potential_consequences="URGENT: Do not pay any fee. This is a classic advance-fee scam. File police report immediately. All money already sent is likely unrecoverable.",
                    potential_consequences_de="DRINGEND: Keine Gebühr zahlen. Dies ist ein klassischer Vorschussbetrug. Sofortige Strafanzeige erstatten. Bereits überwiesenes Geld ist wahrscheinlich nicht mehr abrufbar."
                )
            ),
        ]
    )
]


def get_all_cases() -> list[Case]:
    return MOCK_CASES


def get_case_by_id(case_id: str) -> Case | None:
    return next((c for c in MOCK_CASES if c.id == case_id), None)
