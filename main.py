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
        st.error(f"Erro ao acessar aba {nome_aba}: {e}")
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
                # Limpeza para comparação segura
                user_match = df_user[
                    (df_user['Email'].str.lower() == u_email.lower()) & 
                    (df_user['Senha'].astype(str) == u_senha) & 
                    (df_user['CPF'].astype(str).str.replace(r'\D', '', regex=True) == u_cpf.replace(r'\D', '', regex=True))
                ]
                if not user_match.empty:
                    st.session_state.logado = True
                    st.session_state.usuario_cidade = user_match.iloc['Cidade']
                    st.session_state.usuario_nome = u_email.split('@').capitalize()
                    st.rerun()
                else:
                    st.error("⚠️ Dados de acesso incorretos.")
    st.stop()

# --- TELA 02: SELEÇÃO DE COMPETÊNCIA ---
if not st.session_state.competencia_confirmada:
    st.title(f"Bem-vindo, {st.session_state.usuario_nome}!")
    st.subheader(f"📍 Unidade Gestora: {st.session_state.usuario_cidade}")
    
    with st.container(border=True):
        st.markdown("### Selecione o período de trabalho:")
        c1, c2 = st.columns(2)
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        st.session_state.temp_mes = c1.selectbox("Mês de Referência", meses)
        st.session_state.temp_ano = c2.selectbox("Ano",, index=1)
        
        if st.button("🚀 Confirmar e Abrir Lançamentos", use_container_width=True):
            st.session_state.mes_ativo = st.session_state.temp_mes
            st.session_state.ano_ativo = st.session_state.temp_ano
            st.session_state.competencia_confirmada = True
            st.rerun()
    st.stop()

# --- TELA 03: PAINEL PRINCIPAL (LADO A LADO) ---
st.sidebar.title(f"📍 {st.session_state.usuario_cidade}")
st.sidebar.info(f"📅 **Competência:** {st.session_state.mes_ativo}/{st.session_state.ano_ativo}")

if st.sidebar.button("🔄 Alterar Competência"):
    st.session_state.competencia_confirmada = False
    st.rerun()

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.competencia_confirmada = False
    st.rerun()

# Carregar Dados de Configuração e Cadastros
df_conf = carregar_aba("Configuracoes")
df_cad = carregar_aba("Cadastros_Fixos")

# Filtrar alíquotas da cidade
conf_cid = df_conf[df_conf['Cidade'] == st.session_state.usuario_cidade].iloc[-1]
aliq_serv = float(conf_cid['Al_Servidor']) / 100
aliq_patr_total = (float(conf_cid['Al_Patronal']) + float(conf_cid['Al_Suplementar'])) / 100

col_form, col_hist = st.columns([1, 1.2])

with col_form:
    st.subheader("📝 Lançamento Mensal")
    with st.container(border=True):
        # Dropdown Centros de Custo
        df_cid_cad = df_cad[df_cad['Cidade'] == st.session_state.usuario_cidade]
        centro = st.selectbox("1. Centro de Custo", [""] + df_cid_cad['Nome_Centro'].tolist())
        
        if centro != "":
            sec_vinculada = df_cid_cad[df_cid_cad['Nome_Centro'] == centro]['Secretaria'].values
            st.text_input("2. Secretaria (Automática)", value=sec_vinculada, disabled=True)
        else:
            st.text_input("2. Secretaria (Automática)", value="", disabled=True)
            if st.button("➕ Novo Centro/Secretaria"):
                st.info("Formulário de cadastro rápido em desenvolvimento.")

        st.divider()
        # Campos Numéricos com "Máscara" de Digitação
        v_bruto = st.number_input("3. Valor Bruto da Folha (R$)", min_value=0.0, step=0.01, format="%.2f", key="v_bruto")
        v_base = st.number_input("4. Base de Cálculo (R$)", min_value=0.0, step=0.01, format="%.2f", key="v_base")
        
        # Exibição dos Cálculos Automáticos
        st.markdown(f"""
        <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; border-left: 5px solid #007bff;">
            <p style="margin:0; font-size:14px;">⚖️ <b>Valores Devidos (Lei {conf_cid['Lei_Referencia']}):</b></p>
            <h4 style="margin:5px 0;">Servidor: R$ {v_base * aliq_serv:,.2f}</h4>
            <h4 style="margin:5px 0;">Patronal: R$ {v_base * aliq_patr_total:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.write("**Dados de Repasse Efetivo**")
        r_serv = st.number_input("V. Repassado Servidor", min_value=0.0, step=0.01, format="%.2f", key="r_serv")
        dt_serv = st.date_input("Data do Repasse Servidor", format="DD/MM/YYYY") if r_serv > 0 else None
        
        r_patr = st.number_input("V. Repassado Patronal", min_value=0.0, step=0.01, format="%.2f", key="r_patr")
        dt_patr = st.date_input("Data do Repasse Patronal", format="DD/MM/YYYY") if r_patr > 0 else None

    if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
        st.toast("Salvando dados na planilha...", icon="⏳")
        # Lógica de gravação entra aqui na próxima etapa

with col_hist:
    # Botão de Finalização no Topo (Azul)
    st.button("🟦 FINALIZAR E ENVIAR MÊS", use_container_width=True)
    
    st.subheader(f"📋 Conferência: {st.session_state.mes_ativo}")
    # Tabela de Histórico
    df_hist = carregar_aba("Lançamentos_Mensais")
    filtro_mes = df_hist[(df_hist['Cidade'] == st.session_state.usuario_cidade) & 
                         (df_hist['Mes'] == st.session_state.mes_ativo) & 
                         (df_hist['Ano'] == st.session_state.ano_ativo)]
    
    if not filtro_mes.empty:
        st.dataframe(filtro_mes[["Centro_Custo", "Base_Calculo", "V_Devido_Servidor", "V_Devido_Patronal", "Total_Repassado"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum lançamento encontrado para {st.session_state.mes_ativo}/{st.session_state.ano_ativo}.")
