import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import base64
import io

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SUPERTV4K - GESTÃO", layout="wide")
st.image_https://imgur.com/a/kwmTPvd
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
    try:
        if isinstance(venc_data, str):
            venc_data = datetime.strptime(venc_data, '%Y-%m-%d').date()
        elif isinstance(venc_data, datetime):
            venc_data = venc_data.date()
    except:
        return "Erro na Data", "", "⚪"
    
    dias = (venc_data - hoje).days
    pix = "62.326.879/0001-13"
    
    mensagens = {
        5: f"Sua Assinatura vai Vencer em 5 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        4: f"Sua Assinatura vai Vencer em 4 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        3: f"Sua Assinatura vai Vencer em 3 dias! Renove Agora e Fique Tranquilo! PIX {pix}",
        2: f"Sua Assinatura vai Vencer em 2 dias!",
        1: f"Sua Assinatura Vence Amanhã! Não fique sem TV. Renove Agora! PIX {pix}",
        0: f"Sua Assinatura Vence Hoje! Não fique sem TV. Renove Agora! PIX {pix}",
    }
    
    if dias < 0:
        return "Vencido 🟥", f"Sua Assinatura Venceu! Não Se Preocupe, faça o Pagamento que logo será Liberado! PIX {pix}", "🟥"
    elif dias in mensagens:
        return f"Vence em {dias} dias", mensagens[dias], "🟨" if dias > 1 else "🟧"
    return "Em dia 🟩", "", "🟩"

# --- CARREGAMENTO DE DADOS ---
conn = sqlite3.connect('supertv_gestao.db')
df = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# --- INTERFACE PRINCIPAL ---
st.image("https://i.imgur.com/CKq9BVx.png,width=500")
st.title("🎬 GESTÃO DE CLIENTES ")

if not df.empty:
    bruto = df['mensalidade'].sum()
    custo = df['custo'].sum()
    lucro = bruto - custo
    vencidos = len([i for i, r in df.iterrows() if calcular_regua_cobranca(r['vencimento'])[2] == "🟥"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clientes Ativos", len(df) - vencidos)
    m2.metric("Vencidos", vencidos)
    m3.metric("Faturamento Bruto", f"R$ {bruto:.2f}")
    m4.metric("Lucro Líquido", f"R$ {lucro:.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["👥 Clientes", "➕ Novo Cadastro", "📢 Cobrança em Massa", "📂 Importar/Exportar"])

with tab2:
    with st.form("cadastro"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Cliente")
        user = c2.text_input("Usuário")
        senha = c3.text_input("Senha")
        srv = c1.text_input("Servidor")
        wpp = c2.text_input("WhatsApp (Ex: 5511999999999)")
        venc = c3.date_input("Vencimento")
        v_custo = c1.number_input("Custo Crédito", value=0.0)
        v_mensal = c2.number_input("Mensalidade", value=0.0)
        img = c3.file_uploader("Logo Servidor", type=['png', 'jpg'])
        
        if st.form_submit_button("CADASTRAR"):
            b64 = img_to_b64(img)
            conn = sqlite3.connect('supertv_gestao.db')
            conn.execute("INSERT INTO clientes (servidor, img_servidor, cliente, usuario, senha, vencimento, custo, mensalidade, whatsapp) VALUES (?,?,?,?,?,?,?,?,?)",
                         (srv, b64, nome, user, senha, str(venc), v_custo, v_mensal, wpp))
            conn.commit()
            st.success("Cliente cadastrado com sucesso!")
            st.rerun()

with tab1:
    busca = st.text_input("🔍 Buscar por nome ou usuário...")
    if not df.empty:
        for i, r in df.iterrows():
            if busca.lower() in str(r['cliente']).lower() or busca.lower() in str(r['usuario']).lower():
                status, msg, icon = calcular_regua_cobranca(r['vencimento'])
                with st.expander(f"{icon} {r['cliente']} | Status: {status}"):
                    c_img, c_txt, c_act = st.columns([1, 2, 1])
                    if r['img_servidor']: 
                        c_img.image(f"data:image/png;base64,{r['img_servidor']}", width=80)
                    else:
                        c_img.write("📺")
                    
                    c_txt.write(f"**User:** {r['usuario']} | **Senha:** {r['senha']}")
                    c_txt.write(f"**WhatsApp:** {r['whatsapp']}")
                    c_txt.write(f"**Vencimento:** {r['vencimento']}")
                    
                    nova_data = c_act.date_input("Renovar para:", value=datetime.now().date()+timedelta(days=30), key=f"d{r['id']}")
                    if c_act.button("🔄 Renovar", key=f"r{r['id']}"):
                        conn = sqlite3.connect('supertv_gestao.db')
                        conn.execute("UPDATE clientes SET vencimento=? WHERE id=?", (str(nova_data), r['id']))
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
        if icon != "🟩": cobrar.append({"cliente": r['cliente'], "wpp": r['whatsapp'], "msg": msg})
    
    if cobrar:
        st.write(f"Total de avisos para hoje: {len(cobrar)}")
        for item in cobrar:
            link = f"https://wa.me/{item['wpp']}?text={urllib.parse.quote(item['msg'])}"
            st.link_button(f"📲 Enviar para {item['cliente']}", link)
    else:
        st.success("Nenhum cliente vencendo nos próximos 5 dias!")

# --- ABA 4: IMPORTAÇÃO E EXPORTAÇÃO INTELIGENTE ---
with tab4:
    st.header("📂 Gerenciar Dados em Massa")
    
    col_imp, col_exp = st.columns(2)
    
    with col_imp:
        st.subheader("📥 Importar Lista")
        st.write("O sistema identifica as colunas automaticamente (mesmo em ordens diferentes).")
        file_upload = st.file_uploader("Subir arquivo Excel ou CSV", type=['csv', 'xlsx'])
        
        if file_upload:
            if file_upload.name.endswith('.csv'):
                df_imp = pd.read_csv(file_upload)
            else:
                df_imp = pd.read_excel(file_upload)
            
            # DICIONÁRIO DE MAPEAMENTO (Sinônimos)
            mapeamento = {
                'cliente': ['nome', 'cliente', 'nome do cliente', 'nome_cliente', 'pax'],
                'usuario': ['user', 'usuario', 'login', 'usuário', 'username'],
                'senha': ['pass', 'password', 'senha', 'key', 'pw'],
                'servidor': ['srv', 'servidor', 'painel', 'server', 'fonte'],
                'vencimento': ['vencimento', 'data_venc', 'venc', 'validade', 'expira'],
                'whatsapp': ['whatsapp', 'wpp', 'celular', 'tel', 'telefone', 'contato'],
                'custo': ['custo', 'valor_pago', 'custo_credito', 'compra'],
                'mensalidade': ['mensalidade', 'valor_cobrado', 'preco', 'preço', 'venda']
            }

            df_final = pd.DataFrame()
            colunas_encontradas = [c.lower().strip() for c in df_imp.columns]
            
            # Tenta encontrar cada campo do banco nas colunas do arquivo
            for campo_db, sinonimos in mapeamento.items():
                achou = False
                for col_arquivo in df_imp.columns:
                    if col_arquivo.lower().strip() in sinonimos:
                        df_final[campo_db] = df_imp[col_arquivo]
                        achou = True
                        break
                if not achou:
                    df_final[campo_db] = None # Se não achar, cria a coluna vazia

            st.write("### Prévia da Organização:")
            st.dataframe(df_final.head())
            
            if st.button("Confirmar Importação"):
                try:
                    # Garantir que a data esteja no formato texto ISO para o banco
                    if 'vencimento' in df_final.columns:
                        df_final['vencimento'] = pd.to_datetime(df_final['vencimento']).dt.strftime('%Y-%m-%d')
                    
                    conn = sqlite3.connect('supertv_gestao.db')
                    df_final.to_sql('clientes', conn, if_exists='append', index=False)
                    conn.close()
                    st.success(f"✅ {len(df_final)} Clientes importados com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

    with col_exp:
        st.subheader("📤 Exportar para Backup")
        if not df.empty:
            # Exportar Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Clientes')
            
            st.download_button(
                label="📥 Baixar Tudo em Excel",
                data=buffer.getvalue(),
                file_name=f"backup_gestao_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Exportar JSON (mais seguro para sistema)
            json_data = df.to_json(orient='records', indent=4)
            st.download_button(
                label="📥 Baixar Tudo em JSON",
                data=json_data,
                file_name="backup_dados.json",
                mime="application/json"
            )
