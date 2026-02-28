import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da Página
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# --- FUNÇÕES DE APOIO ---
def carregar_aba(nome_aba):
    try:
        return conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
    except:
        return pd.DataFrame()

# --- ESTADO DA SESSÃO (MEMÓRIA DO NAVEGADOR) ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'competencia_confirmada' not in st.session_state: st.session_state.competencia_confirmada = False

# --- 1. TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema DIPR")
    with st.form("login_form"):
        u_email = st.text_input("E-mail Institucional")
        u_senha = st.text_input("Senha", type="password")
        u_cpf = st.text_input("CPF (Apenas números)")
        if st.form_submit_button("Entrar no Sistema"):
            df_user = carregar_aba("Base_Usuários")
            if not df_user.empty:
                validacao = df_user[(df_user['Email'] == u_email) & 
                                    (df_user['Senha'].astype(str) == u_senha) & 
                                    (df_user['CPF'].astype(str) == u_cpf)]
                if not validacao.empty:
                    st.session_state.logado = True
                    st.session_state.usuario_cidade = validacao.iloc['Cidade']
                    st.session_state.usuario_nome = u_email.split('@').capitalize()
                    st.rerun()
                else:
                    st.error("Dados de acesso incorretos.")
            else:
                st.error("Erro ao conectar com a base de usuários.")
    st.stop()

# --- 2. TELA DE SELEÇÃO DE COMPETÊNCIA (TRAVA) ---
if not st.session_state.competencia_confirmada:
    st.title(f"Olá, {st.session_state.usuario_nome}! 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")
    st.info("Selecione a competência antes de iniciar os lançamentos:")
    
    col_sel1, col_sel2 = st.columns(2)
    mes_sel = col_sel1.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    ano_sel = col_sel2.selectbox("Ano",, index=1)
    
    if st.button("Confirmar Competência e Abrir Formulário", use_container_width=True):
        st.session_state.mes_ativo = mes_sel
        st.session_state.ano_ativo = ano_sel
        st.session_state.competencia_confirmada = True
        st.rerun()
    st.stop()

# --- 3. INTERFACE DE LANÇAMENTOS (LADO A LADO) ---
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.write(f"📅 **Mês Ativo:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("Trocar Mês/Ano"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Layout Lado a Lado
col_form, col_hist = st.columns([1, 1.3])

with col_form:
    st.subheader("📝 Entrada de Dados")
    with st.container(border=True):
        # Busca Centros de Custo da Cidade
        df_cad = carregar_aba("Cadastros_Fixos")
        df_cid = df_cad[df_cad['Cidade'] == st.session_state.usuario_cidade]
        
        centro = st.selectbox("1. Centro de Custo", [""] + df_cid['Nome_Centro'].tolist())
        
        if centro != "":
            sec = df_cid[df_cid['Nome_Centro'] == centro]['Secretaria'].values
            st.text_input("2. Secretaria", value=sec, disabled=True)
        else:
            st.text_input("2. Secretaria", value="", disabled=True)
            st.button("➕ Novo Centro")

        st.divider()
        v_bruto = st.number_input("3. Valor Bruto (R$)", min_value=0.0, step=0.01, format="%.2f")
        v_base = st.number_input("4. Base Cálculo (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        # Alíquotas Exemplo (Puxar da aba Configuracoes no futuro)
        st.write(f"**Devido Servidor (11%):** R$ {v_base * 0.11:,.2f}")
        st.write(f"**Devido Patronal (16%):** R$ {v_base * 0.16:,.2f}")

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.success("Lançamento Registrado!")

with col_hist:
    if st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True):
        st.info("Botão de Finalização Acionado")
    
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    st.info("Aqui aparecerá a tabela com os lançamentos deste mês.")
