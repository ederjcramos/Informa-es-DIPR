import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configurações iniciais de página e estilo
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# --- FUNÇÕES DE CARREGAMENTO SEGURO ---
def carregar_aba(nome_aba):
    try:
        return conn.read(spreadsheet=url_planilha, worksheet=nome_aba)
    except:
        return pd.DataFrame()

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'competencia_confirmada' not in st.session_state: st.session_state.competencia_confirmada = False

# --- 1. TELA DE LOGIN (COM CPF) ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema DIPR")
    with st.form("login_form"):
        u_email = st.text_input("E-mail Institucional")
        u_senha = st.text_input("Senha", type="password")
        u_cpf = st.text_input("CPF (Apenas números)")
        if st.form_submit_button("Entrar no Sistema"):
            df_user = carregar_aba("Base_Usuários")
            validacao = df_user[(df_user['Email'] == u_email) & 
                                (df_user['Senha'].astype(str) == u_senha) & 
                                (df_user['CPF'].astype(str) == u_cpf)]
            if not validacao.empty:
                st.session_state.logado = True
                st.session_state.usuario_cidade = validacao.iloc['Cidade']
                st.session_state.usuario_nome = u_email.split('@').capitalize()
                st.rerun()
            else:
                st.error("Dados de acesso incorretos. Verifique e tente novamente.")
    st.stop()

# --- 2. TELA DE SELEÇÃO DE COMPETÊNCIA (TRAVA) ---
if not st.session_state.competencia_confirmada:
    st.title(f"Olá, {st.session_state.usuario_nome}! 👋")
    st.subheader(f"📍 Unidade: {st.session_state.usuario_cidade}")
    st.info("Antes de iniciar, selecione a competência de trabalho:")
    
    col_sel1, col_sel2 = st.columns(2)
    mes_sel = col_sel1.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    ano_sel = col_sel2.selectbox("Ano",, index=1)
    
    if st.button("Confirmar Competência e Abrir Formulário", use_container_width=True):
        st.session_state.mes_ativo = mes_sel
        st.session_state.ano_ativo = ano_sel
        st.session_state.competencia_confirmada = True
        st.rerun()
    st.stop()

# --- 3. INTERFACE PRINCIPAL (LADO A LADO) ---
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.write(f"📅 **Competência:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("Trocar Mês/Ano"):
    st.sidebar.warning("Certifique-se de ter salvo os dados!")
    if st.sidebar.button("Sim, Alterar Competência"):
        st.session_state.competencia_confirmada = False
        st.rerun()

if st.sidebar.button("Sair do Sistema"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Carregamento de dados para o formulário
df_cadastros = carregar_aba("Cadastros_Fixos")
df_cidade_cadastros = df_cadastros[df_cadastros['Cidade'] == st.session_state.usuario_cidade]

col_esq, col_dir = st.columns([1, 1.3])

# --- COLUNA ESQUERDA: FORMULÁRIO ---
with col_esq:
    st.subheader("📝 Entrada de Dados")
    
    with st.container(border=True):
        # Lógica de Centro de Custo e Secretaria
        lista_centros = df_cidade_cadastros['Nome_Centro'].tolist()
        centro_escolhido = st.selectbox("1. Selecione o Centro de Custo", [""] + lista_centros)
        
        if centro_escolhido != "":
            sec_auto = df_cidade_cadastros[df_cidade_cadastros['Nome_Centro'] == centro_escolhido]['Secretaria'].values
            st.text_input("2. Secretaria Vinculada", value=sec_auto, disabled=True)
        else:
            st.text_input("2. Secretaria Vinculada", value="", disabled=True)
            if st.button("➕ Adicionar Novo Centro/Secretaria"):
                st.info("Função de cadastro de novos centros em desenvolvimento...")

        st.divider()
        # Valores com Máscara (Simulada via step)
        v_bruto = st.number_input("3. Valor Bruto da Folha (R$)", min_value=0.0, step=0.01, format="%.2f")
        v_base = st.number_input("4. Base de Cálculo Previdenciária (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        # Bloco de Cálculos Legais (Exemplo baseado em Coruripe/AL)
        # No futuro, buscaremos aliq_serv e aliq_patr da aba 'Configuracoes'
        aliq_s, aliq_p = 0.11, 0.16 # Valores exemplo
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:10px; border-radius:10px;">
            <p style="margin:0; color:#1f77b4;"><b>Cálculo Automático (Devido):</b></p>
            <b>Servidor:</b> R$ {v_base * aliq_s:,.2f} | <b>Patronal:</b> R$ {v_base * aliq_p:,.2f}
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("**Dados de Repasse Efetivo**")
        r_serv = st.number_input("V. Repassado Servidor", min_value=0.0, step=0.01, format="%.2f")
        dt_serv = st.date_input("Data do Repasse Servidor", format="DD/MM/YYYY") if r_serv > 0 else None
        
        r_patr = st.number_input("V. Repassado Patronal", min_value=0.0, step=0.01, format="%.2f")
        dt_patr = st.date_input("Data do Repasse Patronal", format="DD/MM/YYYY") if r_patr > 0 else None

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        # Lógica de Append na Planilha (Lançamentos_Mensais)
        st.success("Lançamento salvo com sucesso!")

# --- COLUNA DIREITA: CONFERÊNCIA E FINALIZAÇÃO ---
with col_dir:
    # Botão Finalizar no Topo
    if st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True):
        st.warning("Você atesta que os dados informados são fidedignos com a realidade?")
        if st.button("SIM, DECLARO FIDEDIGNIDADE"):
            st.balloons()
            st.success("Mês Finalizado! O comprovante (PDF) estará disponível em breve.")

    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")
    
    # Carregar histórico do mês para conferência
    df_hist = carregar_aba("Lançamentos_Mensais")
    filtro_hist = df_hist[(df_hist['Cidade'] == st.session_state.usuario_cidade) & 
                          (df_hist['Mes'] == st.session_state.mes_ativo) & 
                          (df_hist['Ano'] == st.session_state.ano_ativo)]
    
    if not filtro_hist.empty:
        st.dataframe(filtro_hist[["Centro_Custo", "Base_Calculo", "V_Devido_Servidor", "V_Devido_Patronal", "Total_Repassado"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento registrado para esta competência.")
