import streamlit as st

# CONFIGURAÇÃO DA PÁGINA E ESTILO TERMINAL
st.set_page_config(page_title="DIPR Terminal", page_icon="📟")

st.markdown("""
    <style>
    /* Fundo Grafite e Texto Verde */
    .stApp {
        background-color: #262626;
    }
    h1, label, p, span {
        color: #00FF00 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    /* Estilização dos inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1a1a1a !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
    }
    /* Botões Coloridos (Amarelo, Azul, Vermelho) */
    .stButton>button {
        border: none;
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 INFORMAÇÕES-DIPR")

# CAMPOS DO FORMULÁRIO
email = st.text_input("USUÁRIO (E-MAIL)")

# Simulação da Cidade (Depois conectamos com sua planilha)
cidade = st.text_input("CIDADE", value="Sincronizando...", disabled=True)

valor = st.number_input("VALOR PAGO (R$)", min_value=0.0, step=0.01, format="%.2f")

# CONFIRMAÇÃO VISUAL (ESTILO TERMINAL)
if valor > 0:
    valor_formatado = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"### [ CONFIRMAÇÃO: {valor_formatado} ]")

# BOTÕES DE AÇÃO
col1, col2, col3 = st.columns(3)
with col1:
    st.button("ENVIAR", type="primary", use_container_width=True) # Ficará Amarelo/Destaque
with col2:
    st.button("LIMPAR", use_container_width=True) # Ficará Azul
with col3:
    st.button("CANCELAR", use_container_width=True) # Ficará Vermelho
