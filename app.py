import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="FinançasPro Mensal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nome do arquivo onde os dados serão salvos
DATA_FILE = "dados_financeiros.csv"

# Função para carregar os dados
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Garante que a coluna valor é numérica
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Descrição", "Valor", "Tipo", "Data"])

# Função para salvar os dados
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Inicializar os dados no Streamlit
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# Título Principal
st.title("💰 FinançasPro Mensal")
mes_atual = datetime.now().strftime("%B / %Y").capitalize()
st.subheader(f"📅 Período: {mes_atual}")

st.markdown("---")

# --- PROCESSAMENTO DOS TOTAIS ---
df_atual = st.session_state.df

entradas = df_atual[df_atual['Tipo'] == '💰 Entrada']['Valor'].sum()
gastos_fixos = df_atual[df_atual['Tipo'] == '🏠 Gasto Fixo']['Valor'].sum()
gastos_extras = df_atual[df_atual['Tipo'] == '🛍️ Gasto Extra']['Valor'].sum()
caixinha_viagem = df_atual[df_atual['Tipo'] == '✈️ Caixinha Viagem']['Valor'].sum()

# Total de saídas inclui gastos e o que foi guardado na caixinha
total_saidas = gastos_fixos + gastos_extras + caixinha_viagem
saldo_livre = entradas - total_saidas

# --- CARDS DE RESUMO (Se adaptam ao celular automaticamente) ---
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.metric(label="Quanto Entrou", value=f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with col2:
    st.metric(label="Quanto Saiu", value=f"R$ {total_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"-R$ {total_saidas:,.2f}", delta_color="inverse")
with col3:
    st.metric(label="Saldo Livre", value=f"R$ {saldo_livre:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"R$ {saldo_livre:,.2f}" if saldo_livre >= 0 else f"R$ {saldo_livre:,.2f}")
with col4:
    # Card destacado para a caixinha viagem
    st.info(f"✈️ **Caixinha Viagem**\n\n### R$ {caixinha_viagem:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- FORMULÁRIO DE CADASTRO ---
st.markdown("### ➕ Novo Lançamento")
with st.form(key='finance_form', clear_on_submit=True):
    col_desc, col_val, col_tipo = st.columns([2, 1, 1.5])
    
    with col_desc:
        descricao = st.text_input("Descrição", placeholder="Ex: Salário, Aluguel, Mercado...")
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["💰 Entrada", "🏠 Gasto Fixo", "🛍️ Gasto Extra", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

# Ação ao clicar no botão
if submit_button:
    if descricao and valor > 0:
        nova_linha = {
            "Descrição": descricao,
            "Valor": valor,
            "Tipo": tipo,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        # Adiciona ao DataFrame
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Lançamento adicionado com sucesso!")
        st.rerun()
    else:
        st.warning("Por favor, preencha a descrição e um valor maior que zero.")

st.markdown("---")

# --- TABELA DE LANÇAMENTOS (EXTRATO) ---
st.markdown("### 📋 Extrato Mensal")

if not st.session_state.df.empty:
    # Exibe a tabela formatada e bonita
    df_exibicao = st.session_state.df.copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    
    # Botão para limpar o mês/histórico se necessário
    if st.button("🗑️ Limpar Todos os Dados"):
        st.session_state.df = pd.DataFrame(columns=["Descrição", "Valor", "Tipo", "Data"])
        save_data(st.session_state.df)
        st.success("Todos os dados foram apagados!")
        st.rerun()
else:
    st.info("Nenhum lançamento cadastrado ainda.")