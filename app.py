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

# --- INTELIGÊNCIA: DESCOBRIR HISTÓRICO PARA O MENU SUSPENSO ---
itens_ja_usados = []
if not st.session_state.df.empty:
    descricoes_salvas = st.session_state.df["Descrição"].dropna().unique().tolist()
    itens_ja_usados = sorted([d.strip().upper() for d in descricoes_salvas if d.strip()])

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
    st.markdown(
        f"""<div style="border: 1px solid #d1fae5; border-left: 5px solid #10b981; background-color: #f0fdf4; padding: 15px; border-radius: 12px; margin-bottom: 10px;">
            <span style="color: #065f46; font-size: 14px; font-weight: 600;">QUANTO ENTROU</span><br>
            <span style="color: #10b981; font-size: 24px; font-weight: 700;">R$ {entradas:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f"""<div style="border: 1px solid #fee2e2; border-left: 5px solid #ef4444; background-color: #fef2f2; padding: 15px; border-radius: 12px; margin-bottom: 10px;">
            <span style="color: #991b1b; font-size: 14px; font-weight: 600;">QUANTO SAIU</span><br>
            <span style="color: #ef4444; font-size: 24px; font-weight: 700;">R$ {total_saidas:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col3:
    if saldo_livre >= 0:
        cor_borda, cor_fundo, cor_texto, txt_label = "#10b981", "#f0fdf4", "#10b981", "#065f46"
    else:
        cor_borda, cor_fundo, cor_texto, txt_label = "#ef4444", "#fef2f2", "#ef4444", "#991b1b"
        
    st.markdown(
        f"""<div style="border: 1px solid {cor_fundo}; border-left: 5px solid {cor_borda}; background-color: {cor_fundo}; padding: 15px; border-radius: 12px; margin-bottom: 10px;">
            <span style="color: {txt_label}; font-size: 14px; font-weight: 600;">SALDO LIVRE</span><br>
            <span style="color: {cor_texto}; font-size: 24px; font-weight: 700;">R$ {saldo_livre:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col4:
    st.markdown(
        f"""<div style="border: 1px solid #fef3c7; border-left: 5px solid #f59e0b; background-color: #fffbeb; padding: 15px; border-radius: 12px; margin-bottom: 10px;">
            <span style="color: #92400e; font-size: 14px; font-weight: 600;">✈️ CAIXINHA VIAGEM</span><br>
            <span style="color: #f59e0b; font-size: 24px; font-weight: 700;">R$ {caixinha_viagem:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )

# --- TERMÔMETRO MENSAL ---
if entradas > 0:
    porcentagem_gasta = (total_saidas / entradas) * 100
    if porcentagem_gasta <= 60:
        status_texto = "🟢 SITUAÇÃO CONTROLADA: Excelente! Gastos dentro da meta ideal (até 60%)."
    elif porcentagem_gasta <= 100:
        status_texto = "🟡 ATENÇÃO: Gastos ultrapassaram 60% da renda. Fique atento!"
    else:
        status_texto = "🔴 INVERSÃO PATRIMONIAL: Alerta! Você gastou mais do que arrecadou."
    st.markdown(f"### 📊 Como estou no mês?")
    st.markdown(f"**Status:** {status_texto}")
    st.progress(min(porcentagem_gasta / 100, 1.0))
    st.caption(f"Comprometido: **{porcentagem_gasta:.1f}%** | Livre: **{max(0.0, 100.0 - porcentagem_gasta):.1f}%**")
else:
    st.markdown(f"### 📊 Como estou no mês?")
    st.caption("Insira uma Entrada para ativar o termômetro de saúde do mês.")

st.markdown("---")

# --- FORMULÁRIO COM CAMPOS FIXOS (FOCADO EM AGILIDADE MOBILE) ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

# Opções do menu com os itens que já existem
opcoes_selectbox = ["-- Selecione da lista --"] + itens_ja_usados + ["💰 ENTRADA (Salário/Pix)", "✈️ CAIXINHA VIAGEM"]

with st.form(key='finance_form', clear_on_submit=True):
    col_desc_select, col_desc_input, col_val, col_tipo = st.columns([1.5, 1.5, 1, 1])
    
    with col_desc_select:
        item_selecionado = st.selectbox("Escolha da lista:", opcoes_selectbox)
        
    with col_desc_input:
        # Fica SEMPRE visível! Se o item for novo, é só digitar aqui.
        descricao_manual = st.text_input("Ou digite um gasto novo:", placeholder="Ex: SERCOM, MERCADO...")
        
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    # Lógica inteligente: se digitou na caixinha, prioriza o texto manual. Se não, pega a lista.
    if descricao_manual.strip():
        desc_final = descricao_manual.strip().upper()
    elif item_selecionado != "-- Selecione da lista --":
        if "💰" in item_selecionado or "✈️" in item_selecionado:
            desc_final = item_selecionado.split("(")[0].strip().replace("💰 ", "").replace("✈️ ", "")
        else:
            desc_final = item_selecionado
    else:
        desc_final = None

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
        st.warning("Por favor, informe uma descrição (selecionando ou digitando) e um valor maior que zero.")

st.markdown("---")

# --- EXTRATO MENSAL INTERATIVO NATIVO ---
st.markdown(f"### 📋 Extrato Completo de {mes_selecionado}")

if not df_mes.empty:
    st.caption("💡 Para excluir: Clique no quadradinho no início da linha desejada e pressione o botão de lixeira no topo da tabela.")
    
    df_visual = df_mes[["index_original", "Descrição", "Valor", "Tipo", "Data Registro"]].copy()
    
    def colorir_linhas(row):
        styles = [''] * len(row)
        if row['Tipo'] == '💰 Entrada':
            styles = ['background-color: #e6fcf5; color: #0ca678; font-weight: bold;'] * len(row)
        elif row['Tipo'] == '✈️ Caixinha Viagem':
            styles = ['background-color: #fff9db; color: #f59e0b; font-weight: bold;'] * len(row)
        return styles

    tabela_editada = st.data_editor(
        df_visual.style.apply(colorir_linhas, axis=1),
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
