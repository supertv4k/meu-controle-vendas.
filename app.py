import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GESTÃO SUPER TV", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    div[data-baseweb="radio"] > div { flex-direction: row !important; gap: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('supertv_gestao.db')
    c = conn.cursor()
    # Tabela de Clientes
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, servidor TEXT, sistema TEXT, 
                  cliente TEXT, usuario TEXT, senha TEXT, vencimento DATE, 
                  custo REAL, mensalidade REAL, whatsapp TEXT)''')
    # Tabela de Servidores (Para ser editável)
    c.execute('''CREATE TABLE IF NOT EXISTS lista_servidores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # Inserção inicial dos seus servidores (apenas se a tabela estiver vazia)
    c.execute("SELECT COUNT(*) FROM lista_servidores")
    if c.fetchone()[0] == 0:
        servidores_iniciais = [
            "Uniplay", "Mundo GF", "P2Braz", "Play TV", "P2Cine", "Balde TV", 
            "Speed Tv", "Unitv", "Mega TV", "New Mais", "P2Imperial", "Seven", 
            "Zeus", "Ninety", "Alphaplay", "Genial", "RushPlay", "ClubTV", 
            "EasyPlay", "Horizon", "BobPlayer", "IboPlayer", "IboPlayer pro"
        ]
        for s in servidores_iniciais:
            c.execute("INSERT OR IGNORE INTO lista_servidores (nome) VALUES (?)", (s,))
    
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE DADOS ---
def get_servidores():
    conn = sqlite3.connect('supertv_gestao.db')
    lista = pd.read_sql_query("SELECT nome FROM lista_servidores ORDER BY nome", conn)['nome'].tolist()
    conn.close()
    return lista if lista else ["Padrão"]

def calcular_regua_cobranca(venc_data):
    hoje = datetime.now().date()
    try:
        venc_data = datetime.strptime(str(venc_data), '%Y-%m-%d').date() if isinstance(venc_data, str) else venc_data
        dias = (venc_data - hoje).days
        pix = "62.326.879/0001-13"
        if dias < 0: return "Vencido 🟥", f"Sua Assinatura Venceu! PIX {pix}", "🟥"
        if dias <= 5: return f"Vence em {dias} dias", f"Sua Assinatura vence em {dias} dias! PIX {pix}", "🟨"
        return "Em dia 🟩", "", "🟩"
    except: return "Erro Data", "", "⚪"

# --- INTERFACE ---
st.title("🚀 GESTÃO PROFISSIONAL - SUPER TV")

conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

tab1, tab2, tab3 = st.tabs(["👥 Lista de Clientes", "➕ Novo Cadastro", "⚙️ Configurações & Financeiro"])

# --- ABA 1: LISTA E EDIÇÃO ---
with tab1:
    busca = st.text_input("🔍 Buscar por nome...")
    servidores_atualizados = get_servidores()
    
    if not df.empty:
        for _, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower():
                status, _, icon = calcular_regua_cobranca(r['vencimento'])
                edit_key = f"edit_{r['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False

                with st.expander(f"{icon} {r['cliente']} | {r['sistema']} | {status}"):
                    if not st.session_state[edit_key]:
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"**User/Senha:** `{r['usuario']}` / `{r['senha']}`")
                        c1.write(f"**Servidor:** {r['servidor']}")
                        c2.write(f"**WhatsApp:** {r['whatsapp']}")
                        c2.write(f"**Vencimento:** {r['vencimento']}")
                        c3.write(f"**Mensalidade:** R$ {r['mensalidade']:.2f}")
                        
                        col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
                        if col_b1.button("📝 Editar", key=f"btn_e_{r['id']}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                        if col_b2.button("🗑️ Excluir", key=f"btn_d_{r['id']}"):
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                            c.commit()
                            st.rerun()
                        if col_b3.button("♻️ Renovar +30 dias", key=f"btn_r_{r['id']}"):
                            nova_data = (datetime.strptime(str(r['vencimento']), '%Y-%m-%d') + pd.Timedelta(days=30)).date()
                            c = sqlite3.connect('supertv_gestao.db')
                            c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova_data), r['id']))
                            c.commit()
                            st.success("Renovado!")
                            st.rerun()
                    else:
                        with st.form(f"f_ed_{r['id']}"):
                            new_nome = st.text_input("Nome", value=r['cliente'])
                            ce1, ce2 = st.columns(2)
                            new_sis = ce1.radio("Sistema", ["IPTV", "P2P"], index=0 if r['sistema']=="IPTV" else 1, horizontal=True)
                            # Usa a lista editável de servidores
                            new_srv = ce2.selectbox("Servidor", servidores_atualizados, 
                                                   index=servidores_atualizados.index(r['servidor']) if r['servidor'] in servidores_atualizados else 0)
                            
                            ce3, ce4, ce5 = st.columns(3)
                            new_user = ce3.text_input("User", value=r['usuario'])
                            new_pass = ce4.text_input("Senha", value=r['senha'])
                            new_wpp = ce5.text_input("WhatsApp", value=r['whatsapp'])
                            
                            if st.form_submit_button("Salvar Alterações"):
                                c = sqlite3.connect('supertv_gestao.db')
                                c.execute("UPDATE clientes SET cliente=?, sistema=?, servidor=?, usuario=?, senha=?, whatsapp=? WHERE id=?",
                                         (new_nome, new_sis, new_srv, new_user, new_pass, new_wpp, r['id']))
                                c.commit()
                                st.session_state[edit_key] = False
                                st.rerun()

# --- ABA 2: NOVO CADASTRO ---
with tab2:
    servidores_atualizados = get_servidores()
    with st.form("novo_cadastro"):
        st.subheader("Cadastro Rápido")
        f1, f2 = st.columns(2)
        nome_c = f1.text_input("Nome do Cliente")
        whatsapp_c = f2.text_input("WhatsApp (Ex: 5511999999999)")
        
        f3, f4 = st.columns(2)
        sistema_c = f3.radio("Sistema", ["IPTV", "P2P"], horizontal=True)
        servidor_c = f4.selectbox("Servidor", servidores_atualizados)
        
        f5, f6, f7 = st.columns(3)
        user_c = f5.text_input("Usuário")
        senha_c = f6.text_input("Senha")
        venc_c = f7.date_input("Vencimento", value=datetime.now() + pd.Timedelta(days=30))
        
        f8, f9 = st.columns(2)
        custo_c = f8.number_input("Custo (R$)", value=0.0)
        venda_c = f9.number_input("Venda (R$)", value=35.0)
        
        if st.form_submit_button("🚀 FINALIZAR CADASTRO"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (cliente, whatsapp, sistema, servidor, usuario, senha, vencimento, custo, mensalidade) VALUES (?,?,?,?,?,?,?,?,?)",
                     (nome_c, whatsapp_c, sistema_c, servidor_c, user_c, senha_c, str(venc_c), custo_c, venda_c))
            c.commit()
            st.success("Cadastrado!")
            st.rerun()

# --- ABA 3: CONFIGURAÇÕES E FINANCEIRO ---
with tab3:
    col_fin, col_conf = st.columns(2)
    
    with col_fin:
        st.subheader("📊 Financeiro")
        if not df.empty:
            lucro = df['mensalidade'].sum() - df['custo'].sum()
            st.metric("Lucro Mensal Estimado", f"R$ {lucro:.2f}")
            
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Backup Excel", buf.getvalue(), "backup_clientes.xlsx")

    with col_conf:
        st.subheader("🛠️ Gerenciar Servidores")
        novo_serv = st.text_input("Adicionar novo servidor:")
        if st.button("➕ Adicionar"):
            if novo_serv:
                try:
                    c = sqlite3.connect('supertv_gestao.db')
                    c.execute("INSERT INTO lista_servidores (nome) VALUES (?)", (novo_serv,))
                    c.commit()
                    st.success(f"{novo_serv} adicionado!")
                    st.rerun()
                except:
                    st.error("Servidor já existe.")
        
        st.divider()
        serv_para_apagar = st.selectbox("Remover servidor:", get_servidores())
        if st.button("🗑️ Remover"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("DELETE FROM lista_servidores WHERE nome=?", (serv_para_apagar,))
            c.commit()
            st.warning(f"{serv_para_apagar} removido!")
            st.rerun()
