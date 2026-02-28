import streamlit as st
import pandas as pd
import bcrypt
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=1216958417#gid=1216958417"

# --- FUNÇÕES DE APOIO ---
@st.cache_data(ttl=300)
def carregar_aba(nome_aba):
    try:
        df = conn.read(spreadsheet=url_planilha, worksheet=nome_aba)

        # Se não carregou nada
        if df is None or df.empty:
            return pd.DataFrame()

        # Remove espaços invisíveis nos nomes das colunas
        df.columns = df.columns.str.strip()

        # Padroniza nomes das colunas automaticamente
        df.columns = df.columns.str.replace(" ", "")
        df.columns = df.columns.str.replace("-", "")
        df.columns = df.columns.str.lower()

        # Renomeia para padrão interno do sistema
        df = df.rename(columns={
            "email": "Email",
            "senha": "Senha",
            "nome": "Nome",
            "cpf": "CPF",
            "cidade": "Cidade"
        })

        return df

    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return pd.DataFrame()

# --- SEGURANÇA SENHA ---
def verificar_senha(senha_digitada, senha_hash):
    try:
        return bcrypt.checkpw(
            senha_digitada.encode(),
            senha_hash.encode()
        )
    except:
        return False

# --- ESTADO DA SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'competencia_confirmada' not in st.session_state:
    st.session_state.competencia_confirmada = False

if 'tentativas_login' not in st.session_state:
    st.session_state.tentativas_login = 0

if 'bloqueado' not in st.session_state:
    st.session_state.bloqueado = False


# =============================
# TELA 01 — LOGIN
# =============================
if not st.session_state.logado:

    st.title("🔐 Acesso ao Sistema DIPR")

    if st.session_state.bloqueado:
        st.error("""
        🚫 **Acesso bloqueado por excesso de tentativas.**

        Por favor, contate o responsável pelo sistema para liberação do acesso.
        """)
        st.stop()

    with st.form("login_form"):

        u_email = st.text_input("E-mail Institucional").strip()
        u_senha = st.text_input("Senha", type="password")

        if st.form_submit_button("Entrar no Sistema"):

            df_user = carregar_aba("Base_Usuários")

            if not df_user.empty:

                # procura usuário só por email
                user_match = df_user[
                    df_user['Email'].str.lower() == u_email.lower()
                ]

                if not user_match.empty:

                    senha_hash = str(user_match.iloc[0]['Senha'])

                    if verificar_senha(u_senha, senha_hash):

                        # LOGIN OK
                        st.session_state.logado = True
                        st.session_state.tentativas_login = 0

                        st.session_state.usuario_nome = user_match.iloc[0]['Nome']
                        st.session_state.usuario_cpf = user_match.iloc[0]['CPF']
                        st.session_state.usuario_cidade = user_match.iloc[0]['Cidade']

                        st.rerun()

                    else:
                        st.session_state.tentativas_login += 1

                        if st.session_state.tentativas_login >= 5:
                            st.session_state.bloqueado = True
                            st.rerun()

                        st.error(
                            f"⚠️ Senha incorreta. Tentativas restantes: {5 - st.session_state.tentativas_login}"
                        )

                else:
                    st.error("⚠️ Usuário não encontrado.")

            else:
                st.error("❌ Erro de conexão com a planilha.")

    st.stop()


# =============================
# TELA 02 — COMPETÊNCIA
# =============================
if not st.session_state.competencia_confirmada:

    st.title(f"Bem-vindo, {st.session_state.usuario_nome}! 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")

    with st.container(border=True):

        st.markdown("### Selecione a competência para preenchimento:")
        c1, c2 = st.columns(2)

        lista_meses = [
            "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
        ]

        lista_anos = [2024, 2025, 2026, 2027]

        mes_escolhido = c1.selectbox("Mês de Referência", lista_meses)
        ano_escolhido = c2.selectbox("Ano", lista_anos, index=2)

        if st.button("🚀 Confirmar Competência", use_container_width=True):
            st.session_state.mes_ativo = mes_escolhido
            st.session_state.ano_ativo = ano_escolhido
            st.session_state.competencia_confirmada = True
            st.rerun()

    st.stop()


# =============================
# TELA 03 — PAINEL
# =============================
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(
    f"👤 {st.session_state.usuario_nome}\n\n📅 {st.session_state.mes_ativo}/{st.session_state.ano_ativo}"
)

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Carregar dados
df_conf = carregar_aba("Configuracoes") 
st.write("Teste Configuracoes:", df_conf)

df_cad = carregar_aba("Cadastros_Fixos")

aliq_serv, aliq_patr_total, lei_ref = 0.11, 0.22, "Não cadastrada"

if not df_conf.empty:
    conf_cid = df_conf[df_conf['Cidade'] == st.session_state.usuario_cidade]
    if not conf_cid.empty:
        ref = conf_cid.iloc[-1]
        aliq_serv = float(ref['Al_Servidor']) / 100
        aliq_patr_total = (
            float(ref['Al_Patronal']) + float(ref['Al_Suplementar'])
        ) / 100
        lei_ref = ref['Lei_Referencia']

col_form, col_hist = st.columns([1, 1.2])

with col_form:
    st.subheader("📝 Lançamento Mensal")

    with st.container(border=True):

        df_cid_cad = df_cad[df_cad['Cidade'] == st.session_state.usuario_cidade] if not df_cad.empty else pd.DataFrame()
        centros = [""] + df_cid_cad['Nome_Centro'].tolist() if not df_cad.empty else [""]

        centro_sel = st.selectbox(
    "1. Centro de Custo",
    centros,
    key="centro_principal"
)

novo_centro = st.text_input("➕ Ou digite um novo centro de custo")

if novo_centro:
    centro_sel = novo_centro

        if centro_sel != "":
            filtro_sec = df_cid_cad[df_cid_cad['Nome_Centro'] == centro_sel]['Secretaria']
            sec_vinculada = filtro_sec.iloc[0] if not filtro_sec.empty else ""
            st.text_input("2. Secretaria", value=sec_vinculada, disabled=True)
        else:
            st.text_input("2. Secretaria", value="", disabled=True)

        st.divider()

        v_bruto = st.number_input("3. Valor Bruto (R$)", min_value=0.0, step=0.01, format="%.2f")
        v_base = st.number_input("4. Base Cálculo (R$)", min_value=0.0, step=0.01, format="%.2f")

        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #007bff;">
            <p style="margin:0;">⚖️ <b>Devido (Lei: {lei_ref}):</b></p>
            <h4>Servidor: R$ {v_base * aliq_serv:,.2f}</h4>
            <h4>Patronal: R$ {v_base * aliq_patr_total:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento processado!")

with col_hist:
    st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True)
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    st.info("O histórico aparecerá aqui.")
