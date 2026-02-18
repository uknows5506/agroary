import streamlit as st
import ee
import geemap.foliumap as geemap
import datetime
import pandas as pd
import altair as alt
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Farmer Insight Pro", layout="wide", page_icon="🚜")

# --- KESİN ÇÖZÜM BAĞLANTI BLOĞU ---
def gee_baglan():
    if "EARTHENGINE_TOKEN" in st.secrets:
        try:
            # Secrets'tan anahtarı al
            anahtar_verisi = json.loads(st.secrets["EARTHENGINE_TOKEN"])

            # 1. Burası Önemli: Servis hesabı kimliğini oluştur
            kimlik = ee.ServiceAccountCredentials(
                anahtar_verisi['client_email'],
                key_data=st.secrets["EARTHENGINE_TOKEN"]
            )

            # 2. Burası Önemli:setDefaultWorkloadTag ekleyerek bağlantıyı mühürle
            ee.data.setDefaultWorkloadTag('farmer-insight-app')

            # 3. Proje ID'si ile başlat
            ee.Initialize(kimlik, project='environmental-analysis-482013')
            return True
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
            return False
    else:
        # Lokal çalışma alanı (PyCharm)
        try:
            ee.Initialize()
            return True
        except:
            st.error("Lütfen Streamlit Secrets ayarlarını yapın!")
            return False

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; }
    h1 { color: #2e7d32; } /* Nature Green */
    .analysis-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e0e0e0; }
    .report-box { padding: 15px; border-radius: 6px; margin-top: 10px; font-size: 0.95em; line-height: 1.6; }
    .success { background-color: #e8f5e9; border: 1px solid #c8e6c9; color: #1b5e20; }
    .warning { background-color: #fff3e0; border: 1px solid #ffe0b2; color: #e65100; }
    .danger { background-color: #ffebee; border: 1px solid #ffcdd2; color: #b71c1c; }
    iframe { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KNOWLEDGE BASE (NBS - ENGLISH) ---
ANALYSIS_CONFIG = {
    'NDVI': {
        'name': '1. Vegetation Health (NDVI)',
        'desc': 'Plant vigor & Biomass density.',
        'breaks': [0.20, 0.40, 0.60, 0.80],
        'colors': ['danger', 'warning', 'warning', 'success', 'success'],
        'msgs': [
            "🛑 STATUS: Critical/Dead.<br>💡 <b>NBS REMEDY:</b> Soil is degraded. Apply <b>'Green Manure'</b> (vetch/clover) to restore organic matter.",
            "⚠️ STATUS: Weak / Stressed.<br>💡 <b>NBS REMEDY:</b> Root activity is low. Apply <b>Compost Tea</b> or Seaweed extract to stimulate microbiome.",
            "⚖️ STATUS: Developing.<br>💡 <b>NBS REMEDY:</b> Enhance biodiversity. Consider <b>Intercropping</b> with companion plants.",
            "✅ STATUS: Healthy.<br>💡 <b>NBS REMEDY:</b> Great job! Continue with <b>Regenerative Practices</b>.",
            "🌟 STATUS: Peak Vigor.<br>💡 <b>NBS REMEDY:</b> Excellent biomass. Plan for <b>Residue Management</b> post-harvest (do not burn)."
        ],
        'reverse': False
    },
    'GDNVI': {
        'name': '2. Nitrogen Status (GDNVI)',
        'desc': 'Chlorophyll & Nitrogen content.',
        'breaks': [0.35, 0.50, 0.70, 0.85],
        'colors': ['danger', 'warning', 'success', 'success', 'warning'],
        'msgs': [
            "🛑 STATUS: Critical N Deficiency.<br>💡 <b>NBS REMEDY:</b> Plant <b>Nitrogen-Fixing Legumes</b> (Beans/Peas) in rotation. Use composted animal manure.",
            "⚠️ STATUS: Low Chlorophyll (Hidden Hunger).<br>💡 <b>NBS REMEDY:</b> Apply liquid organic fertilizer (e.g., <b>Nettle Slurry</b>) for quick uptake.",
            "✅ STATUS: Optimal Nitrogen.<br>💡 <b>NBS REMEDY:</b> Balance is good. Maintain <b>Crop Rotation</b> to naturally replenish soil N.",
            "🌟 STATUS: High / Lush.<br>💡 <b>NBS REMEDY:</b> Nitrogen is sufficient. Prevent leaching by maintaining continuous root cover.",
            "🔵 STATUS: Excess Nitrogen Risk.<br>💡 <b>NBS REMEDY:</b> Caution! Too much N makes plants tasty to pests. Monitor for aphids."
        ],
        'reverse': False
    },
    'SI': {
        'name': '3. Salinity Index (SI)',
        'desc': 'Soil salt accumulation.',
        'breaks': [0.08, 0.14, 0.18, 0.22],
        'colors': ['success', 'success', 'warning', 'danger', 'danger'],
        'msgs': [
            "🌟 STATUS: No Salinity.<br>💡 <b>NBS REMEDY:</b> Soil is healthy. Maintain <b>Organic Mulch</b> to prevent surface evaporation/salting.",
            "✅ STATUS: Low Risk.<br>💡 <b>NBS REMEDY:</b> Keep soil moist. Use <b>Bio-drainage</b> (planting deep-rooted trees on borders).",
            "⚖️ STATUS: Moderate Salinity.<br>💡 <b>NBS REMEDY:</b> Increase Soil Organic Matter (SOM) with <b>Humic Acid</b> to buffer salts.",
            "⚠️ STATUS: High Salinity!<br>💡 <b>NBS REMEDY:</b> Plant <b>Halophytes</b> (salt-tolerant crops like Barley/Beets). Avoid chemical fertilizers.",
            "🛑 STATUS: Critical Salinization.<br>💡 <b>NBS REMEDY:</b> Soil structure collapsed. Needs bioremediation and heavy organic amendments."
        ],
        'reverse': True
    },
    'NDWI': {
        'name': '4. Water Content (NDWI)',
        'desc': 'Plant water stress.',
        'breaks': [-0.15, -0.05, 0.05, 0.30],
        'colors': ['danger', 'warning', 'success', 'success', 'warning'],
        'msgs': [
            "🛑 STATUS: Severe Drought.<br>💡 <b>NBS REMEDY:</b> Urgent! Apply <b>Heavy Mulch</b> (Straw/Leaves) to stop evaporation immediately.",
            "⚠️ STATUS: Water Stress.<br>💡 <b>NBS REMEDY:</b> Improve soil water retention with <b>Biochar</b>. Irrigate at night.",
            "✅ STATUS: Optimal Moisture.<br>💡 <b>NBS REMEDY:</b> Soil structure is holding water well. Good organic matter levels.",
            "🌟 STATUS: High Moisture.<br>💡 <b>NBS REMEDY:</b> Good. Ensure <b>Swales</b> or contour lines are working to capture runoff.",
            "💧 STATUS: Saturated / Waterlogging.<br>💡 <b>NBS REMEDY:</b> Roots need air! Improve aeration with <b>Cover Crops</b> (Tillage Radish)."
        ],
        'reverse': False
    },
    'SAVI': {
        'name': '5. Soil Adjusted Health (SAVI)',
        'desc': 'Early growth health (Soil corrected).',
        'breaks': [0.30, 0.50, 0.65, 0.80],
        'colors': ['danger', 'warning', 'success', 'success', 'success'],
        'msgs': [
            "🛑 STATUS: Bare Soil / No Emergence.<br>💡 <b>NBS REMEDY:</b> Protect bare soil with <b>Straw Mulch</b> or cover crops.",
            "⚠️ STATUS: Sparse / Establishing.<br>💡 <b>NBS REMEDY:</b> Support seedlings with <b>Mycorrhizal Fungi</b> inoculation.",
            "✅ STATUS: Developing Well.<br>💡 <b>NBS REMEDY:</b> Mechanical weeding (if needed) or mulching to suppress weeds naturally.",
            "🌟 STATUS: Canopy Closing.<br>💡 <b>NBS REMEDY:</b> Crop is outcompeting weeds naturally.",
            "🌟 STATUS: Dense Canopy.<br>💡 <b>NBS REMEDY:</b> Perfect solar capture. Soil is fully shaded and protected."
        ],
        'reverse': False
    },
    'BSI': {
        'name': '6. Bare Soil Index (BSI)',
        'desc': 'Erosion risk indicator.',
        'breaks': [0.05, 0.15, 0.25, 0.35],
        'colors': ['success', 'success', 'warning', 'danger', 'danger'],
        'msgs': [
            "🌟 STATUS: Fully Covered.<br>💡 <b>NBS REMEDY:</b> Excellent! Zero erosion risk. Soil biology is protected.",
            "✅ STATUS: Good Coverage.<br>💡 <b>NBS REMEDY:</b> Maintain <b>Continuous Living Cover</b> on the field.",
            "⚖️ STATUS: Some Exposure.<br>💡 <b>NBS REMEDY:</b> Do not burn stubble! Leave crop residues on the field.",
            "⚠️ STATUS: Erosion Risk.<br>💡 <b>NBS REMEDY:</b> Danger! Plant <b>Cover Crops</b> (Rye/Vetch) immediately.",
            "🛑 STATUS: Bare / Degraded.<br>💡 <b>NBS REMEDY:</b> Stop Tillage! Adopt <b>No-Till</b> farming to save topsoil."
        ],
        'reverse': True
    },
    'MSI': {
        'name': '7. Moisture Stress (MSI)',
        'desc': 'Leaf water potential stress (Lower is better).',
        'breaks': [0.6, 0.8, 1.2, 1.5],
        'colors': ['success', 'success', 'warning', 'danger', 'danger'],
        'msgs': [
            "🌟 STATUS: No Stress.<br>💡 <b>NBS:</b> Ideal turgor pressure.",
            "✅ STATUS: Low Stress.<br>💡 <b>NBS:</b> Keep monitoring.",
            "⚖️ STATUS: Mild Stress.<br>💡 <b>NBS:</b> Consider shade nets if heat is high.",
            "⚠️ STATUS: High Stress!<br>💡 <b>NBS:</b> Focus irrigation on root zone.",
            "🛑 STATUS: Critical Wilting.<br>💡 <b>NBS:</b> Emergency irrigation needed."
        ],
        'reverse': True
    }
}


# --- 4. HELPER FUNCTIONS ---

def get_compass_direction(azimuth):
    """Aspect Degrees -> English Direction"""
    if azimuth > 337.5 or azimuth <= 22.5:
        return "North (N)"
    elif 22.5 < azimuth <= 67.5:
        return "North-East (NE)"
    elif 67.5 < azimuth <= 112.5:
        return "East (E)"
    elif 112.5 < azimuth <= 157.5:
        return "South-East (SE)"
    elif 157.5 < azimuth <= 202.5:
        return "South (S)"
    elif 202.5 < azimuth <= 247.5:
        return "South-West (SW)"
    elif 247.5 < azimuth <= 292.5:
        return "West (W)"
    else:
        return "North-West (NW)"


def get_status_data(idx, val):
    cfg = ANALYSIS_CONFIG[idx]
    level = 0
    if not cfg['reverse']:
        if val < cfg['breaks'][0]:
            level = 0
        elif val < cfg['breaks'][1]:
            level = 1
        elif val < cfg['breaks'][2]:
            level = 2
        elif val < cfg['breaks'][3]:
            level = 3
        else:
            level = 4
    else:
        if val < cfg['breaks'][0]:
            level = 0
        elif val < cfg['breaks'][1]:
            level = 1
        elif val < cfg['breaks'][2]:
            level = 2
        elif val < cfg['breaks'][3]:
            level = 3
        else:
            level = 4
    return cfg['name'], cfg['desc'], cfg['msgs'][level], cfg['colors'][level]


def mask_clouds(image):
    qa = image.select('QA60')
    return image.updateMask(qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0)))


def calculate_indices(image):
    # DÜZELTME: Sentinel-2 verisini 10000'e bölerek 0-1 arasına çekiyoruz.
    b = {
        'B2': image.select('B2').divide(10000.0),
        'B3': image.select('B3').divide(10000.0),
        'B4': image.select('B4').divide(10000.0),
        'B8': image.select('B8').divide(10000.0),
        'B11': image.select('B11').divide(10000.0)
    }

    return image.addBands([
        image.normalizedDifference(['B8', 'B4']).rename('NDVI'),
        image.normalizedDifference(['B8', 'B11']).rename('NDWI'),
        image.normalizedDifference(['B8', 'B3']).rename('GDNVI'),
        image.expression('((NIR - RED) * 1.5) / (NIR + RED + 0.5)', {'NIR': b['B8'], 'RED': b['B4']}).rename('SAVI'),
        image.expression('((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2) + 0.0001)', b).rename('BSI'),
        image.expression('sqrt(B2 * B4)', b).rename('SI'),
        image.expression('B11 / B8', b).rename('MSI')  # Moisture Stress Index
    ]).copyProperties(image, ['system:time_start'])


def get_full_timeseries(collection, roi):
    def extract(img):
        # DÜZELTME: Scale=10 ve Median kullanımı (Precision Mode)
        stats = img.reduceRegion(reducer=ee.Reducer.median(), geometry=roi, scale=10, bestEffort=True)
        return ee.Feature(None, {
            'Date': ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'),
            'NDVI': stats.get('NDVI'), 'GDNVI': stats.get('GDNVI'),
            'SI': stats.get('SI'), 'NDWI': stats.get('NDWI'),
            'SAVI': stats.get('SAVI'), 'BSI': stats.get('BSI'), 'MSI': stats.get('MSI')
        })

    return collection.map(extract).filter(ee.Filter.notNull(['NDVI'])).limit(100)

# --- 5. SIDEBAR (SOL MENÜ) ---
with st.sidebar:
    st.title("🚜 Farmer Insight")
    st.markdown("---")
    st.header("📅 Date Range")
    start_date = st.date_input("Start", datetime.date(2024, 1, 1))
    end_date = st.date_input("End", datetime.date(2024, 12, 31))

    st.header("⚙️ Settings")
    cloud_perc = st.slider("Cloud Tolerance (%)", 0, 30, 15)

    st.header("👁️ Layers")
    layer_select = st.selectbox("View Layer",
                                ["Natural Color", "NDVI", "GDNVI", "SI", "SAVI", "NDWI", "BSI", "MSI", "Slope"])
    st.info("👇 **Instruction:** Draw a polygon on the map to start.")

# --- 6. GÜVENLİ BAĞLANTI FONKSİYONU ---
def connect_gee():
    """Google Earth Engine bağlantısını güvenli şekilde kurar."""
    # 1. Streamlit Cloud (Secrets) Kontrolü
    if "EARTHENGINE_TOKEN" in st.secrets:
        try:
            secret_dict = json.loads(st.secrets["EARTHENGINE_TOKEN"])
            credentials = ee.ServiceAccountCredentials(
                secret_dict['client_email'],
                key_data=st.secrets["EARTHENGINE_TOKEN"]
            )
            ee.Initialize(credentials, project='environmental-analysis-482013')
            return True
        except Exception as e:
            st.error(f"Bulut Bağlantı Hatası: {e}")
            return False
    # 2. Lokal Bilgisayar Kontrolü
    else:
        try:
            ee.Initialize()
            return True
        except Exception:
            st.warning("GEE Yetkisi Bulunamadı. Lokalde 'earthengine authenticate' yapın veya Secrets ekleyin.")
            return False

# --- 7. ANA UYGULAMA (TEK HARİTA) ---
if connect_gee():
    st.title("🚜 Farmer Insight Pro - Precision Edition 🔬")

    # Haritayı oluştur
    m = geemap.Map(center=[39.0, 35.0], zoom=6)
    m.add_basemap("HYBRID")
    m.add_basemap("ROADMAP")
    m.add_layer_control()

    # Haritayı ekrana bas
    map_output = st_folium(m, height=500, width=None, key="farmer_map")

    # Çizim varsa analizi başlat
    if map_output and map_output.get("last_active_drawing"):
        roi_coords = map_output["last_active_drawing"]["geometry"]["coordinates"]
        roi = ee.Geometry.Polygon(roi_coords)
        roi_veg = roi.buffer(-5)

        st.success("✅ Field Successfully Identified! Precision Mode Active...")

        with st.spinner('🚀 Calculating Advanced Analytics...'):
            try:
                # 1. UYDU GÖRÜNTÜSÜ
                s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                          .filterBounds(roi_veg).filterDate(str(start_date), str(end_date))
                          .filter(ee.Filter.lt('CLOUDY_PIXEL_OVER_LAND_PERCENTAGE', cloud_perc))
                          .map(mask_clouds).map(calculate_indices))

                if s2_col.size().getInfo() > 0:
                    # 2. ARAZİ ANALİZİ
                    srtm = ee.Image('USGS/SRTMGL1_003').clip(roi)
                    terrain = ee.Algorithms.Terrain(srtm)
                    t_stats = terrain.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30, bestEffort=True).getInfo()

                    slope_val = t_stats.get('slope', 0)
                    aspect_val = t_stats.get('aspect', 0)
                    elevation_val = t_stats.get('elevation', 0)
                    compass = get_compass_direction(aspect_val) if aspect_val is not None else "N/A"

                    # 3. İSTATİSTİKLER VE GRAFİKLER
                    image = s2_col.median().clip(roi_veg)
                    stats = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi_veg, scale=10, bestEffort=True).getInfo()

                    ts_data = get_full_timeseries(s2_col, roi_veg)
                    ts_list = ts_data.reduceColumns(ee.Reducer.toList(8),
                                                    ['Date', 'NDVI', 'GDNVI', 'SI', 'SAVI', 'NDWI', 'BSI', 'MSI']).values().get(0).getInfo()
                    df = pd.DataFrame(ts_list, columns=['Date', 'NDVI', 'GDNVI', 'SI', 'SAVI', 'NDWI', 'BSI', 'MSI'])
                    df['Date'] = pd.to_datetime(df['Date'])

                    # --- SEKMELER ---
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 NBS Prescriptions", "🧠 AI Cross-Analysis", "⛰️ Topography", "🌦️ Climate (NBS)"])

                    # TAB 1: REÇETELER
                    with tab1:
                        st.markdown("### 🌱 Nature-based Solutions (NBS) Report")
                        for idx in ['NDVI', 'GDNVI', 'SI', 'NDWI', 'SAVI', 'BSI', 'MSI']:
                            val = stats.get(idx, 0)
                            name, desc, msg, color = get_status_data(idx, val)
                            st.markdown(f'<div class="analysis-card"><h4>{name}</h4><p style="color:gray; font-size:0.9em;">{desc}</p>', unsafe_allow_html=True)
                            c_a, c_b = st.columns([1, 2])
                            with c_a:
                                st.metric("Current Value", f"{val:.3f}")
                                st.markdown(f'<div class="report-box {color}">{msg}</div>', unsafe_allow_html=True)
                            with c_b:
                                line_color = {'NDVI': 'green', 'GDNVI': 'magenta', 'SI': 'red', 'NDWI': 'blue', 'SAVI': 'brown', 'BSI': 'orange', 'MSI': '#795548'}[idx]
                                chart_df = df[df[idx] != 0]
                                if idx in ['NDVI', 'GDNVI', 'SAVI']: chart_df = chart_df[chart_df[idx] > 0.05]
                                chart = alt.Chart(chart_df).mark_line(point=True, color=line_color).encode(
                                    x=alt.X('Date', title='Date'),
                                    y=alt.Y(idx, title=idx, scale=alt.Scale(zero=False, padding=1)),
                                    tooltip=['Date', alt.Tooltip(idx, format='.3f')]
                                ).properties(height=180)
                                st.altair_chart(chart, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    # TAB 2: YAPAY ZEKA ANALİZİ
                    with tab2:
                        col_ai1, col_ai2 = st.columns(2)
                        with col_ai1:
                            st.markdown("#### ⛰️ Erosion Risk Analysis")
                            if slope_val > 10 and stats.get('BSI', 0) > 0.15:
                                st.error("🚨 CRITICAL RISK! Steep slope & bare soil.\n\n💡 **NBS:** Urgent! Implement **Contour Farming** and plant Vetiver.", icon="🚨")
                            elif slope_val > 5:
                                st.warning("⚠️ Moderate Risk.\n\n💡 **NBS:** Avoid tillage. Use **Strip Cropping**.", icon="⚠️")
                            else:
                                st.success("✅ Stable Terrain (Low Erosion Risk).", icon="✅")
                        with col_ai2:
                            st.markdown("#### ☀️ Micro-Climate & Aspect")
                            if "South" in compass:
                                st.warning(f"🔥 **{compass} Facing:** Hot & Dry.\n\n💡 **NBS:** Plant **Windbreaks** to reduce evaporation.", icon="🔥")
                            elif "North" in compass:
                                st.info(f"❄️ **{compass} Facing:** Cool/Shady.\n\n💡 **NBS:** Good for moisture retention.", icon="❄️")
                            else:
                                st.success(f"✅ **{compass} Facing:** Balanced sunlight exposure.", icon="✅")

                        # GİZLİ AÇLIK
                        st.markdown("---")
                        st.markdown("#### 🧪 Nutrient Efficiency (Hidden Hunger)")
                        ndvi_val = stats.get('NDVI', 0)
                        gdnvi_val = stats.get('GDNVI', 0)
                        if ndvi_val > 0.5:
                            if gdnvi_val < 0.35:
                                st.error("📉 **HIDDEN HUNGER DETECTED!**\n\nHigh Biomass (NDVI) but Low Nitrogen (GDNVI).\n💡 **Diagnosis:** Plant is growing but lacks protein. Apply foliar organic fertilizer.", icon="📉")
                            elif gdnvi_val < 0.45:
                                st.warning("⚠️ **Mild Deficiency.**\n\nNitrogen is lagging behind growth.\n💡 **Remedy:** Prepare compost tea.", icon="⚠️")
                            else:
                                st.success("✅ **Balanced Nutrition.**\n\nBiomass and Nitrogen levels are synced.", icon="✅")
                        elif ndvi_val < 0.2:
                            st.info("🍂 **Low Biomass.**\n\nPlants are too small to determine hidden hunger.", icon="🍂")
                        else:
                            st.success("⚖️ **Status OK.**\n\nStandard growth observed.", icon="⚖️")

                    # TAB 3: TOPOGRAFYA
                    with tab3:
                        st.markdown("### ⛰️ Field Topography")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Elevation", f"{elevation_val:.0f} m")
                        c2.metric("Slope", f"{slope_val:.2f}°")
                        c3.metric("Aspect", f"{compass} ({aspect_val:.0f}°)")
                        st.info(f"ℹ️ **Note:** Field faces **{compass}**. Slope is {slope_val:.1f} degrees.")

                    # TAB 4: İKLİM ANALİZİ
                    with tab4:
                        st.markdown("### 🌦️ Climate Analysis (Monthly Averages)")

                        def get_rain_status(total_mm):
                            if total_mm < 300: return "🛑 Arid / Water Scarcity.", "danger", "💡 <b>NBS REMEDY:</b> Critical! Implement <b>Rainwater Harvesting</b> ponds."
                            elif total_mm < 500: return "⚠️ Semi-Arid.", "warning", "💡 <b>NBS REMEDY:</b> Use <b>Agroforestry</b> to create micro-climates."
                            elif total_mm < 800: return "✅ Optimal Rain.", "success", "💡 <b>NBS REMEDY:</b> Focus on <b>Soil Sponge</b> building (compost/mulch)."
                            else: return "💧 High Rainfall.", "success", "💡 <b>NBS REMEDY:</b> Manage runoff with <b>Buffer Strips</b>."

                        def get_temp_status(avg_c):
                            if avg_c < 12: return "❄️ Cold Soil.", "blue-box", "💡 <b>NBS REMEDY:</b> Use Passive Solar heating (Greenhouses)."
                            elif avg_c < 25: return "✅ Optimal Temp.", "success", "💡 <b>NBS REMEDY:</b> Maintain biodiversity for pollinators."
                            else: return "🔥 Heat Stress.", "danger", "💡 <b>NBS REMEDY:</b> Use <b>Shade Trees</b> or Silvopasture."

                        try:
                            climate_roi = roi.centroid(1).buffer(5000)
                            raw_era = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(climate_roi).filterDate(str(start_date), str(end_date)).select(['total_precipitation_hourly', 'soil_temperature_level_1'])
                            if raw_era.size().getInfo() > 0:
                                def extract_clim(img):
                                    stats = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=climate_roi, scale=11132, bestEffort=True)
                                    t = stats.get('soil_temperature_level_1')
                                    r = stats.get('total_precipitation_hourly')
                                    t_safe = ee.Algorithms.If(t, ee.Number(t).subtract(273.15), -999)
                                    r_safe = ee.Algorithms.If(r, ee.Number(r).multiply(1000), -999)
                                    return ee.Feature(None, {'Date': ee.Date(img.get('system:time_start')).format('YYYY-MM-dd HH:mm'), 'Temp': t_safe, 'Rain': r_safe})

                                clim_list = raw_era.limit(5000).map(extract_clim).reduceColumns(ee.Reducer.toList(3), ['Date', 'Temp', 'Rain']).values().get(0).getInfo()
                                if clim_list:
                                    cdf = pd.DataFrame(clim_list, columns=['Date', 'Temp', 'Rain'])
                                    cdf['Date'] = pd.to_datetime(cdf['Date'])
                                    cdf = cdf[cdf['Temp'] != -999]
                                    cdf = cdf[cdf['Rain'] >= 0]
                                    if not cdf.empty:
                                        cdf = cdf.set_index('Date')
                                        monthly_df = cdf.resample('M').agg({'Temp': 'mean', 'Rain': 'sum'}).reset_index()
                                        avg_temp_season = monthly_df['Temp'].mean()
                                        total_rain_season = monthly_df['Rain'].sum()

                                        col_temp, col_rain = st.columns(2)
                                        with col_temp:
                                            st.markdown("#### 🌡️ Monthly Temperature")
                                            st.metric("Avg Soil Temp", f"{avg_temp_season:.1f} °C")
                                            t_msg, t_col, t_rec = get_temp_status(avg_temp_season)
                                            box_style = "background-color: #e3f2fd; border: 1px solid #2196f3;" if t_col == "blue-box" else ""
                                            if t_col == "success": box_style = "background-color: #e8f5e9; border: 1px solid #2e7d32;"
                                            if t_col == "warning": box_style = "background-color: #fff3e0; border: 1px solid #ef6c00;"
                                            if t_col == "danger": box_style = "background-color: #ffebee; border: 1px solid #c62828;"
                                            st.markdown(f'<div style="{box_style} padding: 15px; border-radius: 8px; margin-bottom: 10px;"><b>{t_msg}</b><br>{t_rec}</div>', unsafe_allow_html=True)
                                            chart_t = alt.Chart(monthly_df).mark_line(color='#d32f2f', point=True).encode(x=alt.X('Date', title='Month', axis=alt.Axis(format='%b %Y')), y=alt.Y('Temp', title='Avg Temp (°C)'), tooltip=[alt.Tooltip('Date', format='%B %Y'), 'Temp']).properties(height=250)
                                            st.altair_chart(chart_t, use_container_width=True)
                                        with col_rain:
                                            st.markdown("#### 🌧️ Monthly Precipitation")
                                            st.metric("Total Rainfall", f"{total_rain_season:.1f} mm")
                                            r_msg, r_col, r_rec = get_rain_status(total_rain_season)
                                            r_style = ""
                                            if r_col == "success": r_style = "background-color: #e8f5e9; border: 1px solid #2e7d32;"
                                            if r_col == "warning": r_style = "background-color: #fff3e0; border: 1px solid #ef6c00;"
                                            if r_col == "danger": r_style = "background-color: #ffebee; border: 1px solid #c62828;"
                                            st.markdown(f'<div style="{r_style} padding: 15px; border-radius: 8px; margin-bottom: 10px;"><b>{r_msg}</b><br>{r_rec}</div>', unsafe_allow_html=True)
                                            chart_r = alt.Chart(monthly_df).mark_bar(color='#1976d2', opacity=0.7).encode(x=alt.X('Date', title='Month', axis=alt.Axis(format='%b %Y')), y=alt.Y('Rain', title='Total Rain (mm)'), tooltip=[alt.Tooltip('Date', format='%B %Y'), 'Rain']).properties(height=250)
                                            st.altair_chart(chart_r, use_container_width=True)
                                    else: st.warning("⚠️ Valid data not found after filtering.")
                                else: st.warning("⚠️ Data extracted but resulted in empty list.")
                            else: st.warning("⚠️ No ERA5 images found.")
                        except Exception as e: st.error(f"Climate Logic Error: {e}")
                else:
                    st.error("❌ No clear satellite imagery found. Try increasing cloud tolerance or changing dates.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")
else:
    st.info("👈 Please draw a polygon on the map.")