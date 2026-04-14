import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import base64

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SUPERTV4K PRO - GESTÃO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; background-color: #ff0000; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { color: white; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, servidor TEXT, img_servidor TEXT, 
                  cliente TEXT, usuario TEXT, senha TEXT, data_inicio DATE, 
                  vencimento DATE, custo REAL, mensalidade REAL, whatsapp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def img_to_b64(file):
    if file: return base64.b64encode(file.read()).decode()
    return None

def calcular_regua_cobranca(venc_data):
    hoje = datetime.now().date()
    if isinstance(venc_data, str):
        venc_data = datetime.strptime(venc_data, '%Y-%m-%d').date()
    
    dias = (venc_data - hoye).days if 'hoye' not in locals() else (venc_data - hoje).days
    pix = "62.326.879/0001-13"
    
    mensagens = {
        5: f"Sua Assinatura vai Vencer 5 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        4: f"Sua Assinatura vai Vencer 4 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        3: f"Sua Assinatura vai Vencer 3 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        2: f"Sua Assinatura vai Vencer 2 dias!",
        1: f"Sua Assinatura vai Amanhã! Não fique sem TV Renove Agora! PIX {pix}",
        0: f"Sua Assinatura Vence Hoje! Não fique sem TV Renove Agora! PIX {pix}",
    }
    
    if dias < 0:
        return "Vencido 🔴", f"Sua Assinatura Venceu! Não Se Preocupe é só Fazer o Pagamento que logo estará Liberado! PIX {pix}", "🔴"
    elif dias in mensagens:
        return f"Vence em {dias} dias", mensagens[dias], "🟡" if dias > 1 else "🟠"
    return "Em dia 🟢", "", "🟢"

# --- INTERFACE ---
st.title("📺 GESTÃO SUPERTV4K PRO")

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

if not df.empty:
    bruto = df['mensalidade'].sum()
    custo = df['custo'].sum()
    lucro = bruto - custo
    vencidos = len([i for i, r in df.iterrows() if calcular_regua_cobranca(r['vencimento'])[2] == "🔴"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clientes Ativos", len(df) - vencidos)
    m2.metric("Vencidos", vencidos)
    m3.metric("Faturamento Bruto", f"R$ {bruto:.2f}")
    m4.metric("Lucro Líquido", f"R$ {lucro:.2f}")

tab1, tab2, tab3 = st.tabs(["👥 Clientes", "➕ Novo Cadastro", "📢 Cobrança em Massa"])

with tab2:
    with st.form("cadastro"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Cliente")
        user = c2.text_input("Usuário")
        senha = c3.text_input("Senha")
        srv = c1.text_input("Servidor")
        wpp = c2.text_input("WhatsApp (55...)")
        venc = c3.date_input("Vencimento")
        v_custo = c1.number_input("Custo Crédito")
        v_mensal = c2.number_input("Mensalidade")
        img = c3.file_uploader("Logo Servidor", type=['png', 'jpg'])
        
        if st.form_submit_button("CADASTRAR"):
            b64 = img_to_b64(img)
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (servidor, img_servidor, cliente, usuario, senha, vencimento, custo, mensalidade, whatsapp) VALUES (?,?,?,?,?,?,?,?,?)",
                         (srv, b64, nome, user, senha, venc, v_custo, v_mensal, wpp))
            conn.commit()
            st.rerun()

with tab1:
    busca = st.text_input("🔍 Buscar...")
    if not df.empty:
        for i, r in df.iterrows():
            if busca.lower() in r['cliente'].lower() or busca.lower() in r['usuario'].lower():
                status, msg, icon = calcular_regua_cobranca(r['vencimento'])
                with st.expander(f"{icon} {r['cliente']} | Status: {status}"):
                    c_img, c_txt, c_act = st.columns([1, 2, 1])
                    if r['img_servidor']: c_img.image(f"data:image/png;base64,{r['img_servidor']}", width=80)
                    c_txt.write(f"**User:** {r['usuario']} | **Senha:** {r['senha']}")
                    c_txt.write(f"**Vencimento:** {r['vencimento']}")
                    
                    nova_data = c_act.date_input("Renovar para:", value=datetime.now().date()+timedelta(days=30), key=f"d{r['id']}")
                    if c_act.button("🔄 Renovar", key=f"r{r['id']}"):
                        conn = sqlite3.connect('supertv_gestao.db')
                        conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (nova_data, r['id']))
                        conn.commit()
                        st.rerun()
                    if c_act.button("🗑️ Excluir", key=f"del{r['id']}"):
                        conn = sqlite3.connect('supertv_gestao.db')
                        conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

with tab3:
    st.subheader("🚀 Disparo de Cobrança Diária")
    cobrar = []
    for i, r in df.iterrows():
        status, msg, icon = calcular_regua_cobranca(r['vencimento'])
        if icon != "🟢": cobrar.append({"cliente": r['cliente'], "wpp": r['whatsapp'], "msg": msg})
    
    if cobrar:
        st.write(f"Total de avisos para hoje: {len(cobrar)}")
        for item in cobrar:
            link = f"https://wa.me/{item['wpp']}?text={urllib.parse.quote(item['msg'])}"
            st.link_button(f"📲 Enviar para {item['cliente']}", link)
    else:
        st.success("Nenhum cliente vencendo nos próximos 5 dias!")
