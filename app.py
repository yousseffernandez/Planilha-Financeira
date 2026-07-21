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
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0.0)
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

# --- CARDS DE RESUMO REESTILIZADOS ---
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.markdown(
        f"""<div style="border: 1px solid #10b981; border-left: 6px solid #10b981; background-color: #0f172a; padding: 15px; border-radius: 12px;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">💰 QUANTO ENTROU</span><br>
            <span style="color: #10b981; font-size: 24px; font-weight: 800;">R$ {entradas:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f"""<div style="border: 1px solid #ef4444; border-left: 6px solid #ef4444; background-color: #0f172a; padding: 15px; border-radius: 12px;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">📉 QUANTO SAIU</span><br>
            <span style="color: #ef4444; font-size: 24px; font-weight: 800;">R$ {total_saidas:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col3:
    cor_status = "#10b981" if saldo_livre >= 0 else "#ef4444"
    st.markdown(
        f"""<div style="border: 1px solid {cor_status}; border-left: 6px solid {cor_status}; background-color: #0f172a; padding: 15px; border-radius: 12px;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">⚖️ SALDO LIVRE</span><br>
            <span style="color: {cor_status}; font-size: 24px; font-weight: 800;">R$ {saldo_livre:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )
with col4:
    st.markdown(
        f"""<div style="border: 1px solid #f59e0b; border-left: 6px solid #f59e0b; background-color: #0f172a; padding: 15px; border-radius: 12px;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">✈️ CAIXINHA VIAGEM</span><br>
            <span style="color: #f59e0b; font-size: 24px; font-weight: 800;">R$ {caixinha_viagem:,.2f}</span>
        </div>""", unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- RETORNO DO TERMÔMETRO MENSAL ---
if entradas > 0:
    st.markdown("### 📊 Saúde Financeira")
    porcentagem_gasta = (total_saidas / entradas) * 100
    if porcentagem_gasta <= 60:
        st.success(f"🟢 **Situação sob controle:** Você gastou **{porcentagem_gasta:.1f}%** das suas entradas (dentro do limite recomendado de 60%).")
    elif porcentagem_gasta <= 100:
        st.warning(f"🟡 **Sinal de atenção:** Seus gastos já tomaram **{porcentagem_gasta:.1f}%** do seu orçamento mensal.")
    else:
        st.error(f"🔴 **Orçamento estourado:** Você gastou **{porcentagem_gasta:.1f}%** em relação ao que arrecadou!")
    st.progress(min(porcentagem_gasta / 100, 1.0))
else:
    st.info("💡 Insira uma entrada de receita para liberar o gráfico de gastos mensais.")

st.markdown("---")

# --- FORMULÁRIO COM LARGURA DE COLUNAS AJUSTADA ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

opcoes_selectbox = ["-- Selecione da lista --"] + itens_ja_usados + ["💰 ENTRADA (Salário/Pix)", "✈️ CAIXINHA VIAGEM"]

with st.form(key='finance_form', clear_on_submit=True):
    # Alteração nas proporções das colunas: Valor ganhou mais espaço
    col_desc_select, col_desc_input, col_val, col_tipo = st.columns([1.2, 1.2, 0.8, 1.2])
    
    with col_desc_select:
        item_selecionado = st.selectbox("Escolha da lista:", opcoes_selectbox)
        
    with col_desc_input:
        descricao_manual = st.text_input("Ou digite um gasto novo:", placeholder="Ex: MERCADO, POSTO...")
        
    with col_val:
        valor_texto = st.text_input("Valor (R$):", placeholder="0,00")
        
    with col_tipo:
        tipo = st.selectbox("Tipo / Categoria", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"])
        
    submit_button = st.form_submit_button(label="🚀 Adicionar Lançamento", use_container_width=True)

if submit_button:
    try:
        valor_limpo = valor_texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_final = float(valor_limpo) if valor_limpo else 0.0
    except ValueError:
        valor_final = 0.0

    if descricao_manual.strip():
        desc_final = descricao_manual.strip().upper()
    elif item_selecionado != "-- Selecione da lista --":
        if "💰" in item_selecionado or "✈️" in item_selecionado:
            desc_final = item_selecionado.split("(")[0].strip().replace("💰 ", "").replace("✈️ ", "")
        else:
            desc_final = item_selecionado
    else:
        desc_final = None

    if desc_final and valor_final > 0:
        nova_linha = {
            "Descrição": desc_final,
            "Valor": valor_final,
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
        st.warning("Por favor, preencha a descrição e insira um valor válido.")

st.markdown("---")

# --- EXTRATO MENSAL INTERATIVO ---
st.markdown(f"### 📋 Extrato Completo de {mes_selecionado}")
st.caption("✏️ **Dica:** Dê dois cliques em qualquer célula para editar na hora. Marque a caixinha lateral e use a lixeira no topo para remover.")

if not df_mes.empty:
    df_visual = df_mes[["index_original", "Descrição", "Valor", "Tipo", "Data Registro"]].copy()
    
    def colorir_linhas(row):
        styles = [''] * len(row)
        if row['Tipo'] in ['💰 Entrada', 'Entrada']:
            styles = ['background-color: #064e3b; color: #34d399; font-weight: bold;'] * len(row)
        elif row['Tipo'] in ['✈️ Caixinha Viagem', 'Caixinha Viagem']:
            styles = ['background-color: #451a03; color: #fbbf24; font-weight: bold;'] * len(row)
        return styles

    tabela_editada = st.data_editor(
        df_visual.style.apply(colorir_linhas, axis=1),
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "index_original": None,
            "Descrição": st.column_config.TextColumn("Descrição", required=True),
            "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0, required=True),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem"], required=True),
            "Data Registro": st.column_config.TextColumn("Data Registro", disabled=True)
        },
        key="editor_extrato"
    )
    
    # Exclusão
    if "editor_extrato" in st.session_state and st.session_state.editor_extrato.get("deleted_rows"):
        indices_deletados_tela = st.session_state.editor_extrato["deleted_rows"]
        indices_reais_para_deletar = [df_visual.iloc[idx_tela]['index_original'] for idx_tela in indices_deletados_tela]
        df_atualizado = load_data().drop(indices_reais_para_deletar).reset_index(drop=True)
        st.session_state.df = df_atualizado
        save_data(df_atualizado)
        st.rerun()
        
    # Edição Celular
    if "editor_extrato" in st.session_state and st.session_state.editor_extrato.get("edited_rows"):
        alteracoes = st.session_state.editor_extrato["edited_rows"]
        df_principal = load_data()
        
        for idx_tela, colunas_alteradas in alteracoes.items():
            idx_real = df_visual.iloc[int(idx_tela)]['index_original']
            for nome_coluna, novo_valor in colunas_alteradas.items():
                df_principal.at[idx_real, nome_coluna] = novo_valor
                df_principal.at[idx_real, 'Data Registro'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
        st.session_state.df = df_principal
        save_data(df_principal)
        st.rerun()
else:
    st.info(f"Nenhum lançamento cadastrado para {mes_selecionado}.")
