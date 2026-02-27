import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SISTEMA DIPR", page_icon="📝", layout="wide")

# CONEXÃO COM A PLANILHA (Usa os Secrets que você salvou)
conn = st.connection("gsheets", type=GSheetsConnection)

# ESTILO VISUAL (BRANCO INSTITUCIONAL)
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #F0F2F6; border-right: 1px solid #DCDFE3; }
    .header-bar {
        background-color: #008080; padding: 10px; color: white;
        text-align: center; font-weight: bold; border-radius: 5px; margin-bottom: 20px;
    }
    .stButton>button { width: 100%; }
    </style>
    <div class="header-bar">SISTEMA DE INFORMAÇÕES - DIPR</div>
    """, unsafe_allow_html=True)

# --- MENU LATERAL ---
with st.sidebar:
    st.title("Navegação")
    mes = st.selectbox("Mês de Referência:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    ano = st.selectbox("Ano:", [2024, 2025, 2026])
    
    st.divider()
    aba = st.radio("Selecione a Aba:", ["Folha Mensal", "Folha 13º", "Unidade Gestora", "Parcelamentos"])

# --- LÓGICA DA ABA FOLHA MENSAL ---
if aba == "Folha Mensal" or aba == "Folha 13º":
    st.subheader(f"📊 {aba} - Competência {mes}/{ano}")
    
    with st.expander("1. Identificação do Centro de Custo", expanded=True):
        col_cc1, col_cc2 = st.columns(2)
        with col_cc1:
            centro_custo = st.text_input("Nome do Centro de Custo (Ex: Sec. Saúde):")
        with col_cc2:
            secretaria = st.selectbox("Vincular à Secretaria:", ["Saúde", "Educação", "Finanças", "Administração", "Assistência Social", "Câmara", "Outros"])
    
    with st.expander("2. Valores e Quantidades", expanded=True):
        c1, c2, c3 = st.columns(3)
        qtd_serv = c1.number_input("Qtde Servidores:", min_value=0, step=1)
        qtd_dep = c2.number_input("Qtde Dependentes:", min_value=0, step=1)
        valor_bruto = c3.number_input("Valor Bruto (R$):", min_value=0.0, format="%.2f")
        
        base_calc = st.number_input("Base de Cálculo (R$):", min_value=0.0, format="%.2f")

    # LÓGICA DE CÁLCULO (Simulando alíquotas - depois puxaremos da sua Base_Usuarios)
    aliq_patronal = 14.0
    aliq_servidor = 11.0
    aliq_suplementar = 2.0
    
    if base_calc > 0:
        v_patronal = base_calc * (aliq_patronal / 100)
        v_servidor = base_calc * (aliq_servidor / 100)
        v_suplemen = base_calc * (aliq_suplementar / 100)
        
        st.info(f"**Cálculos Automáticos:** Patronal: R${v_patronal:,.2f} | Servidor: R${v_servidor:,.2f} | Suplementar: R${v_suplemen:,.2f}")
        
        pago = st.radio("Houve o pagamento?", ["Não", "Sim"], horizontal=True)
        if pago == "Sim":
            data_pagto = st.date_input("Data do Pagamento:")
            st.success("Tudo pronto para salvar!")

    if st.button("ENVIAR LANÇAMENTO"):
        # Criamos os dados
        dados_lista = [[mes, ano, centro_custo, secretaria, valor_bruto, base_calc, aba]]
        colunas = ["Mes", "Ano", "Centro_Custo", "Secretaria", "Valor_Bruto", "Base_Calculo", "Tipo"]
        novo_df = pd.DataFrame(dados_lista, columns=colunas)
        
        try:
            # Lendo os dados existentes primeiro para anexar (Append)
            existentes = conn.read(worksheet="Lançamentos_Mensais")
            updated_df = pd.concat([existentes, novo_df], ignore_index=True)
            
            # Atualiza a planilha inteira
            conn.update(worksheet="Lançamentos_Mensais", data=updated_df)
            
            st.balloons()
            st.success("✅ Dados gravados com sucesso!")
        except Exception as e:
            st.error(f"Erro técnico: {e}")
            st.info("DICA: Verifique se o e-mail do robô está como EDITOR na planilha.")

else:
    st.info("Aba em desenvolvimento conforme o seu modelo.")
