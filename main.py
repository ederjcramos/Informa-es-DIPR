import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# --- FUNÇÕES DE APOIO ---
def carregar_aba(nome_aba):
    try:
        # Tenta ler a aba específica da planilha
        return conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
    except Exception:
        return pd.DataFrame()

# --- CONTROLE DE ESTADO (SESSION STATE) ---
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
                # Limpa o CPF digitado para comparar apenas números
                u_cpf_limpo = u_cpf.replace('.', '').replace('-', '')
                
                # Filtra na planilha buscando o usuário correspondente
                user_match = df_user[
                    (df_user['Email'].str.lower() == u_email.lower()) & 
                    (df_user['Senha'].astype(str) == u_senha) & 
                    (df_user['CPF'].astype(str).str.replace(r'\D', '', regex=True) ==
