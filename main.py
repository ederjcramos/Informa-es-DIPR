import streamlit as st
import pandas as pd
import bcrypt
from streamlit_gsheets import GSheetsConnection

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=1415303845#gid=1415303845"

# ---------------- FUNÇÕES ----------------

@st.cache_data(ttl=300)
def carregar_aba(nome_aba):
    try:
        df = conn.read(spreadsheet=url_planilha, worksheet=nome_aba)

        if df is None or df.empty:
            return pd.DataFrame()

        # limpar nomes das colunas
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(" ", "")
        df.columns = df.columns.str.replace("-", "")
        df.columns = df.columns.str.lower()

        # padronizar nomes internos
        df = df.rename(columns={
            "email": "Email",
            "senha": "Senha",
            "nome": "Nome",
            "cpf": "CPF",
            "cidade": "Cidade"
        })

        return df

    except Exception as e:
        st.error(f"Erro ao carregar aba '{nome_aba}': {e}")
        return pd.DataFrame()


def verificar_senha(senha_digitada, hash_salvo):
    try:
        return bcrypt.checkpw(
            senha_digitada.encode(),
            hash_salvo.encode()
        )
    except:
        return False


def moeda_para_float(valor):
    if not valor:
        return 0.0
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0


# ---------------- SESSION STATE ----------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "competencia_confirmada" not in st.session_state:
    st.session_state.competencia_confirmada = False

if "tentativas_login" not in st.session_state:
    st.session_state.tentativas_login = 0

# ---------------- LOGIN ----------------
if not st.session_state.logado:

    st.title("🔐 Acesso ao Sistema DIPR")

    if st.session_state.tentativas_login >= 5:
        st.error("🚫 Acesso bloqueado. Contate o responsável para liberação.")
        st.stop()

    with st.form("login_form"):
        u_email = st.text_input("E-mail Institucional").strip()
        u_senha = st.text_input("Senha", type="password")

        if st.form_submit_button("Entrar no Sistema"):

            df_user = carregar_aba("Base_Usuários")

            colunas_necessarias = ["Email", "Senha", "Nome", "CPF", "Cidade"]

            if not all(col in df_user.columns for col in colunas_necessarias):
                st.error("❌ Estrutura da planilha Base_Usuários inválida.")
                st.write("Colunas encontradas:", df_user.columns.tolist())
                st.stop()

            user_match = df_user[df_user["Email"].str.lower() == u_email.lower()]

            if not user_match.empty:
                hash_salvo = user_match.iloc[0]["Senha"]

                if verificar_senha(u_senha, hash_salvo):
                    st.session_state.logado = True
                    st.session_state.tentativas_login = 0
                    st.session_state.usuario_nome = user_match.iloc[0]["Nome"]
                    st.session_state.usuario_cpf = user_match.iloc[0]["CPF"]
                    st.session_state.usuario_cidade = user_match.iloc[0]["Cidade"]
                    st.rerun()

            st.session_state.tentativas_login += 1
            restantes = 5 - st.session_state.tentativas_login
            st.error(f"Dados incorretos. Tentativas restantes: {restantes}")

    st.stop()

# ---------------- SELEÇÃO COMPETÊNCIA ----------------
if not st.session_state.competencia_confirmada:

    st.title(f"Bem-vindo, {st.session_state.usuario_nome} 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")

    with st.container(border=True):
        st.markdown("### 📅 Selecione a competência para preenchimento:")

        c1, c2 = st.columns(2)

        lista_meses = [
            "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
        ]

        lista_anos = [2024, 2025, 2026, 2027]

        mes_escolhido = c1.selectbox("Mês", lista_meses)
        ano_escolhido = c2.selectbox("Ano", lista_anos, index=2)

        if st.button("🚀 Confirmar Competência", use_container_width=True):
            st.session_state.mes_ativo = mes_escolhido
            st.session_state.ano_ativo = ano_escolhido
            st.session_state.competencia_confirmada = True
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(
    f"📅 **Competência:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}"
)

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# ---------------- CARREGAR CONFIGURAÇÕES ----------------
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

aliq_serv, aliq_patr_total, lei_ref = 0.11, 0.22, "Não cadastrada"

if not df_conf.empty and "Cidade" in df_conf.columns:
    conf_cid = df_conf[df_conf["Cidade"] == st.session_state.usuario_cidade]
    if not conf_cid.empty:
        ref = conf_cid.iloc[-1]
        aliq_serv = float(ref["Al_Servidor"]) / 100
        aliq_patr_total = (float(ref["Al_Patronal"]) + float(ref["Al_Suplementar"])) / 100
        lei_ref = ref["Lei_Referencia"]

# ---------------- LAYOUT ----------------
col_form, col_hist = st.columns([1, 1.2])

with col_form:

    st.subheader("📝 Lançamento Mensal")

    with st.container(border=True):

        df_cid_cad = (
            df_cad[df_cad["Cidade"] == st.session_state.usuario_cidade]
            if not df_cad.empty and "Cidade" in df_cad.columns
            else pd.DataFrame()
        )

        centros = [""] + df_cid_cad["Nome_Centro"].tolist() if not df_cid_cad.empty else [""]

        centro_sel = st.selectbox("1. Centro de Custo", centros)

        novo_centro = st.text_input("➕ Ou digite um novo centro de custo")

        if novo_centro:
            centro_sel = novo_centro

        st.text_input("Centro selecionado", value=centro_sel, disabled=True)

        st.divider()

        v_bruto_txt = st.text_input("3. Valor Bruto (R$)", placeholder="0,00")
        v_base_txt = st.text_input("4. Base de Contribuição (R$)", placeholder="0,00")

        v_bruto = moeda_para_float(v_bruto_txt)
        v_base = moeda_para_float(v_base_txt)

        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left:5px solid #007bff;">
            <p>⚖️ <b>Devido (Lei: {lei_ref})</b></p>
            <h4>Servidor: R$ {v_base * aliq_serv:,.2f}</h4>
            <h4>Patronal: R$ {v_base * aliq_patr_total:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento processado!")

with col_hist:
    st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True)
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    st.info("O histórico aparecerá aqui.")import streamlit as st
import pandas as pd
import bcrypt
from streamlit_gsheets import GSheetsConnection

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=1415303845#gid=1415303845"

# ---------------- FUNÇÕES ----------------

@st.cache_data(ttl=300)
def carregar_aba(nome_aba):
    try:
        df = conn.read(spreadsheet=url_planilha, worksheet=nome_aba)

        if df is None or df.empty:
            return pd.DataFrame()

        # limpar nomes das colunas
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(" ", "")
        df.columns = df.columns.str.replace("-", "")
        df.columns = df.columns.str.lower()

        # padronizar nomes internos
        df = df.rename(columns={
            "email": "Email",
            "senha": "Senha",
            "nome": "Nome",
            "cpf": "CPF",
            "cidade": "Cidade"
        })

        return df

    except Exception as e:
        st.error(f"Erro ao carregar aba '{nome_aba}': {e}")
        return pd.DataFrame()


def verificar_senha(senha_digitada, hash_salvo):
    try:
        return bcrypt.checkpw(
            senha_digitada.encode(),
            hash_salvo.encode()
        )
    except:
        return False


def moeda_para_float(valor):
    if not valor:
        return 0.0
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0


# ---------------- SESSION STATE ----------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "competencia_confirmada" not in st.session_state:
    st.session_state.competencia_confirmada = False

if "tentativas_login" not in st.session_state:
    st.session_state.tentativas_login = 0

# ---------------- LOGIN ----------------
if not st.session_state.logado:

    st.title("🔐 Acesso ao Sistema DIPR")

    if st.session_state.tentativas_login >= 5:
        st.error("🚫 Acesso bloqueado. Contate o responsável para liberação.")
        st.stop()

    with st.form("login_form"):
        u_email = st.text_input("E-mail Institucional").strip()
        u_senha = st.text_input("Senha", type="password")

        if st.form_submit_button("Entrar no Sistema"):

            df_user = carregar_aba("Base_Usuários")

            colunas_necessarias = ["Email", "Senha", "Nome", "CPF", "Cidade"]

            if not all(col in df_user.columns for col in colunas_necessarias):
                st.error("❌ Estrutura da planilha Base_Usuários inválida.")
                st.write("Colunas encontradas:", df_user.columns.tolist())
                st.stop()

            user_match = df_user[df_user["Email"].str.lower() == u_email.lower()]

            if not user_match.empty:
                hash_salvo = user_match.iloc[0]["Senha"]

                if verificar_senha(u_senha, hash_salvo):
                    st.session_state.logado = True
                    st.session_state.tentativas_login = 0
                    st.session_state.usuario_nome = user_match.iloc[0]["Nome"]
                    st.session_state.usuario_cpf = user_match.iloc[0]["CPF"]
                    st.session_state.usuario_cidade = user_match.iloc[0]["Cidade"]
                    st.rerun()

            st.session_state.tentativas_login += 1
            restantes = 5 - st.session_state.tentativas_login
            st.error(f"Dados incorretos. Tentativas restantes: {restantes}")

    st.stop()

# ---------------- SELEÇÃO COMPETÊNCIA ----------------
if not st.session_state.competencia_confirmada:

    st.title(f"Bem-vindo, {st.session_state.usuario_nome} 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")

    with st.container(border=True):
        st.markdown("### 📅 Selecione a competência para preenchimento:")

        c1, c2 = st.columns(2)

        lista_meses = [
            "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
        ]

        lista_anos = [2024, 2025, 2026, 2027]

        mes_escolhido = c1.selectbox("Mês", lista_meses)
        ano_escolhido = c2.selectbox("Ano", lista_anos, index=2)

        if st.button("🚀 Confirmar Competência", use_container_width=True):
            st.session_state.mes_ativo = mes_escolhido
            st.session_state.ano_ativo = ano_escolhido
            st.session_state.competencia_confirmada = True
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(
    f"📅 **Competência:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}"
)

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# ---------------- CARREGAR CONFIGURAÇÕES ----------------
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

aliq_serv, aliq_patr_total, lei_ref = 0.11, 0.22, "Não cadastrada"

if not df_conf.empty and "Cidade" in df_conf.columns:
    conf_cid = df_conf[df_conf["Cidade"] == st.session_state.usuario_cidade]
    if not conf_cid.empty:
        ref = conf_cid.iloc[-1]
        aliq_serv = float(ref["Al_Servidor"]) / 100
        aliq_patr_total = (float(ref["Al_Patronal"]) + float(ref["Al_Suplementar"])) / 100
        lei_ref = ref["Lei_Referencia"]

# ---------------- LAYOUT ----------------
col_form, col_hist = st.columns([1, 1.2])

with col_form:

    st.subheader("📝 Lançamento Mensal")

    with st.container(border=True):

        df_cid_cad = (
            df_cad[df_cad["Cidade"] == st.session_state.usuario_cidade]
            if not df_cad.empty and "Cidade" in df_cad.columns
            else pd.DataFrame()
        )

        centros = [""] + df_cid_cad["Nome_Centro"].tolist() if not df_cid_cad.empty else [""]

        centro_sel = st.selectbox("1. Centro de Custo", centros)

        novo_centro = st.text_input("➕ Ou digite um novo centro de custo")

        if novo_centro:
            centro_sel = novo_centro

        st.text_input("Centro selecionado", value=centro_sel, disabled=True)

        st.divider()

        v_bruto_txt = st.text_input("3. Valor Bruto (R$)", placeholder="0,00")
        v_base_txt = st.text_input("4. Base de Contribuição (R$)", placeholder="0,00")

        v_bruto = moeda_para_float(v_bruto_txt)
        v_base = moeda_para_float(v_base_txt)

        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left:5px solid #007bff;">
            <p>⚖️ <b>Devido (Lei: {lei_ref})</b></p>
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
