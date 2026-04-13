import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

# Estilização CSS Customizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #ff0000; font-size: 28px; }
    .stButton>button { background-color: #ff0000; color: white; border-radius: 8px; width: 100%; border: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1a1c23; 
        border-radius: 5px 5px 0 0; 
        padding: 10px 20px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('clientes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS assinaturas
                 (id INTEGER PRIMARY KEY, servidor TEXT, cliente TEXT, usuario TEXT, 
                  senha TEXT, vencimento DATE, valor REAL, whatsapp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def calcular_status(vencimento_str):
    hoje = datetime.now().date()
    venc = datetime.strptime(str(vencimento_str), '%Y-%m-%d').date() if isinstance(vencimento_str, str) else vencimento_str
    dias = (venc - hoje).days
    if dias < 0: return "Vencido 🔴", "sua assinatura venceu, vamos renovar?", "🔴"
    if dias == 0: return "Vence Hoje 🟠", "sua assinatura vence hoje, vamos renovar?", "🟠"
    if dias <= 5: return f"Vence em {dias} dias 🟡", f"sua assinatura vence em {dias} dias, vamos renovar?", "🟡"
    return "Em dia 🟢", "", "🟢"

# --- CABEÇALHO COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    
    st.image("https://share.icloud.com/photos/0d4d14_RUi1TZeaC3C-WPlqVA", width=100) 
with col_titulo:
    st.title("GESTÃO DE CLIENTES")

# --- CARREGAR DADOS ---
conn = sqlite3.connect('clientes.db')
df = pd.read_sql_query("SELECT * FROM assinaturas", conn)
conn.close()

# --- DASHBOARD DE MÉTRICAS ---
if not df.empty:
    df['status_info'] = df['vencimento'].apply(lambda x: calcular_status(x))
    total_clientes = len(df)
    receita_total = df['valor'].sum()
    vencidos = len([x for x in df['status_info'] if "🔴" in x[2]])

    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Clientes", total_clientes)
    m2.metric("Receita Mensal", f"R$ {receita_total:.2f}")
    m3.metric("Inadimplentes (Vencidos)", vencidos)

st.divider()

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["👥 Gerenciar Clientes", "➕ Novo Cadastro", "📢 Envios em Massa"])

with tab2:
    with st.form("cadastro_novo"):
        c1, c2 = st.columns(2)
        srv = c1.text_input("Servidor")
        cli = c2.text_input("Nome do Cliente")
        venc_data = c1.date_input("Data de Vencimento")
        val_ass = c2.number_input("Valor R$", format="%.2f")
        wpp_num = st.text_input("WhatsApp (55 + DDD + Número)")
        if st.form_submit_button("Salvar Cliente"):
            conn = sqlite3.connect('clientes.db')
            c = conn.cursor()
            c.execute("INSERT INTO assinaturas (servidor, cliente, vencimento, valor, whatsapp) VALUES (?,?,?,?,?)",
                      (srv, cli, venc_data, val_ass, wpp_num))
            conn.commit()
            st.success("Cliente cadastrado!")
            st.rerun()

with tab1:
    busca = st.text_input("🔍 Buscar cliente...")
    if not df.empty:
        filtered_df = df[df['cliente'].str.contains(busca, case=False)] if busca else df
        for i, r in filtered_df.iterrows():
            status, msg, icon = calcular_status(r['vencimento'])
            with st.expander(f"{icon} {r['cliente']} - {status}"):
                st.write(f"Servidor: {r['servidor']} | Valor: R$ {r['valor']:.2f}")
                if st.button("Remover", key=f"del_{r['id']}"):
                    conn = sqlite3.connect('clientes.db')
                    c = conn.cursor()
                    c.execute(f"DELETE FROM assinaturas WHERE id={r['id']}")
                    conn.commit()
                    st.rerun()

with tab3:
    st.subheader("🚀 Clientes que precisam de atenção")
    if not df.empty:
        # Filtra apenas quem não está "Em dia 🟢"
        precisam_atencao = []
        for i, r in df.iterrows():
            status, msg, icon = calcular_status(r['vencimento'])
            if icon != "🟢":
                precisam_atencao.append(r)
        
        if precisam_atencao:
            for r in precisam_atencao:
                status, msg, icon = calcular_status(r['vencimento'])
                col_c1, col_c2 = st.columns([3, 1])
                col_c1.write(f"**{r['cliente']}** ({status})")
                
                texto = urllib.parse.quote(f"Olá {r['cliente']}, {msg}")
                link = f"https://wa.me/{r['whatsapp']}?text={texto}"
                col_c2.link_button("Enviar", link)
        else:
            st.success("Tudo em dia! Nenhum cliente vencendo nos próximos 5 dias.")

