from typing import Dict

# Complete Avakahada Chakra lookup for all 27 Nakshatras
NAKSHATRA_DATA = {
    "Ashwini": {"yoni": "Horse", "gana": "Deva", "nadi": "Aadi (Vata)", "varna": "Vaishya", "element": "Earth"},
    "Bharani": {"yoni": "Elephant", "gana": "Manushya", "nadi": "Madhya (Pitta)", "varna": "Outcaste", "element": "Earth"},
    "Krittika": {"yoni": "Sheep", "gana": "Rakshasa", "nadi": "Antya (Kapha)", "varna": "Brahmin", "element": "Earth"},
    "Rohini": {"yoni": "Serpent", "gana": "Manushya", "nadi": "Antya (Kapha)", "varna": "Shudra", "element": "Earth"},
    "Mrigashirsha": {"yoni": "Serpent", "gana": "Deva", "nadi": "Madhya (Pitta)", "varna": "Farmer", "element": "Earth"},
    "Ardra": {"yoni": "Dog", "gana": "Manushya", "nadi": "Aadi (Vata)", "varna": "Butcher", "element": "Water"},
    "Punarvasu": {"yoni": "Cat", "gana": "Deva", "nadi": "Aadi (Vata)", "varna": "Merchant", "element": "Water"},
    "Pushya": {"yoni": "Goat", "gana": "Deva", "nadi": "Madhya (Pitta)", "varna": "Kshatriya", "element": "Water"},
    "Ashlesha": {"yoni": "Cat", "gana": "Rakshasa", "nadi": "Antya (Kapha)", "varna": "Outcaste", "element": "Water"},
    "Magha": {"yoni": "Rat", "gana": "Rakshasa", "nadi": "Antya (Kapha)", "varna": "Shudra", "element": "Water"},
    "Purva Phalguni": {"yoni": "Rat", "gana": "Manushya", "nadi": "Madhya (Pitta)", "varna": "Brahmin", "element": "Fire"},
    "Uttara Phalguni": {"yoni": "Cow", "gana": "Manushya", "nadi": "Aadi (Vata)", "varna": "Kshatriya", "element": "Fire"},
    "Hasta": {"yoni": "Buffalo", "gana": "Deva", "nadi": "Aadi (Vata)", "varna": "Vaishya", "element": "Fire"},
    "Chitra": {"yoni": "Tiger", "gana": "Rakshasa", "nadi": "Madhya (Pitta)", "varna": "Farmer", "element": "Fire"},
    "Swati": {"yoni": "Buffalo", "gana": "Deva", "nadi": "Antya (Kapha)", "varna": "Butcher", "element": "Fire"},
    "Vishakha": {"yoni": "Tiger", "gana": "Rakshasa", "nadi": "Antya (Kapha)", "varna": "Outcaste", "element": "Air"},
    "Anuradha": {"yoni": "Deer", "gana": "Deva", "nadi": "Madhya (Pitta)", "varna": "Shudra", "element": "Air"},
    "Jyeshtha": {"yoni": "Deer", "gana": "Rakshasa", "nadi": "Aadi (Vata)", "varna": "Farmer", "element": "Air"},
    "Mula": {"yoni": "Dog", "gana": "Rakshasa", "nadi": "Aadi (Vata)", "varna": "Butcher", "element": "Air"},
    "Purvashada": {"yoni": "Monkey", "gana": "Manushya", "nadi": "Madhya (Pitta)", "varna": "Brahmin", "element": "Air"},
    "Uttarashada": {"yoni": "Mongoose", "gana": "Manushya", "nadi": "Antya (Kapha)", "varna": "Kshatriya", "element": "Ether"},
    "Shravana": {"yoni": "Monkey", "gana": "Deva", "nadi": "Antya (Kapha)", "varna": "Outcaste", "element": "Ether"},
    "Dhanishta": {"yoni": "Lion", "gana": "Rakshasa", "nadi": "Madhya (Pitta)", "varna": "Farmer", "element": "Ether"},
    "Shatabhisha": {"yoni": "Horse", "gana": "Rakshasa", "nadi": "Aadi (Vata)", "varna": "Butcher", "element": "Ether"},
    "Purva Bhadrapada": {"yoni": "Lion", "gana": "Manushya", "nadi": "Aadi (Vata)", "varna": "Brahmin", "element": "Ether"},
    "Uttara Bhadrapada": {"yoni": "Cow", "gana": "Manushya", "nadi": "Madhya (Pitta)", "varna": "Kshatriya", "element": "Ether"},
    "Revati": {"yoni": "Elephant", "gana": "Deva", "nadi": "Antya (Kapha)", "varna": "Shudra", "element": "Ether"}
}

# Ghata Chakra (Inauspicious elements) based on Moon Sign
GHATA_CHAKRA = {
    "Aries": {"month": "Kartika", "tithi": "1st, 6th, 11th", "day": "Sunday", "nakshatra": "Magha"},
    "Taurus": {"month": "Margashirsha", "tithi": "5th, 10th, 15th", "day": "Saturday", "nakshatra": "Hasta"},
    "Gemini": {"month": "Ashadha", "tithi": "2nd, 7th, 12th", "day": "Monday", "nakshatra": "Swati"},
    "Cancer": {"month": "Pausha", "tithi": "2nd, 7th, 12th", "day": "Wednesday", "nakshatra": "Anuradha"},
    "Leo": {"month": "Jyeshtha", "tithi": "3rd, 8th, 13th", "day": "Saturday", "nakshatra": "Mula"},
    "Virgo": {"month": "Bhadrapada", "tithi": "5th, 10th, 15th", "day": "Saturday", "nakshatra": "Shravana"},
    "Libra": {"month": "Ashwin", "tithi": "4th, 9th, 14th", "day": "Thursday", "nakshatra": "Shatabhisha"},
    "Scorpio": {"month": "Kartika", "tithi": "1st, 6th, 11th", "day": "Friday", "nakshatra": "Revati"},
    "Sagittarius": {"month": "Phalguna", "tithi": "3rd, 8th, 13th", "day": "Friday", "nakshatra": "Bharani"},
    "Capricorn": {"month": "Chaitra", "tithi": "4th, 9th, 14th", "day": "Tuesday", "nakshatra": "Rohini"},
    "Aquarius": {"month": "Vaishakha", "tithi": "3rd, 8th, 13th", "day": "Thursday", "nakshatra": "Ardra"},
    "Pisces": {"month": "Shravana", "tithi": "5th, 10th, 15th", "day": "Friday", "nakshatra": "Pushya"}
}

def compute_advanced_panchanga(moon_sign: str, moon_nakshatra_name: str) -> Dict:
    """
    Computes Avakahada Chakra and Ghata Chakra.
    """
    # Normalize nakshatra name to avoid key errors
    avakahada = NAKSHATRA_DATA.get(moon_nakshatra_name, {})
    ghata = GHATA_CHAKRA.get(moon_sign, {})

    return {
        "avakahada_chakra": avakahada,
        "ghata_chakra": ghata
    }
