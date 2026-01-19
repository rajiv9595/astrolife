"""
Tables Module
Computes astrological table data like Lucky Factors, Planetary Positions, etc.
All table-related computations are organized here.
"""

from typing import Dict, Any, List


# Telugu names for lucky factors
LUCKY_FACTORS_TELUGU = {
    "title": "అదృష్ట విషయములు",
    "categories": {
        "lucky_days": "అదృష్ట దినములు",
        "lucky_planets": "అదృష్ట గ్రహములు",
        "friendly_signs": "మిత్రరాశులు",
        "friendly_ascendants": "మిత్రలగ్నములు",
        "life_gemstone": "జీవన రత్నం",
        "lucky_gemstone": "అదృష్ట రత్నం",
        "meritorious_gemstone": "పుణ్యరత్నం",
        "favorable_deity": "అనుకూలదైవం",
        "favorable_metal": "అనుకూల లోహం",
        "lucky_color": "అదృష్ట వర్ణం",
        "lucky_direction": "అదృష్ట దిశ",
        "lucky_time": "అదృష్ట సమయం",
        "favorable_numbers": "అనుకూల సంఖ్యలు"
    },
    "disclaimer": "పైన ఇవ్వబడిన రత్నములు కేవలం సూచన మాత్రమే, రత్ననిర్ణయంలో జ్యోతిష్కుని సలహా తీసుకోవటం మంచిది."
}

# Sanskrit signs mapping
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Day lords mapping
DAY_LORDS = {
    "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars",
    "Wednesday": "Mercury", "Thursday": "Jupiter",
    "Friday": "Venus", "Saturday": "Saturn"
}


# Planet lord of each sign
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}


# Friendly signs mapping
FRIENDLY_SIGNS = {
    "Sun": ["Leo", "Libra", "Aries"],
    "Moon": ["Cancer", "Taurus", "Pisces"],
    "Mars": ["Aries", "Scorpio", "Capricorn", "Leo"],
    "Mercury": ["Virgo", "Gemini", "Aquarius"],
    "Jupiter": ["Sagittarius", "Pisces", "Cancer", "Libra"],
    "Venus": ["Capricorn", "Virgo"],
    "Saturn": ["Capricorn", "Aquarius", "Libra"]
}

# Gemstone mapping
GEMSTONE_MAPPING = {
    "Sun": {"life": "Ruby", "lucky": "Ruby", "meritorious": "Ruby"},
    "Moon": {"life": "Pearl", "lucky": "Moonstone", "meritorious": "Pearl"},
    "Mars": {"life": "Coral", "lucky": "Red Coral", "meritorious": "Coral"},
    "Mercury": {"life": "Emerald", "lucky": "Emerald", "meritorious": "Peridot"},
    "Jupiter": {"life": "Yellow Sapphire", "lucky": "Yellow Sapphire", "meritorious": "Topaz"},
    "Venus": {"life": "Diamond", "lucky": "Blue Sapphire", "meritorious": "Emerald"},
    "Saturn": {"life": "Blue Sapphire", "lucky": "Amethyst", "meritorious": "Lapis Lazuli"},
    "Rahu": {"life": "Gomed", "lucky": "Hessonite", "meritorious": "Gomed"},
    "Ketu": {"life": "Cat's Eye", "lucky": "Lehsunia", "meritorious": "Cat's Eye"}
}

# Deity mapping
DEITY_MAPPING = {
    "Sun": "Lord Surya, Lord Rama, Lord Vishnu",
    "Moon": "Lord Shiva, Goddess Parvati, Lord Krishna",
    "Mars": "Lord Hanuman, Lord Kartikeya, Lord Shiva",
    "Mercury": "Lord Vishnu, Goddess Saraswati, Lord Ganesha",
    "Jupiter": "Lord Vishnu, Lord Brahma, Goddess Lakshmi",
    "Venus": "Goddess Lakshmi, Lord Venkateswara Swamy",
    "Saturn": "Lord Shani, Lord Hanuman, Lord Shiva",
    "Rahu": "Goddess Kali, Lord Shiva, Lord Bhairava",
    "Ketu": "Lord Ganesha, Lord Shiva, Lord Hanuman"
}

# Metal mapping
METAL_MAPPING = {
    "Sun": "Gold",
    "Moon": "Silver",
    "Mars": "Copper",
    "Mercury": "Gold and Silver",
    "Jupiter": "Gold",
    "Venus": "Silver and Iron",
    "Saturn": "Iron and Lead"
}

# Color mapping
COLOR_MAPPING = {
    "Sun": "Red and Orange",
    "Moon": "White and Silver",
    "Mars": "Red",
    "Mercury": "Green",
    "Jupiter": "Yellow and Gold",
    "Venus": "White and Sandalwood",
    "Saturn": "Blue and Black",
    "Rahu": "Blue and Black",
    "Ketu": "Multicolored"
}

# Direction mapping
DIRECTION_MAPPING = {
    "Sun": "East",
    "Moon": "Northwest",
    "Mars": "South",
    "Mercury": "North",
    "Jupiter": "Northeast",
    "Venus": "Southeast, North and West",
    "Saturn": "West"
}

# Lucky numbers mapping
NUMBER_MAPPING = {
    "Sun": [1, 4, 10],
    "Moon": [2, 7],
    "Mars": [3, 9],
    "Mercury": [5, 6],
    "Jupiter": [3, 12],
    "Venus": [5, 6, 8],
    "Saturn": [8, 9]
}


def compute_lucky_factors(asc_sign: str, moon_sign: str, lagna_lord: str) -> Dict[str, Any]:
    """
    Compute all lucky factors based on ascendant sign, moon sign, and lagna lord.
    
    Args:
        asc_sign: The ascendant sign (e.g., "Leo", "Capricorn")
        moon_sign: The moon sign (e.g., "Virgo", "Taurus")
        lagna_lord: The lord of the ascendant sign (e.g., "Sun", "Saturn")
    
    Returns:
        Dictionary containing all lucky factors
    """
    if not asc_sign or not lagna_lord:
        return {}
    
    # Lucky days (based on lagna lord and friendly planets)
    lucky_days = []
    lord_day_mapping = {
        "Sun": "Sunday",
        "Moon": "Monday",
        "Mars": "Tuesday",
        "Mercury": "Wednesday",
        "Jupiter": "Thursday",
        "Venus": "Friday",
        "Saturn": "Saturday"
    }
    
    # Add friendly planet days (not the lagna lord's own day)
    friendly_planets = get_friendly_planets(lagna_lord)
    for planet in friendly_planets:
        if planet in lord_day_mapping:
            day = lord_day_mapping[planet]
            if day not in lucky_days:
                lucky_days.append(day)
    
    # Lucky planets (based on friendly relationships)
    lucky_planets = get_friendly_planets(lagna_lord)
    
    # Friendly signs (based on lagna lord's friends)
    friendly_signs = get_friendly_signs(lagna_lord)
    
    # Friendly ascendants (signs ruled by friendly planets)
    friendly_ascendants = []
    for planet in get_friendly_planets(lagna_lord):
        planet_signs = [sign for sign, lord in SIGN_LORDS.items() if lord == planet]
        friendly_ascendants.extend(planet_signs)
    
    # Add current ascendant if not present
    if asc_sign not in friendly_ascendants:
        friendly_ascendants.insert(0, asc_sign)
    
    # Remove duplicates
    seen = set()
    friendly_ascendants_unique = []
    for sign in friendly_ascendants:
        if sign not in seen:
            seen.add(sign)
            friendly_ascendants_unique.append(sign)
    friendly_ascendants = friendly_ascendants_unique[:5]  # Limit to top 5
    
    # Gemstones (based on lagna lord)
    gemstones = GEMSTONE_MAPPING.get(lagna_lord, {})
    
    # Deity (based on lagna lord)
    deity = DEITY_MAPPING.get(lagna_lord, "")
    
    # Metal (based on lagna lord)
    metal = METAL_MAPPING.get(lagna_lord, "")
    
    # Color (based on lagna lord)
    color = COLOR_MAPPING.get(lagna_lord, "")
    
    # Direction (based on lagna lord)
    direction = DIRECTION_MAPPING.get(lagna_lord, "")
    
    # Lucky time (day of the week specific)
    lucky_time = "Dawn and Sunrise"
    if lagna_lord == "Moon":
        lucky_time = "Evening"
    elif lagna_lord == "Mars":
        lucky_time = "Midday"
    
    # Lucky numbers (based on lagna lord)
    numbers = NUMBER_MAPPING.get(lagna_lord, [])
    
    return {
        "lucky_days": lucky_days,
        "lucky_planets": lucky_planets,
        "friendly_signs": friendly_signs,
        "friendly_ascendants": friendly_ascendants,
        "life_gemstone": gemstones.get("life", ""),
        "lucky_gemstone": gemstones.get("lucky", ""),
        "meritorious_gemstone": gemstones.get("meritorious", ""),
        "favorable_deity": deity,
        "favorable_metal": metal,
        "lucky_color": color,
        "lucky_direction": direction,
        "lucky_time": lucky_time,
        "favorable_numbers": numbers,
        "telugu": LUCKY_FACTORS_TELUGU
    }


def get_friendly_planets(planet: str) -> List[str]:
    """Get friendly planets for a given planet."""
    friends = {
        "Sun": ["Moon", "Mars", "Jupiter"],
        "Moon": ["Sun", "Mercury", "Mars"],
        "Mars": ["Sun", "Moon", "Jupiter"],
        "Mercury": ["Sun", "Venus"],
        "Jupiter": ["Sun", "Moon", "Mars"],
        "Venus": ["Saturn", "Mercury", "Sun"],
        "Saturn": ["Mercury", "Venus", "Rahu"]
    }
    return friends.get(planet, [])


def get_friendly_signs(planet: str) -> List[str]:
    """Get friendly signs for a given planet."""
    return FRIENDLY_SIGNS.get(planet, [])

