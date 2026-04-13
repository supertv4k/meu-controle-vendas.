import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SUPERTV4K ", layout="wide")

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
    # Adicionado IF NOT EXISTS e colunas batendo com o formulário
    c.execute('''CREATE TABLE IF NOT EXISTS assinaturas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, servidor TEXT, cliente TEXT, 
                  vencimento DATE, valor REAL, whatsapp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def calcular_status(vencimento_str):
    hoje = datetime.now().date()
    # Conversão segura de string para data
    if isinstance(vencimento_str, str):
        venc = datetime.strptime(vencimento_str, '%Y-%m-%d').date()
    else:
        venc = vencimento_str
        
    dias = (venc - hoje).days
    if dias < 0: return "Vencido 🔴", "sua assinatura venceu, vamos renovar?", "🔴"
    if dias == 0: return "Vence Hoje 🟠", "sua assinatura vence hoje, vamos renovar?", "🟠"
    if dias <= 5: return f"Vence em {dias} dias 🟡", f"sua assinatura vence em {dias} dias, vamos renovar?", "🟡"
    return "Em dia 🟢", "", "🟢"

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # Correção: width em vez de with
    st.image("https://i.imgur.com/a/kwmTPvd", width=100) 
with col_titulo:
    st.title("GESTÃO DE CLIENTES SUPERTV4K")

# --- CARREGAR DADOS ---
conn = sqlite3.connect('clientes.db')
df = pd.read_sql_query("SELECT * FROM assinaturas", conn)
conn.close()

# --- DASHBOARD ---
if not df.empty:
    # Aplicar cálculo de status para as métricas
    df['status_calculado'] = df['vencimento'].apply(lambda x: calcular_status(x)[2])
    
    total_clientes = len(df)
    receita_total = df['valor'].sum()
    vencidos = len(df[df['status_calculado'] == "🔴"])

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
        wpp_num = st.text_input("WhatsApp (Ex: 5517999999999)")
        
        if st.form_submit_button("Salvar Cliente"):
            conn = sqlite3.connect('clientes.db')
            c = conn.cursor()
            # Removido colunas usuário/senha que não estavam no formulário
            c.execute("INSERT INTO assinaturas (servidor, cliente, vencimento, valor, whatsapp) VALUES (?,?,?,?,?)",
                      (srv, cli, venc_data, val_ass, wpp_num))
            conn.commit()
            conn.close()
            st.success("Cliente cadastrado!")
            st.rerun()

with tab1:
    busca = st.text_input("🔍 Buscar cliente pelo nome...")
    if not df.empty:
        filtered_df = df[df['cliente'].str.contains(busca, case=False)] if busca else df
        for i, r in filtered_df.iterrows():
            status, msg, icon = calcular_status(r['vencimento'])
            with st.expander(f"{icon} {r['cliente']} - {status}"):
                st.write(f"**Servidor:** {r['servidor']} | **Valor:** R$ {r['valor']:.2f}")
                st.write(f"**Vencimento:** {r['vencimento']}")
                
                if st.button("Remover Cliente", key=f"del_{r['id']}"):
                    conn = sqlite3.connect('clientes.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM assinaturas WHERE id=?", (r['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()

with tab3:
    st.subheader("🚀 Alertas de Cobrança")
    if not df.empty:
        enviados = 0
        for i, r in df.iterrows():
            status, msg, icon = calcular_status(r['vencimento'])
            if icon != "🟢":
                enviados += 1
                col_c1, col_c2 = st.columns([3, 1])
                col_c1.write(f"**{r['cliente']}** - {status}")
                
                texto = urllib.parse.quote(f"Olá {r['cliente']}, {msg}")
                link = f"https://wa.me/{r['whatsapp']}?text={texto}"
                col_c2.link_button("Enviar Zap", link)
        
        if enviados == 0:
            st.success("Tudo em dia! Ninguém vencendo nos próximos 5 dias.")
