import streamlit as st

# CONFIGURAÇÃO VISUAL ESTILO "SISTEMA SEI / INSTITUCIONAL"
st.set_page_config(page_title="Sistema DIPR", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    /* Fundo Branco e Texto Escuro */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Barra Superior Colorida (Referência à sua foto) */
    .header-bar {
        background-color: #008080; /* Tom de verde/azul do SEI */
        padding: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    /* Rótulos dos Campos */
    label {
        color: #333333 !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    /* Inputs Estilizados */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #F8F9FA !important;
        color: #333333 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 4px !important;
    }
    /* Botões estilo "Salvar / Cancelar" da foto */
    .stButton>button {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CED4DA;
        box-shadow: 1px 1px 2px #DDD;
    }
    </style>
    <div class="header-bar">SISTEMA DE INFORMAÇÕES - DIPR</div>
    """, unsafe_allow_html=True)

# ORGANIZAÇÃO DOS CAMPOS
col1, col2 = st.columns(2)

with col1:
    email = st.text_input("Nome do Usuário:")
    valor = st.number_input("Valor Pago:", min_value=0.0, step=0.01, format="%.2f")

with col2:
    cidade = st.text_input("Cidade:", value="Sincronizando...", disabled=True)
    data = st.date_input("Data do Lançamento:")

# CONFIRMAÇÃO VISUAL SIMPLES
if valor > 0:
    valor_formatado = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.info(f"Confirmação de Valor: {valor_formatado}")

# BOTÕES NO CANTO (Igual à foto do SEI)
st.markdown("---")
c_bot1, c_bot2, c_bot3 = st.columns([1,1,6])
with c_bot1:
    st.button("Salvar")
with c_bot2:
    st.button("Cancelar")
