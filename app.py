import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuração da Página
st.set_page_config(page_title="AgroFlow - Gestão Hídrica", page_icon="💧", layout="wide")

# Título e Contexto
st.title("💧 AgroFlow: Monitoramento de Umidade do Solo")
st.markdown("Otimização de irrigação baseada em dados de sensores em tempo real e previsão meteorológica.")

# --- 1. GERAR DADOS FICTÍCIOS (MOCK) ---
# Em um cenário real, isso viria do seu Backend/IoT
dados_fazenda = [
    {"id": 1, "lat": -21.208, "lon": -47.795, "cultura": "Soja", "umidade": 18, "chuva_horas": 48, "chuva_mm": 5},
    {"id": 2, "lat": -21.205, "lon": -47.790, "cultura": "Milho", "umidade": 65, "chuva_horas": 2, "chuva_mm": 25},
    {"id": 3, "lat": -21.210, "lon": -47.785, "cultura": "Café", "umidade": 42, "chuva_horas": 12, "chuva_mm": 10},
    {"id": 4, "lat": -21.212, "lon": -47.792, "cultura": "Soja", "umidade": 25, "chuva_horas": 36, "chuva_mm": 0},
    {"id": 5, "lat": -21.202, "lon": -47.798, "cultura": "Trigo", "umidade": 80, "chuva_horas": 1, "chuva_mm": 40},
]

df = pd.DataFrame(dados_fazenda)

# Função para definir a cor baseada na umidade (Lógica do Mapa de Calor)
def get_cor_umidade(umidade):
    if umidade < 30: return 'red'      # Seco / Crítico
    if umidade < 50: return 'orange'   # Atenção
    return 'green'                     # Ideal

# Função para recomendação de ação
def get_acao(row):
    if row['umidade'] < 30 and row['chuva_horas'] > 24:
        return "🚨 IRRIGAR AGORA"
    elif row['umidade'] < 30 and row['chuva_horas'] <= 24:
        return "⚠️ AGUARDAR CHUVA"
    else:
        return "✅ Monitorar"

# Adiciona coluna de Ação ao DataFrame
df['Status'] = df.apply(get_acao, axis=1)

# --- 2. CRIAÇÃO DO MAPA (HEATMAP DE SETORES) ---
col_mapa, col_info = st.columns([2, 1])

with col_mapa:
    st.subheader("Mapa de Calor da Fazenda")
    
    # Centraliza o mapa na média das coordenadas
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=15, tiles="OpenStreetMap")

    # Adiciona os círculos (Setores)
    for index, row in df.iterrows():
        cor = get_cor_umidade(row['umidade'])
        
        # Cria o tooltip (texto que aparece ao passar o mouse)
        tooltip_html = f"""
        <b>Setor {row['id']}</b><br>
        Cultura: {row['cultura']}<br>
        Umidade: {row['umidade']}%
        """
        
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=180, # Tamanho do setor em metros
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.6,
            popup=f"Setor {row['id']}",
            tooltip=tooltip_html
        ).add_to(m)
        
        # Adiciona o número do setor no centro do círculo
        folium.Marker(
            location=[row['lat'], row['lon']],
            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; font-size: 12pt">{row['id']}</div>""")
        ).add_to(m)

    # Renderiza o mapa no Streamlit
    st_folium(m, width="100%", height=400)

# --- 3. TABELA DE DETALHES ---
st.divider()
st.subheader("📊 Detalhamento por Região")

# Formatação visual da tabela
def highlight_critico(s):
    is_critico = s['umidade'] < 30
    return ['background-color: #ffcccc' if is_critico else '' for _ in s]

# Prepara o DF para exibição (renomeia colunas para ficar bonito)
df_display = df[['id', 'cultura', 'umidade', 'chuva_horas', 'chuva_mm', 'Status']].copy()
df_display.columns = ['Região', 'Cultura', 'Umidade (%)', 'Previsão Chuva (h)', 'Qtd. Chuva (mm)', 'Recomendação']

# Mostra a tabela com destaque condicional (Pandas Styler)
st.dataframe(
    df_display.style.map(lambda x: 'color: red; font-weight: bold' if x == '🚨 IRRIGAR AGORA' else '', subset=['Recomendação'])
    .format({'Umidade (%)': '{}%', 'Previsão Chuva (h)': '{}h', 'Qtd. Chuva (mm)': '{}mm'}),
    use_container_width=True,
    hide_index=True
)

# --- 4. MÉTRICAS RÁPIDAS (BÔNUS) ---
st.divider()
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Média de Umidade", f"{df['umidade'].mean()}%", "-5%")
kpi2.metric("Área Crítica", f"{len(df[df['umidade'] < 30])} Setores", "Ação Necessária", delta_color="inverse")
kpi3.metric("Economia de Água Estimada", "15.000 L", "+12%")