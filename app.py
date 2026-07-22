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
            if "Status" not in df.columns:
                df["Status"] = "⏳ Pendente"
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0.0)
            return df
        except:
            pass
    return pd.DataFrame(columns=["Descrição", "Valor", "Tipo", "Mês/Ano", "Data Registro", "Status"])

# Função para salvar os dados
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Inicializar os dados na memória do Streamlit
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

anos_disponiveis = [ano_atual - 1, ano_atual]

for ano in sorted(anos_disponiveis):
    esta_aberto = (ano == ano_atual)
    with st.sidebar.expander(f"📁 Ano {ano}", expanded=esta_aberto):
        for mes in meses_ano:
            nome_opcao = f"{mes} / {ano}"
            
            if st.session_state.mes_ativo == nome_opcao:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #10b981; 
                        color: white; 
                        padding: 8px 16px; 
                        border-radius: 8px; 
                        text-align: center; 
                        font-weight: 800; 
                        font-size: 14px; 
                        letter-spacing: 0.5px;
                        border: 1px solid #059669;
                        margin-bottom: 4px;
                        box-shadow: 0px 0px 8px rgba(16, 185, 129, 0.3);
                    ">
                        {mes.upper()}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                if st.button(mes, key=f"btn_{mes}_{ano}", use_container_width=True):
                    st.session_state.mes_ativo = nome_opcao
                    st.rerun()

mes_selecionado = st.session_state.mes_ativo

# --- INTELIGÊNCIA: DESCOBRIR HISTÓRICO PARA O MENU SUSPENSO ---
itens_ja_usados = []
if not st.session_state.df.empty:
    descricoes_salvas = st.session_state.df["Descrição"].dropna().unique().tolist()
    itens_ja_usados = sorted([str(d).strip().upper() for d in descricoes_salvas if str(d).strip()])

# --- AUTOMATIZAÇÃO DE REPETIÇÃO DE GASTOS FIXOS ---
df_geral = st.session_state.df.copy()

def converter_mes_ano_para_data(string_mes_ano):
    try:
        partes = string_mes_ano.split("/")
        m_nome = partes[0].strip()
        a_num = int(partes[1].strip())
        m_num = meses_ano.index(m_nome) + 1
        return datetime(a_num, m_num, 1)
    except:
        return datetime(2000, 1, 1)

df_geral['Data_Ordem'] = df_geral['Mês/Ano'].apply(converter_mes_ano_para_data)
data_limite_atual = converter_mes_ano_para_data(mes_selecionado)

df_mes_verificacao = df_geral[df_geral['Mês/Ano'] == mes_selecionado]

if df_mes_verificacao.empty smash not st.session_state.df.empty:
    meses_com_dados = df_geral.dropna(subset=['Mês/Ano'])
    if not meses_com_dados.empty:
        ultimo_mes_com_registro = meses_com_dados.sort_values(by='Data_Ordem', ascending=False).iloc[0]['Mês/Ano']
        
        df_fixos_anterior = df_geral[
            (df_geral['Mês/Ano'] == ultimo_mes_com_registro) & 
            (df_geral['Tipo'] == '🏠 Gasto Fixo')
        ].copy()
        
        if not df_fixos_anterior.empty:
            novos_fixos = pd.DataFrame({
                "Descrição": df_fixos_anterior["Descrição"],
                "Valor": df_fixos_anterior["Valor"],
                "Tipo": "🏠 Gasto Fixo",
                "Mês/Ano": mes_selecionado,
                "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Status": "⏳ Pendente"
            })
            st.session_state.df = pd.concat([st.session_state.df, novos_fixos], ignore_index=True)
            save_data(st.session_state.df)
            st.rerun()

# Atualiza os filtros após processamento
df_geral = st.session_state.df.copy()
df_geral['index_original'] = df_geral.index
if "Status" not in df_geral.columns:
    df_geral["Status"] = "⏳ Pendente"
df_geral['Data_Ordem'] = df_geral['Mês/Ano'].apply(converter_mes_ano_para_data)
df_mes = df_geral[df_geral['Mês/Ano'] == mes_selecionado]

# --- PROCESSAMENTO DOS TOTAIS ---
entradas = df_mes[df_mes['Tipo'] == '💰 Entrada']['Valor'].sum()
gastos_fixos = df_mes[df_mes['Tipo'] == '🏠 Gasto Fixo']['Valor'].sum()
gastos_extras = df_mes[df_mes['Tipo'] == '🛍️ Gasto Extra']['Valor'].sum()
caixinha_mes_atual = df_mes[df_mes['Tipo'] == '✈️ Caixinha Viagem']['Valor'].sum()
investimentos = df_mes[df_mes['Tipo'] == '📈 Investimentos']['Valor'].sum()

caixinha_total_acumulada = df_geral[
    (df_geral['Tipo'] == '✈️ Caixinha Viagem') & 
    (df_geral['Data_Ordem'] <= data_limite_atual)
]['Valor'].sum()

saldo_livre = entradas - (gastos_fixos + gastos_extras + caixinha_mes_atual + investimentos)

# --- REORGANIZAÇÃO EM 4 COLUNAS ---
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    cor_saldo_texto = "#10b981" if saldo_livre >= 0 else "#ef4444"
    st.markdown(
        f"""<div style="border: 1px solid #10b981; border-left: 6px solid #10b981; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; min-height: 125px; display: flex; flex-direction: column; justify-content: space-between;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">💰 ENTRADAS & SALDO</span>
            <div style="margin-top: 6px; display: flex; flex-direction: column;">
                <span style="color: #10b981; font-size: 18px; font-weight: 700; padding-bottom: 4px;">💰 Receita: R$ {entradas:,.2f}</span>
                <div style="border-top: 1px dashed rgba(148, 163, 184, 0.2); margin: 3px 0;"></div>
                <span style="color: {cor_saldo_texto}; font-size: 18px; font-weight: 700; padding-top: 4px;">⚖️ Livre: R$ {saldo_livre:,.2f}</span>
            </div>
        </div>""", unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""<div style="border: 1px solid #ef4444; border-left: 6px solid #ef4444; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; min-height: 125px; display: flex; flex-direction: column; justify-content: space-between;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">📊 GASTOS MENSAIS</span>
            <div style="margin-top: 6px; display: flex; flex-direction: column;">
                <span style="color: #ef4444; font-size: 18px; font-weight: 700; padding-bottom: 4px;">🏠 Fixos: R$ {gastos_fixos:,.2f}</span>
                <div style="border-top: 1px dashed rgba(148, 163, 184, 0.2); margin: 3px 0;"></div>
                <span style="color: #cbd5e1; font-size: 18px; font-weight: 700; padding-top: 4px;">🛍️ Extras: R$ {gastos_extras:,.2f}</span>
            </div>
        </div>""", unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""<div style="border: 1px solid #3b82f6; border-left: 6px solid #3b82f6; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; min-height: 125px; display: flex; flex-direction: column; justify-content: space-between;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">📈 INVESTIMENTOS</span>
            <div style="flex-grow: 1; display: flex; align-items: center; margin-top: 12px;">
                <span style="color: #3b82f6; font-size: 24px; font-weight: 800;">R$ {investimentos:,.2f}</span>
            </div>
        </div>""", unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""<div style="border: 1px solid #f59e0b; border-left: 6px solid #f59e0b; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; min-height: 125px; display: flex; flex-direction: column; justify-content: space-between;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">✈️ CAIXINHA VIAGEM</span>
            <div style="flex-grow: 1; display: flex; align-items: center; margin-top: 12px;">
                <span style="color: #f59e0b; font-size: 24px; font-weight: 800;">R$ {caixinha_total_acumulada:,.2f}</span>
            </div>
        </div>""", unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- TERMÔMETRO MENSAL ---
st.markdown("### 📊 Saúde Financeira")
if entradas > 0:
    porcentagem_gasta = ((gastos_fixos + gastos_extras) / entradas) * 100
    porcentagem_investida = (investimentos / entradas) * 100
    
    if porcentagem_gasta <= 60:
        st.success(f"🟢 **Custo de Vida sob controle:** Seus gastos fixos/extras consomem **{porcentagem_gasta:.1f}%** da renda (dentro da meta ideal de 60%).")
    else:
        st.error(f"🔴 **Custo de Vida alto:** Seus custos fixos/extras já comprometeram **{porcentagem_gasta:.1f}%** da sua renda!")
        
    st.info(f"📊 **Aporte Patrimonial:** Você separou **{porcentagem_investida:.1f}%** da sua receita para Investimentos neste mês.")
    st.progress(min((gastos_fixos + gastos_extras + investimentos) / entradas, 1.0))
else:
    st.info("💡 Insira um lançamento do tipo '💰 Entrada' para ativar a análise de saúde do mês.")

st.markdown("---")

# --- FORMULÁRIO COMPACTO 2X2 ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

opcoes_selectbox = ["-- Selecione da lista --"] + itens_ja_usados + ["💰 ENTRADA (Salário/Pix)", "✈️ CAIXINHA VIAGEM", "📈 INVESTIMENTO"]

with st.form(key='finance_form', clear_on_submit=True):
    col_l1_a, col_l1_b = st.columns(2)
    with col_l1_a:
        item_selecionado = st.selectbox("Escolha um gasto da lista:", opcoes_selectbox)
    with col_l1_b:
        descricao_manual = st.text_input("Ou digite um item novo:", placeholder="Ex: MERCADO, TESOURO SELIC, CDB...")
        
    col_l2_a, col_l2_b = st.columns(2)
    with col_l2_a:
        valor_texto = st.text_input("Valor do Lançamento (R$):", placeholder="0,00")
    with col_l2_b:
        tipo = st.selectbox("Tipo / Categoria:", ["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem", "📈 Investimentos"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    submit_button = st.form_submit_button(label="Adicionar Lançamento", use_container_width=True)

if submit_button:
    try:
        valor_limpo = valor_texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_final = float(valor_limpo) if valor_limpo else 0.0
    except ValueError:
        valor_final = 0.0

    if descricao_manual.strip():
        desc_final = descricao_manual.strip().upper()
    elif item_selecionado != "-- Selecione da lista --":
        if "💰" in item_selecionado or "✈️" in item_selecionado or "📈" in item_selecionado:
            desc_final = item_selecionado.replace("💰 ", "").replace("✈️ ", "").replace("📈 ", "").strip()
        else:
            desc_final = item_selecionado
    else:
        desc_final = None

    status_inicial = "✅ Pago" if tipo in ["💰 Entrada", "📈 Investimentos"] else "⏳ Pendente"

    if desc_final and valor_final > 0:
        nova_linha = {
            "Descrição": desc_final,
            "Valor": valor_final,
            "Tipo": tipo,
            "Mês/Ano": mes_selecionado,
            "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Status": status_inicial
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

if not df_mes.empty:
    df_visual = df_mes[["index_original", "Descrição", "Valor", "Tipo", "Status", "Data Registro"]].copy()
    
    # Ordenação alfabética
    df_visual = df_visual.sort_values(by="Descrição", key=lambda col: col.str.lower(), ascending=True)
    df_visual = df_visual.reset_index(drop=True)
    
    def colorir_linhas(row):
        styles = [''] * len(row)
        if row['Status'] == '⏳ Pendente':
            styles = ['background-color: #451c1c; color: #fca5a5; font-weight: normal;'] * len(row)
        else:
            if row['Tipo'] in ['💰 Entrada', 'Entrada']:
                styles = ['background-color: #064e3b; color: #34d399; font-weight: bold;'] * len(row)
            elif row['Tipo'] in ['✈️ Caixinha Viagem', 'Caixinha Viagem']:
                styles = ['background-color: #451a03; color: #fbbf24; font-weight: bold;'] * len(row)
            elif row['Tipo'] in ['📈 Investimentos', 'Investimentos']:
                styles = ['background-color: #1e3a8a; color: #60a5fa; font-weight: bold;'] * len(row)
        return styles

    # FORÇANDO CENTRALIZAÇÃO VISUAL GLOBAL
    st.markdown(
        """
        <style>
            div[data-testid="stDataEditor"] div div div div div div div div div {
                text-align: center !important;
                justify-content: center !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # REMOVIDO: O 'alignment="center"' que quebrava nas colunas incompatíveis
    tabela_editada = st.data_editor(
        df_visual.style.apply(colorir_linhas, axis=1),
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "index_original": None,
            "Descrição": st.column_config.TextColumn("Descrição", required=True, width="large"),
            "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0, required=True, width="medium", alignment="center"),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["🏠 Gasto Fixo", "🛍️ Gasto Extra", "💰 Entrada", "✈️ Caixinha Viagem", "📈 Investimentos"], required=True, width="medium"),
            "Status": st.column_config.SelectboxColumn("Status", options=["✅ Pago", "⏳ Pendente"], required=True, width="medium"),
            "Data Registro": st.column_config.TextColumn("Data Registro", disabled=True, width="medium")
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
