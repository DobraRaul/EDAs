import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="EDA SEN 2025 - Analiză SEN",
    layout="wide"
)

st.title("Analiză SEN Transelectrica 2025")
st.markdown("**Setul 7: Sinteză Cross-Tematică (Imagine de Ansamblu)**")

@st.cache_data
def load_and_preprocess_data(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path)
    df.columns = [col.strip() for col in df.columns]

    rename_map = {
        'Data': 'Data',
        'Consum[MW]': 'Consum',
        'Medie Consum[MW]': 'Medie_Consum',
        'Productie[MW]': 'Productie',
        'Carbune[MW]': 'Carbune',
        'Hidrocarburi[MW]': 'Hidrocarburi',
        'Ape[MW]': 'Ape',
        'Nuclear[MW]': 'Nuclear',
        'Eolian[MW]': 'Eolian',
        'Foto[MW]': 'Foto',
        'Biomasa[MW]': 'Biomasa',
        'Sold[MW]': 'Sold'
    }
    df = df.rename(columns=rename_map)

    df['Data'] = pd.to_datetime(df['Data'], format='%d-%m-%Y %H:%M:%S')
    df = df.sort_values('Data').set_index('Data')

    df_hourly = df.resample('1h').mean()

    df_hourly['Sarcina_Reziduala'] = df_hourly['Consum'] - (df_hourly['Eolian'] + df_hourly['Foto'])

    return df_hourly

try:
    df_hourly = load_and_preprocess_data("data/Grafic_SEN.xlsx")
    st.sidebar.success("Datele orare pentru 2025 au fost încărcate cu succes!")
except Exception as e:
    st.error(f"Eroare la citirea fișierului de date: {e}. Asigură-te că `Grafic_SEN.xlsx` se află în folderul `data/`.")
    st.stop()

st.sidebar.header("Configurare Analiză")
zi_implicita = pd.to_datetime("2025-05-14").date()
min_date = df_hourly.index.min().date()
max_date = df_hourly.index.max().date()

data_selectata = st.sidebar.date_input(
    "Selectează data pentru analiza orară:",
    value=zi_implicita,
    min_value=min_date,
    max_value=max_date
)

str_date = data_selectata.strftime("%Y-%m-%d")
df_day = df_hourly.loc[str_date].copy()

st.subheader(f"1. Poza Orară Completă a Sistemului — Ziua {str_date}")
st.write(
    "Graficul de mai jos prezintă echilibrul complet al SEN: mixul de producție pe surse (stacked area), "
    "curba consumului total, sarcina reziduală și soldul de schimb transfrontalier (pe axa secundară)."
)

if df_day.empty:
    st.warning("Nu există date disponibile pentru ziua selectată.")
else:
    df_day['Ora'] = df_day.index.hour

    fig = go.Figure()

    mix_surse = [
        ('Nuclear', '#8c564b', 'Nuclear'),
        ('Carbune', '#4d4d4d', 'Cărbune'),
        ('Hidrocarburi', '#ff7f0e', 'Hidrocarburi'),
        ('Biomasa', '#8c6d31', 'Biomasă'),
        ('Ape', '#1f77b4', 'Ape (Hidroelectrica)'),
        ('Eolian', '#2ca02c', 'Eolian'),
        ('Foto', '#f5b041', 'Solar (Foto)')
    ]

    for sursa, col, eticheta in mix_surse:
        fig.add_trace(go.Scatter(
            x=df_day['Ora'],
            y=df_day[sursa],
            mode='lines',
            name=eticheta,
            stackgroup='productie_interna',
            line=dict(width=0.5, color=col),
            hovertemplate='%{y:.1f} MW'
        ))

    fig.add_trace(go.Scatter(
        x=df_day['Ora'],
        y=df_day['Consum'],
        mode='lines+markers',
        name='Consum Total',
        line=dict(color='black', width=3),
        hovertemplate='%{y:.1f} MW'
    ))

    fig.add_trace(go.Scatter(
        x=df_day['Ora'],
        y=df_day['Sarcina_Reziduala'],
        mode='lines',
        name='Sarcină Reziduală (Consum - Eolian - Foto)',
        line=dict(color='#6a0dad', width=2, dash='dash'),
        hovertemplate='%{y:.1f} MW'
    ))

    fig.add_trace(go.Scatter(
        x=df_day['Ora'],
        y=df_day['Sold'],
        mode='lines+markers',
        name='Sold (Import + / Export -)',
        yaxis='y2',
        line=dict(color='#d62728', width=2.5, dash='dot'),
        hovertemplate='%{y:.1f} MW'
    ))

    fig.update_layout(
        title=dict(
            text=f"Bilanț Energetic SEN Orar — {str_date}",
            x=0.01,
            xanchor='left'
        ),
        xaxis=dict(
            title="Ora Zilei (00:00 - 23:00)",
            tickmode='linear',
            dtick=1,
            gridcolor='#eaeaea'
        ),
        yaxis=dict(
            title="Producție și Consum (MW)",
            gridcolor='#eaeaea'
        ),
        yaxis2=dict(
            title="Sold Schimb Transfrontalier (MW)",
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified',
        template='plotly_white',
        height=600,
        margin=dict(l=40, r=40, t=60, b=80)
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    v_max = df_day['Consum'].max()
    v_min = df_day['Consum'].min()
    raport_vg = v_max / v_min if v_min > 0 else 0
    sold_mediu = df_day['Sold'].mean()

    col1.metric("Consum Maxim (Vârf)", f"{v_max:.0f} MW")
    col2.metric("Consum Minim (Gol)", f"{v_min:.0f} MW")
    col3.metric("Raport Vârf / Gol", f"{raport_vg:.2f}")
    col4.metric("Sold Mediu Zilnic", f"{sold_mediu:.0f} MW", delta="Import Net" if sold_mediu > 0 else "Export Net")

    st.markdown("### Concluzii și Observații pe Ziua Analizată")
    st.markdown(f"""
    1. **Banda de Bază (Base Load):**
       - Componenta Nucleară rămâne stabilă pe tot parcursul celor 24 de ore (~1.300–1.400 MW), asigurând stabilitatea de fond a SEN.
       - Cărbunele menține un nivel constant, participând mai puțin la reglajul dinamic rapid intrazilnic.

    2. **Urmărirea de Sarcină și Rolul Hidro & Gaz:**
       - Producția hidrocentrale (`Ape`) și hidrocarburi (`Gaz`) funcționează ca elemente flexibile de echilibrare: acestea își reduc turația la orele prânzului când parcurile fotovoltaice (`Foto`) injectează putere maximă și urcă alert pentru a acoperi vârful de seară (orele 19:00–22:00).

    3. **Sarcina Reziduală**
       - Curba sarcinii reziduale evidențiază golul de la amiază creat de sursele solare. Diferența dintre minimul de la prânz și vârful de seară dictează rampa necesară de acoperit din centralele dispecerizabile și importuri.

    4. **Comportamentul Soldului Transfrontalier:**
       - Se observă cum soldul urmărește diferențialul dintre cerere și generarea locală: în perioadele de vârf de sarcină sau cădere a producției regenerabile, sistemul apelează la importuri (sold pozitiv), revenind spre export sau echilibru la golul de noapte sau în orele de supraproducție eoliană/solară.
    """)

    #TASK 2: ORELE DE VÂRF VS. ORELE DE GOL
st.markdown("---")
st.header("2. Analiză Comparativă: Ore de Vârf vs. Ore de Gol")
st.write(
    "Analiza compară modul în care cererea de consum este acoperită în momentele de minimă solicitare "
    "(Gol: 02:00–05:00) față de momentele de maximă solicitare (Vârf de Seară: 18:00–21:00) pe tot parcursul anului 2025."
)

df_hourly['Interval'] = 'Altele'
df_hourly.loc[df_hourly.index.hour.isin([2, 3, 4, 5]), 'Interval'] = 'Gol de Noapte (02-05)'
df_hourly.loc[df_hourly.index.hour.isin([18, 19, 20, 21]), 'Interval'] = 'Vârf de Seară (18-21)'

surse_lista = ['Nuclear', 'Carbune', 'Hidrocarburi', 'Ape', 'Eolian', 'Foto', 'Biomasa']
variabile_analiza = ['Consum', 'Productie', 'Sold', 'Sarcina_Reziduala'] + surse_lista

df_vg = df_hourly[df_hourly['Interval'] != 'Altele'].groupby('Interval')[variabile_analiza].mean().reset_index()

for col in surse_lista + ['Sold']:
    df_vg[f'Pondere_{col}'] = (df_vg[col] / df_vg['Consum']) * 100

st.subheader("Bilanț Mediu Anual pe Interval (MW)")
df_display = df_vg.set_index('Interval')[['Consum', 'Productie', 'Sold', 'Sarcina_Reziduala'] + surse_lista].round(1)
st.dataframe(df_display, use_container_width=True)

df_melted_mw = df_vg.melt(
    id_vars=['Interval'],
    value_vars=surse_lista + ['Sold'],
    var_name='Componenta',
    value_name='Putere_MW'
)

fig_comp = px.bar(
    df_melted_mw,
    x='Interval',
    y='Putere_MW',
    color='Componenta',
    barmode='group',
    title="Comparație Producție pe Surse și Sold: Vârf de Seară vs. Gol de Noapte",
    labels={'Putere_MW': 'Putere Medie (MW)', 'Interval': 'Regim de Funcționare'},
    color_discrete_map={
        'Nuclear': '#8c564b',
        'Carbune': '#4d4d4d',
        'Hidrocarburi': '#ff7f0e',
        'Biomasa': '#8c6d31',
        'Ape': '#1f77b4',
        'Eolian': '#2ca02c',
        'Foto': '#f5b041',
        'Sold': '#d62728'
    }
)
fig_comp.update_layout(template='plotly_white', height=500)
st.plotly_chart(fig_comp, use_container_width=True)

col_v1, col_v2, col_v3, col_v4 = st.columns(4)
consum_gol = df_vg.loc[df_vg['Interval'] == 'Gol de Noapte (02-05)', 'Consum'].values[0]
consum_varf = df_vg.loc[df_vg['Interval'] == 'Vârf de Seară (18-21)', 'Consum'].values[0]
sold_gol = df_vg.loc[df_vg['Interval'] == 'Gol de Noapte (02-05)', 'Sold'].values[0]
sold_varf = df_vg.loc[df_vg['Interval'] == 'Vârf de Seară (18-21)', 'Sold'].values[0]

col_v1.metric("Consum Mediu Gol", f"{consum_gol:.0f} MW")
col_v2.metric("Consum Mediu Vârf", f"{consum_varf:.0f} MW", delta=f"+{consum_varf - consum_gol:.0f} MW")
col_v3.metric("Sold Mediu Gol", f"{sold_gol:.0f} MW", delta="Import" if sold_gol > 0 else "Export")
col_v4.metric("Sold Mediu Vârf", f"{sold_varf:.0f} MW", delta="Import" if sold_varf > 0 else "Export")

st.markdown("### Concluzii & Interpretare EDA: Vârf vs. Gol")
st.markdown("""
* **Comportamentul Benzii:** Producția Nucleară rămâne neschimbată între vârf și gol (~1.300 MW). Cărbunele prezintă o rigiditate ridicată, modificându-și puțin producția între cele două regimuri.
* **Sursele de Acoperire a Vârfului:** Diferența masivă de consum între noapte și seară este preluată preponderent de **Hidroelectrica (`Ape`)**, centralele flexibile pe gaz (**`Hidrocarburi`**) și **Soldul de schimb (creșterea importurilor)**.
* **Contribuția Regenerabilelor:** La vârful de seară (18:00–21:00), energia solară (`Foto`) este nulă sau neglijabilă din cauza apusului. Eolianul are o producție distribuită uniform/variabil, fără garanție de acoperire la oră fixă.
* **Dinamica Soldului:** În golul de noapte, raportul dintre producția fixă și consum permite reducerea importurilor sau apariția exporturilor; la vârful de seară, soldul devine frecvent pozitiv (import net substanțial).
""")