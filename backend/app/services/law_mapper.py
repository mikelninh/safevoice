"""
International law mapper — returns applicable laws for a given country.
Supports Germany (de), Austria (at), and Switzerland (ch).
"""

from app.models.evidence import GermanLaw, Category

# German laws
from app.data.mock_data import (
    LAW_185, LAW_186, LAW_241, LAW_126A, NETZ_DG,
    LAW_263, LAW_263A, LAW_269,
)

# Austrian laws
from app.data.laws_austria import (
    AT_LAW_107, AT_LAW_107A, AT_LAW_107C,
    AT_LAW_111, AT_LAW_115, AT_LAW_105,
)

# Swiss laws
from app.data.laws_switzerland import (
    CH_LAW_173, CH_LAW_174, CH_LAW_177,
    CH_LAW_180, CH_LAW_181, CH_LAW_179SEPTIES,
)


# ---- Category-to-law mappings per country ----

GERMAN_LAW_MAP: dict[str, list[GermanLaw]] = {
    Category.HARASSMENT: [LAW_185],
    Category.THREAT: [LAW_241],
    Category.DEATH_THREAT: [LAW_126A, LAW_241],
    Category.DEFAMATION: [LAW_186],
    Category.FALSE_FACTS: [LAW_186],
    Category.MISOGYNY: [LAW_185],
    Category.BODY_SHAMING: [LAW_185],
    Category.SEXUAL_HARASSMENT: [LAW_185],
    Category.COORDINATED_ATTACK: [LAW_185],
    Category.SCAM: [LAW_263, LAW_263A],
    Category.PHISHING: [LAW_263, LAW_263A],
    Category.INVESTMENT_FRAUD: [LAW_263, LAW_263A],
    Category.ROMANCE_SCAM: [LAW_263, LAW_263A],
    Category.IMPERSONATION: [LAW_263, LAW_269],
}

AUSTRIAN_LAW_MAP: dict[str, list[GermanLaw]] = {
    Category.HARASSMENT: [AT_LAW_115, AT_LAW_107C],
    Category.THREAT: [AT_LAW_107],
    Category.DEATH_THREAT: [AT_LAW_107],
    Category.DEFAMATION: [AT_LAW_111],
    Category.FALSE_FACTS: [AT_LAW_111],
    Category.MISOGYNY: [AT_LAW_115],
    Category.BODY_SHAMING: [AT_LAW_115],
    Category.SEXUAL_HARASSMENT: [AT_LAW_105, AT_LAW_107C],
    Category.COORDINATED_ATTACK: [AT_LAW_107C],
    Category.SCAM: [AT_LAW_105],
    Category.PHISHING: [AT_LAW_105],
    Category.INVESTMENT_FRAUD: [AT_LAW_105],
    Category.ROMANCE_SCAM: [AT_LAW_105],
    Category.IMPERSONATION: [AT_LAW_105],
}

SWISS_LAW_MAP: dict[str, list[GermanLaw]] = {
    Category.HARASSMENT: [CH_LAW_177, CH_LAW_179SEPTIES],
    Category.THREAT: [CH_LAW_180],
    Category.DEATH_THREAT: [CH_LAW_180, CH_LAW_181],
    Category.DEFAMATION: [CH_LAW_173, CH_LAW_174],
    Category.FALSE_FACTS: [CH_LAW_173, CH_LAW_174],
    Category.MISOGYNY: [CH_LAW_177],
    Category.BODY_SHAMING: [CH_LAW_177],
    Category.SEXUAL_HARASSMENT: [CH_LAW_181, CH_LAW_179SEPTIES],
    Category.COORDINATED_ATTACK: [CH_LAW_179SEPTIES],
    Category.SCAM: [CH_LAW_181],
    Category.PHISHING: [CH_LAW_181],
    Category.INVESTMENT_FRAUD: [CH_LAW_181],
    Category.ROMANCE_SCAM: [CH_LAW_181],
    Category.IMPERSONATION: [CH_LAW_181],
}

COUNTRY_MAPS: dict[str, dict[str, list[GermanLaw]]] = {
    "de": GERMAN_LAW_MAP,
    "at": AUSTRIAN_LAW_MAP,
    "ch": SWISS_LAW_MAP,
}

# Platform enforcement laws that always apply per country
PLATFORM_LAWS: dict[str, list[GermanLaw]] = {
    "de": [NETZ_DG],
    "at": [],   # Austria does not have an equivalent to NetzDG
    "ch": [],   # Switzerland does not have an equivalent to NetzDG
}

SUPPORTED_COUNTRIES = ("de", "at", "ch")


def get_laws_for_country(
    country: str,
    categories: list,
    severity: str = "medium",
) -> list[GermanLaw]:
    """
    Return the applicable laws for a given country based on detected categories.

    Args:
        country: ISO country code — "de", "at", or "ch"
        categories: list of Category values (strings or Category enums)
        severity: severity level (unused for filtering but reserved for future use)

    Returns:
        Deduplicated list of GermanLaw objects relevant to the categories in the
        specified country's legal system.

    Raises:
        ValueError: if the country code is not supported.
    """
    country = country.lower().strip()
    if country not in SUPPORTED_COUNTRIES:
        raise ValueError(
            f"Unsupported country '{country}'. "
            f"Supported: {', '.join(SUPPORTED_COUNTRIES)}"
        )

    law_map = COUNTRY_MAPS[country]
    collected: list[GermanLaw] = []

    for cat in categories:
        # Accept both Category enum values and plain strings
        cat_key = cat.value if hasattr(cat, "value") else cat
        # Try direct key, then fall back to the string as-is
        laws = law_map.get(cat_key, law_map.get(cat, []))
        collected.extend(laws)

    # Add platform-level enforcement laws
    collected.extend(PLATFORM_LAWS.get(country, []))

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduplicated: list[GermanLaw] = []
    for law in collected:
        if law.paragraph not in seen:
            seen.add(law.paragraph)
            deduplicated.append(law)

    return deduplicated
