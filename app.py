import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO VISUAL PREMIUM ---
st.set_page_config(page_title="SUPERTV4K PRO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { background-color: #ff0000; color: white; border-radius: 10px; border: none; width: 100%; }
    .stTextInput>div>div>input { background-color: #1a1c23; color: white; border: 1px solid #3e424b; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE BANCO DE DADOS ---
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
    # Verifica se o vencimento já vem como objeto date ou string
    if isinstance(vencimento_str, str):
        venc = datetime.strptime(vencimento_str, '%Y-%m-%d').date()
    else:
        venc = vencimento_str
        
    dias = (venc - hoje).days
    
    if dias < 0: return "Vencido 🔴", "sua assinatura venceu, vamos renovar?"
    if dias == 0: return "Vence Hoje 🟠", "sua assinatura vence hoje, vamos renovar?"
    if dias <= 5: return f"Vence em {dias} dias 🟡", f"sua assinatura vence em {dias} dias, vamos renovar?"
    return "Em dia 🟢", ""

# --- INTERFACE ---
st.title("🔴 SUPERTV4K - Gestão Pro")

aba1, aba2 = st.tabs(["📋 Lista de Clientes", "➕ Novo Cadastro"])

with aba2:
    st.subheader("Cadastrar Nova Assinatura")
    with st.form("cadastro"):
        col1, col2 = st.columns(2)
        srv = col1.text_input("Nome do Servidor")
        cli = col2.text_input("Nome do Cliente")
        usr = col1.text_input("Usuário")
        sen = col2.text_input("Senha")
        venc = st.date_input("Data de Vencimento")
        wpp = st.text_input("WhatsApp (Ex: 5511999999999)")
        val = st.number_input("Valor da Assinatura R$", format="%.2f")
        
        if st.form_submit_button("Salvar Assinatura"):
            if cli and wpp:
                conn = sqlite3.connect('clientes.db')
                c = conn.cursor()
                c.execute("INSERT INTO assinaturas (servidor, cliente, usuario, senha, vencimento, valor, whatsapp) VALUES (?,?,?,?,?,?,?)",
                          (srv, cli, usr, sen, venc, val, wpp))
                conn.commit()
                st.success(f"Cliente {cli} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha o nome do cliente e o WhatsApp!")

with aba1:
    busca = st.text_input("🔍 Buscar Cliente por Nome")
    conn = sqlite3.connect('clientes.db')
    df = pd.read_sql_query("SELECT * FROM assinaturas ORDER BY vencimento ASC", conn)
    conn.close()

    if not df.empty:
        if busca:
            df = df[df['cliente'].str.contains(busca, case=False)]
        
        for i, r in df.iterrows():
            status, msg = calcular_status(r['vencimento'])
            with st.expander(f"{r['cliente']} | {status}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Servidor:** {r['servidor']}")
                c1.write(f"**Usuário:** {r['usuario']}")
                c1.write(f"**Senha:** {r['senha']}")
                c2.write(f"**Vencimento:** {r['vencimento']}")
                c2.write(f"**Valor:** R$ {r['valor']:.2f}")
                
                # Link do WhatsApp dinâmico
                texto_wpp = urllib.parse.quote(f"Olá {r['cliente']}, {msg}")
                st.link_button(f"📲 Chamar no WhatsApp", f"https://wa.me/{r['whatsapp']}?text={texto_wpp}")
                
                if st.button("Excluir Cliente", key=f"del_{r['id']}"):
                    conn = sqlite3.connect('clientes.db')
                    c = conn.cursor()
                    c.execute(f"DELETE FROM assinaturas WHERE id={r['id']}")
                    conn.commit()
                    st.rerun()
    else:
        st.info("Nenhum cliente cadastrado ainda.")
