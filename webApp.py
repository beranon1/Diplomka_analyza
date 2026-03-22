# --- SPUŠTĚNÍ APLIKACE ---
# přepnutí do prostředí =>  .venv\Scripts\activate
# spuštění aplikace =>  streamlit run webApp.py


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests

# KONFIGURACE
st.set_page_config(page_title="Analýza: COVID-19 vs Chřipka", layout="wide")

# NAČTENÍ DAT 
@st.cache_data
def load_data():
    covid_cr = pd.read_csv("DataApp/covid_cr_final.csv")
    covid_hosp_kraje = pd.read_csv("DataApp/covid_hosp_umrti_kraje.csv")
    covid_ock_kraje = pd.read_csv("DataApp/covid_ockov_kraje.csv")
    flu_kraje = pd.read_csv("DataApp/flu_hosp_umrti_kraje.csv")
    flu_umr = pd.read_csv("DataApp/flu_umrti_detail.csv")
    flu_ock_kraje = pd.read_csv("DataApp/flu_ockov_vse.csv")
    return covid_cr, covid_hosp_kraje, covid_ock_kraje, flu_kraje, flu_umr, flu_ock_kraje

try:
    covid_cr, covid_hosp_kraje, covid_ock_kraje, flu_kraje, flu_umr, flu_ock_kraje = load_data()
except Exception as e:
    st.error(f"Chyba při načítání dat: {e}")
    st.stop()

# MENU
st.sidebar.title("Menu")
menu = st.sidebar.radio("**Přejí na:**", [
    "Úvodní stránka", 
    "Covid-19", 
    "Chřipka", 
    "Interaktivní srovnávač",
    "Covid-19 (LIVE)"
])

# 1. ÚVODNÍ STRÁNKA 
if menu == "Úvodní stránka":
    st.title("Srovnání dopadů COVID-19 a Chřipky v ČR")
    st.markdown("---")

    # HLAVNÍ DATA (Metriky)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Celková úmrtí")
        c_deaths = covid_cr['Počet zemřelých'].sum()
        f_deaths = len(flu_umr)
        st.metric("COVID-19 (od 2020)", f"{c_deaths:,.0f} osob")
        st.metric("Chřipka (od 1994)", f"{f_deaths:,.0f} osob")

    with col2:
        st.subheader("Celkové hospitalizace")
        c_hosp = covid_cr['Počet hospitalizovaných'].sum()
        f_hosp = flu_kraje['pocet_hosp'].sum()
        st.metric("COVID-19", f"{c_hosp:,.0f} hospitalizací")
        st.metric("Chřipka", f"{f_hosp:,.0f} hospitalizací")

    st.markdown("---")

    categories = ['Celkový počet úmrtí', 'Celkový počet hospitalizací']

    fig_final_compare = go.Figure()

    fig_final_compare.add_trace(go.Bar(
        x=categories,
        y=[c_deaths, c_hosp],
        name='COVID-19 (2020–2025)',
        marker_color='firebrick',
        text=[f"{c_deaths:,.0f}", f"{c_hosp:,.0f}"],
        textposition='outside'
    ))

    fig_final_compare.add_trace(go.Bar(
        x=categories,
        y=[f_deaths, f_hosp],
        name='Chřipka (1994–2024)',
        marker_color='royalblue',
        text=[f"{f_deaths:,.0f}", f"{f_hosp:,.0f}"],
        textposition='outside'
    ))

    fig_final_compare.update_layout(
        title='Finální srovnání COVID-19 vs. Sezónní chřipka v ČR',
        yaxis_title='Absolutní počet osob',
        barmode='group',
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=100),
        height=500
    )

    st.plotly_chart(fig_final_compare, use_container_width=True)

    death_ratio = c_deaths / f_deaths if f_deaths > 0 else 0
    hosp_ratio = c_hosp / f_hosp if f_hosp > 0 else 0

    st.info(f"""
    **💡 Rychlá fakta z analýzy:**
    * COVID-19 způsobil přibližně **{death_ratio:.1f}x více úmrtí** než chřipka (srovnání 6 let vs 31 let).
    * COVID-19 vyžadoval **{hosp_ratio:.1f}x více hospitalizací** než chřipka (srovnání 6 let vs 31 let).
    """)

# 2. COVID-19 
elif menu == "Covid-19":
    st.title("Detailní analýza onemocnění COVID-19")
    st.markdown("---")

    st.subheader("Vývoj hospitalizací a úmrtnosti v čase")
    
    covid_cr['datum_dt'] = pd.to_datetime(covid_cr['Datum'])
    
    fig_trends = go.Figure()
    
    fig_trends.add_trace(go.Scatter(
        x=covid_cr['datum_dt'], y=covid_cr['Počet hospitalizovaných'],
        name='Hospitalizace', fill='tozeroy', line_color="#FFBF00"
    ))
    
    fig_trends.add_trace(go.Bar(
        x=covid_cr['datum_dt'], y=covid_cr['Počet zemřelých'],
        name='Úmrtí', marker_color="#FF0000"
    ))
    
    fig_trends.update_layout(
        title="Vlny pandemie: Hospitalizace vs. Úmrtí",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trends, use_container_width=True)

# --- 2. REGIONÁLNÍ MAPA (OPRAVENÁ VERZE) ---
    # --- 2. REGIONÁLNÍ MAPA (MAPBOX VERZE - ODOLNÁ PROTI CHYBÁM) ---
    st.markdown("---")
    st.subheader("Mapa krajů")
    
    try:
        with open("DataApp/kraje.json", encoding="utf-8") as f:
            geojson_kraje = json.load(f)
        
        # Oprava ID (Zkrácení z CZ0100000000 na CZ010 pro tvá data)
        for feature in geojson_kraje['features']:
            feature['id'] = feature['id'][:5]

        c1, c2 = st.columns([1, 3])
        with c1:
            map_metrika = st.radio(
                "**Co chcete zobrazit:**",
                ["Počet hospitalizovaných", "Počet zemřelých", "Počet nakažených", "Počet dávek očkování"],
                key="map_radio"
            )
        
        # Příprava dat (výběr tabulky a barev)
        if map_metrika == "Počet dávek očkování":
            df_map = covid_ock_kraje.groupby(['kraj_nuts_kod', 'kraj_nazev'])['celkem_davek'].sum().reset_index()
            lokace, hodnota, popisek, barva = "kraj_nuts_kod", "celkem_davek", "kraj_nazev", "Reds"
        else:
            map_mapping = {
                "Počet hospitalizovaných": "Počet hospitalizovaných celkem v daném dni",
                "Počet zemřelých": "Počet zemřelých",
                "Počet nakažených": "Celkový počet nakažených"
            }
            tech_nazev = map_mapping[map_metrika]
            df_map = covid_hosp_kraje.groupby(['Kraj_ID', 'Kraj_Název'])[tech_nazev].sum().reset_index()
            lokace, hodnota, popisek, barva = "Kraj_ID", tech_nazev, "Kraj_Název", "Reds"

        with c2:
            fig_map = px.choropleth_mapbox(
                df_map,
                geojson=geojson_kraje,
                locations=lokace,
                featureidkey="id",
                color=hodnota,
                color_continuous_scale=barva,
                mapbox_style="white-bg",
                zoom=6.3, 
                center={"lat": 49.8175, "lon": 15.4730}, 
                hover_name=popisek,
                labels={hodnota: 'Celkem'}
            )

            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
            st.plotly_chart(fig_map, use_container_width=True)
            
    except Exception as e:
        st.error(f"Chyba při vykreslování Mapboxu: {e}")

    st.markdown("---")
    st.subheader("Věková struktura úmrtí")

    age_cols_covid = {
        '0–19': ['Zemřelí ve věku 0-4 let', 'Zemřelí ve věku 5-9 let', 'Zemřelí ve věku 10-14 let', 'Zemřelí ve věku 15-19 let'],
        '20–44': ['Zemřelí ve věku 20-24 let', 'Zemřelí ve věku 25-29 let', 'Zemřelí ve věku 30-34 let', 'Zemřelí ve věku 35-39 let', 'Zemřelí ve věku 40-44 let'],
        '45–64': ['Zemřelí ve věku 45-49 let', 'Zemřelí ve věku 50-54 let', 'Zemřelí ve věku 55-59 let', 'Zemřelí ve věku 60-64 let'],
        '65–74': ['Zemřelí ve věku 65-69 let', 'Zemřelí ve věku 70-74 let'],
        '75–84': ['Zemřelí ve věku 75-79 let', 'Zemřelí ve věku 80-84 let'],
        '85+': ['Zemřelí ve věku 85+ let']
    }

    covid_age_data = []
    for label, cols in age_cols_covid.items():
        total = covid_cr[cols].sum().sum() # Sečteme sloupce a pak celou řadu
        covid_age_data.append({'Věková kategorie': label, 'Počet úmrtí': total})

    df_covid_age = pd.DataFrame(covid_age_data)

    fig_age_covid = go.Figure()

    fig_age_covid.add_trace(go.Bar(
        x=df_covid_age['Věková kategorie'], 
        y=df_covid_age['Počet úmrtí'],
        name='Počet úmrtí (COVID-19)',
        marker_color="#FF0000",
        text=df_covid_age['Počet úmrtí'].apply(lambda x: f"{x:,.0f}"),
        textposition='outside'
    ))

    fig_age_covid.update_layout(
        title="Rozdělení úmrtí na COVID-19 podle věkových kategorií",
        xaxis_title="Věková skupina",
        yaxis_title="Absolutní počet úmrtí",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(t=80)
    )

    st.plotly_chart(fig_age_covid, use_container_width=True)

    st.markdown("---")
    st.subheader("Strategie testování")
    
    fig_tests = go.Figure()
    fig_tests.add_trace(go.Bar(
        x=covid_cr['datum_dt'], y=covid_cr['Počet PCR testů'],
        name='Počet PCR testů', marker_color="#30A900"
    ))
    fig_tests.add_trace(go.Bar(
        x=covid_cr['datum_dt'], y=covid_cr['Počet antigenních testů'],
        name='Počet antigenních testů', marker_color="#8400ff"
    ))
    fig_tests.update_layout(
        title="Srovnání PCR a Antigenních testů",
        barmode='stack',
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_tests, use_container_width=True)

    st.subheader("Nárůst nakažených")
    
    fig_cases = go.Figure()
    fig_cases.add_trace(go.Scatter(
        x=covid_cr['datum_dt'], y=covid_cr['Celkový počet nakažených'],
        name='Nakažení', line_color="#16aaff"
    ))
    fig_cases.update_layout(
        title="Denní přírůstky nakažených",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cases, use_container_width=True)

    st.markdown("---")
    st.subheader("Dynamika a pokrok vakcinace")

    df_vax_detail = covid_ock_kraje.copy()
    df_vax_detail['datum_dt'] = pd.to_datetime(df_vax_detail['datum'], dayfirst=True)

    df_vax_daily = df_vax_detail.groupby('datum_dt').agg({
        'prvnich_davek': 'sum',
        'druhych_davek': 'sum'
    }).reset_index()

    populace_cr = 10500000
    df_vax_daily['proockovanost_perc'] = (df_vax_daily['druhych_davek'].cumsum() / populace_cr) * 100

    fig_vax_cool = go.Figure()

    fig_vax_cool.add_trace(go.Bar(
        x=df_vax_daily['datum_dt'],
        y=df_vax_daily['prvnich_davek'] + df_vax_daily['druhych_davek'],
        name='Počet vakcín',
        marker_color="#0084ff"
    ))

    fig_vax_cool.add_trace(go.Scatter(
        x=df_vax_daily['datum_dt'],
        y=df_vax_daily['proockovanost_perc'],
        name='Celková proočkovanost',
        line=dict(color="#00aa09", width=3, dash='dot'),
        yaxis='y2'
    ))

    fig_vax_cool.update_layout(
        title='Rychlost vakcinace a celkový pokrok v čase',
        xaxis_title='Datum',
        yaxis=dict(title='Počet vyočkovaných dávek'),
        yaxis2=dict(
            title='Celková proočkovanost',
            overlaying='y',
            side='right',
            dtick=10,
            range=[0,100]
        ),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_vax_cool, use_container_width=True)

# 3. CHŘIPKA 
elif menu == "Chřipka":
    st.title("Detailní analýza Sezónní chřipky")
    st.markdown("---")

    st.subheader("Vývoj hospitalizací a úmrtnosti v čase")

    flu_hosp_year = flu_kraje.groupby('rok').agg({'pocet_hosp': 'sum', 'umrti': 'sum'}).reset_index()
    
    flu_umr['rok'] = pd.to_datetime(flu_umr['datum_umrti'], dayfirst=True).dt.year
    flu_deaths_year = flu_umr.groupby('rok').size().reset_index(name='pocet_umrti_detail')

    fig_flu_trends = go.Figure()
    
    fig_flu_trends.add_trace(go.Scatter(
        x=flu_hosp_year['rok'], y=flu_hosp_year['pocet_hosp'],
        name='Hospitalizace', fill='tozeroy', line_color="#FFBF00"
    ))
    
    fig_flu_trends.add_trace(go.Bar(
        x=flu_deaths_year['rok'], y=flu_deaths_year['pocet_umrti_detail'],
        name='Úmrtí', marker_color="#FF0000"
    ))

    fig_flu_trends.update_layout(
        title="Historické trendy chřipky v ČR",
        hovermode="x unified",
        template="plotly_white",
        xaxis=dict(type='category'), # Roky jako kategorie, aby nebyly desetinné čárky
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_flu_trends, use_container_width=True)

    st.markdown("---")
    st.subheader("Věková struktura úmrtí")

    # Definice mappingu pro věkovou kategorii
    mapping_flu_jednotny = {
        '66000004': '0–19', '66005009': '0–19', '66010014': '0–19', '66015019': '0–19',
        '66020024': '20–44', '66025029': '20–44', '66030034': '20–44', '66035039': '20–44', '66040044': '20–44',
        '66045049': '45–64', '66050054': '45–64', '66055059': '45–64', '66060064': '45–64',
        '66065069': '65–74', '66070074': '65–74',
        '66075079': '75–84', '66080084': '75–84',
        '66085089': '85+', '66090094': '85+', '66095999': '85+' 
    }

    df_age_mapped = flu_umr.copy()

    df_age_mapped['Věk'] = df_age_mapped['vek_kat'].astype(str).map(mapping_flu_jednotny)

    age_dist = df_age_mapped['Věk'].value_counts().reset_index()
    age_dist.columns = ['Věková kategorie', 'Počet úmrtí']

    order = ['0–19', '20–44', '45–64', '65–74', '75–84', '85+']
    age_dist['Věková kategorie'] = pd.Categorical(age_dist['Věková kategorie'], categories=order, ordered=True)
    age_dist = age_dist.sort_values('Věková kategorie')

    fig_age = go.Figure()

    fig_age.add_trace(go.Bar(
        x=age_dist['Věková kategorie'], 
        y=age_dist['Počet úmrtí'],
        name='Počet úmrtí',
        marker_color="#FF0000",
        text=age_dist['Počet úmrtí'],
        textposition='outside'
    ))

    fig_age.update_layout(
        title="Rozdělení úmrtí na chřipku podle věkových kategorií",
        xaxis_title="Věková skupina",
        yaxis_title="Absolutní počet úmrtí",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(t=80)
    )

    st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.subheader("Dynamika a pokrok vakcinace")

    flu_vax_season = flu_ock_kraje.groupby('sezona').agg({
        'pocet_vakcinovanych': 'sum',
        'proockovanost_procenta': 'mean'
    }).reset_index()

    fig_flu_vax = go.Figure()

    fig_flu_vax.add_trace(go.Bar(
        x=flu_vax_season['sezona'], 
        y=flu_vax_season['pocet_vakcinovanych'],
        name='Počet vakcín',
        marker_color="#0084ff"
    ))

    fig_flu_vax.add_trace(go.Scatter(
        x=flu_vax_season['sezona'], 
        y=flu_vax_season['proockovanost_procenta'],
        name='Celková pročkovanost', 
        line=dict(color="#00aa09", width=3, dash='dot'),
        yaxis='y2'
    ))

    fig_flu_vax.update_layout(
        title="Rychlost vakcinace a celkový pokrok v čase",
        xaxis_title='Datum',
        yaxis=dict(title="Počet vyočkovaných dávek"),
        yaxis2=dict(
            title="Celková proočkovanost", 
            overlaying='y', 
            side='right', 
            range=[0, 10]),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_flu_vax, use_container_width=True)

# 4. INTERAKTIVNÍ SROVNÁVAČ 
elif menu == "Interaktivní srovnávač":
    st.title("Generátor vlastních srovnání")

    covid_cr['datum_dt'] = pd.to_datetime(covid_cr['Datum'])
    covid_cr['rok'] = covid_cr['datum_dt'].dt.year
    
    df_vax_full = covid_ock_kraje.copy()
    df_vax_full['datum_dt'] = pd.to_datetime(df_vax_full['datum'], dayfirst=True)
    df_vax_full['rok'] = df_vax_full['datum_dt'].dt.year   
    
    df_vax_full['chranene_osoby'] = df_vax_full.apply(
        lambda row: row['prvnich_davek'] if 'Janssen' in str(row['vakcina']) else row['druhych_davek'], axis=1
    )

    df_vax_full = df_vax_full.sort_values('datum_dt')
    df_vax_full['kumulativni_celkem'] = df_vax_full['chranene_osoby'].cumsum()
    
    covid_vax_yearly = df_vax_full.groupby('rok')['kumulativni_celkem'].max().reset_index()
    covid_vax_yearly.columns = ['rok', 'chranene_osoby']

    flu_mapping = {
        'Počet hospitalizovaných': 'pocet_hosp',
        'Počet zemřelých': 'umrti',
        'Počet chráněných osob': 'pocet_vakcinovanych'
    }

    covid_metrics = ['Počet zemřelých', 'Počet hospitalizovaných', 'Počet PCR testů', 'Počet antigenních testů', 'Celkový počet nakažených', 'Počet chráněných osob']
    flu_metrics = list(flu_mapping.keys())

    covid_years = set(covid_cr['rok'].dropna().unique().astype(int))
    flu_years = set(flu_kraje['rok'].dropna().unique().astype(int))
    all_years = sorted([y for y in (covid_years | flu_years) if y > 1993])
    
    vybrane_roky = st.multiselect("Vyberte roky pro srovnání:", all_years, key="ms_roky")
    
    c1, c2 = st.columns(2)
    with c1:
        param_c = st.multiselect("**Metriky COVID-19:**", covid_metrics, key="ms_covid")
    with c2:
        param_f = st.multiselect("**Metriky Chřipka:**", flu_metrics, key="ms_flu")

    typ_grafu = st.radio("**Typ grafu:**", ["Sloupcový (Bar)", "Liniový (Line)", "Výsekový (Pie)"], key="typ_grafu", horizontal=True)

    d1 = pd.DataFrame()
    if param_c:
        base_c_params = [p for p in param_c if p != 'Počet chráněných osob']
        if base_c_params:
            d1 = covid_cr[covid_cr['rok'].isin(vybrane_roky)].groupby('rok')[base_c_params].sum().reset_index()
        
        if 'Počet chráněných osob' in param_c:
            vax_sel = covid_vax_yearly[covid_vax_yearly['rok'].isin(vybrane_roky)]
            if d1.empty:
                d1 = vax_sel
            else:
                d1 = d1.merge(vax_sel, on='rok', how='outer')
        
        if not d1.empty:
            d1 = d1.melt('rok', var_name='Metrika', value_name='Hodnota')
            d1['Metrika'] = 'COVID: ' + d1['Metrika'].replace('chranene_osoby', 'Počet chráněných osob')
    
    d2 = pd.DataFrame()
    if param_f:
        param_f_tech = [flu_mapping[p] for p in param_f]
        
        base_f_params = [p for p in param_f_tech if p != 'pocet_vakcinovanych']

        if base_f_params:
            d2 = flu_kraje[flu_kraje['rok'].isin(vybrane_roky)].groupby('rok')[base_f_params].sum().reset_index()
            
        if 'pocet_vakcinovanych' in param_f_tech:
            df_f_vax_work = flu_ock_kraje.copy()
            df_f_vax_work['rok'] = df_f_vax_work['sezona'].str.split('-').str[1].astype(int)
            
            f_vax_yearly = df_f_vax_work[df_f_vax_work['rok'].isin(vybrane_roky)].groupby('rok')['pocet_vakcinovanych'].sum().reset_index()
            
            if d2.empty:
                d2 = f_vax_yearly
            else:
                d2 = d2.merge(f_vax_yearly, on='rok', how='outer')

        if not d2.empty:
            d2 = d2.melt('rok', var_name='Metrika', value_name='Hodnota')
            
            reverse_mapping = {v: k for k, v in flu_mapping.items()}
            d2['Metrika'] = 'Chřipka: ' + d2['Metrika'].map(reverse_mapping)  

    df_plot = pd.concat([d1, d2]).dropna()
    
    if not df_plot.empty:

        vsechny_metriky = df_plot['Metrika'].unique()
        index_kombinace = pd.MultiIndex.from_product(
            [vybrane_roky, vsechny_metriky], 
            names=['rok', 'Metrika']
        )
        
        df_plot = df_plot.set_index(['rok', 'Metrika']).reindex(index_kombinace, fill_value=0).reset_index()

        df_plot['rok'] = df_plot['rok'].astype(int)
        fig_custom = go.Figure()

        if typ_grafu == "Sloupcový (Bar)":
            for m in df_plot['Metrika'].unique():
                sub = df_plot[df_plot['Metrika'] == m]
                fig_custom.add_trace(go.Bar(x=sub['rok'], y=sub['Hodnota'], name=m, text=sub['Hodnota'].apply(lambda x: f"{x:,.0f}"), textposition='outside'))
            fig_custom.update_layout(barmode='group')

        elif typ_grafu == "Liniový (Line)":
            for m in df_plot['Metrika'].unique():
                sub = df_plot[df_plot['Metrika'] == m]
                fig_custom.add_trace(go.Scatter(x=sub['rok'], y=sub['Hodnota'], name=m, mode='lines+markers+text', text=sub['Hodnota'].apply(lambda x: f"{x:,.0f}"), textposition='top center'))

        elif typ_grafu == "Výsekový (Pie)":
            pie_data = df_plot.groupby('Metrika')['Hodnota'].sum().reset_index()
            fig_custom = px.pie(pie_data, values='Hodnota', names='Metrika', hole=0.3, title="Podíl vybraných metrik za zvolené období")

        fig_custom.update_layout(template='plotly_white', height=600, xaxis={'type': 'category'})
        st.plotly_chart(fig_custom, use_container_width=True)
        
        st.title("Detailní data")
        pivot_df = df_plot.pivot(index='rok', columns='Metrika', values='Hodnota').fillna(0)
        pivot_df.index = pivot_df.index.astype(str)
        st.dataframe(pivot_df.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("Vyberte prosím parametry.")

elif menu == "Covid-19 (LIVE)":
    st.title("Aktuální situace COVID-19 v ČR")
    
    MY_API_TOKEN = "7c12f49908c4e976ae3a9e3336d2ad51" 

    @st.cache_data(ttl=3600)
    def fetch_api_platform_data(token):
        headers = {"Accept": "application/ld+json"}
        base_path = "https://onemocneni-aktualne.mzcr.cz/api/v3"
        
        import datetime
        dnes = datetime.date.today()
        datum_od = (dnes - datetime.timedelta(days=40)).strftime('%Y-%m-%d')

        params_hist = {
            "apiToken": token,
            "items_per_page": 100, 
            "datum[after]": datum_od
        }

        try:
            # 1. ZÁKLADNÍ PŘEHLED
            r_base = requests.get(f"{base_path}/zakladni-prehled", params={"apiToken": token}, headers=headers)
            current = r_base.json()['hydra:member'][0]
                            
            # 2. NAKAŽENÍ A REINFEKCE (pro graf nakažených)
            r_cases = requests.get(f"{base_path}/nakazeni-reinfekce", params=params_hist, headers=headers)
            df_cases = pd.DataFrame(r_cases.json().get('hydra:member', []))
            
            # 3. HOSPITALIZACE A ÚMRTÍ (pro graf hospitalizací a úmrtí)
            r_hosp = requests.get(f"{base_path}/hospitalizace", params=params_hist, headers=headers)
            df_hosp = pd.DataFrame(r_hosp.json().get('hydra:member', []))
            
            # 4. TESTY A ÚMRTÍ (komplexní přehled)
            r_tests = requests.get(f"{base_path}/nakazeni-vyleceni-umrti-testy", params=params_hist, headers=headers)
            df_tests = pd.DataFrame(r_tests.json().get('hydra:member', []))
            
            # Formátování všech DataFrame
            for df in [df_cases, df_hosp, df_tests]:
                if not df.empty:
                    df['datum'] = pd.to_datetime(df['datum'])
                    df.sort_values('datum', ascending=True, inplace=True)
                    df.reset_index(drop=True, inplace=True)

            return current, df_cases, df_hosp, df_tests

        except Exception as e:
            st.error(f"Chyba při volání API: {e}")
            return None, None, None, None

    # --- Volání dat ---
    current, df_cases, df_hosp, df_tests = fetch_api_platform_data(MY_API_TOKEN)

    if current is not None:
        # --- SEKCE 1: KARTY (ROZŠÍŘENO) ---
        st.header("Aktuální stav pandemie v ČR")
            
        def fmt(val):
                try:
                    return f"{int(val):,}".replace(",", " ")
                except:
                    return "0"

            # PRVNÍ ŘADA: Hlavní epidemiologická data
        row1_1, row1_2, row1_3 = st.columns(3)
        with row1_1:
            st.metric("Celkem potvrzené případy", fmt(current.get('potvrzene_pripady_celkem')), 
                    delta=f"+{fmt(current.get('potvrzene_pripady_vcerejsi_den'))} včera")
        with row1_2:
            st.metric("Aktivní případy", fmt(current.get('aktivni_pripady')))
        with row1_3:
            st.metric("Celkem úmrtí", fmt(current.get('umrti')))

        # DRUHÁ ŘADA: Nemocnice a ohrožené skupiny
        row2_1, row2_2, row2_3 = st.columns(3)
        with row2_1:
            st.metric("Aktuálně hospitalizovaní", fmt(current.get('aktualne_hospitalizovani')))
        with row2_2:
            st.metric("Případy 65+ celkem", fmt(current.get('potvrzene_pripady_65_celkem')),
                    delta=f"+{fmt(current.get('potvrzene_pripady_65_vcerejsi_den'))} včera")
        with row2_3:
            st.metric("Celkem reinfekce", fmt(current.get('reinfekce_celkem')),
                    delta=f"+{fmt(current.get('reinfekce_vcerejsi_den'))} včera")

        # TŘETÍ ŘADA: Testy a očkování
        row3_1, row3_2, row3_3 = st.columns(3)
        with row3_1:
            st.metric("PCR & AG testy celkem", fmt(current.get('provedene_testy_celkem')),
                    delta=f"+{fmt(current.get('provedene_testy_vcerejsi_den'))} včera")
        with row3_2:
            # Celkový počet plně očkovaných osob
            st.metric("Očkované osoby celkem", fmt(current.get('ockovane_osoby_celkem')),
                    delta=f"+{fmt(current.get('ockovane_osoby_vcerejsi_den'))} včera")
        with row3_3:
            # Počet vykázaných dávek (může být víc než osob)
            st.metric("Vykázaná očkování (dávky)", fmt(current.get('vykazana_ockovani_celkem')))


        st.markdown("---")
        st.header("Vývoj za posledních 30 dní")
        

        # --- SEKCE 2: PRVNÍ ŘADA GRAFŮ ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Hospitalizace")
            st.line_chart(df_hosp.set_index('datum')['pocet_hosp'], color="#FF4B4B")
        with col2:
            st.subheader("Noví nakažení")
            st.bar_chart(df_cases.set_index('datum')['nove_pripady'], color="#FFAA00")

        # --- SEKCE 3: DRUHÁ ŘADA GRAFŮ (NOVÉ) ---
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Denní úmrtí")
            # Používáme sloupec 'umrti' z endpointu hospitalizace (denní počet)
            st.bar_chart(df_hosp.set_index('datum')['umrti'], color="#333333")
        with col4:
            st.subheader("Provedené testy")
            # Používáme 'prirustkovy_pocet_provedenych_testu' z nového endpointu
            st.area_chart(df_tests.set_index('datum')['prirustkovy_pocet_provedenych_testu'], color="#29B6F6")

        # Info o aktuálnosti
        posledni_datum = df_cases['datum'].max().strftime('%d. %m. %Y')
        st.info(f"Všechna data jsou aktuální k: {posledni_datum}")