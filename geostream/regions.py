"""Country -> continent lookup for grouping the dashboard."""

from __future__ import annotations

COUNTRY_CONTINENT = {
    # Asia
    "Sri Lanka": "Asia", "Indonesia": "Asia", "Philippines": "Asia", "India": "Asia",
    "United Arab Emirates": "Asia", "Saudi Arabia": "Asia", "Iran": "Asia", "Iraq": "Asia",
    "Pakistan": "Asia", "Bangladesh": "Asia", "Nepal": "Asia", "Thailand": "Asia",
    "Vietnam": "Asia", "Malaysia": "Asia", "Singapore": "Asia", "China": "Asia",
    "Japan": "Asia", "South Korea": "Asia", "Taiwan": "Asia",
    # Europe
    "United Kingdom": "Europe", "France": "Europe", "Spain": "Europe", "Portugal": "Europe",
    "Germany": "Europe", "Italy": "Europe", "Netherlands": "Europe", "Sweden": "Europe",
    "Norway": "Europe", "Russia": "Europe", "Greece": "Europe", "Turkey": "Europe",
    # Africa
    "Kenya": "Africa", "Egypt": "Africa", "Nigeria": "Africa", "Ghana": "Africa",
    "Ethiopia": "Africa", "South Africa": "Africa", "Morocco": "Africa", "Tanzania": "Africa",
    "Angola": "Africa", "Senegal": "Africa",
    # North America
    "United States": "North America", "Mexico": "North America", "Canada": "North America",
    # South America
    "Peru": "South America", "Ecuador": "South America", "Colombia": "South America",
    "Brazil": "South America", "Argentina": "South America", "Chile": "South America",
    "Venezuela": "South America",
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Papua New Guinea": "Oceania",
    "Fiji": "Oceania", "Samoa": "Oceania", "French Polynesia": "Oceania",
}


def continent_of(country: str) -> str:
    return COUNTRY_CONTINENT.get(country, "Other")
