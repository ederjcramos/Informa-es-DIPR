import streamlit as st

# CONFIGURAÇÃO PROFISSIONAL DARK MODE
st.set_page_config(page_title="DIPR Terminal", page_icon="📟")

st.markdown("""
    <style>
    /* Fundo Dark Profissional */
    .stApp {
        background-color: #0E1117;
    }
    /* Títulos e Rótulos em Branco Gelo */
    h1, label, p, span {
        color: #E0E0E0 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Campos de Entrada Modernos */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #4B4B4B !important;
        border-radius: 8px !important;
    }
    /* Letreiro de Confirmação em Verde Esmeralda */
    .confirmacao-box {
        background-color: #1E3A1E;
        color: #00FF7F;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #00FF7F;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 INFORMAÇÕES-DIPR")

# CAMPOS DO FORMULÁRIO
email = st.text_input("USUÁRIO (E-MAIL)")
cidade = st.text_input("CIDADE", value="Sincronizando...", disabled=True)
valor = st.number_input("VALOR PAGO (R$)", min_value=0.0, step=0.01, format="%.2f")

# CONFIRMAÇÃO VISUAL REFINADA
if valor > 0:
    valor_formatado = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f'<div class="confirmacao-box">CONFIRMAÇÃO: {valor_formatado}</div>', unsafe_allow_html=True)

# BOTÕES DE AÇÃO (Agora com cores padrão do sistema)
st.write("")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("ENVIAR", type="primary", use_container_width=True) 
with col2:
    st.button("LIMPAR", use_container_width=True)
with col3:
    st.button("CANCELAR", use_container_width=True)
