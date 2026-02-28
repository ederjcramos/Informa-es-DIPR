import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com a Planilha
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# --- FUNÇÕES DE APOIO ---
def carregar_aba(nome_aba):
    try:
        return conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
    except Exception as e:
        return pd.DataFrame()

# --- CONTROLE DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'competencia_confirmada' not in st.session_state: st.session_state.competencia_confirmada = False

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
                # Limpeza para comparação segura de CPF (remove pontos e traços se houver)
                u_cpf_limpo = u_cpf.replace('.', '').replace('-', '')
                
                user_match = df_user[
                    (df_user['Email'].str.lower() == u_email.lower()) & 
                    (df_user['Senha'].astype(str) == u_senha) & 
                    (df_user['CPF'].astype(str).str.replace(r'\D', '', regex=True) == u_cpf_limpo)
                ]
                
                if not user_match.empty:
                    st.session_state.logado = True
                    st.session_state.usuario_cidade = user_match.iloc['Cidade']
                    st.session_state.usuario_nome = u_email.split('@').capitalize()
                    st.rerun()
                else:
                    st.error("⚠️ Dados de acesso incorretos. Verifique e-mail, senha e CPF.")
            else:
                st.error("Erro ao carregar base de usuários. Verifique a conexão com a planilha.")
    st.stop()

# --- TELA 02: SELEÇÃO DE COMPETÊNCIA (TRAVA) ---
if not st.session_state.competencia_confirmada:
    st.title(f"Bem-vindo, {st.session_state.usuario_nome}! 👋")
    st.subheader(f"📍 Unidade Gestora: {st.session_state.usuario_cidade}")
    
    with st.container(border=True):
        st.markdown("### Selecione o período de trabalho:")
        c1, c2 = st.columns(2)
        meses_lista = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        anos_lista =
        
        mes_escolhido = c1.selectbox("Mês de Referência", meses_lista)
        ano_escolhido = c2.selectbox("Ano", anos_lista, index=1)
        
        if st.button("🚀 Confirmar e Abrir Lançamentos", use_container_width=True):
            st.session_state.mes_ativo = mes_escolhido
            st.session_state.ano_ativo = ano_escolhido
            st.session_state.competencia_confirmada = True
            st.rerun()
    st.stop()

# --- TELA 03: PAINEL PRINCIPAL ---
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(f"📅 **Competência:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Carregar Dados das Abas
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

# Filtrar alíquotas da cidade do usuário
aliq_serv, aliq_patr_total, lei_ref = 0.11, 0.22, "Não cadastrada"
if not df_conf.empty:
    conf_cid = df_conf[df_conf['Cidade'] == st.session_state.usuario_cidade]
    if not conf_cid.empty:
        linha_ref = conf_cid.iloc[-1]
        aliq_serv = float(linha_ref['Al_Servidor']) / 100
        aliq_patr_total = (float(linha_ref['Al_Patronal']) + float(linha_ref['Al_Suplementar'])) / 100
        lei_ref = linha_ref['Lei_Referencia']

col_form, col_hist = st.columns([1, 1.2])

with col_form:
    st.subheader("📝 Lançamento Mensal")
    with st.container(border=True):
        # Lógica de Centro de Custo e Secretaria
        df_cid_cad = df_cad[df_cad['Cidade'] == st.session_state.usuario_cidade] if not df_cad.empty else pd.DataFrame()
        centros_lista = [""] + df_cid_cad['Nome_Centro'].tolist() if not df_cid_cad.empty else [""]
        
        centro = st.selectbox("1. Centro de Custo", centros_lista)
        
        if centro != "":
            sec_vinculada = df_cid_cad[df_cid_cad['Nome_Centro'] == centro]['Secretaria'].values
            st.text_input("2. Secretaria", value=sec_vinculada, disabled=True)
        else:
            st.text_input("2. Secretaria", value="", disabled=True)
            if st.button("➕ Novo Centro/Secretaria"):
                st.info("Funcionalidade de cadastro em breve.")

        st.divider()
        v_bruto = st.number_input("3. Valor Bruto (R$)", min_value=0.0, step=0.01, format="%.2f", key="v_bruto")
        v_base = st.number_input("4. Base Cálculo (R$)", min_value=0.0, step=0.01, format="%.2f", key="v_base")
        
        # Display de Cálculo em destaque
        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #007bff;">
            <p style="margin:0; font-size:14px;">⚖️ <b>Valores Devidos (Lei: {lei_ref}):</b></p>
            <h4 style="margin:5px 0;">Servidor: R$ {v_base * aliq_serv:,.2f}</h4>
            <h4 style="margin:5px 0;">Patronal: R$ {v_base * aliq_patr_total:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        r_serv = st.number_input("V. Repassado Servidor", min_value=0.0, step=0.01, format="%.2f", key="r_serv")
        dt_serv = st.date_input("Data Repasse Servidor", format="DD/MM/YYYY") if r_serv > 0 else None
        
        r_patr = st.number_input("V. Repassado Patronal", min_value=0.0, step=0.01, format="%.2f", key="r_patr")
        dt_patr = st.date_input("Data Repasse Patronal", format="DD/MM/YYYY") if r_patr > 0 else None

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento processado!")

with col_hist:
    st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True)
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    st.info("Aqui aparecerá o histórico de lançamentos salvos.")
