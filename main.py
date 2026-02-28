import streamlit as st
import pandas as pd
import bcrypt
from streamlit_gsheets import GSheetsConnection

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# ---------------- FUNÇÕES ----------------

@st.cache_data(ttl=300)
def carregar_aba(nome_aba):
    try:
        df = conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
        if df is None or df.empty:
            return pd.DataFrame()
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar aba '{nome_aba}': {e}")
        return pd.DataFrame()


def verificar_senha(senha_digitada, hash_salvo):
    try:
        return bcrypt.checkpw(senha_digitada.encode(), hash_salvo.encode())
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


def formatar_real(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

            colunas = ["Email", "Senha", "Nome", "CPF", "Cidade"]
            if not all(c in df_user.columns for c in colunas):
                st.error("❌ Estrutura inválida da aba Base_Usuários")
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
            st.error(f"Dados incorretos. Tentativas restantes: {5 - st.session_state.tentativas_login}")

    st.stop()

# ---------------- COMPETÊNCIA ----------------
if not st.session_state.competencia_confirmada:

    st.title(f"Bem-vindo, {st.session_state.usuario_nome} 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")

    with st.container(border=True):
        st.markdown("### 📅 Selecione a competência para preenchimento")

        c1, c2 = st.columns(2)

        meses = [
            "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
        ]
        anos = [2024, 2025, 2026, 2027]

        mes = c1.selectbox("Mês", meses)
        ano = c2.selectbox("Ano", anos, index=2)

        if st.button("Confirmar Competência", use_container_width=True):
            st.session_state.mes_ativo = mes
            st.session_state.ano_ativo = ano
            st.session_state.competencia_confirmada = True
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title(st.session_state.usuario_cidade)
st.sidebar.info(f"Competência: {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# ---------------- CONFIGURAÇÕES ----------------
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

aliq_serv, aliq_patr_total, lei_ref = 0.0, 0.0, "Não cadastrada"

if not df_conf.empty:
    conf = df_conf[df_conf["Cidade"] == st.session_state.usuario_cidade]
    if not conf.empty:
        ref = conf.iloc[-1]
        aliq_serv = float(ref["Al_Servidor"]) / 100
        aliq_patr_total = (float(ref["Al_Patronal"]) + float(ref["Al_Suplementar"])) / 100
        lei_ref = ref["Lei_Referencia"]

# ---------------- LAYOUT ----------------
col_form, col_hist = st.columns([1, 1.2])

with col_form:

    st.subheader("📝 Lançamento Mensal")

    with st.container(border=True):

        # ---------- CENTRO DE CUSTO ----------
        df_cid_cad = df_cad[df_cad["Cidade"] == st.session_state.usuario_cidade] if not df_cad.empty else pd.DataFrame()
        centros = [""] + df_cid_cad["Nome_Centro"].tolist() if not df_cid_cad.empty else [""]

        centro_sel = st.selectbox("1. Centro de Custo", centros)
        novo_centro = st.text_input("➕ Ou digite novo centro")

        if novo_centro:
            centro_sel = novo_centro

        # ---------- SECRETARIA AUTOMÁTICA ----------
        if centro_sel and not df_cid_cad.empty:
            filtro = df_cid_cad[df_cid_cad["Nome_Centro"] == centro_sel]
            secretaria = filtro.iloc[0]["Secretaria"] if not filtro.empty else ""
        else:
            secretaria = ""

        st.text_input("2. Secretaria", value=secretaria, disabled=True)

        st.divider()

        # ---------- VALORES COM ESTADO ----------
        if "valor_bruto" not in st.session_state:
            st.session_state.valor_bruto = ""

        if "valor_base" not in st.session_state:
            st.session_state.valor_base = ""

        st.text_input(
            "3. Valor Bruto da Folha (R$)",
            key="valor_bruto",
            placeholder="Ex: 15000,00"
        )

        st.text_input(
            "4. Base de Contribuição (R$)",
            key="valor_base",
            placeholder="Ex: 12000,00"
        )

        v_bruto = moeda_para_float(st.session_state.valor_bruto)
        v_base = moeda_para_float(st.session_state.valor_base)

        valor_devido_servidor = v_base * aliq_serv
        valor_devido_patronal = v_base * aliq_patr_total

        # ---------- MEMÓRIA DE CÁLCULO ----------
        st.markdown(f"""
        <div style="background-color:#e8f4f8;padding:15px;border-radius:10px;border-left:5px solid #007bff;">
        <b>Lei:</b> {lei_ref}<br><br>
        <b>Servidor devido:</b> R$ {formatar_real(valor_devido_servidor)}<br>
        <b>Patronal devido:</b> R$ {formatar_real(valor_devido_patronal)}
        </div>
        """, unsafe_allow_html=True)

        # ---------- REPASSES ----------
        st.divider()
        st.subheader("Verificação de Repasse")

        houve_pag_serv = st.checkbox("Houve pagamento do Servidor?")
        if houve_pag_serv:
            r_serv = moeda_para_float(st.text_input("Valor Repassado Servidor"))
            dt_serv = st.date_input("Data Repasse Servidor", format="DD/MM/YYYY")
        else:
            r_serv, dt_serv = 0, None

        houve_pag_patr = st.checkbox("Houve pagamento Patronal?")
        if houve_pag_patr:
            r_patr = moeda_para_float(st.text_input("Valor Repassado Patronal"))
            dt_patr = st.date_input("Data Repasse Patronal", format="DD/MM/YYYY")
        else:
            r_patr, dt_patr = 0, None

        # ---------- DIFERENÇAS ----------
        if houve_pag_serv:
            dif_serv = valor_devido_servidor - r_serv
            if abs(dif_serv) > 0.01:
                st.warning(f"⚠ Diferença Servidor: R$ {formatar_real(dif_serv)}")

        if houve_pag_patr:
            dif_patr = valor_devido_patronal - r_patr
            if abs(dif_patr) > 0.01:
                st.warning(f"⚠ Diferença Patronal: R$ {formatar_real(dif_patr)}")

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento registrado (em breve salvará na planilha).")

with col_hist:
    st.button("FINALIZAR E ENVIAR MÊS", use_container_width=True)
    st.subheader(f"Conferência: {st.session_state.mes_ativo}")
    st.info("O histórico aparecerá aqui.")
