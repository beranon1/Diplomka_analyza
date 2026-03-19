# --- SPUŠTĚNÍ APLIKACE ---
# přepnutí do prostředí =>  .venv\Scripts\activate
# spuštění aplikace =>  streamlit run webApp.py


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
menu = st.sidebar.radio("Přejí na:", [
    "Úvodní stránka", 
    "Covid-19", 
    "Chřipka", 
    "Interaktivní srovnávač"
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
        c_hosp = covid_cr['Počet nově hospitalizovaných celkem'].sum()
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
        x=covid_cr['datum_dt'], y=covid_cr['Počet nově hospitalizovaných celkem'],
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
        name='Počet PCR testů', marker_color="#48FF00"
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
        name='Nakažení', fill='tozeroy', line_color="#16aaff"
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

    df_vax_daily['denni_davky_avg'] = (df_vax_daily['prvnich_davek'] + df_vax_daily['druhych_davek']).rolling(window=7).mean()

    fig_vax_cool = go.Figure()

    fig_vax_cool.add_trace(go.Bar(
        x=df_vax_daily['datum_dt'],
        y=df_vax_daily['prvnich_davek'] + df_vax_daily['druhych_davek'],
        name='Denně vyočkované dávky',
        marker_color="#0084ff",
        opacity=0.6
    ))

    fig_vax_cool.add_trace(go.Scatter(
        x=df_vax_daily['datum_dt'],
        y=df_vax_daily['denni_davky_avg'],
        name='7denní průměr (trend)',
        line=dict(color="#8edfff", width=2)
    ))

    fig_vax_cool.add_trace(go.Scatter(
        x=df_vax_daily['datum_dt'],
        y=df_vax_daily['proockovanost_perc'],
        name='Celková proočkovanost (%)',
        line=dict(color="#00ff0d", width=3, dash='dot'),
        yaxis='y2'
    ))

    fig_vax_cool.update_layout(
        title='Rychlost vakcinace a celkový pokrok v čase',
        xaxis_title='Datum',
        yaxis=dict(title='Počet vyočkovaných dávek za den'),
        yaxis2=dict(
            title='Celková proočkovanost (%)',
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
        'proockovanost_procenta': 'mean' # Průměr z krajů
    }).reset_index()

    fig_flu_vax = go.Figure()

    fig_flu_vax.add_trace(go.Bar(
        x=flu_vax_season['sezona'], y=flu_vax_season['pocet_vakcinovanych'],
        name='Počet vakcinovaných', marker_color="#8edfff", opacity=0.6
    ))

    fig_flu_vax.add_trace(go.Scatter(
        x=flu_vax_season['sezona'], y=flu_vax_season['proockovanost_procenta'],
        name='Proočkovanost (%)', line=dict(color="#00ff0d", width=3),
        yaxis='y2'
    ))

    fig_flu_vax.update_layout(
        title="Rychlost vakcinace a celkový pokrok v čase",
        yaxis=dict(title="Počet osob"),
        yaxis2=dict(title="Proočkovanost (%)", overlaying='y', side='right', range=[0, 10]), # Chřipka má nízká %
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
        'Počet úmrtí': 'umrti',
        'Počet chráněných osob': 'pocet_vakcinovanych'
    }

    covid_metrics = ['Počet zemřelých', 'Počet nově hospitalizovaných celkem', 'Počet PCR testů', 'Počet antigenních testů', 'Celkový počet nakažených', 'Počet chráněných osob']
    flu_metrics = list(flu_mapping.keys())

    covid_years = set(covid_cr['rok'].dropna().unique().astype(int))
    flu_years = set(flu_kraje['rok'].dropna().unique().astype(int))
    all_years = sorted([y for y in (covid_years | flu_years) if y > 1993])
    
    vybrane_roky = st.multiselect("Vyberte roky pro srovnání:", all_years, key="ms_roky")
    
    c1, c2 = st.columns(2)
    with c1:
        param_c = st.multiselect("Metriky COVID-19:", covid_metrics, key="ms_covid")
    with c2:
        param_f = st.multiselect("Metriky Chřipka:", flu_metrics, key="ms_flu")

    typ_grafu = st.radio("Typ grafu:", ["Sloupcový (Bar)", "Liniový (Line)", "Výsekový (Pie)"], key="typ_grafu", horizontal=True)

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
        
        st.markdown("### 📋 Detailní data")
        pivot_df = df_plot.pivot(index='rok', columns='Metrika', values='Hodnota').fillna(0)
        pivot_df.index = pivot_df.index.astype(str)
        st.dataframe(pivot_df.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("Vyberte prosím parametry.")