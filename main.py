import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configurações iniciais
st.set_page_config(page_title="Sistema DIPR 2026", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
url_planilha = "https://docs.google.com/spreadsheets/d/1g0Vafzks-zgn7HcJkzwnwB4IqA5itXB0G-MRB35aGGU/edit?gid=0#gid=0"

# --- LOGIN E SEGURANÇA (Mantido conforme conversamos) ---
# ... (Código de login aqui) ...

# Título Principal com o Mês Selecionado na Sidebar
st.title(f"📊 Folha Mensal - Competência {st.sidebar.selectbox('Mês', ['Janeiro', 'Fevereiro', 'Março'])}, 2026")

# Divisão da Tela: Formulário vs Histórico (Igual ao seu Excel)
col_form, col_hist = st.columns([1, 1.2])

with col_form:
    st.subheader("Entrada de Dados")
    with st.container(border=True):
        centro = st.selectbox("Centro de Custo", ["PSF", "Educação", "Administração"])
        secretaria = st.text_input("Secretaria", value="Saúde", disabled=True)
        
        v_bruto = st.number_input("Valor Bruto (R$)", format="%.2f", step=100.0)
        base_calc = st.number_input("Base de Cálculo (R$)", format="%.2f", step=100.0)
        
        # Simulação de alíquota (isso virá da sua aba Configuracoes)
        aliq_serv = 0.11
        aliq_patr_total = 0.16 # Exemplo: 14% + 2% supl.
        
        st.write("---")
        st.write("**Valores Devidos (Automáticos):**")
        c1, c2 = st.columns(2)
        c1.metric("Aliq. Servidor", f"R$ {base_calc * aliq_serv:.2f}")
        c2.metric("Aliq. Patronal Total", f"R$ {base_calc * aliq_patr_total:.2f}")
        
        st.write("---")
        houve_pgto = st.radio("Houve o pagamento?", ["Não", "Sim"], horizontal=True)
        
        if houve_pgto == "Sim":
            v_pago_serv = st.number_input("Valor Pago Servidor", format="%.2f")
            dt_pago_serv = st.date_input("Data Pagamento Servidor")
            
            v_pago_patr = st.number_input("Valor Pago Patronal", format="%.2f")
            dt_pago_patr = st.date_input("Data Pagamento Patronal")
            
    if st.button("SALVAR LANÇAMENTO", use_container_width=True):
        st.success("Dados enviados para a planilha!")

with col_hist:
    st.subheader("📋 Histórico de Lançamentos (Conferência)")
    # Simulando a tabela que você desenhou no Excel
    dados_exemplo = pd.DataFrame({
        "Centro de Custo": ["PSF", "Sec. Educação"],
        "V. Bruto": [103510.50, 85000.00],
        "Base Cálculo": [1320.50, 1320.50],
        "Dev. Servidor": [145.25, 145.25],
        "Dev. Patronal": [211.28, 211.28],
        "Pago Servidor": [145.25, 0.00],
        "Pago Patronal": [211.28, 0.00]
    })
    st.dataframe(dados_exemplo, use_container_width=True, hide_index=True)
    
    st.divider()
    if st.button("🔴 FINALIZAR E ENVIAR MÊS", use_container_width=True):
        st.warning("Você atesta que os dados estão fidedignos?")
        if st.button("SIM, DECLARO FIDEDIGNIDADE"):
            st.balloons()
