import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.graph_objects as go

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
            if "Banco" not in df.columns:
                df["Banco"] = "🟣 Nubank"
            if "Cartão" not in df.columns:
                df["Cartão"] = "⚡ Pix"
            
            # Limpa registros antigos ou nulos migrando para a opção Pix padrão
            if not df.empty and "Cartão" in df.columns:
                df["Cartão"] = df["Cartão"].fillna("⚡ Pix").replace({
                    "❌ Nenhum": "⚡ Pix", 
                    "❌ Nenhum (Pix/Débito)": "⚡ Pix",
                    "❌ Não Utilizou Cartão": "⚡ Pix",
                    "": "⚡ Pix"
                })
                
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0.0)
            return df
        except:
            pass
    return pd.DataFrame(columns=["Descrição", "Valor", "Tipo", "Mês/Ano", "Data Registro", "Status", "Banco", "Cartão"])

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

# --- INTELIGÊNCIA: DESCOBRIR HISTÓRICO ---
itens_ja_usados = []
if not st.session_state.df.empty:
    descricoes_salvas = st.session_state.df["Descrição"].dropna().unique().tolist()
    itens_ja_usados = sorted([str(d).strip().upper() for d in descricoes_salvas if str(d).strip()])

# --- AUTOMATIZAÇÃO DE GASTOS FIXOS ---
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

if df_mes_verificacao.empty and not st.session_state.df.empty:
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
                "Status": "⏳ Pendente",
                "Banco": df_fixos_anterior["Banco"] if "Banco" in df_fixos_anterior.columns else "🟣 Nubank",
                "Cartão": df_fixos_anterior["Cartão"] if "Cartão" in df_fixos_anterior.columns else "⚡ Pix"
            })
            st.session_state.df = pd.concat([st.session_state.df, novos_fixos], ignore_index=True)
            save_data(st.session_state.df)
            st.rerun()

# Filtros e Totais principais
df_geral = st.session_state.df.copy()
df_geral['index_original'] = df_geral.index
df_geral['Data_Ordem'] = df_geral['Mês/Ano'].apply(converter_mes_ano_para_data)
df_mes = df_geral[df_geral['Mês/Ano'] == mes_selecionado]

entradas = df_mes[df_mes['Tipo'].isin(['💰 Entrada', '🚨 Retirada Reserva'])]['Valor'].sum()
gastos_fixos = df_mes[df_mes['Tipo'] == '🏠 Gasto Fixo']['Valor'].sum()
gastos_cartao = df_mes[df_mes['Tipo'] == '💳 Cartão de Crédito']['Valor'].sum()
gastos_extras = df_mes[df_mes['Tipo'] == '🛍️ Gasto Extra']['Valor'].sum()
caixinha_mes_atual = df_mes[df_mes['Tipo'] == '✈️ Caixinha Viagem']['Valor'].sum()
investimentos = df_mes[df_mes['Tipo'].isin(['📈 Investimentos', '🟢 Reposição Reserva'])]['Valor'].sum()

caixinha_total_acumulada = df_geral[(df_geral['Tipo'] == '✈️ Caixinha Viagem') & (df_geral['Data_Ordem'] <= data_limite_atual)]['Valor'].sum()
saldo_livre = entradas - (gastos_fixos + gastos_cartao + gastos_extras + caixinha_mes_atual + investimentos)
porcentagem_investida = (investimentos / entradas) * 100 if entradas > 0 else 0.0

df_historico_ate_aqui = df_geral[df_geral['Data_Ordem'] <= data_limite_atual]
entradas_nu = df_historico_ate_aqui[(df_historico_ate_aqui['Tipo'].isin(['💰 Entrada', '🚨 Retirada Reserva'])) & (df_historico_ate_aqui['Banco'] == '🟣 Nubank')]['Valor'].sum()
saidas_nu = df_historico_ate_aqui[(~df_historico_ate_aqui['Tipo'].isin(['💰 Entrada', '🚨 Retirada Reserva'])) & (df_historico_ate_aqui['Banco'] == '🟣 Nubank') & (df_historico_ate_aqui['Status'] == '✅ Pago')]['Valor'].sum()
saldo_nu = entradas_nu - saidas_nu

entradas_bb = df_historico_ate_aqui[(df_historico_ate_aqui['Tipo'].isin(['💰 Entrada', '🚨 Retirada Reserva'])) & (df_historico_ate_aqui['Banco'] == '🟡 Banco do Brasil')]['Valor'].sum()
saidas_bb = df_historico_ate_aqui[(~df_historico_ate_aqui['Tipo'].isin(['💰 Entrada', '🚨 Retirada Reserva'])) & (df_historico_ate_aqui['Banco'] == '🟡 Banco do Brasil') & (df_historico_ate_aqui['Status'] == '✅ Pago')]['Valor'].sum()
saldo_bb = entradas_bb - saidas_bb

retiradas_reserva = df_historico_ate_aqui[(df_historico_ate_aqui['Tipo'] == '🚨 Retirada Reserva') | ((df_historico_ate_aqui['Tipo'] == '💰 Entrada') & (df_historico_ate_aqui['Descrição'].str.contains('RESERVA', case=False, na=False)))]['Valor'].sum()
reposicoes_reserva = df_historico_ate_aqui[(df_historico_ate_aqui['Tipo'] == '🟢 Reposição Reserva') | ((df_historico_ate_aqui['Tipo'] == '📈 Investimentos') & (df_historico_ate_aqui['Descrição'].str.contains('RESERVA', case=False, na=False)))]['Valor'].sum()
deficit_reserva = retiradas_reserva - reposicoes_reserva

# --- LAYOUT SUPERIOR ---
st.markdown("### 🏦 Saldos Disponíveis nos Bancos")
col_b1, col_b2 = st.columns(2)
with col_b1:
    st.markdown(f"""<div style="border: 1px solid #8a05be; border-left: 6px solid #8a05be; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; text-align: center;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">🟣 SALDO NUBANK</span><br><span style="color: #8a05be; font-size: 22px; font-weight: 800; display: inline-block; margin-top: 5px;">R$ {saldo_nu:,.2f}</span></div>""", unsafe_allow_html=True)
with col_b2:
    st.markdown(f"""<div style="border: 1px solid #facc15; border-left: 6px solid #facc15; background-color: #0f172a; padding: 12px 15px; border-radius: 12px; text-align: center;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">🟡 SALDO BANCO DO BRASIL</span><br><span style="color: #facc15; font-size: 22px; font-weight: 800; display: inline-block; margin-top: 5px;">R$ {saldo_bb:,.2f}</span></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    cor_saldo_texto = "#10b981" if saldo_livre >= 0 else "#ef4444"
    st.markdown(f"""<div style="border: 1px solid #10b981; border-left: 6px solid #10b981; background-color: #0f172a; padding: 10px 15px; border-radius: 12px; min-height: 135px; display: flex; flex-direction: column; justify-content: space-between;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">💰 ENTRADAS & SALDO</span><div><span style="color: #10b981; font-size: 17px; font-weight: 700;">💰 Receita: R$ {entradas:,.2f}</span><div style="border-top: 1px dashed rgba(148, 163, 184, 0.2); margin: 3px 0;"></div><span style="color: {cor_saldo_texto}; font-size: 17px; font-weight: 700;">⚖️ Livre: R$ {saldo_livre:,.2f}</span></div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div style="border: 1px solid #ef4444; border-left: 6px solid #ef4444; background-color: #0f172a; padding: 10px 15px; border-radius: 12px; min-height: 135px; display: flex; flex-direction: column; justify-content: space-between;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">📊 GASTOS MENSAIS</span><div><span style="color: #ef4444; font-size: 14px; font-weight: 700;">🏠 Fixos: R$ {gastos_fixos:,.2f}</span><br><span style="color: #f43f5e; font-size: 14px; font-weight: 700;">💳 Cartão: R$ {gastos_cartao:,.2f}</span><div style="border-top: 1px dashed rgba(148, 163, 184, 0.2); margin: 2px 0;"></div><span style="color: #cbd5e1; font-size: 14px; font-weight: 700;">🛍️ Extras: R$ {gastos_extras:,.2f}</span></div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div style="border: 1px solid #3b82f6; border-left: 6px solid #3b82f6; background-color: #0f172a; padding: 10px 15px; border-radius: 12px; min-height: 135px; display: flex; flex-direction: column; justify-content: space-between;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">📈 INVESTIMENTOS</span><div style="margin-top: 8px;"><span style="color: #3b82f6; font-size: 24px; font-weight: 800;">R$ {investimentos:,.2f}</span></div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div style="border: 1px solid #f59e0b; border-left: 6px solid #f59e0b; background-color: #0f172a; padding: 10px 15px; border-radius: 12px; min-height: 135px; display: flex; flex-direction: column; justify-content: space-between;"><span style="color: #94a3b8; font-size: 13px; font-weight: bold;">✈️ CAIXINHA VIAGEM</span><div style="margin-top: 8px;"><span style="color: #f59e0b; font-size: 24px; font-weight: 800;">R$ {caixinha_total_acumulada:,.2f}</span></div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SAÚDE FINANCEIRA ---
st.markdown("### 📊 Saúde Financeira")
col_analise, col_grafico = st.columns([1.2, 1])
with col_analise:
    if deficit_reserva > 0:
        st.markdown(f"""<div style="border: 1px solid #f59e0b; border-left: 5px solid #f59e0b; background-color: #0f172a; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;"><span style="font-size: 15px; color: #cbd5e1;">⚠️ <b>Reposição Pendente:</b> Resta repor <b>R$ {deficit_reserva:,.2f}</b> à Reserva.</span></div>""", unsafe_allow_html=True)
    if entradas > 0:
        porcentagem_gasta = ((gastos_fixos + gastos_cartao + gastos_extras) / entradas) * 100
        if porcentagem_gasta <= 60:
            st.markdown(f"""<div style="border: 1px solid #10b981; border-left: 5px solid #10b981; background-color: #0f172a; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;"><span style="font-size: 15px; color: #cbd5e1;">🟢 <b>Custo de Vida sob controle:</b> Seus custos consomem <b>{porcentagem_gasta:.1f}%</b> da renda.</span></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="border: 1px solid #ef4444; border-left: 5px solid #ef4444; background-color: #0f172a; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;"><span style="font-size: 15px; color: #cbd5e1;">🔴 <b>Custo de Vida alto:</b> Comprometido <b>{porcentagem_gasta:.1f}%</b> da renda!</span></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="border: 1px solid #3b82f6; border-left: 3px solid #3b82f6; background-color: #0f172a; padding: 12px 16px; border-radius: 8px;"><span style="font-size: 15px; color: #cbd5e1;">📊 <b>Aporte Patrimonial:</b> Você separou <b>{porcentagem_investida:.1f}%</b> da sua receita para Investimentos neste mês.</span></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="border: 1px solid #3b82f6; border-left: 3px solid #3b82f6; background-color: #0f172a; padding: 12px 16px; border-radius: 8px;"><span style="font-size: 15px; color: #cbd5e1;">💡 Insira uma Entrada para ativar os gráficos.</span></div>""", unsafe_allow_html=True)
with col_grafico:
    if entradas > 0:
        raw_labels = ['🏠 Gastos Fixos', '💳 Cartão', '🛍️ Extras', '📈 Investimentos', '✈️ Caixinha', '⚖️ Saldo Livre']
        valores_pizza = [gastos_fixos, gastos_cartao, gastos_extras, investimentos, caixinha_mes_atual, max(0, saldo_livre)]
        fig = go.Figure(data=[go.Pie(labels=raw_labels, values=valores_pizza, hole=.55, textinfo='none', marker=dict(colors=['#ef4444', '#f43f5e', '#cbd5e1', '#3b82f6', '#f59e0b', '#10b981']))])
        fig.update_layout(margin=dict(t=15, b=15, l=15, r=15), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250, annotations=[dict(text=f"Livre<br><b style='font-size:15px;color:#10b981;'>R$ {saldo_livre:,.2f}</b>", x=0.5, y=0.5, font=dict(size=12, color='#94a3b8'), showarrow=False, align="center")])
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- FORMULÁRIO DE CADASTRO PRINCIPAL ---
st.markdown(f"### ➕ Novo Lançamento em {mes_selecionado}")

with st.form(key='finance_form', clear_on_submit=True):
    col_l1_a, col_l1_b = st.columns(2)
    with col_l1_a:
        item_selecionado = st.selectbox("Escolha um gasto da lista:", ["-- Selecione da lista --"] + itens_ja_usados + ["💰 ENTRADA (Salário/Pix)", "🚨 RETIRADA RESERVA", "🟢 REPOSIÇÃO RESERVA", "✈️ CAIXINHA VIAGEM", "📈 INVESTIMENTO"])
    with col_l1_b:
        descricao_manual = st.text_input("Ou digite um item novo:", placeholder="Ex: NETFLIX, ACADEMIA, SPOTIFY...")
        
    col_l2_a, col_l2_b, col_l2_c, col_l2_d = st.columns(4)
    with col_l2_a:
        valor_texto = st.text_input("Valor do Lançamento (R$):", placeholder="0,00")
    with col_l2_b:
        tipo = st.selectbox("Tipo / Categoria:", ["🏠 Gasto Fixo", "💳 Cartão de Crédito", "🛍️ Gasto Extra", "💰 Entrada", "🚨 Retirada Reserva", "🟢 Reposição Reserva", "✈️ Caixinha Viagem", "📈 Investimentos"])
    with col_l2_c:
        banco_movimentado = st.selectbox("Opção de Pagamento:", ["🟣 Nubank", "🟡 Banco do Brasil"])
    with col_l2_d:
        # NOVAS OPÇÕES NO MENU DO FORMULÁRIO: Pix, Boleto e Débito Automático adicionados!
        cartao_usado = st.selectbox("Cartão / Forma de Movimentação:", ["⚡ Pix", "📄 Boleto", "🔄 Débito Automático", "🟣 Nubank", "🟡 Banco do Brasil", "🔵 Mercado Pago"])
        
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
        desc_final = item_selecionado.replace("💰 ", "").replace("✈️ ", "").replace("📈 ", "").replace("🚨 ", "").replace("🟢 ", "").strip().upper()
    else:
        desc_final = tipo.upper()

    status_inicial = "✅ Pago" if tipo in ["💰 Entrada", "🚨 Retirada Reserva", "🟢 Reposição Reserva", "📈 Investimentos"] else "⏳ Pendente"

    if desc_final and valor_final > 0:
        nova_linha = {"Descrição": desc_final, "Valor": valor_final, "Tipo": tipo, "Mês/Ano": mes_selecionado, "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M"), "Status": status_inicial, "Banco": banco_movimentado, "Cartão": cartao_usado}
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nova_linha])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Adicionado!")
        st.rerun()

st.markdown("---")

# --- EXTRATO COMPLETO ---
st.markdown(f"### 📋 Extrato Completo de {mes_selecionado}")

if not df_mes.empty:
    df_visual = df_mes[["index_original", "Descrição", "Valor", "Tipo", "Cartão", "Status", "Banco", "Data Registro"]].copy()
    df_visual = df_visual.sort_values(by="Descrição", key=lambda col: col.str.lower(), ascending=True).reset_index(drop=True)
    
    tabela_editada = st.data_editor(
        df_visual,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "index_original": None,
            "Descrição": st.column_config.TextColumn("Descrição", required=True, width=2.5),
            "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0, required=True, width=1.5, alignment="center"),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["🏠 Gasto Fixo", "💳 Cartão de Crédito", "🛍️ Gasto Extra", "💰 Entrada", "🚨 Retirada Reserva", "🟢 Reposição Reserva", "✈️ Caixinha Viagem", "📈 Investimentos"], required=True, width=1.5),
            
            # NOVAS OPÇÕES NO EXTRATO: As opções de Pix, Boleto e Débito automático estão mapeadas perfeitamente para seleção rápida!
            "Cartão": st.column_config.SelectboxColumn("Cartão / Canal", options=["⚡ Pix", "📄 Boleto", "🔄 Débito Automático", "🟣 Nubank", "🟡 Banco do Brasil", "🔵 Mercado Pago"], required=True, width=1.5),
            
            "Status": st.column_config.SelectboxColumn("Status", options=["✅ Pago", "⏳ Pendente"], required=True, width=1),
            "Banco": st.column_config.SelectboxColumn("Opção de Pagamento", options=["🟣 Nubank", "🟡 Banco do Brasil"], required=True, width=1.5),
            "Data Registro": st.column_config.TextColumn("Data Registro", disabled=True, width=1.5)
        },
        key="editor_extrato"
    )
    
    # Processa exclusões
    if "editor_extrato" in st.session_state and st.session_state.editor_extrato.get("deleted_rows"):
        indices_deletados = st.session_state.editor_extrato["deleted_rows"]
        reais_deletar = [df_visual.iloc[idx]['index_original'] for idx in indices_deletados]
        st.session_state.df = st.session_state.df.drop(reais_deletar).reset_index(drop=True)
        save_data(st.session_state.df)
        st.rerun()
        
    # Processa edições
    if "editor_extrato" in st.session_state and st.session_state.editor_extrato.get("edited_rows"):
        alteracoes = st.session_state.editor_extrato["edited_rows"]
        df_principal = load_data()
        
        for idx_tela, colunas in alteracoes.items():
            idx_real = df_visual.iloc[int(idx_tela)]['index_original']
            for col_nome, novo_val in colunas.items():
                df_principal.at[idx_real, col_nome] = novo_val
                df_principal.at[idx_real, 'Data Registro'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
        st.session_state.df = df_principal
        save_data(df_principal)
        st.rerun()
else:
    st.markdown('<div style="text-align: center; color: #cbd5e1;">Nenhum lançamento cadastrado.</div>', unsafe_allow_html=True)
