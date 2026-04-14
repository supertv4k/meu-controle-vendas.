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
    .stButton>button { border-radius: 8px; }
    .status-vencido { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('super_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, servidor TEXT, img_servidor TEXT, 
                  cliente TEXT, usuario TEXT, senha TEXT, data_inicio DATE, 
                  vencimento DATE, custo REAL, mensalidade REAL, whatsapp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE LÓGICA ---
def calcular_mensagens(venc_data):
    hoje = datetime.now().date()
    if isinstance(venc_data, str):
        venc_data = datetime.strptime(venc_data, '%Y-%m-%d').date()
    
    dias = (venc_data - hoje).days
    pix = "62.326.879/0001-13"
    
    mensagens = {
        5: f"Sua Assinatura vai Vencer em 5 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        4: f"Sua Assinatura vai Vencer em 4 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        3: f"Sua Assinatura vai Vencer em 3 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        2: f"Sua Assinatura vai Vencer em 2 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        1: f"Sua Assinatura vence AMANHÃ! Não fique sem TV, Renove Agora! PIX {pix}",
        0: f"Sua Assinatura Vence HOJE! Não fique sem TV, Renove Agora! PIX {pix}",
    }
    
    if dias < 0:
        return "Vencido 🔴", f"Sua Assinatura Venceu! Não Se Preocupe, é só fazer o pagamento que logo estará Liberado! PIX {pix}", "🔴"
    elif dias in mensagens:
        status = "Vence Hoje 🟠" if dias == 0 else f"Vence em {dias} dias 🟡"
        return status, mensagens[dias], "🟠" if dias == 0 else "🟡"
    else:
        return "Em dia 🟢", "", "🟢"

def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.read()).decode()
    return None

# --- CARREGAR DADOS ---
conn = sqlite3.connect('super_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- DASHBOARD ---
st.title("📺 SUPERTV4K PRO - CONTROLE TOTAL")

if not df.empty:
    # Cálculos Financeiros
    bruto = df['mensalidade'].sum()
    custo_total = df['custo'].sum()
    liquido = bruto - custo_total
    
    # Status
    df['status_tuple'] = df['vencimento'].apply(calcular_mensagens)
    vencidos_count = len([x for x in df['status_tuple'] if x[2] == "🔴"])
    em_dia_count = len(df) - vencidos_count

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes Ativos", em_dia_count)
    c2.metric("Vencidos", vencidos_count, delta_color="inverse")
    c3.metric("Faturamento Bruto", f"R$ {bruto:.2f}")
    c4.metric("Lucro Líquido", f"R$ {liquido:.2f}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📋 Lista de Clientes", "➕ Novo Cadastro", "📢 Disparo em Massa"])

# --- TABELA DE CLIENTES ---
with tab1:
    busca = st.text_input("🔍 Buscar por nome ou usuário")
    if not df.empty:
        f_df = df[df['cliente'].str.contains(busca, case=False)] if busca else df
        
        for i, r in f_df.iterrows():
            status, msg_wpp, icon = calcular_mensagens(r['vencimento'])
            with st.expander(f"{icon} {r['cliente']} | Usuário: {r['usuario']} | {status}"):
                col_img, col_info, col_btns = st.columns([1, 2, 1])
                
                with col_img:
                    if r['img_servidor']:
                        st.image(f"data:image/png;base64,{r['img_servidor']}", width=120)
                    st.write(f"**Servidor:** {r['servidor']}")
                
                with col_info:
                    st.write(f"🔑 **Senha:** {r['senha']}")
                    st.write(f"📅 **Vencimento:** {r['vencimento']}")
                    st.write(f"💰 **Mensalidade:** R$ {r['mensalidade']:.2f} (Lucro: R$ {r['mensalidade']-r['custo']:.2f})")
                    st.write(f"📱 **WhatsApp:** {r['whatsapp']}")

                with col_btns:
                    nova_data = st.date_input("Nova Data", value=datetime.now().date() + timedelta(days=30), key=f"date_{r['id']}")
                    if st.button("🔄 Renovar", key=f"ren_{r['id']}"):
                        conn = sqlite3.connect('super_gestao.db')
                        c = conn.cursor()
                        c.execute("UPDATE clientes SET vencimento=? WHERE id=?", (nova_data, r['id']))
                        conn.commit()
                        st.rerun()
                    
                    if st.button("🗑️ Excluir", key=f"del_{r['id']}"):
                        conn = sqlite3.connect('super_gestao.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM clientes WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

# --- NOVO CADASTRO ---
with tab2:
    with st.form("cadastro"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Cliente")
        user = c2.text_input("Usuário")
        senha = c3.text_input("Senha")
        
        srv = c1.text_input("Nome do Servidor")
        upload_img = c2.file_uploader("Logo do Servidor", type=['png', 'jpg', 'jpeg'])
        wpp = c3.text_input("WhatsApp (Ex: 5511999999999)")
        
        ini = c1.date_input("Data de Início")
        venc = c2.date_input("Data de Vencimento")
        custo = c1.number_input("Custo do Crédito R$", format="%.2f")
        mensal = c2.number_input("Valor Cobrado R$", format="%.2f")
        
        if st.form_submit_button("🚀 Cadastrar Cliente"):
            img_b64 = image_to_base64(upload_img)
            conn = sqlite3.connect('super_gestao.db')
            c = conn.cursor()
            c.execute("""INSERT INTO clientes (servidor, img_servidor, cliente, usuario, senha, data_inicio, vencimento, custo, mensalidade, whatsapp) 
                         VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                      (srv, img_b64, nome, user, senha, ini, venc, custo, mensal, wpp))
            conn.commit()
            st.success("Cliente cadastrado com sucesso!")
            st.rerun()

# --- DISPARO EM MASSA ---
with tab3:
    st.subheader("📢 Selecione os clientes para cobrança")
    if not df.empty:
        # Criar checkbox de seleção
        df['enviar'] = False
        # Filtro rápido para quem está vencendo
        vencendo_hoje_ou_vencidos = [i for i, r in df.iterrows() if calcular_mensagens(r['vencimento'])[2] != "🟢"]
        
        edited_df = st.data_editor(
            df[['enviar', 'cliente', 'vencimento', 'whatsapp']],
            column_config={"enviar": st.column_config.CheckboxColumn("Enviar?", default=False)},
            disabled=["cliente", "vencimento", "whatsapp"],
            hide_index=True
        )
        
        if st.button("Gerar Links de Mensagens"):
            selecionados = edited_df[edited_df['enviar'] == True]
            if not selecionados.empty:
                for _, row in selecionados.iterrows():
                    # Puxa a mensagem correta baseada nos dias
                    status, msg, icon = calcular_mensagens(row['vencimento'])
                    msg_encoded = urllib.parse.quote(msg)
                    link = f"https://wa.me/{row['whatsapp']}?text={msg_encoded}"
                    st.link_button(f"Enviar para {row['cliente']} ({icon})", link)
            else:
                st.warning("Selecione pelo menos um cliente na tabela acima.")
