import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="FinançasPro Mensal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Arquivo de armazenamento principal
DATA_FILE = "dados_financeiros.csv"

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

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- COLETAR SUGESTÕES ANTIGAS PARA AUTOCOMPLETAR ---
sugestoes = []
if not st.session_state.df.empty:
    sugestoes = sorted(list(set(st.session_state.df["Descrição"].dropna().astype(str).tolist())))

# --- VARIÁVEIS DE DATA ---
meses_ano = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
data_hoje = datetime.now()
ano_atual = data_hoje.year
mes_atual_nome = meses_ano[data_hoje.month - 1]

if 'mes_ativo' not in st.session_state:
    st.session_state.mes_ativo = f"{mes_atual_nome} / {ano_atual}"

# --- NAVEGAÇÃO NA SIDEBAR ---
st.sidebar.title("📅 Histórico Financeiro")
anos_disponiveis = [ano_atual - 1, ano_atual, ano_atual + 1]

for ano in list(reversed(anos_disponiveis)):
    esta_aberto = (ano == ano_atual)
    with st.sidebar.expander(f"📁 Ano {ano}", expanded=esta_aberto):
        for mes in meses_ano:
            nome_opcao = f"{mes} / {ano}"
            label_botao = f"📌 {mes}" if st.session_state.mes_ativo == nome_opcao else mes
            if st.button(label_botao, key=f"btn_{mes}_{ano}", use_container_width=True):
                st.session_state.mes_ativo = nome_opcao
                st.rerun()

mes_selecionado = st.session_state.mes_ativo

# --- TÍTULO PRINCIPAL ---
st.title(f"💰 FinançasPro — {mes_selecionado}")
st.markdown("---")

# --- FILTRAR DADOS DO MÊS ---
df_geral = st.session_state.df.copy()
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

# --- FORMULÁRIO RÁPIDO E INTELIGENTE ---
st.markdown(f"### ➕ Novo Lançamento")

with st.form(key='finance_form', clear_on_submit=True):
    col_desc, col_val, col_tipo = st.columns([2, 1, 1.5])
    
    with col_desc:
        # st.text_input com autocomplete: digite qualquer coisa ou escolha das sugestões antigas!
        descricao = st.text_input("Descrição (Digite novo ou escolha sugestão)", autocomplete=sugestoes, placeholder="Ex: CASA, PASSE MÃE, ALUGUEL...")
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    desc_final = descricao.strip().upper()
    if desc_final and valor > 0:
        nova_linha = {
            "Descrição": desc_final,
            "Valor": valor,
            "Tipo": tipo,
            "Mês/Ano": mes_selecionado,
            "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        st.session_state.df = pd.concat([load_data(), pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Adicionado!")
        st.rerun()
    else:
        st.warning("Preencha a descrição e o valor corretamente.")

st.markdown("---")

# --- EXTRATO MENSAL COM O BOTÃO X DO LADO ---
st.markdown(f"### 📋 Extrato de {mes_selecionado}")

if not df_mes.empty:
    # Criamos um layout limpo simulando linhas de aplicativo
    for idx, row in df_mes.iterrows():
        # Renderiza cada linha gastando espaço dinâmico proporcional
        c_desc, c_val, c_tipo, c_del = st.columns([2.5, 1.5, 1.5, 0.5])
        
        with c_desc:
            st.markdown(f"**{row['Descrição']}**")
        with c_val:
            st.markdown(f"R$ {row['Valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with c_tipo:
            st.markdown(f"<small>{row['Tipo']}</small>", unsafe_allow_html=True)
        with c_del:
            # Botão X direto na linha com identificação única pelo índice real do banco
            if st.button("❌", key=f"del_{idx}"):
                st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                save_data(st.session_state.df)
                st.rerun()
        st.markdown("<div style='border-bottom: 1px solid #eee; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
else:
    st.info("Nenhum lançamento cadastrado para este mês.")
