import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="FinançasPro Mensal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nome do arquivo onde os dados serão salvos
DATA_FILE = "dados_financeiros.csv"

# Função para carregar os dados protegendo contra arquivos antigos
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Se o arquivo antigo não tiver a coluna nova, nós criamos ela vazia aqui
            if "Mês/Ano" not in df.columns:
                df["Mês/Ano"] = datetime.now().strftime("%B / %Y").capitalize()
            if "Data Registro" not in df.columns:
                df["Data Registro"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
            return df
        except:
            pass
    return pd.DataFrame(columns=["Descrição", "Valor", "Tipo", "Mês/Ano", "Data Registro"])

# Função para salvar os dados
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Inicializar os dados no Streamlit
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- NAVEGAÇÃO ENTRE MESES (AS "ABAS DO EXCEL") ---
st.sidebar.title("📅 Meses (Abas)")

meses_ano = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
ano_atual = 2026

opcoes_meses = [f"{mes} / {ano_atual}" for mes in meses_ano]
padrao_index = 6  # Padrão em Julho / 2026

mes_selecionado = st.sidebar.radio(
    "Selecione o mês para gerenciar:",
    opcoes_meses,
    index=padrao_index
)

# --- TÍTULO DO MÊS ATUAL ---
st.title(f"💰 FinançasPro — {mes_selecionado}")
st.markdown("---")

# --- FILTRAR DADOS DO MÊS SELECIONADO ---
df_geral = st.session_state.df
df_mes = df_geral[df_geral['Mês/Ano'] == mes_selecionado]

# --- PROCESSAMENTO DOS TOTAIS DO MÊS ---
entradas = df_mes[df_mes['Tipo'] == '💰 Entrada']['Valor'].sum()
gastos_fixos = df_mes[df_mes['Tipo'] == '🏠 Gasto Fixo']['Valor'].sum()
gastos_extras = df_mes[df_mes['Tipo'] == '🛍️ Gasto Extra']['Valor'].sum()
caixinha_viagem = df_mes[df_mes['Tipo'] == '✈️ Caixinha Viagem']['Valor'].sum()

total_saidas = gastos_fixos + gastos_extras + caixinha_viagem
saldo_livre = entradas - total_saidas

# --- CARDS DE RESUMO ---
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    st.metric(label="Quanto Entrou", value=f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with col2:
    st.metric(label="Quanto Saiu", value=f"R$ {total_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with col3:
    st.metric(label="Saldo Livre", value=f"R$ {saldo_livre:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with col4:
    st.info(f"✈️ **Caixinha Viagem**\n\n### R$ {caixinha_viagem:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- FORMULÁRIO DE CADASTRO ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")
with st.form(key='finance_form', clear_on_submit=True):
    col_desc, col_val, col_tipo = st.columns([2, 1, 1.5])
    
    with col_desc:
        descricao = st.text_input("Descrição", placeholder="Ex: Salário, Aluguel, Internet...")
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["💰 Entrada", "🏠 Gasto Fixo", "🛍️ Gasto Extra", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    if descricao and valor > 0:
        nova_linha = {
            "Descrição": descricao,
            "Valor": valor,
            "Tipo": tipo,
            "Mês/Ano": mes_selecionado,
            "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success(f"Adicionado com sucesso em {mes_selecionado}!")
        st.rerun()
    else:
        st.warning("Por favor, preencha a descrição e um valor maior que zero.")

st.markdown("---")

# --- EXTRATO MENSAL ---
st.markdown(f"### 📋 Extrato de {mes_selecionado}")

if not df_mes.empty:
    df_exibicao = df_mes.copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(df_exibicao[["Descrição", "Valor", "Tipo", "Data Registro"]], use_container_width=True, hide_index=True)
else:
    st.info(f"Nenhum lançamento cadastrado para {mes_selecionado}.")
