import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="SISTEMA DIPR 2026", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=638862407#gid=638862407"

# --- FUNÇÕES DE APOIO ---
def carregar_dados(aba):
    try:
        return conn.read(spreadsheet=url_planilha, worksheet=aba)
    except:
        st.error(f"Erro ao carregar a aba: {aba}. Verifique o nome na planilha.")
        return pd.DataFrame()

# --- SISTEMA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema DIPR")
    with st.form("login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        cpf = st.text_input("CPF (Somente números ou formato padrão)")
        if st.form_submit_button("Entrar"):
            df_usuarios = carregar_dados("Base_Usuários")
            # Validação simples de login
            usuario = df_usuarios[(df_usuarios['Email'] == email) & 
                                  (df_usuarios['Senha'].astype(str) == senha) &
                                  (df_usuarios['CPF'].astype(str) == cpf)]
            
            if not usuario.empty:
                st.session_state.logado = True
                st.session_state.cidade = usuario.iloc[0]['Cidade']
                st.rerun()
            else:
                st.error("Dados de acesso incorretos. Verifique e-mail, senha e CPF.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"📍 {st.session_state.cidade}")
menu = st.sidebar.radio("Navegação", ["Folha Mensal", "Parcelamentos", "Unidade Gestora (Breve)"])

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# 1. ABA FOLHA MENSAL
if menu == "Folha Mensal":
    # Carregar Configurações de Alíquotas
    df_conf = carregar_dados("Configuracoes")
    conf_cidade = df_conf[df_conf['Cidade'] == st.session_state.cidade].iloc[-1]
    
    aliq_serv = float(conf_cidade['Al_Servidor']) / 100
    aliq_patr = float(conf_cidade['Al_Patronal']) / 100
    aliq_supl = float(conf_cidade['Al_Suplementar']) / 100
    aliq_patr_total = aliq_patr + aliq_supl

    st.title("📋 Lançamento de Folha Mensal")
    st.info(f"⚖️ **Base Legal Atual:** {conf_cidade['Lei_Referencia']} de {conf_cidade['Data_Lei']}")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        with st.expander("Dados da Competência", expanded=True):
            mes = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
            ano = st.selectbox("Ano de Referência", [2025, 2026])
        
        # Busca Centros de Custo
        df_fixos = carregar_dados("Cadastros_Fixos")
        centros_cidade = df_fixos[df_fixos['Cidade'] == st.session_state.cidade]
        centro = st.selectbox("Centro de Custo", centros_cidade['Nome_Centro'].tolist())
        secretaria = centros_cidade[centros_cidade['Nome_Centro'] == centro]['Secretaria'].values[0]
        
        valor_bruto = st.number_input("Valor Bruto (Folha)", min_value=0.0, format="%.2f")
        base_calc = st.number_input("Base de Cálculo Previdenciária", min_value=0.0, format="%.2f")
        
        # Cálculos Automáticos
        v_dev_serv = base_calc * aliq_serv
        v_dev_patr = base_calc * aliq_patr_total
        
        st.subheader("📊 Valores Devidos (Calculados)")
        st.write(f"Servidor ({conf_cidade['Al_Servidor']}%): **R$ {v_dev_serv:.2f}**")
        st.write(f"Patronal ({conf_cidade['Al_Patronal']}% + {conf_cidade['Al_Suplementar']}% Supl.): **R$ {v_dev_patr:.2f}**")
        
        st.divider()
        st.subheader("💸 Valores Repassados")
        v_rep_serv = st.number_input("V. Repassado Servidor", min_value=0.0, format="%.2f")
        dt_rep_serv = st.date_input("Data do Repasse Servidor") if v_rep_serv > 0 else None
        
        v_rep_patr = st.number_input("V. Repassado Patronal", min_value=0.0, format="%.2f")
        dt_rep_patr = st.date_input("Data do Repasse Patronal") if v_rep_patr > 0 else None

        if st.button("SALVAR LANÇAMENTO"):
            novo = pd.DataFrame([{
                "Mes": mes, "Ano": ano, "Cidade": st.session_state.cidade,
                "Centro_Custo": centro, "Secretaria": secretaria,
                "Valor_Bruto": valor_bruto, "Base_Calculo": base_calc,
                "V_Devido_Servidor": v_dev_serv, "V_Devido_Patronal": v_dev_patr,
                "V_Repassado_Servidor": v_rep_serv, "Data_Repasse_Servidor": str(dt_rep_serv),
                "V_Repassado_Patronal": v_rep_patr, "Data_Repasse_Patronal": str(dt_rep_patr),
                "Total_Repassado": v_rep_serv + v_rep_patr, "Status": "Em Aberto"
            }])
            hist = carregar_dados("Lançamentos_Mensais")
            updated = pd.concat([hist, novo], ignore_index=True)
            conn.update(spreadsheet=url_planilha, worksheet="Lançamentos_Mensais", data=updated)
            st.success("Lançamento salvo com sucesso!")
            st.rerun()

    with col2:
        st.subheader(f"🔍 Conferência: {mes}/{ano}")
        df_hist = carregar_dados("Lançamentos_Mensais")
        filtro = df_hist[(df_hist['Cidade'] == st.session_state.cidade) & (df_hist['Mes'] == mes) & (df_hist['Ano'] == ano)]
        if not filtro.empty:
            st.dataframe(filtro[["Centro_Custo", "V_Devido_Servidor", "V_Devido_Patronal", "Total_Repassado"]], use_container_width=True)
            if st.button("🔴 FINALIZAR E ENVIAR MÊS"):
                st.warning("Atesta a fidedignidade dos dados?")
                if st.button("SIM, ENVIAR"):
                    st.balloons()
        else:
            st.write("Nenhum lançamento registrado para este mês.")

# 2. ABA PARCELAMENTOS
elif menu == "Parcelamentos":
    st.title("📑 Pagamento de Parcelamentos")
    # Estrutura para a aba Parcelamentos será similar ao formulário acima
    st.write("Configurando campos para os acordos da cidade...")
