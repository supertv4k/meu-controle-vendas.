import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import base64
import io

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="GESTÃO DE CLIENTES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; background-color: #ff0000; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { color: white; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO NO TOPO ---
col_l, _ = st.columns([1, 4])
with col_l:
    st.image("https://i.imgur.com/CKq9BVx.png", width=500)

st.title("🎬 GESTÃO DE CLIENTES")

# ---BANCO DE DADOS ---
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

def calcular_regua_cobranca(venc_data):
    hoje = datetime.now().date()
    try:
        if isinstance(venc_data, str):
            venc_data = datetime.strptime(venc_data, '%Y-%m-%d').date()
        elif hasattr(venc_data, 'date'):
            venc_data = venc_data.date()
    except:
        return "Erro Data", "", "⚪"
    
    dias = (venc_data - hoje).days
    pix = "62.326.879/0001-13"
    
    if dias < 0:
        return "Vencido 🟥", f"Sua Assinatura Venceu! PIX {pix}", "🟥"
    elif dias <= 5:
        msg = f"Sua Assinatura vence em {dias} dias! Renove via PIX {pix}"
        return f"Vence em {dias} dias", msg, "🟨"
    return "Em dia 🟩", "", "🟩"

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 Lista de Clientes", "➕ Novo Cadastro", "📢 Cobrança WhatsApp", "📂 IMPORTAR / EXPORTAR"])

with tab1:
    busca = st.text_input("🔍 Pesquisar cliente...")
    if not df.empty:
        for i, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower():
                status, _, icon = calcular_regua_cobranca(r['vencimento'])
                with st.expander(f"{icon} {r['cliente']} | {status}"):
                    st.write(f"**Usuário:** {r['usuario']} | **Senha:** {r['senha']}")
                    if st.button("Excluir", key=f"del{r['id']}"):
                        c = sqlite3.connect('supertv_gestao.db')
                        c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        c.commit()
                        st.rerun()

with tab2:
    with st.form("cad"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome")
        u = c2.text_input("Usuário")
        v = c1.date_input("Vencimento")
        w = c2.text_input("WhatsApp (55...)")
        if st.form_submit_button("CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (cliente, usuario, vencimento, whatsapp) VALUES (?,?,?,?)", (n, u, str(v), w))
            c.commit()
            st.rerun()

with tab3:
    st.subheader("Envio de Cobrança")
    for i, r in df.iterrows():
        status, msg, icon = calcular_regua_cobranca(r['vencimento'])
        if icon != "🟩":
            link = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
            st.link_button(f"📲 Cobrar {r['cliente']}", link)

# --- AQUI ESTÃO OS BOTÕES QUE FALTAVAM ---
with tab4:
    st.header("📂 Gerenciamento de Arquivos")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📥 Importar Lista")
        st.write("Arraste sua planilha (Excel ou CSV) aqui.")
        up = st.file_uploader("Escolher arquivo", type=['csv', 'xlsx'])
        
        if up:
            df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            
            # Mapeamento Inteligente
            mapa = {
                'cliente': ['nome', 'cliente', 'usuario_nome'],
                'usuario': ['user', 'usuario', 'login'],
                'vencimento': ['vencimento', 'validade', 'venc'],
                'whatsapp': ['whatsapp', 'wpp', 'telefone']
            }
            
            df_f = pd.DataFrame()
            for k, v in mapa.items():
                for c in df_up.columns:
                    if c.lower().strip() in v:
                        df_f[k] = df_up[c]
                        break
            
            st.dataframe(df_f.head())
            if st.button("🚀 Confirmar Importação"):
                conn = sqlite3.connect('supertv_gestao.db')
                df_f.to_sql('clientes', conn, if_exists='append', index=False)
                conn.close()
                st.success("Clientes importados com sucesso!")
                st.rerun()

    with col_b:
        st.subheader("📤 Exportar Backup")
        st.write("Baixe sua lista atual para segurança.")
        if not df.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Clientes')
            
            st.download_button(
                label="📥 Baixar Planilha Excel",
                data=buf.getvalue(),
                file_name=f"backup_supertv_{datetime.now().strftime('%d_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

