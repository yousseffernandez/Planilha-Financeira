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

# Função para carregar os dados
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
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

# --- VARIÁVEIS DE DATA ---
meses_ano = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
data_hoje = datetime.now()
ano_atual = data_hoje.year
mes_atual_nome = meses_ano[data_hoje.month - 1]

# Estado para controlar qual mês está ativo no app (Padrão: Mês Atual)
if 'mes_ativo' not in st.session_state:
    st.session_state.mes_ativo = f"{mes_atual_nome} / {ano_atual}"

# --- NAVEGAÇÃO NA SIDEBAR (ANOS RECOLHÍVEIS COM SETINHA) ---
st.sidebar.title("📅 Histórico Financeiro")
st.sidebar.markdown("Escolha o ano e clique no mês:")

# Exibir Ano Passado, Ano Atual e Próximo Ano
anos_disponiveis = [ano_atual - 1, ano_atual, ano_atual + 1]

for ano in list(reversed(anos_disponiveis)):
    # Deixa o expansor do ano atual aberto por padrão, os outros começam fechados
    esta_aberto = (ano == ano_atual)
    
    with st.sidebar.expander(f"📁 Ano {ano}", expanded=esta_aberto):
        # Cria botões verticais organizados para cada mês
        for mes in meses_ano:
            nome_opcao = f"{mes} / {ano}"
            # Se for o mês que está selecionado, ganha um destaque visual básico
            label_botao = f"📌 {mes}" if st.session_state.mes_ativo == nome_opcao else mes
            
            if st.button(label_botao, key=f"btn_{mes}_{ano}", use_container_width=True):
                st.session_state.mes_ativo = nome_opcao
                st.rerun()

# Recupera o mês selecionado pelo usuário
mes_selecionado = st.session_state.mes_ativo

# --- TÍTULO PRINCIPAL ---
st.title(f"💰 FinançasPro — {mes_selecionado}")
st.markdown("---")

# --- FILTRAR DADOS ---
df_geral = st.session_state.df
df_mes = df_geral[df_geral['Mês/Ano'] == mes_selecionado]

# --- PROCESSAMENTO DOS TOTAIS ---
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
        st.success(f"Adicionado com sucesso!")
        st.rerun()
    else:
        st.warning("Por favor, preencha a descrição e um valor maior que zero.")

st.markdown("---")

# --- EXTRATO MENSAL COM OPÇÃO DE DELETAR ITEM ---
st.markdown(f"### 📋 Extrato de {mes_selecionado}")

if not df_mes.empty:
    # Exibe a tabela normal formatada
    df_exibicao = df_mes.copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(df_exibicao[["Descrição", "Valor", "Tipo", "Data Registro"]], use_container_width=True, hide_index=True)
    
    # Caixa para deletar algum item errado
    st.markdown("#### 🗑️ Remover um lançamento")
    lista_itens = df_mes["Descrição"].tolist()
    item_para_deletar = st.selectbox("Selecione o item para excluir:", ["-- Selecione --"] + lista_itens)
    
    if item_para_deletar != "-- Selecione --":
        if st.button("Confirmar Exclusão", type="primary"):
            # Encontra o índice real no dataframe geral e remove
            idx_deletar = df_mes[df_mes["Descrição"] == item_para_deletar].index[0]
            st.session_state.df = st.session_state.df.drop(idx_deletar).reset_index(drop=True)
            save_data(st.session_state.df)
            st.success("Item removido com sucesso!")
            st.rerun()
else:
    st.info(f"Nenhum lançamento cadastrado para {mes_selecionado}.")
