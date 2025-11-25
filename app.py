import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import math

def prever_umidade_solo(umidade_atual, chuva_mm, tipo_solo):    
    if tipo_solo.lower() == 'arenoso':
        fator_absorcao = 1.48  
        teto_saturacao = 20.0
        perda_diaria = 2.0
        
    elif tipo_solo.lower() == 'argiloso':
        fator_absorcao = 3.28
        teto_saturacao = 45.0
        perda_diaria = 1.0
        
    if chuva_mm > 0:
        ganho_umidade = fator_absorcao * math.log(chuva_mm + 1)
    else:
        ganho_umidade = 0
        umidade_atual -= perda_diaria

    nova_umidade = umidade_atual + ganho_umidade

    if nova_umidade > teto_saturacao:
        nova_umidade = teto_saturacao
    if nova_umidade < 0:
        nova_umidade = 0

    return round(nova_umidade,2)


# Configuração da Página
st.set_page_config(page_title="AgroFlow", page_icon="💧", layout="wide")
st.title("💧 AgroFlow: Monitoramento Inteligente")

# --- 1. DADOS (7 Regiões com Coordenadas de Polígonos) ---
SEDE_COORDS = {"lat": -12.760, "lon": -54.270, "id": "Sede"}

dados_fazenda = [
  {
    "id": "Região A",
    "culture": "Trigo",
    "soil": "Arenoso",
    "humidity": 33,
    "expectedRainfall": 0.6,
    "hoursToNextRainfall": 19,
    "coordinates": [
      [-12.7663, -54.2813],
      [-12.7689, -54.2735],
      [-12.7465, -54.267],
      [-12.7453, -54.2767]
    ]
  },
  {
    "id": "Região B",
    "culture": "Milho",
    "soil": "Argiloso",
    "humidity": 17,
    "expectedRainfall": 12,
    "hoursToNextRainfall": 17,
    "coordinates": [
      [-12.7499, -54.2584],
      [-12.7718, -54.2651],
      [-12.7689, -54.2732],
      [-12.7465, -54.267]
    ]
  },
  {
    "id": "Região C",
    "culture": "Milho",
    "soil": "Argiloso",
    "humidity": 13,
    "expectedRainfall": 1,
    "hoursToNextRainfall": 17,
    "coordinates": [
      [-12.75, -54.2579],
      [-12.753, -54.2503],
      [-12.7742, -54.2572],
      [-12.7719, -54.265]
    ]
  },
  {
    "id": "Região D",
    "culture": "Café",
    "soil": "Argiloso",
    "humidity": 4,
    "expectedRainfall": 0.8,
    "hoursToNextRainfall": 18,
    "coordinates": [
      [-12.7745, -54.2567],
      [-12.7535, -54.2498],
      [-12.7616, -54.2273],
      [-12.7826, -54.2342]
    ]
  },
  {
    "id": "Região E",
    "culture": "Trigo",
    "soil": "Arenoso",
    "humidity": 46,
    "expectedRainfall": 1.2,
    "hoursToNextRainfall": 20,
    "coordinates": [
      [-12.7661, -54.2816],
      [-12.7593, -54.3029],
      [-12.7417, -54.3003],
      [-12.7452, -54.2769]
    ]
  }
]

df = pd.DataFrame(dados_fazenda)

# --- 2. LÓGICA (Centróides e Status) ---
def get_centroid(coords):
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    return np.mean(lats), np.mean(lons)

df['center_lat'] = df['coordinates'].apply(lambda x: get_centroid(x)[0])
df['center_lon'] = df['coordinates'].apply(lambda x: get_centroid(x)[1])

def get_acao(row):
    row['nova_umidade'] = prever_umidade_solo(row['humidity'], row['expectedRainfall'], row['soil'])
    if row['humidity'] > 25: return "✅ Monitorar"
    elif row['nova_umidade'] > 25 and row['hoursToNextRainfall'] <= 20: return "⚠️ AGUARDAR CHUVA"
    else: return "🚨 IRRIGAR AGORA"

df['Status'] = df.apply(get_acao, axis=1)
def get_cor(h): return 'red' if h < 30 else 'orange' if h < 80 else 'green'

# --- 3. ALGORITMO DE ROTA ---
def calcular_rota(pontos_destino):
    rota = [SEDE_COORDS]
    nao_visitados = pontos_destino.copy()
    atual = SEDE_COORDS
    while nao_visitados:
        mais_proximo = min(nao_visitados, key=lambda p: np.sqrt((p['center_lat']-atual['lat'])**2 + (p['center_lon']-atual['lon'])**2))
        rota.append({'lat': mais_proximo['center_lat'], 'lon': mais_proximo['center_lon'], 'id': mais_proximo['id']})
        nao_visitados.remove(mais_proximo)
        atual = {'lat': mais_proximo['center_lat'], 'lon': mais_proximo['center_lon']}
    return rota

# --- 4. LAYOUT DA PÁGINA (AQUI ESTÁ A MUDANÇA PARA O VISUAL PEDIDO) ---

if "rota" not in st.session_state: st.session_state.rota = None

# Cria colunas: Mapa (75%) | Indicadores (25%)
col_map, col_kpi = st.columns([3, 1])

# === COLUNA DA DIREITA (INDICADORES/KPIs) ===
with col_kpi:
    st.subheader("📈 Indicadores")
    
    # KPI 1
    with st.container(border=True):
        media = df['humidity'].mean()
        st.metric("Média de Umidade", f"{media:.1f}%", "-5% (vs ontem)")
        
    # KPI 2
    with st.container(border=True):
        criticos = len(df[df['humidity'] < 30])
        st.metric("Setores Críticos", f"{criticos}", "Ação Necessária", delta_color="inverse")
        
    # KPI 3
    with st.container(border=True):
        st.metric("Economia Estimada (mensal)", "2.000 m³", "+12%")

# === COLUNA DA ESQUERDA (MAPA) ===
with col_map:
    # Centraliza o mapa
    m = folium.Map(location=[df['center_lat'].mean(), df['center_lon'].mean()], zoom_start=13)
    
    # Sede
    folium.Marker([SEDE_COORDS['lat'], SEDE_COORDS['lon']], icon=folium.Icon(color="blue", icon="home")).add_to(m)

    # Desenha Polígonos
    for _, row in df.iterrows():
        cor = get_cor(row['humidity'])
        folium.Polygon(
            locations=row['coordinates'],
            color=cor, fill=True, fill_opacity=0.5,
            popup=f"Setor {row['id']}: {row['culture']}",
            tooltip=f"Umidade: {row['humidity']}%"
        ).add_to(m)
        
        # Rótulo (Fixed f-string error with triple quotes)
        folium.Marker(
            [row['center_lat'], row['center_lon']],
            icon=folium.DivIcon(html=f"""<div style='font-weight:bold; color:black; font-size:14px; text-shadow: 1px 1px 2px white;'>{row['id']}</div>""")
        ).add_to(m)

    # Rota
    if st.session_state.rota:
        points = [[p['lat'], p['lon']] for p in st.session_state.rota]
        folium.PolyLine(points, color="blue", weight=4, dash_array='10').add_to(m)

    st_folium(m, width="100%", height=600)

# --- TABELA DETALHADA ---
st.divider()
st.subheader("📋 Detalhamento por Região")

# 1. Selecionar e Copiar apenas as colunas que queremos
df_display = df[['id', 'culture', 'soil', 'humidity', 'hoursToNextRainfall', 'expectedRainfall', 'Status']].copy()

# 2. Renomear para ficar igual à imagem (Nomes Bonitinhos)
df_display.columns = [
    "Região", 
    "Cultura", 
    "Solo",
    "Umidade (%)", 
    "Previsão Chuva (h)", 
    "Qtd. Chuva (mm)", 
    "Recomendação"
]

# 3. Exibir com Estilo (Cores e Formatos de Unidade)
st.dataframe(
    df_display.style
    # Pinta de vermelho negrito se for para IRRIGAR
    .map(lambda x: 'color: #ff4b4b; font-weight: bold' if 'IRRIGAR' in str(x) else 'color: #3dd56d; font-weight: bold', subset=['Recomendação'])
    # Adiciona as unidades de medida (%, h, mm)
    .format({
        'Umidade (%)': '{:.1f}%',
        'Previsão Chuva (h)': '{}h',
        'Qtd. Chuva (mm)': '{}mm'
    }),
    use_container_width=True,
    hide_index=True
)