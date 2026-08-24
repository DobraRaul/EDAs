import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
       - Producția hidrocentrale (`Ape`) și hidrocarburi (`Gaz`) funcționează ca elemente flexibile de echilibrare: acestea își reduc turația la orele prânzului când parcurile fotovoltaice (`Foto`) injectează putere maximă și urcă alert pentru a acoperi vârful de seară (orele 19:00–22:00)[cite: 1].

    3. **Sarcina Reziduală și Efectul «Duck Curve»:**
       - Curba sarcinii reziduale evidențiază golul de la amiază creat de sursele solare[cite: 1]. Diferența dintre minimul de la prânz și vârful de seară dictează rampa necesară de acoperit din centralele dispecerizabile și importuri[cite: 1].

    4. **Comportamentul Soldului Transfrontalier:**
       - Se observă cum soldul urmărește diferențialul dintre cerere și generarea locală: în perioadele de vârf de sarcină sau cădere a producției regenerabile, sistemul apelează la importuri (sold pozitiv), revenind spre export sau echilibru la golul de noapte sau în orele de supraproducție eoliană/solară[cite: 1].
    """)