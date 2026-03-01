import streamlit as st
import pandas as pd
import gspread
st.set_page_config(page_title="Helipe Gestão", layout="wide")
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. CONFIGURAÇÕES ---
ID_PLANILHA = "1vOjr5SnrTHHf6lV5pP73nyfl42QwWiahw25lvHFCKnw"

def connect_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    else:
        creds = Credentials.from_service_account_file("credenciais.json", scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(ID_PLANILHA)

# Função auxiliar para ler dados com segurança (Evita o erro de cabeçalho duplicado/vazio)
def get_data_safe(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        dados = ws.get_all_values()
        if not dados:
            return pd.DataFrame()
        df = pd.DataFrame(dados[1:], columns=dados[0])
        return df.loc[:, df.columns != ''] # Remove colunas sem nome
    except Exception as e:
        st.error(f"Erro ao ler aba {worksheet_name}: {e}")
        return pd.DataFrame()

# --- 2. CONEXÃO ---
sh = None 
try:
    sh = connect_sheets()
except Exception as e:
    st.error(f"Erro de conexão: {e}")

# --- 3. ESTILIZAÇÃO ---
st.markdown("""
    <style>
    /* Cores e Botões Padrão */
    .stApp { background-color: #FDFBF7; }
    [data-testid="stSidebar"] { background-color: #A3AD8B !important; }
    .stButton>button { background-color: #8B5A2B; color: white; border-radius: 6px; border: none; width: 100%; }
    
    /* Ajuste para telas pequenas (Celular) */
    @media (max-width: 640px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DO SISTEMA ---
if sh:
    if 'page' not in st.session_state: st.session_state.page = 'Dashboard'
    def navegar(p): st.session_state.page = p

    # Sidebar
    with st.sidebar:
        try: st.image("logo.png", width=150)
        except: st.title("HELIPE ATELIÊ")
        st.write("---")
        if st.button("📊 Dashboard"): navegar('Dashboard')
        if st.button("💰 Financeiro"): navegar('Financeiro')
        if st.button("📦 Estoque & Produção"): navegar('Estoque')
        if st.button("📋 Pedidos"): navegar('Pedidos')
        if st.button("🚚 Expedição"): navegar('Expedicao')
        st.write("---")
        if st.button("⬅ Voltar"): navegar('Dashboard')

    # --- TELAS ---

    if st.session_state.page == 'Dashboard':
        st.title("🌿 Painel de Controle Helipe")
        col1, col2, col3 = st.columns(3)
        col1.metric("Contas a Pagar", "R$ 450,00")
        col2.metric("Pedidos Pendentes", "8")
        col3.metric("Estoque Crítico", "Pinus 20mm")

        st.write("### Produção em Andamento")
        st.dataframe(get_data_safe("Producao_OP"))

    elif st.session_state.page == 'Financeiro':
        st.title("💰 Gestão Financeira")
        tab1, tab2, tab3 = st.tabs(["Contas a Pagar", "Contas a Receber", "Fluxo de Caixa"])

        with tab1:
            st.write("#### Registrar Conta a Pagar")
            with st.form("novo_pagar"):
                desc = st.text_input("Descrição da Despesa")
                val = st.number_input("Valor (R$)", min_value=0.0)
                venc = st.date_input("Vencimento")
                if st.form_submit_button("Salvar Conta"):
                    sh.worksheet("Financeiro_Pagar").append_row([desc, str(val), venc.strftime("%d/%m/%Y"), "Pendente"])
                    st.success("Salvo!")
                    st.rerun()
            
            st.write("---")
            st.dataframe(get_data_safe("Financeiro_Pagar"))

        with tab3:
            st.write("#### Histórico do Fluxo de Caixa")
            df_fluxo = get_data_safe("Fluxo_Caixa")
            st.dataframe(df_fluxo, use_container_width=True)
            
            st.write("---")
            st.write("#### Registrar Entrada/Saída Avulsa")
            with st.form("form_fluxo"):
                col_f1, col_f2 = st.columns(2)
                tipo = col_f1.selectbox("Tipo", ["Entrada", "Saída"])
                valor = col_f2.number_input("Valor R$", min_value=0.0)
                desc_f = st.text_input("Descrição")
                if st.form_submit_button("Lançar no Caixa"):
                    data_hoje = datetime.now().strftime("%d/%m/%Y")
                    ent = str(valor) if tipo == "Entrada" else ""
                    sai = str(valor) if tipo == "Saída" else ""
                    sh.worksheet("Fluxo_Caixa").append_row([data_hoje, tipo, desc_f, ent, sai, ""])
                    st.success("Lançado!")
                    st.rerun()

    elif st.session_state.page == 'Estoque':
        st.title("📦 Marcenaria - Estoque")
        cat = st.selectbox("Categoria", ["Estoque_MP", "Estoque_Pecas"])
        
        # Formulário para nova matéria prima
        with st.form("novo_estoque"):
            st.write(f"Adicionar item em {cat}")
            nome_item = st.text_input("Nome do Item")
            qtd_item = st.number_input("Quantidade Inicial", min_value=0)
            if st.form_submit_button("Adicionar"):
                sh.worksheet(cat).append_row([nome_item, str(qtd_item)])
                st.success("Item adicionado!")
                st.rerun()

        st.dataframe(get_data_safe(cat))

    elif st.session_state.page == 'Pedidos':
        st.title("📋 Pedidos")
        
        with st.form("novo_pedido"):
            st.write("Cadastrar Novo Pedido")
            c1, c2 = st.columns(2)
            num_p = c1.text_input("Nº Pedido")
            cli = c2.text_input("Cliente")
            prod = st.text_input("Produto")
            val_p = st.number_input("Valor Total", min_value=0.0)
            if st.form_submit_button("Cadastrar Pedido"):
                sh.worksheet("Pedidos").append_row([num_p, cli, prod, str(val_p), "Pendente", ""])
                st.success("Pedido Cadastrado!")
                st.rerun()

        df_pedidos = get_data_safe("Pedidos")
        st.dataframe(df_pedidos, use_container_width=True)

    elif st.session_state.page == 'Expedicao':
        st.title("🚚 Expedição e Logística")
        df_exp = get_data_safe("Expedicao")
        st.dataframe(df_exp, use_container_width=True)
