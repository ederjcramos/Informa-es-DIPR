import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SISTEMA DIPR", page_icon="📝", layout="wide")

# ESTILO CSS PARA O BRANCO INSTITUCIONAL E MENU LATERAL
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #F0F2F6; border-right: 1px solid #DCDFE3; }
    .header-bar {
        background-color: #008080;
        padding: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    label { color: #333333 !important; font-weight: bold !important; }
    </style>
    <div class="header-bar">SISTEMA DE INFORMAÇÕES - DIPR</div>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL (NAVEGAÇÃO E COMPETÊNCIA) ---
with st.sidebar:
    st.title("Menu de Navegação")
    
    # 1. ESCOLHA DA COMPETÊNCIA (Obrigatório)
    st.subheader("Competência")
    mes = st.selectbox("Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    ano = st.number_input("Ano:", min_value=2024, max_value=2030, value=2025)
    
    st.divider()
    
    # 2. SELEÇÃO DA ABA
    aba_selecionada = st.radio(
        "Selecione a Categoria:",
        ["Folha Mensal", "Folha 13º", "Unidade Gestora", "Parcelamentos"]
    )

# --- ÁREA PRINCIPAL ---
st.write(f"### Competência Atual: {mes} / {ano}")

if aba_selecionada == "Folha Mensal":
    st.subheader("📊 Lançamento de Folha Mensal")
    
    # Simulação de Centros de Custo já salvos
    centros_salvos = ["Sec. de Saúde - Efetivos", "Sec. de Educação - Contratados", "Câmara Municipal"]
    
    centro_escolhido = st.selectbox("Selecione um Centro de Custo existente ou crie um novo:", 
                                    ["-- Criar Novo --"] + centros_salvos)
    
    if centro_escolhido == "-- Criar Novo --":
        nome_novo = st.text_input("Nome do novo Centro de Custo:")
        vinculo = st.selectbox("Vincular à Secretaria:", ["Saúde", "Educação", "Finanças", "Câmara", "Outros"])
    else:
        st.info(f"Editando: {centro_escolhido}")
        
    col1, col2 = st.columns(2)
    with col1:
        servidores = st.number_input("Qtde de Servidores:", min_value=0)
        bruto = st.number_input("Valor Bruto Remuneração (R$):", min_value=0.0, format="%.2f")
    with col2:
        dependentes = st.number_input("Qtde de Dependentes:", min_value=0)
        base_calc = st.number_input("Base de Cálculo (R$):", min_value=0.0, format="%.2f")

    # Lógica de Alíquota (Simulação)
    aliquota_exemplo = 14.0  # Isso virá da base de usuários depois
    valor_devido = base_calc * (aliquota_exemplo / 100)
    
    if base_calc > 0:
        st.warning(f"Contribuição Estimada ({aliquota_exemplo}%): R$ {valor_devido:,.2f}")

elif aba_selecionada == "Parcelamentos":
    st.subheader("📜 Gestão de Parcelamentos")
    st.write("Aqui o sistema listará os parcelamentos cadastrados para você apenas informar o pagamento.")
    # Lista simulada
    st.checkbox("Parcelamento 001/2023 - Termo de Acordo")
    st.checkbox("Parcelamento 042/2024 - Déficit Atuarial")

# BOTÃO DE SALVAR FINAL
st.markdown("---")
if st.button("SALVAR TODAS AS INFORMAÇÕES"):
    st.success(f"Dados salvos com sucesso para a competência {mes}/{ano}!")
