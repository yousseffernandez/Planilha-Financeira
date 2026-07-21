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

# Arquivo de armazenamento principal
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

# Inicializar os dados na memória do Streamlit
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- INTELIGÊNCIA: DESCOBRIR HISTÓRICO DE GASTOS PARA LEMBRETE ---
itens_ja_usados = []
if not st.session_state.df.empty:
    descricoes_salvas = st.session_state.df["Descrição"].dropna().unique().tolist()
    itens_ja_usados = sorted(list(set(descricoes_salvas)))

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

# --- FILTRAR DADOS ---
df_geral = st.session_state.df.copy()
df_geral['index_original'] = df_geral.index
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

# --- FORMULÁRIO 100% DIRETO E SEGURO ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

with st.form(key='finance_form', clear_on_submit=True):
    col_desc, col_val, col_tipo = st.columns([2, 1, 1.5])
    
    with col_desc:
        # Campo de digitação livre: escreva o que quiser sem travar a tela
        descricao_digitada = st.text_input("Descrição do Gasto:", placeholder="Ex: CASA, PASSE MÃE, LUZ...")
        
        # Exibe lembretes clicáveis logo abaixo para ajudar na digitação pelo celular
        if itens_ja_usados:
            st.caption(f"💡 Histórico de itens já usados: {', '.join(itens_ja_usados)}")
            
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    desc_final = list(descricao_digitada.strip().upper())
    desc_final = "".join(desc_final)

    if desc_final and valor > 0:
        nova_linha = {
            "Descrição": desc_final,
            "Valor": valor,
            "Tipo": tipo,
            "Mês/Ano": mes_selecionado,
            "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        df_atual = load_data()
        st.session_state.df = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Adicionado com sucesso!")
        st.rerun()
    else:
        st.warning("Por favor, preencha o valor e a descrição corretamente.")

st.markdown("---")

# --- EXTRATO MENSAL INTERATIVO NATIVO ---
st.markdown(f"### 📋 Extrato Completo de {mes_selecionado}")

if not df_mes.empty:
    st.caption("💡 Para excluir: Clique no quadradinho no início da linha desejada e pressione o botão de lixeira no topo da tabela.")
    
    df_visual = df_mes[["index_original", "Descrição", "Valor", "Tipo", "Data Registro"]].copy()
    
    tabela_editada = st.data_editor(
        df_visual,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={"index_original": None},
        key="editor_extrato"
    )
    
    if "editor_extrato" in st.session_state and st.session_state.editor_extrato.get("deleted_rows"):
        indices_deletados_tela = st.session_state.editor_extrato["deleted_rows"]
        indices_reais_para_deletar = [df_visual.iloc[idx_tela]['index_original'] for idx_tela in indices_deletados_tela]
            
        df_limpo = load_data()
        df_atualizado = df_limpo.drop(indices_reais_para_deletar).reset_index(drop=True)
        st.session_state.df = df_atualizado
        save_data(df_atualizado)
        st.rerun()
else:
    st.info(f"Nenhum lançamento cadastrado para {mes_selecionado}.")
