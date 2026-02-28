import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets (Link da sua planilha)
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# --- FUNÇÕES DE APOIO ---
def carregar_aba(nome_aba):
    try:
        return conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
    except Exception:
        return pd.DataFrame()

# --- ESTADO DA SESSÃO (SESSION STATE) ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False
if 'competencia_confirmada' not in st.session_state: 
    st.session_state.competencia_confirmada = False

# --- TELA 01: LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema DIPR")
    with st.form("login_form"):
        u_email = st.text_input("E-mail Institucional").strip()
        u_senha = st.text_input("Senha", type="password")
        u_cpf = st.text_input("CPF (Apenas números)").strip()
        
        if st.form_submit_button("Entrar no Sistema"):
            df_user = carregar_aba("Base_Usuários")
            if not df_user.empty:
                u_cpf_limpo = u_cpf.replace('.', '').replace('-', '')
                
                # Validação de login com tratamento de CPF e fechamento de parênteses correto
                user_match = df_user[
                    (df_user['Email'].str.lower() == u_email.lower()) & 
                    (df_user['Senha'].astype(str) == u_senha) & 
                    (df_user['CPF'].astype(str).str.replace(r'\D', '', regex=True) == u_cpf_limpo)
                ]
                
                if not user_match.empty:
                    st.session_state.logado = True
                    # Extração segura da cidade (String, não Array)
                    st.session_state.usuario_cidade = user_match['Cidade'].values
                    st.session_state.usuario_nome = u_email.split('@').capitalize()
                    st.rerun()
                else:
                    st.error("⚠️ Dados incorretos. Verifique e-mail, senha e CPF.")
            else:
                st.error("❌ Erro de conexão com a planilha.")
    st.stop()

# --- TELA 02: SELEÇÃO DE COMPETÊNCIA (TRAVA) ---
if not st.session_state.competencia_confirmada:
    st.title(f"Bem-vindo, {st.session_state.usuario_nome}! 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")
    
    with st.container(border=True):
        st.markdown("### Selecione o período de trabalho:")
        c1, c2 = st.columns(2)
        
        # LISTAS DE DEFINIÇÃO (CONFERIDAS)
        lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        lista_anos =
        
        mes_escolhido = c1.selectbox("Mês de Referência", lista_meses, key="sel_mes_work")
        ano_escolhido = c2.selectbox("Ano", lista_anos, index=2, key="sel_ano_work")
        
        if st.button("🚀 Confirmar Competência e Abrir Painel", use_container_width=True):
            st.session_state.mes_ativo = mes_escolhido
            st.session_state.ano_ativo = ano_escolhido
            st.session_state.competencia_confirmada = True
            st.rerun()
    st.stop()

# --- TELA 03: PAINEL PRINCIPAL (LADO A LADO) ---
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(f"📅 **Mês Ativo:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Carregar Dados das Abas (Config e Cadastros)
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

# Buscar Alíquotas Reais da Cidade Logada
aliq_serv, aliq_patr_total, lei_ref = 0.14, 0.22, "Padrão"
if not df_conf.empty:
    conf_cid = df_conf[df_conf['Cidade'] == st.session_state.usuario_cidade]
    if not conf_cid.empty:
        ref = conf_cid.iloc[-1]
        aliq_serv = float(ref['Al_Servidor']) / 100
        aliq_patr_total = (float(ref['Al_Patronal']) + float(ref['Al_Suplementar'])) / 100
        lei_ref = ref['Lei_Referencia']

# DIVISÃO DA TELA
col_form, col_hist = st.columns([1, 1.2])

with col_form:
    st.subheader("📝 Lançamento Mensal")
    with st.container(border=True):
        # Filtra Centros de Custo da Cidade do Usuário
        df_cid_cad = df_cad[df_cad['Cidade'] == st.session_state.usuario_cidade] if not df_cad.empty else pd.DataFrame()
        lista_centros = [""] + df_cid_cad['Nome_Centro'].tolist() if not df_cid_cad.empty else [""]
        
        centro_sel = st.selectbox("1. Centro de Custo", lista_centros, key="main_centro")
        
        # --- LÓGICA DE SECRETARIA (EXTRAÇÃO SEGURA DE STRING) ---
        if centro_sel != "":
            filtro_sec = df_cid_cad[df_cid_cad['Nome_Centro'] == centro_sel]['Secretaria']
            sec_vinculada = filtro_sec.values if not filtro_sec.empty else "Não encontrada"
            st.text_input("2. Secretaria Vinculada", value=sec_vinculada, disabled=True)
        else:
            st.text_input("2. Secretaria Vinculada", value="", disabled=True)
            if st.button("➕ Novo Centro"):
                st.info("Função de cadastro em desenvolvimento.")

        st.divider()
        v_bruto = st.number_input("3. Valor Bruto da Folha (R$)", min_value=0.0, step=0.01, format="%.2f", key="bruto_val")
        v_base = st.number_input("4. Base de Cálculo (R$)", min_value=0.0, step=0.01, format="%.2f", key="base_val")
        
        # Painel Visual de Cálculos
        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #007bff;">
            <p style="margin:0; font-size:14px;">⚖️ <b>Cálculo Prévio (Lei: {lei_ref}):</b></p>
            <h4 style="margin:5px 0;">Devido Servidor: R$ {v_base * aliq_serv:,.2f}</h4>
            <h4 style="margin:5px 0;">Devido Patronal: R$ {v_base * aliq_patr_total:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.write("**Dados de Repasse (Pagamento)**")
        r_serv = st.number_input("Valor Repassado Servidor", min_value=0.0, step=0.01, format="%.2f", key="rep_s")
        dt_serv = st.date_input("Data do Repasse Servidor", format="DD/MM/YYYY") if r_serv > 0 else None
        
        r_patr = st.number_input("Valor Repassado Patronal", min_value=0.0, step=0.01, format="%.2f", key="rep_p")
        dt_patr = st.date_input("Data do Repasse Patronal", format="DD/MM/YYYY") if r_patr > 0 else None

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento processado!")

with col_hist:
    st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True)
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    st.info("O histórico de lançamentos aparecerá aqui.")
