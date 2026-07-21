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

# Arquivos de armazenamento
DATA_FILE = "dados_financeiros.csv"
MENU_FILE = "itens_menu.txt"

# --- GERENCIAMENTO DO MENU SUSPENSO DINÂMICO ---
def carregar_itens_menu():
    # Se o arquivo não existir, cria com uma lista base padrão
    if not os.path.exists(MENU_FILE):
        itens_padrao = ["ÁGUA", "ASSINATURAS", "CASA", "CELULAR MÃE", "CONSULTOR", "FIES", "INTERNET BACKUP", "INTERNET SERCOMT", "LUZ", "MEU CELULAR", "PASSE MÃE", "SEGURO DE VIDA"]
        salvar_itens_menu(itens_padrao)
        return itens_padrao
    
    with open(MENU_FILE, "r", encoding="utf-8") as f:
        return [linha.strip().upper() for item in f.readlines() if (linha := item.strip())]

def salvar_itens_menu(lista_itens):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        for item in sorted(list(set(lista_itens))): # Remove duplicados e ordena de A-Z
            f.write(f"{item}\n")

# Inicializa o menu suspenso na memória do app
if 'itens_menu' not in st.session_state:
    st.session_state.itens_menu = carregar_itens_menu()

# --- GERENCIAMENTO DE DADOS ---
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

# --- FORMULÁRIO PRINCIPAL ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

# Prepara a lista do menu trazendo os itens dinâmicos do usuário + as opções fixas do app
opcoes_finais_menu = st.session_state.itens_menu + ["💰 ENTRADA (Salário/Pix)", "✈️ CAIXINHA VIAGEM", "➕ OUTRO (Digitar manualmente...)"]

with st.form(key='finance_form', clear_on_submit=True):
    col_desc, col_val, col_tipo = st.columns([2, 1, 1.5])
    
    with col_desc:
        item_selecionado = st.selectbox("Descrição (Item do Menu Suspenso)", opcoes_finais_menu)
        descricao_manual = ""
        if item_selecionado == "➕ OUTRO (Digitar manualmente...)":
            descricao_manual = st.text_input("Digite o nome do gasto personalizado:")
            
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    if item_selecionado == "➕ OUTRO (Digitar manualmente...)":
        desc_final = descricao_manual.strip().upper()
    elif "💰" in item_selecionado or "✈️" in item_selecionado:
        desc_final = item_selecionado.split("(")[0].strip().replace("💰 ", "").replace("✈️ ", "")
    else:
        desc_final = item_selecionado

    if desc_final and valor > 0:
        nova_linha = {
            "Descrição": desc_final,
            "Valor": valor,
            "Tipo": tipo,
            "Mês/Ano": mes_selecionado,
            "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Adicionado com sucesso!")
        st.rerun()
    else:
        st.warning("Por favor, preencha o valor e a descrição corretamente.")

st.markdown("---")

# --- EXTRATO MENSAL ---
st.markdown(f"### 📋 Extrato Completo de {mes_selecionado}")
if not df_mes.empty:
    df_exibicao = df_mes.copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(df_exibicao[["Descrição", "Valor", "Tipo", "Data Registro"]], use_container_width=True, hide_index=True)
    
    st.markdown("#### 🗑️ Remover um lançamento")
    lista_itens_extrato = df_mes["Descrição"].tolist()
    item_para_deletar = st.selectbox("Selecione o item para excluir:", ["-- Selecione --"] + lista_itens_extrato, key="del_item_extrato")
    
    if item_para_deletar != "-- Selecione --":
        if st.button("Confirmar Exclusão", type="primary", key="btn_del_extrato"):
            idx_deletar = df_mes[df_mes["Descrição"] == item_para_deletar].index[0]
            st.session_state.df = st.session_state.df.drop(idx_deletar).reset_index(drop=True)
            save_data(st.session_state.df)
            st.success("Item removido!")
            st.rerun()
else:
    st.info(f"Nenhum lançamento cadastrado para {mes_selecionado}.")

st.markdown("---")

# --- NOVA SEÇÃO: GERENCIADOR DO MENU SUSPENSO ---
st.markdown("### ⚙️ Personalizar Itens do Menu Suspenso")
st.caption("Adicione ou remova permanentemente opções da sua lista de validação de dados:")

col_add, col_rem = st.columns(2)

with col_add:
    st.markdown("#### 📥 Adicionar Novo Item à Lista")
    novo_item_lista = st.text_input("Nome do novo item (Ex: ACADEMIA, MERCADO):", key="input_novo_item_lista")
    if st.button("Salvar no Menu", use_container_width=True):
        if novo_item_lista:
            item_formatado = novo_item_lista.strip().upper()
            if item_formatado not in st.session_state.itens_menu:
                st.session_state.itens_menu.append(item_formatado)
                salvar_itens_menu(st.session_state.itens_menu)
                st.success(f"'{item_formatado}' adicionado à lista permanente!")
                st.rerun()
            else:
                st.warning("Este item já existe na lista.")
        else:
            st.warning("Digite um nome válido.")

with col_rem:
    st.markdown("#### 📤 Remover Item Existente da Lista")
    item_para_remover_lista = st.selectbox("Selecione o item para sumir do menu:", ["-- Selecione --"] + st.session_state.itens_menu, key="select_rem_item_lista")
    if item_para_remover_lista != "-- Selecione --":
        if st.button("Excluir do Menu Permanentemente", type="primary", use_container_width=True):
            st.session_state.itens_menu.remove(item_para_remover_lista)
            salvar_itens_menu(st.session_state.itens_menu)
            st.success(f"'{item_para_remover_lista}' removido com sucesso!")
            st.rerun()
