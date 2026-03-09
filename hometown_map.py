import folium
import pandas as pd
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
MAPBOX_TOKEN = "pk.eyJ1IjoibWFyaXNzYWhvdWZmIiwiYSI6ImNtbHRxbnZyNzAzOXMzZ3EwaTk3dGI3N2YifQ.G7G7J7DyAWWxdslqbPvkmg"
CSV_FILE = "hometown_locations.csv"
OUTPUT_HTML = "hometown_map.html"

# Mapbox tile URL – using your custom Mapbox Studio style
MAPBOX_TILE_URL = (
    "https://api.mapbox.com/styles/v1/marissahouff/cmme0m6s6002r01s3dtfk8yk0/tiles/256/{z}/{x}/{y}@2x"
    f"?access_token={MAPBOX_TOKEN}"
)

# ── Pastel color / emoji mapping by location type ─────────────────────────────
TYPE_STYLE = {
    "Park":             {"bg": "#b8e6c8", "border": "#7ecb96", "emoji": "🌳"},
    "Restaurant":       {"bg": "#f7c5c5", "border": "#e89a9a", "emoji": "🍽️"},
    "Restaurant/Bar":   {"bg": "#f7c5c5", "border": "#e89a9a", "emoji": "🍹"},
    "Sports Venue":     {"bg": "#b8d4f0", "border": "#85b3de", "emoji": "🏟️"},
    "Music Venue":      {"bg": "#d8b8f0", "border": "#b68ade", "emoji": "🎵"},
    "Cafe":             {"bg": "#fde2b5", "border": "#f0c67a", "emoji": "☕"},
    "Recreation":       {"bg": "#b8e6d8", "border": "#7ecbb0", "emoji": "🌊"},
    "Event/Recreation": {"bg": "#c5d9f7", "border": "#95b5e8", "emoji": "🐴"},
    "Fitness":          {"bg": "#f0b8d8", "border": "#de85b3", "emoji": "💪"},
}
DEFAULT_STYLE = {"bg": "#e0e0e0", "border": "#b0b0b0", "emoji": "📍"}


def make_pastel_icon(style):
    """Return a folium DivIcon styled as a pastel circle with an emoji."""
    html = f"""
    <div style="
        background: {style['bg']};
        border: 2.5px solid {style['border']};
        width: 36px; height: 36px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.18);
        cursor: pointer;
    ">{style['emoji']}</div>
    """
    return folium.DivIcon(html=html, icon_size=(36, 36), icon_anchor=(18, 18))


# ── Geocoding with Mapbox ──────────────────────────────────────────────────────
def geocode_address(address):
    """Use the Mapbox Geocoding API to convert an address to (lat, lon)."""
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/" + requests.utils.quote(address) + ".json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}
    response = requests.get(url, params=params)
    data = response.json()

    if data.get("features"):
        lon, lat = data["features"][0]["center"]  # Mapbox returns [lon, lat]
        return lat, lon
    else:
        print(f"  ⚠ Could not geocode: {address}")
        return None, None


# ── Build popup HTML ───────────────────────────────────────────────────────────
def build_popup_html(row):
    """Return an HTML string for a marker popup showing name, description, and image."""
    html = f"""
    <div style="width:280px; font-family:Arial,sans-serif;">
        <h4 style="margin:0 0 6px 0; color:#333;">{row['Name']}</h4>
        <p style="font-size:12px; color:#555; margin:0 0 8px 0; font-style:italic;">
            {row['Type']}
        </p>
        <img src="{row['Image_URL']}" alt="{row['Name']}"
             style="width:100%; max-height:160px; object-fit:cover;
                    border-radius:6px; margin-bottom:8px;">
        <p style="font-size:13px; color:#444; line-height:1.4; margin:0;">
            {row['Description']}
        </p>
    </div>
    """
    return html


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # 1. Read CSV
    print("📖 Reading CSV …")
    df = pd.read_csv(CSV_FILE)
    # Strip any extra whitespace from column names
    df.columns = df.columns.str.strip()

    # 2. Geocode each address
    print("🌐 Geocoding addresses with Mapbox …")
    latitudes, longitudes = [], []
    for _, row in df.iterrows():
        lat, lon = geocode_address(row["Address"])
        latitudes.append(lat)
        longitudes.append(lon)
        print(f"  ✓ {row['Name']}: ({lat}, {lon})")

    df["Latitude"] = latitudes
    df["Longitude"] = longitudes

    # Drop rows that failed to geocode
    df = df.dropna(subset=["Latitude", "Longitude"])

    # 3. Create Folium map centred on Nashville with Mapbox basemap
    print("🗺️  Building map …")
    nashville_center = [36.1627, -86.7816]
    m = folium.Map(
        location=nashville_center,
        zoom_start=12,
        tiles=MAPBOX_TILE_URL,
        attr="Mapbox",
    )

    # 4. Add markers
    for _, row in df.iterrows():
        style = TYPE_STYLE.get(row["Type"].strip(), DEFAULT_STYLE)
        popup_html = build_popup_html(row)

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=row["Name"],
            icon=make_pastel_icon(style),
        ).add_to(m)

    # 5. Save to HTML
    m.save(OUTPUT_HTML)
    print(f"✅ Map saved to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()