import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import base64
import io

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="GESTÃO DE CLIENTES", layout="wide")

# Estilização para modo escuro e botões destacados
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; background-color: #ff0000; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { color: white; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# --- EXIBIÇÃO DA LOGO NO TOPO ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image("https://i.imgur.com/CKq9BVx.png", width=200)

st.title(" GESTÃO DE CLIENTES")

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
        return "Vencido 🟥", f"Sua Assinatura Venceu! Não Se Preocupe, faça o Pagamento que logo será Liberado! PIX {pix}", "🟥"
    elif dias <= 5:
        msg = f"Sua Assinatura vence em {dias} dias! Renove Agora e Fique Tranquilo! PIX {pix}"
        return f"Vence em {dias} dias", msg, "🟨"
    return "Em dia 🟩", "", "🟩"

# --- CARREGAR DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- MÉTRICAS ---
if not df.empty:
    bruto = df['mensalidade'].sum()
    custo_total = df['custo'].sum()
    lucro = bruto - custo_total
    vencidos = len([i for i, r in df.iterrows() if calcular_regua_cobranca(r['vencimento'])[2] == "🟥"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clientes Ativos", len(df) - vencidos)
    m2.metric("Vencidos", vencidos)
    m3.metric("Faturamento Bruto", f"R$ {bruto:.2f}")
    m4.metric("Lucro Líquido", f"R$ {lucro:.2f}")

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 Clientes", "➕ Novo Cadastro", "📢 Cobrança", "📂 IMPORTAR / EXPORTAR"])

with tab1:
    busca = st.text_input("🔍 Buscar cliente...")
    if not df.empty:
        for i, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower():
                status, _, icon = calcular_regua_cobranca(r['vencimento'])
                with st.expander(f"{icon} {r['cliente']} | {status}"):
                    st.write(f"**User:** {r['usuario']} | **Senha:** {r['senha']}")
                    st.write(f"**WhatsApp:** {r['whatsapp']}")
                    if st.button("🗑️ Excluir", key=f"del{r['id']}"):
                        c = sqlite3.connect('supertv_gestao.db')
                        c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        c.commit()
                        st.rerun()

with tab2:
    with st.form("cad"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome")
        user = c2.text_input("Usuário")
        senha = c3.text_input("Senha")
        venc = c1.date_input("Vencimento")
        wpp = c2.text_input("WhatsApp (Ex: 5511999999999)")
        srv = c3.text_input("Servidor")
        v_custo = c1.number_input("Custo", value=0.0)
        v_mensal = c2.number_input("Mensalidade", value=0.0)
        if st.form_submit_button("CADASTRAR"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (servidor, cliente, usuario, senha, vencimento, custo, mensalidade, whatsapp) VALUES (?,?,?,?,?,?,?,?)", 
                     (srv, nome, user, senha, str(venc), v_custo, v_mensal, wpp))
            c.commit()
            st.rerun()

with tab3:
    st.subheader("🚀 Cobrança WhatsApp")
    for i, r in df.iterrows():
        status, msg, icon = calcular_regua_cobranca(r['vencimento'])
        if icon != "🟩":
            link = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
            st.link_button(f"📲 Enviar para {r['cliente']}", link)

with tab4:
    st.header("📂 Gerenciamento de Dados")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📥 Importar Lista")
        up = st.file_uploader("Subir arquivo Excel ou CSV", type=['csv', 'xlsx'])
        if up:
            try:
                # O motor 'openpyxl' será usado automaticamente para .xlsx se estiver no requirements.txt
                df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                
                # Mapeamento Inteligente: Identifica as colunas pelos sinônimos
                mapa = {
                    'cliente': ['nome', 'cliente', 'nome do cliente', 'usuario_nome'],
                    'usuario': ['user', 'usuario', 'login', 'usuário'],
                    'vencimento': ['vencimento', 'validade', 'venc', 'data_venc'],
                    'whatsapp': ['whatsapp', 'wpp', 'telefone', 'contato'],
                    'custo': ['custo', 'compra', 'valor_pago'],
                    'mensalidade': ['mensalidade', 'valor', 'venda', 'preço']
                }
                
                df_f = pd.DataFrame()
                for k, v in mapa.items():
                    for col_planilha in df_up.columns:
                        if col_planilha.lower().strip() in v:
                            df_f[k] = df_up[col_planilha]
                            break
                
                st.write("Prévia dos Dados Identificados:")
                st.dataframe(df_f.head())
                
                if st.button("🚀 Confirmar Importação"):
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_f.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close()
                    st.success(f"✅ {len(df_f)} clientes importados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

    with col_b:
        st.subheader("📤 Exportar Backup")
        if not df.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Clientes')
            
            st.download_button(
                label="📥 Baixar Planilha Excel",
                data=buf.getvalue(),
                file_name=f"backup_supertv_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
