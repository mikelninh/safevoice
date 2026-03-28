"""
UK law definitions for SafeVoice.
Covers key statutes relevant to online harassment, threats, fraud, and platform duties.
"""

from app.models.evidence import GermanLaw

# --- Online Safety Act 2023 ---

UK_ONLINE_SAFETY_ACT = GermanLaw(
    paragraph="Online Safety Act 2023",
    title="Online Safety Act 2023 — Platform duty of care",
    title_de="Online-Sicherheitsgesetz 2023 — Sorgfaltspflicht der Plattformen",
    description=(
        "The Online Safety Act 2023 imposes a duty of care on providers of "
        "user-to-user services and search services to protect users from illegal "
        "content and, for Category 1 services, content that is harmful to adults. "
        "Ofcom is the regulator with enforcement powers including fines of up to "
        "GBP 18 million or 10% of qualifying worldwide revenue."
    ),
    description_de=(
        "Das Online-Sicherheitsgesetz 2023 verpflichtet Anbieter von Nutzer-zu-Nutzer-"
        "Diensten und Suchdiensten, Nutzer vor illegalen Inhalten und — bei Diensten "
        "der Kategorie 1 — vor für Erwachsene schädlichen Inhalten zu schützen. "
        "Ofcom ist die Aufsichtsbehörde mit Durchsetzungsbefugnissen einschließlich "
        "Geldbußen von bis zu 18 Millionen GBP oder 10 % des weltweiten Umsatzes."
    ),
    max_penalty="Fines up to GBP 18 million or 10% of qualifying worldwide revenue for platforms",
    applies_because=(
        "The platform has a legal duty to proactively address illegal content and "
        "protect users from harm. Failure to act on reported harmful content may "
        "constitute a breach of the platform's duty of care under the Act."
    ),
    applies_because_de=(
        "Die Plattform ist gesetzlich verpflichtet, proaktiv gegen illegale Inhalte "
        "vorzugehen und Nutzer vor Schaden zu schützen. Untätigkeit bei gemeldeten "
        "schädlichen Inhalten kann einen Verstoß gegen die Sorgfaltspflicht der "
        "Plattform nach dem Gesetz darstellen."
    ),
)

# --- Communications Act 2003 s.127 ---

UK_COMMUNICATIONS_ACT_S127 = GermanLaw(
    paragraph="Communications Act 2003, s. 127",
    title="Improper use of public electronic communications network",
    title_de="Missbräuchliche Nutzung eines öffentlichen elektronischen Kommunikationsnetzes",
    description=(
        "Section 127 of the Communications Act 2003 makes it an offence to send "
        "a message or other matter by means of a public electronic communications "
        "network that is grossly offensive, indecent, obscene, or menacing, or to "
        "send a message known to be false for the purpose of causing annoyance, "
        "inconvenience or needless anxiety."
    ),
    description_de=(
        "§ 127 des Kommunikationsgesetzes 2003 stellt das Versenden einer Nachricht "
        "oder anderer Inhalte über ein öffentliches elektronisches Kommunikationsnetz "
        "unter Strafe, wenn diese grob beleidigend, anstößig, obszön oder bedrohlich "
        "sind, oder wenn eine wissentlich falsche Nachricht zum Zweck der Belästigung, "
        "Unannehmlichkeit oder unnötigen Beunruhigung gesendet wird."
    ),
    max_penalty="Up to 6 months imprisonment and/or unlimited fine (summary conviction)",
    applies_because=(
        "The content was sent via a public electronic communications network and "
        "constitutes a grossly offensive or menacing message directed at the victim."
    ),
    applies_because_de=(
        "Der Inhalt wurde über ein öffentliches elektronisches Kommunikationsnetz "
        "gesendet und stellt eine grob beleidigende oder bedrohliche Nachricht dar, "
        "die an das Opfer gerichtet ist."
    ),
)

# --- Malicious Communications Act 1988 s.1 ---

UK_MALICIOUS_COMMS_S1 = GermanLaw(
    paragraph="Malicious Communications Act 1988, s. 1",
    title="Sending threatening or offensive communications",
    title_de="Versenden bedrohlicher oder beleidigender Mitteilungen",
    description=(
        "Section 1 of the Malicious Communications Act 1988 makes it an offence "
        "to send a letter, electronic communication, or article which conveys a "
        "threat, or which is indecent or grossly offensive, with the purpose of "
        "causing distress or anxiety to the recipient."
    ),
    description_de=(
        "§ 1 des Gesetzes über böswillige Mitteilungen von 1988 stellt das Versenden "
        "eines Briefes, einer elektronischen Mitteilung oder eines Gegenstands unter "
        "Strafe, der eine Drohung enthält oder anstößig oder grob beleidigend ist, "
        "mit dem Zweck, dem Empfänger Leid oder Angst zuzufügen."
    ),
    max_penalty="Up to 2 years imprisonment on indictment",
    applies_because=(
        "The communication was sent with the purpose of causing distress or anxiety "
        "to the victim, and its content is threatening, indecent, or grossly offensive."
    ),
    applies_because_de=(
        "Die Mitteilung wurde mit dem Zweck gesendet, dem Opfer Leid oder Angst "
        "zuzufügen, und ihr Inhalt ist bedrohlich, anstößig oder grob beleidigend."
    ),
)

# --- Protection from Harassment Act 1997 s.2 ---

UK_HARASSMENT_S2 = GermanLaw(
    paragraph="Protection from Harassment Act 1997, s. 2",
    title="Criminal harassment",
    title_de="Strafrechtliche Belästigung",
    description=(
        "Section 2 of the Protection from Harassment Act 1997 makes it an offence "
        "to pursue a course of conduct which amounts to harassment of another person "
        "and which the perpetrator knows or ought to know amounts to harassment. "
        "A 'course of conduct' must involve conduct on at least two occasions."
    ),
    description_de=(
        "§ 2 des Gesetzes zum Schutz vor Belästigung von 1997 stellt es unter "
        "Strafe, eine Handlungsweise zu verfolgen, die eine Belästigung einer "
        "anderen Person darstellt und von der der Täter weiß oder wissen müsste, "
        "dass sie Belästigung darstellt. Eine 'Handlungsweise' muss Verhalten "
        "bei mindestens zwei Gelegenheiten umfassen."
    ),
    max_penalty="Up to 6 months imprisonment and/or fine (summary conviction)",
    applies_because=(
        "The perpetrator engaged in a course of conduct on multiple occasions that "
        "amounts to harassment of the victim, and they knew or ought to have known "
        "that their behaviour constituted harassment."
    ),
    applies_because_de=(
        "Der Täter hat bei mehreren Gelegenheiten eine Handlungsweise verfolgt, "
        "die eine Belästigung des Opfers darstellt, und wusste oder hätte wissen "
        "müssen, dass sein Verhalten Belästigung darstellt."
    ),
)

# --- Protection from Harassment Act 1997 s.4 ---

UK_HARASSMENT_S4 = GermanLaw(
    paragraph="Protection from Harassment Act 1997, s. 4",
    title="Putting people in fear of violence",
    title_de="Versetzen von Personen in Angst vor Gewalt",
    description=(
        "Section 4 of the Protection from Harassment Act 1997 makes it an offence "
        "to pursue a course of conduct which causes another to fear, on at least "
        "two occasions, that violence will be used against them. The perpetrator "
        "must know or ought to know that the conduct will cause fear of violence."
    ),
    description_de=(
        "§ 4 des Gesetzes zum Schutz vor Belästigung von 1997 stellt es unter "
        "Strafe, eine Handlungsweise zu verfolgen, die bei einer anderen Person "
        "bei mindestens zwei Gelegenheiten die Befürchtung auslöst, dass Gewalt "
        "gegen sie angewendet wird. Der Täter muss wissen oder hätte wissen müssen, "
        "dass sein Verhalten Angst vor Gewalt auslöst."
    ),
    max_penalty="Up to 10 years imprisonment on indictment",
    applies_because=(
        "The perpetrator's repeated conduct has caused the victim to fear on at "
        "least two occasions that violence will be used against them."
    ),
    applies_because_de=(
        "Das wiederholte Verhalten des Täters hat beim Opfer bei mindestens "
        "zwei Gelegenheiten die Befürchtung ausgelöst, dass Gewalt gegen sie "
        "angewendet wird."
    ),
)

# --- Fraud Act 2006 s.2 ---

UK_FRAUD_ACT_S2 = GermanLaw(
    paragraph="Fraud Act 2006, s. 2",
    title="Fraud by false representation",
    title_de="Betrug durch falsche Darstellung",
    description=(
        "Section 2 of the Fraud Act 2006 makes it an offence to dishonestly make "
        "a false representation with intent to make a gain for oneself or another, "
        "or to cause loss to another or expose another to risk of loss. A "
        "representation may be express or implied and can be as to fact, law, or "
        "the state of mind of the person making it."
    ),
    description_de=(
        "§ 2 des Betrugsgesetzes 2006 stellt es unter Strafe, unehrlich eine "
        "falsche Darstellung zu machen mit der Absicht, sich oder einem anderen "
        "einen Vorteil zu verschaffen oder einem anderen einen Verlust zuzufügen "
        "oder ihn dem Risiko eines Verlustes auszusetzen. Eine Darstellung kann "
        "ausdrücklich oder stillschweigend sein und sich auf Tatsachen, Recht oder "
        "die Gesinnung des Erklärenden beziehen."
    ),
    max_penalty="Up to 10 years imprisonment on indictment and/or unlimited fine",
    applies_because=(
        "The perpetrator made false representations — such as a fake identity, "
        "fabricated credentials, or deceptive investment promises — with intent "
        "to make a financial gain or cause loss to the victim."
    ),
    applies_because_de=(
        "Der Täter hat falsche Darstellungen gemacht — wie eine gefälschte "
        "Identität, erfundene Referenzen oder irreführende Anlageversprechen — "
        "mit der Absicht, einen finanziellen Vorteil zu erlangen oder dem Opfer "
        "einen Verlust zuzufügen."
    ),
)

# --- Computer Misuse Act 1990 s.1 ---

UK_COMPUTER_MISUSE_S1 = GermanLaw(
    paragraph="Computer Misuse Act 1990, s. 1",
    title="Unauthorised access to computer material",
    title_de="Unbefugter Zugang zu Computerdaten",
    description=(
        "Section 1 of the Computer Misuse Act 1990 makes it an offence to cause "
        "a computer to perform any function with intent to secure access to any "
        "program or data held in any computer, where the access is unauthorised "
        "and the person knows at the time that it is unauthorised."
    ),
    description_de=(
        "§ 1 des Computermissbrauchsgesetzes 1990 stellt es unter Strafe, einen "
        "Computer dazu zu veranlassen, eine Funktion auszuführen, mit der Absicht, "
        "Zugang zu einem Programm oder Daten zu erlangen, die auf einem Computer "
        "gespeichert sind, wenn der Zugang unbefugt ist und die Person zum "
        "Zeitpunkt der Handlung weiß, dass er unbefugt ist."
    ),
    max_penalty="Up to 2 years imprisonment on indictment and/or unlimited fine",
    applies_because=(
        "The perpetrator accessed computer systems or accounts without authorisation, "
        "such as hacking into the victim's social media account or email."
    ),
    applies_because_de=(
        "Der Täter hat ohne Genehmigung auf Computersysteme oder Konten zugegriffen, "
        "beispielsweise durch Hacken des Social-Media-Kontos oder der E-Mail des Opfers."
    ),
)


# Convenience list of all UK laws
ALL_UK_LAWS = [
    UK_ONLINE_SAFETY_ACT,
    UK_COMMUNICATIONS_ACT_S127,
    UK_MALICIOUS_COMMS_S1,
    UK_HARASSMENT_S2,
    UK_HARASSMENT_S4,
    UK_FRAUD_ACT_S2,
    UK_COMPUTER_MISUSE_S1,
]
