"""
French law definitions for SafeVoice.
Covers key statutes relevant to online harassment, threats, privacy, fraud,
and platform content moderation obligations.
"""

from app.models.evidence import GermanLaw

# --- Loi Avia (Loi n° 2020-766) ---

FR_LOI_AVIA = GermanLaw(
    paragraph="Loi n° 2020-766 du 24 juin 2020 (Loi Avia)",
    title="Loi Avia — Platform content moderation obligations",
    title_de="Avia-Gesetz — Pflichten der Plattformen zur Inhaltsmoderation",
    description=(
        "The Loi Avia (Law No. 2020-766 of 24 June 2020) aims to combat hateful "
        "content online. Although the Conseil constitutionnel struck down the "
        "24-hour removal obligation, key provisions remain in force requiring "
        "platforms to implement transparent content moderation procedures, provide "
        "accessible reporting mechanisms, and cooperate with judicial authorities. "
        "The DSA (EU Digital Services Act) now supplements these obligations."
    ),
    description_de=(
        "Das Avia-Gesetz (Gesetz Nr. 2020-766 vom 24. Juni 2020) zielt auf die "
        "Bekämpfung von Hassinhalten im Internet ab. Obwohl der Verfassungsrat die "
        "24-Stunden-Löschpflicht aufgehoben hat, bleiben wesentliche Bestimmungen "
        "in Kraft, die Plattformen verpflichten, transparente Inhaltsmoderationsverfahren "
        "einzuführen, zugängliche Meldemechanismen bereitzustellen und mit den "
        "Justizbehörden zusammenzuarbeiten. Die DSA (EU-Gesetz über digitale Dienste) "
        "ergänzt diese Verpflichtungen nun."
    ),
    max_penalty="Fines up to EUR 250,000 for non-compliant platforms; further sanctions under the EU DSA",
    applies_because=(
        "The platform is required to provide effective content reporting mechanisms "
        "and to cooperate with French judicial authorities in removing illegal "
        "hateful content."
    ),
    applies_because_de=(
        "Die Plattform ist verpflichtet, wirksame Meldemechanismen für Inhalte "
        "bereitzustellen und mit den französischen Justizbehörden bei der Entfernung "
        "illegaler Hassinhalte zusammenzuarbeiten."
    ),
)

# --- Art. 222-33-2-2 Code pénal — Harcèlement moral ---

FR_HARCELEMENT_MORAL = GermanLaw(
    paragraph="Art. 222-33-2-2 Code pénal",
    title="Moral harassment / cyberbullying (Harcèlement moral)",
    title_de="Psychische Belästigung / Cybermobbing (Harcèlement moral)",
    description=(
        "Article 222-33-2-2 of the French Penal Code criminalises moral harassment "
        "carried out through the use of a digital communications service or via "
        "electronic means. This includes repeated acts targeting a specific person "
        "that have the effect of degrading their living conditions, resulting in "
        "an impairment of their physical or mental health. It also covers "
        "concerted action by multiple persons even if each individual act is not "
        "repeated."
    ),
    description_de=(
        "Artikel 222-33-2-2 des französischen Strafgesetzbuches stellt die "
        "psychische Belästigung unter Strafe, die über einen digitalen "
        "Kommunikationsdienst oder elektronische Mittel erfolgt. Dazu gehören "
        "wiederholte Handlungen gegen eine bestimmte Person, die deren "
        "Lebensbedingungen verschlechtern und eine Beeinträchtigung der "
        "körperlichen oder geistigen Gesundheit zur Folge haben. Auch "
        "abgestimmtes Handeln mehrerer Personen fällt darunter, selbst wenn "
        "die Einzelhandlungen nicht wiederholt werden."
    ),
    max_penalty="Up to 2 years imprisonment and EUR 30,000 fine (up to 3 years and EUR 45,000 with aggravating circumstances)",
    applies_because=(
        "The victim was subjected to repeated harassing conduct via digital "
        "communications that degraded their living conditions and caused "
        "psychological harm."
    ),
    applies_because_de=(
        "Das Opfer wurde über digitale Kommunikation wiederholter belästigender "
        "Handlungen ausgesetzt, die seine Lebensbedingungen verschlechterten und "
        "psychischen Schaden verursachten."
    ),
)

# --- Art. 222-17 Code pénal — Menaces de mort ---

FR_MENACES_DE_MORT = GermanLaw(
    paragraph="Art. 222-17 Code pénal",
    title="Death threats (Menaces de mort)",
    title_de="Todesdrohungen (Menaces de mort)",
    description=(
        "Article 222-17 of the French Penal Code criminalises threats of death "
        "made against a person. When the threat is made in writing, by image, "
        "or through any other materialised medium — including electronic "
        "communications — the penalty is increased. Repeated threats or threats "
        "conditional on a demand carry heavier sentences."
    ),
    description_de=(
        "Artikel 222-17 des französischen Strafgesetzbuches stellt Todesdrohungen "
        "gegen eine Person unter Strafe. Wenn die Drohung schriftlich, durch "
        "Bilder oder über ein anderes materialisiertes Medium — einschließlich "
        "elektronischer Kommunikation — erfolgt, wird die Strafe erhöht. "
        "Wiederholte Drohungen oder an Forderungen geknüpfte Drohungen werden "
        "schwerer bestraft."
    ),
    max_penalty="Up to 3 years imprisonment and EUR 45,000 fine (up to 5 years and EUR 75,000 if conditional on a demand)",
    applies_because=(
        "The perpetrator made explicit death threats against the victim through "
        "an electronic communication, constituting a materialised threat."
    ),
    applies_because_de=(
        "Der Täter hat über elektronische Kommunikation explizite Todesdrohungen "
        "gegen das Opfer ausgesprochen, was eine materialisierte Drohung darstellt."
    ),
)

# --- Art. 226-1 Code pénal — Atteinte à la vie privée ---

FR_VIE_PRIVEE = GermanLaw(
    paragraph="Art. 226-1 Code pénal",
    title="Privacy violation (Atteinte à la vie privée)",
    title_de="Verletzung der Privatsphäre (Atteinte à la vie privée)",
    description=(
        "Article 226-1 of the French Penal Code criminalises the wilful violation "
        "of the intimacy of another person's private life by capturing, recording, "
        "or transmitting, without consent, the image of a person in a private "
        "place, or words spoken in private or confidential circumstances. This "
        "includes sharing private images or information online without consent "
        "(doxxing, revenge porn)."
    ),
    description_de=(
        "Artikel 226-1 des französischen Strafgesetzbuches stellt die vorsätzliche "
        "Verletzung der Privatsphäre einer anderen Person unter Strafe durch "
        "Aufnahme, Aufzeichnung oder Übermittlung — ohne Einwilligung — des Bildes "
        "einer Person an einem privaten Ort oder von Worten, die unter privaten "
        "oder vertraulichen Umständen gesprochen wurden. Dazu gehört auch das "
        "Veröffentlichen privater Bilder oder Informationen im Internet ohne "
        "Einwilligung (Doxxing, Rachepornografie)."
    ),
    max_penalty="Up to 1 year imprisonment and EUR 45,000 fine",
    applies_because=(
        "Private images or personal information of the victim were captured, "
        "recorded, or shared online without their consent, violating the "
        "intimacy of their private life."
    ),
    applies_because_de=(
        "Private Bilder oder persönliche Informationen des Opfers wurden ohne "
        "dessen Einwilligung aufgenommen, aufgezeichnet oder online geteilt, "
        "wodurch die Intimität seines Privatlebens verletzt wurde."
    ),
)

# --- Art. R621-1 Code pénal — Diffamation ---

FR_DIFFAMATION = GermanLaw(
    paragraph="Art. R621-1 Code pénal / Art. 29 Loi du 29 juillet 1881",
    title="Defamation (Diffamation)",
    title_de="Verleumdung (Diffamation)",
    description=(
        "Defamation in French law is defined by the Press Law of 29 July 1881 "
        "(Article 29) as any allegation or imputation of a specific fact that "
        "damages the honour or reputation of the person to whom it is attributed. "
        "When committed via online communications, the offence falls under the "
        "same framework. Article R621-1 of the Penal Code covers non-public "
        "defamation. Public online defamation is prosecuted under Articles 29 "
        "and 32 of the 1881 Press Law."
    ),
    description_de=(
        "Verleumdung wird im französischen Recht durch das Pressegesetz vom "
        "29. Juli 1881 (Artikel 29) definiert als jede Behauptung oder "
        "Zuschreibung einer bestimmten Tatsache, die die Ehre oder den Ruf "
        "der Person schädigt, der sie zugeschrieben wird. Bei Begehung über "
        "Online-Kommunikation gilt derselbe Rechtsrahmen. Artikel R621-1 des "
        "Strafgesetzbuches erfasst die nichtöffentliche Verleumdung. Öffentliche "
        "Online-Verleumdung wird nach den Artikeln 29 und 32 des Pressegesetzes "
        "von 1881 verfolgt."
    ),
    max_penalty="Up to EUR 12,000 fine for public defamation (Art. 32 Press Law); EUR 38 fine for non-public defamation (Art. R621-1 CP)",
    applies_because=(
        "The perpetrator publicly attributed specific false facts to the victim "
        "that damage their honour or reputation, constituting public defamation "
        "via an online communication."
    ),
    applies_because_de=(
        "Der Täter hat dem Opfer öffentlich bestimmte falsche Tatsachen "
        "zugeschrieben, die dessen Ehre oder Ruf schädigen, was eine öffentliche "
        "Verleumdung über Online-Kommunikation darstellt."
    ),
)

# --- Art. 313-1 Code pénal — Escroquerie ---

FR_ESCROQUERIE = GermanLaw(
    paragraph="Art. 313-1 Code pénal",
    title="Fraud (Escroquerie)",
    title_de="Betrug (Escroquerie)",
    description=(
        "Article 313-1 of the French Penal Code defines fraud (escroquerie) as "
        "the act of deceiving a natural or legal person by the use of a false "
        "name or false capacity, by the abuse of a genuine capacity, or by the "
        "use of fraudulent manoeuvres, to induce them to hand over funds, "
        "valuables, or any property, to provide a service, or to consent to an "
        "act that creates an obligation or a discharge. Online scams, phishing, "
        "and investment fraud fall under this provision."
    ),
    description_de=(
        "Artikel 313-1 des französischen Strafgesetzbuches definiert Betrug "
        "(Escroquerie) als die Handlung, eine natürliche oder juristische Person "
        "durch Verwendung eines falschen Namens oder einer falschen Eigenschaft, "
        "durch Missbrauch einer echten Eigenschaft oder durch betrügerische "
        "Machenschaften zu täuschen, um sie dazu zu bringen, Geld, Wertgegenstände "
        "oder sonstiges Eigentum auszuhändigen, eine Dienstleistung zu erbringen "
        "oder einer Handlung zuzustimmen, die eine Verpflichtung oder eine "
        "Entlastung begründet. Online-Betrug, Phishing und Investitionsbetrug "
        "fallen unter diese Vorschrift."
    ),
    max_penalty="Up to 5 years imprisonment and EUR 375,000 fine (up to 7 years and EUR 750,000 with aggravating circumstances)",
    applies_because=(
        "The perpetrator used deceptive means — such as a fake identity, "
        "fabricated credentials, or fraudulent investment promises — to induce "
        "the victim to hand over money or personal data."
    ),
    applies_because_de=(
        "Der Täter hat betrügerische Mittel eingesetzt — wie eine gefälschte "
        "Identität, erfundene Referenzen oder betrügerische Anlageversprechen — "
        "um das Opfer dazu zu bringen, Geld oder persönliche Daten herauszugeben."
    ),
)


# Convenience list of all French laws
ALL_FR_LAWS = [
    FR_LOI_AVIA,
    FR_HARCELEMENT_MORAL,
    FR_MENACES_DE_MORT,
    FR_VIE_PRIVEE,
    FR_DIFFAMATION,
    FR_ESCROQUERIE,
]
