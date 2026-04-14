import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CLIENTES", layout="wide"

# Estilização Profissional
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    div[data-baseweb="radio"] > div { flex-direction: row !important; gap: 20px; }
    .stCheckbox { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS E MIGRAÇÃO ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    # Criar tabela com todos os campos necessários
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, whatsapp TEXT, 
                  usuario TEXT, senha TEXT, servidor TEXT, sistema TEXT, 
                  vencimento DATE, custo REAL, mensalidade REAL, observacao TEXT, logo BLOB)''')
    
    # Tabela de Servidores
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # Garantir que colunas novas existam (Migração)
    colunas_necessarias = [
        ("sistema", "TEXT DEFAULT 'IPTV'"),
        ("observacao", "TEXT"),
        ("logo", "BLOB")
    ]
    for col, tipo in colunas_necessarias:
        try:
            c.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except:
            pass

    # Inserção inicial de servidores se estiver vazio
    c.execute("SELECT COUNT(*) FROM lista_servidores")
    if c.fetchone()[0] == 0:
        servs = ["UNIPlAY", "MUNDOGF", "P2BRAZ", "PLAYTV", "P2CINE", "BLADETV", "SPEEDTV", "UNITV", "MEGATV", "BobPlayer", "IboPlayer", "IboPlayer pro"]
        for s in servs: c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (s,))
    
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE APOIO ---
def obter_regua(venc_data):
    hoje = datetime.now().date()
    pix = "62.326.879/0001-13"
    try:
        venc_data = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc_data - hoje).days
        
        if dias == 3:
            msg = f"Sua Assinatura Vence em  3️⃣ dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence em 3 dias", msg, "🟨", dias
        elif dias == 2:
            msg = f"Sua Assinatura Vence em 2️⃣ dias! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence em 2 dias", msg, "🟨", dias
        elif dias == 1:
            msg = f"Sua Assinatura Vence  1️⃣ Amanhã ! Faça Agora o pagamento pelo PIX e Fique tranquilo !\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence Amanhã", msg, "🟧", dias
        elif dias == 0:
            msg = f"Sua Assinatura Vence Hoje⏰ ! Faça Agora o pagamento pelo PIX e Já Já Estará Renovado mais 30 Dias!\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "Vence HOJE", msg, "🟥", dias
        elif dias < 0:
            msg = f"Sua Assinatura Venceu! Não se Preocupe é só Fazer o Pagamento que Renovamos mais 30 Dias pra Você!\n\nCopia e Cola no seu Banco!\n\n{pix}"
            return "VENCIDO", msg, "🚨", dias
        return f"{dias} dias restantes", "", "🟩", dias
    except: return "Erro", "", "❌", 0

def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista

# --- INTERFACE ---
st.image("https://i.imgur.com/CKq9BVx.png,width=250")
st.title("CLIENTES",layout=wide)

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

tab1, tab2, tab3, tab4 = st.tabs(["👥CLIENTES", "➕ADD CLIENTE", "🚨AVISO NO WHATHSAAP", "📡ADD SERVIDoR"])

# --- ABA 1: LISTA E RENOVAÇÃO ---
with tab1:
    busca = st.text_input("🔍 Buscar cliente...")
    servs_at = get_servidores()
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in str(r['nome']).lower():
                status, _, icon, _ = obter_regua(r['vencimento'])
                edit_key = f"ed_{r['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False

                with st.expander(f"{icon} {r['nome']} | {r['sistema']} | {status}"):
                    if not st.session_state[edit_key]:
                        c1, c2, c3 = st.columns([1, 2, 2])
                        with c1:
                            if r['logo']: st.image(r['logo'], width=100)
                            else: st.write("🚫 Sem Logo")
                        with c2:
                            st.write(f"**Dados:** `{r['usuario']}` / `{r['senha']}`")
                            st.write(f"**Vencimento:** {r['vencimento']}")
                            st.write(f"**WhatsApp:** {r['whatsapp']}")
                        with c3:
                            st.write(f"**Servidor:** {r['servidor']}")
                            st.write(f"**Obs:** {r['observacao']}")
                        
                        st.divider()
                        b1, b2, b3 = st.columns([1,1,2])
                        if b1.button("📝 Editar", key=f"be_{r['id']}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                        if b2.button("🗑️ Excluir", key=f"bd_{r['id']}"):
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM clientes WHERE id=?", (r['id'],)); c.commit(); st.rerun()
                        
                        d_add = b3.number_input("Dias", value=30, step=1, key=f"n{r['id']}")
                        if b3.button(f"🔄 Renovar +{d_add} dias", key=f"br_{r['id']}"):
                            nova = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=d_add)).date()
                            c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova), r['id'])); c.commit(); st.rerun()
                    else:
                        with st.form(f"fe_{r['id']}"):
                            up_l = st.file_uploader("Trocar Logo", type=['png', 'jpg'], key=f"ul_{r['id']}")
                            ed_n = st.text_input("Nome", value=r['nome'])
                            ce1, ce2 = st.columns(2); ed_u = ce1.text_input("User", value=r['usuario']); ed_p = ce2.text_input("Senha", value=r['senha'])
                            ce3, ce4 = st.columns(2); ed_s = ce3.radio("Sistema", ["IPTV", "P2P"], index=0 if r['sistema']=="IPTV" else 1, horizontal=True); ed_srv = ce4.selectbox("Servidor", servs_at, index=servs_at.index(r['servidor']) if r['servidor'] in servs_at else 0)
                            ed_v = st.date_input("Vencimento", value=datetime.strptime(str(r['vencimento']), '%Y-%m-%d').date())
                            ed_o = st.text_area("Observação", value=r['observacao'])
                            if st.form_submit_button("Salvar"):
                                l_b = up_l.read() if up_l else r['logo']
                                c = sqlite3.connect('supertv_gestao.db'); c.execute("UPDATE clientes SET nome=?, usuario=?, senha=?, sistema=?, servidor=?, vencimento=?, observacao=?, logo=? WHERE id=?", (ed_n, ed_u, ed_p, ed_s, ed_srv, str(ed_v), ed_o, l_b, r['id'])); c.commit(); st.session_state[edit_key] = False; st.rerun()

# --- ABA 2: NOVO CADASTRO (ORDEM SOLICITADA) ---
with tab2:
    with st.form("novo"):
        st.subheader("➕ Novo Cliente")
        # Ordem pedida: NOME, WHATSAPP, USUÁRIO, SENHA, SERVIDOR, SISTEMA, VENCIMENTO, CUSTO, MENSALIDADE, OBSERVAÇÃO
        n_c = st.text_input("NOME")
        w_c = st.text_input("WHATSAPP (Ex: 5511999999999)")
        c1, c2 = st.columns(2); u_c = c1.text_input("USUÁRIO"); s_c = c2.text_input("SENHA")
        c3, c4 = st.columns(2); srv_c = c3.selectbox("SERVIDOR", get_servidores()); sis_c = c4.radio("SISTEMA", ["IPTV", "P2P"], horizontal=True)
        v_c = st.date_input("VENCIMENTO", value=datetime.now() + pd.Timedelta(days=30))
        c5, c6 = st.columns(2); cu_c = c5.number_input("CUSTO (R$)", value=0.0); me_c = c6.number_input("MENSALIDADE (R$)", value=35.0)
        o_c = st.text_area("OBSERVAÇÃO")
        l_c = st.file_uploader("LOGO DO SERVIDOR (Opcional)", type=['png', 'jpg'])
        if st.form_submit_button("🚀 CADASTRAR"):
            lb = l_c.read() if l_c else None
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT INTO clientes (nome, whatsapp, usuario, senha, servidor, sistema, vencimento, custo, mensalidade, observacao, logo) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (n_c, w_c, u_c, s_c, srv_c, sis_c, str(v_c), cu_c, me_c, o_c, lb)); c.commit(); st.success("Cadastrado!"); st.rerun()

# --- ABA 3: DISPARO EM MASSA (FRASES DO GILMAR) ---
with tab3:
    st.subheader("📢 Cobrança Selecionada")
    if not df.empty:
        cobranca_list = []
        for _, r in df.iterrows():
            status, msg, icon, _ = obter_regua(r['vencimento'])
            if icon != "🟩": cobranca_list.append(r)
        
        if cobranca_list:
            sel_todos = st.checkbox("Marcar Todos")
            selecionados = []
            for r in cobranca_list:
                status, msg, icon, _ = obter_regua(r['vencimento'])
                col_sel, col_inf = st.columns([0.5, 9.5])
                with col_sel:
                    if st.checkbox("", value=sel_todos, key=f"chk_{r['id']}"): selecionados.append(r)
                with col_inf: st.write(f"{icon} **{r['nome']}** | {status} | {r['whatsapp']}")
            
            if selecionados and st.button("🔗 GERAR LINKS"):
                for s in selecionados:
                    _, msg_f, _, _ = obter_regua(s['vencimento'])
                    link = f"https://wa.me/{s['whatsapp']}?text={urllib.parse.quote(msg_f)}"
                    st.link_button(f"Enviar para: {s['nome']}", link)
        else: st.success("Ninguém para cobrar hoje!")

# --- ABA 4: CONFIGURAÇÕES E FINANCEIRO ---
with tab4:
    c_fin, c_srv = st.columns(2)
    with c_fin:
        st.subheader("⚖️ Financeiro")
        if not df.empty:
            st.metric("Lucro Estimado", f"R$ {df['mensalidade'].sum() - df['custo'].sum():.2f}")
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as wr: df.to_excel(wr, index=False)
            st.download_button("📥 Backup Excel", buf.getvalue(), "gestao.xlsx")
    with c_srv:
        st.subheader("📡 Servidores")
        ns = st.text_input("Novo Nome"); 
        if st.button("Add"): 
            c = sqlite3.connect('supertv_gestao.db'); c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (ns,)); c.commit(); st.rerun()
        rs = st.selectbox("Remover", get_servidores())
        if st.button("Remover"):
            c = sqlite3.connect('supertv_gestao.db'); c.execute("DELETE FROM lista_servidores WHERE nome=?", (rs,)); c.commit(); st.rerun()
