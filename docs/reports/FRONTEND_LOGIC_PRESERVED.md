# Preserved Logic for Frontend Rebuild

## 1. Geolocation Logic (from `BirthForm.jsx`)
- **Endpoint**: `http://localhost:8001/geocode/search?query=${locationQuery}`
- **Behavior**:
  - Debounce time: 800ms
  - Validates latitude (-90 to 90) and longitude (-180 to 180).
  - Auto-fills lat/long when a location is selected from the search.
  - Allows manual entry if auto-search fails.

## 2. Chart Logic (from `Chart.jsx`)
- **Type**: South Indian Chart Layout.
- **Layout Definition**:
  - The chart uses a fixed layout where signs are always in the same position.
  - **Pisces** is Top-Left.
  - **Aries** is Top-Middle-Left.
  - The sequence follows clockwise.
  
```javascript
const SOUTH_INDIAN_LAYOUT = [
  { house: 12, signIndex: 11 }, // Pisces - Top Left
  { house: 1, signIndex: 0 },   // Aries - Top Middle Left
  { house: 2, signIndex: 1 },   // Taurus - Top Middle Right
  { house: 3, signIndex: 2 },   // Gemini - Top Right
  { house: 4, signIndex: 3 },   // Cancer - Right Middle Upper
  { house: 5, signIndex: 4 },   // Leo - Right Middle Lower
  { house: 6, signIndex: 5 },   // Virgo - Bottom Right
  { house: 7, signIndex: 6 },   // Libra - Bottom Middle Right
  { house: 8, signIndex: 7 },   // Scorpio - Bottom Middle Left
  { house: 9, signIndex: 8 },   // Sagittarius - Bottom Left
  { house: 10, signIndex: 9 },  // Capricorn - Left Middle Lower
  { house: 11, signIndex: 10 }  // Aquarius - Left Middle Upper
]
```

- **Planet Placement Algorithm**:
  1. Iterate through planets in `chartData.planets`.
  2. Get the planet's sign (`sign_manual` or `sign_flag`).
  3. Find the house number associated with that sign in the fixed layout (`findHouseBySign`).
  4. Place the planet in that house.
  5. Handle Ascendant separately by finding the house matching `chartData.ascendant.sign`.

- **Visual Elements**:
  - "Asc" label for the ascendant house.
  - Planet names (with 'R' for retrograde).
  - Tooltips showing degrees, exalted/debilitated status.
