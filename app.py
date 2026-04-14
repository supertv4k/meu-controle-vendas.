import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GESTÃO DE CLIENTES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .stCheckbox { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, servidor TEXT, sistema TEXT, 
                  cliente TEXT, usuario TEXT, senha TEXT, vencimento DATE, 
                  custo REAL, mensalidade REAL, whatsapp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # Inserção inicial de servidores se vazio
    c.execute("SELECT COUNT(*) FROM lista_servidores")
    if c.fetchone()[0] == 0:
        servs = ["Uniplay", "Mundo GF", "P2Braz", "Play TV", "P2Cine", "Balde TV", "Speed Tv", "Unitv", "Mega TV", "New Mais", "P2Imperial", "Seven", "Zeus", "Ninety", "Alphaplay", "Genial", "RushPlay", "ClubTV", "EasyPlay", "Horizon", "BobPlayer", "IboPlayer", "IboPlayer pro"]
        for s in servs: c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (s,))
    
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE COBRANÇA (Suas Frases) ---
def obter_regua(venc_data):
    hoje = datetime.now().date()
    pix = "62.326.879/0001-13"
    try:
        venc_data = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc_data - hoje).days
        
        if dias == 3:
            return "Vence em 3 dias", f"Sua Assinatura Vence em 3 dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}", "🟨"
        elif dias == 2:
            return "Vence em 2 dias", f"Sua Assinatura Vence em 2 dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}", "🟨"
        elif dias == 1:
            return "Vence Amanhã", f"Sua Assinatura Vence Amanhã ! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}", "🟧"
        elif dias == 0:
            return "Vence HOJE", f"Sua Assinatura Vence Hoje ! Faça Agora o pagamento pelo PIX e Já Já Estará Renovado mais 30 Dias!\n\nCopia e Cola no seu Banco!\n\n{pix}", "🟥"
        elif dias < 0:
            return "VENCIDO", f"Sua Assinatura Venceu! Não se Preocupe é só Fazer o Pagamento que Renovamos mais 30 Dias pra Você!\n\nCopia e Cola no seu Banco!\n\n{pix}", "⬛"
        return "Em dia", "", "🟩"
    except: return "Erro", "", "⚪"

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista

# --- INTERFACE ---
st.title("🚀 SUPER TV GESTÃO DE CLIENTES")
st.image("https://i.imgur.com/CKq9BVx.png,width=250")

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["👥 Lista", "➕ Novo", "📢 DISPARO EM MASSA", "⚙️ Config"])

# --- TAB 3: DISPARO EM MASSA (A NOVIDADE) ---
with tab3:
    st.subheader("📢 Envio de Mensagens em Massa")
    st.info("Selecione os clientes abaixo e clique no botão para gerar os links de envio sequencial.")
    
    if not df.empty:
        clientes_cobranca = []
        # Filtrar apenas quem não está "Em dia"
        for idx, r in df.iterrows():
            status, msg, icon = obter_regua(r['vencimento'])
            if icon != "🟩":
                clientes_cobranca.append(r)
        
        if clientes_cobranca:
            df_cob = pd.DataFrame(clientes_cobranca)
            
            # Seleção de "Marcar Todos"
            selecionar_todos = st.checkbox("Selecionar Todos para Cobrança")
            
            selecionados = []
            for idx, r in df_cob.iterrows():
                status, msg, icon = obter_regua(r['vencimento'])
                # Cria um checkbox para cada cliente
                col_sel, col_info = st.columns([0.5, 9.5])
                with col_sel:
                    marcado = st.checkbox("", value=selecionar_todos, key=f"check_{r['id']}")
                    if marcado: selecionados.append(r)
                with col_info:
                    st.write(f"{icon} **{r['cliente']}** | {status} | {r['whatsapp']}")

            st.divider()
            if selecionados:
                st.warning(f"Você selecionou {len(selecionados)} clientes.")
                if st.button("🚀 GERAR LINKS DE ENVIO"):
                    for s in selecionados:
                        _, msg_final, _ = obter_regua(s['vencimento'])
                        link = f"https://wa.me/{s['whatsapp']}?text={urllib.parse.quote(msg_final)}"
                        st.link_button(f"Clique para enviar para: {s['cliente']}", link)
        else:
            st.success("Tudo em dia! Nenhum cliente precisando de cobrança no momento.")

# --- TAB 1: LISTA E RENOVAÇÃO RÁPIDA ---
with tab1:
    busca = st.text_input("🔍 Buscar...")
    servs_at = get_servidores()
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower():
                status, msg, icon = obter_regua(r['vencimento'])
                with st.expander(f"{icon} {r['cliente']} | {r['sistema']} | {status}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Dados:** `{r['usuario']}` / `{r['senha']}`")
                    c2.write(f"**WhatsApp:** {r['whatsapp']}")
                    c3.write(f"**Vencimento:** {r['vencimento']}")
                    
                    b1, b2, b3 = st.columns([1,1,2])
                    if b1.button("🗑️", key=f"d{r['id']}"):
                        c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                    if b3.button("♻️ Renovar +30 dias", key=f"r{r['id']}"):
                        nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=30)).date()
                        c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()

# --- TAB 2: NOVO CADASTRO ---
with tab2:
    with st.form("novo"):
        st.subheader("Cadastro Rápido")
        servs_at = get_servidores()
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome")
        w = c2.text_input("WhatsApp (Ex: 5511999999999)")
        c3, c4 = st.columns(2)
        sis = c3.radio("Sistema", ["IPTV", "P2P"], horizontal=True)
        srv = c4.selectbox("Servidor", servs_at)
        c5, c6, c7 = st.columns(3)
        u = c5.text_input("Usuário")
        s = c6.text_input("Senha")
        v = c7.date_input("Vencimento", value=datetime.now() + pd.Timedelta(days=30))
        if st.form_submit_button("CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (cliente, whatsapp, sistema, servidor, usuario, senha, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?,?)", (n, w, sis, srv, u, s, str(v), 0, 35))
            c.commit(); st.success("Cadastrado!"); st.rerun()

# --- TAB 4: CONFIGURAÇÕES ---
with tab4:
    st.subheader("🛠️ Servidores")
    ns = st.text_input("Novo Servidor")
    if st.button("Adicionar"):
        try:
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
        except: st.error("Já existe")
