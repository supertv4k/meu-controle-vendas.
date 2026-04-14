import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="GESTÃO DE CLIENTES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { color: #00ff00; font-size: 24px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .stTabs [data-baseweb="tab"] { color: white; font-size: 18px; }
    /* Botão de excluir vermelho */
    div.stButton > button:first-child[key^="del"] {
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- EXIBIÇÃO DA LOGO ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image("https://i.imgur.com/CKq9BVx.png", width=200)

st.title("🚀 GESTÃO DE CLIENTES - SUPER TV")

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
def get_data():
    conn = sqlite3.connect('supertv_gestao.db')
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

df = get_data()

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
    busca = st.text_input("🔍 Buscar cliente por nome...")
    if not df.empty:
        for i, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower():
                status, _, icon = calcular_regua_cobranca(r['vencimento'])
                
                edit_key = f"edit_mode_{r['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                with st.expander(f"{icon} {r['cliente']} | {status}"):
                    if not st.session_state[edit_key]:
                        # MODO VISUALIZAÇÃO
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"**👤 Usuário:** {r['usuario']}")
                            st.write(f"**🔑 Senha:** {r['senha']}")
                        with c2:
                            st.write(f"**📞 WhatsApp:** {r['whatsapp']}")
                            st.write(f"**🖥️ Servidor:** {r['servidor']}")
                        with c3:
                            st.write(f"**📅 Vencimento:** {r['vencimento']}")
                            st.write(f"**💰 Valor:** R$ {r['mensalidade']:.2f}")
                        
                        st.divider()
                        col_btn1, col_btn2, _ = st.columns([1, 1, 3])
                        with col_btn1:
                            if st.button("📝 Editar", key=f"btn_ed_{r['id']}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col_btn2:
                            if st.button("🗑️ Excluir", key=f"del_{r['id']}"):
                                conn = sqlite3.connect('supertv_gestao.db')
                                conn.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                                conn.commit()
                                conn.close()
                                st.rerun()
                    else:
                        # MODO EDIÇÃO
                        with st.form(key=f"form_ed_{r['id']}"):
                            st.write(f"### Editando: {r['cliente']}")
                            new_nome = st.text_input("Nome do Cliente", value=r['cliente'])
                            
                            ce1, ce2, ce3 = st.columns(3)
                            new_user = ce1.text_input("Usuário", value=r['usuario'])
                            new_pass = ce2.text_input("Senha", value=r['senha'])
                            new_wpp = ce3.text_input("WhatsApp", value=r['whatsapp'])
                            
                            ce4, ce5, ce6 = st.columns(3)
                            venc_atual = datetime.strptime(str(r['vencimento']), '%Y-%m-%d').date()
                            new_venc = ce4.date_input("Vencimento", value=venc_atual)
                            new_custo = ce5.number_input("Custo", value=float(r['custo']))
                            new_mensal = ce6.number_input("Mensalidade", value=float(r['mensalidade']))
                            
                            new_serv = st.text_input("Servidor", value=r['servidor'])
                            
                            b_save, b_canc = st.columns(2)
                            if b_save.form_submit_button("💾 Salvar Alterações"):
                                conn = sqlite3.connect('supertv_gestao.db')
                                conn.execute("""UPDATE clientes SET 
                                             cliente=?, usuario=?, senha=?, vencimento=?, 
                                             whatsapp=?, custo=?, mensalidade=?, servidor=? 
                                             WHERE id=?""", 
                                             (new_nome, new_user, new_pass, str(new_venc), 
                                              new_wpp, new_custo, new_mensal, new_serv, r['id']))
                                conn.commit()
                                conn.close()
                                st.session_state[edit_key] = False
                                st.rerun()
                            
                            if b_canc.form_submit_button("❌ Cancelar"):
                                st.session_state[edit_key] = False
                                st.rerun()

with tab2:
    with st.form("cad_novo"):
        st.subheader("🆕 Cadastrar Novo Cliente")
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome")
        user = c2.text_input("Usuário")
        senha = c3.text_input("Senha")
        venc = c1.date_input("Vencimento")
        wpp = c2.text_input("WhatsApp (Ex: 5511999999999)")
        srv = c3.text_input("Servidor")
        v_custo = c1.number_input("Custo", value=0.0)
        v_mensal = c2.number_input("Mensalidade", value=0.0)
        if st.form_submit_button("CADASTRAR CLIENTE"):
            c = sqlite3.connect('supertv_gestao.db')
            c.execute("INSERT INTO clientes (servidor, cliente, usuario, senha, vencimento, custo, mensalidade, whatsapp) VALUES (?,?,?,?,?,?,?,?)", 
                     (srv, nome, user, senha, str(venc), v_custo, v_mensal, wpp))
            c.commit()
            c.close()
            st.success("Cliente cadastrado!")
            st.rerun()

with tab3:
    st.subheader("🚀 Régua de Cobrança WhatsApp")
    for i, r in df.iterrows():
        status, msg, icon = calcular_regua_cobranca(r['vencimento'])
        if icon != "🟩":
            link = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
            col_c1, col_c2 = st.columns([3, 1])
            col_c1.write(f"**{r['cliente']}** ({status})")
            col_c2.link_button(f"📲 Cobrar", link)

with tab4:
    st.header("📂 Ferramentas de Dados")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📥 Importar Excel/CSV")
        up = st.file_uploader("Selecione o arquivo", type=['csv', 'xlsx'])
        if up:
            try:
                df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                st.write("Dados detectados:")
                st.dataframe(df_up.head())
                if st.button("Confirmar Importação"):
                    # Aqui você pode adicionar a lógica de mapeamento se desejar
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_up.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close()
                    st.success("Dados importados!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    with col_b:
        st.subheader("📤 Backup")
        if not df.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Clientes')
            st.download_button(label="📥 Baixar Excel", data=buf.getvalue(), 
                               file_name="backup_clientes.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

