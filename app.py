import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página para focar no mobile e desktop
st.set_page_config(
    page_title="Central de Chamados & Agenda",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"  # Melhor experiência no mobile
)

# Estilo para adaptar botões e tabelas em telas menores
st.markdown("""
    <style>
    .stButton>button { width: 100%; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# Lista de contextos
CONTEXTOS = ["Todos", "Negócio 1", "Negócio 2", "Negócio 3", "Negócio 4", "Faculdade", "Pessoal"]

# Interface de seleção de contexto (Filtro)
st.title("⚡ Minha Central")
contexto_selecionado = st.selectbox("Selecione o Foco Atual:", CONTEXTOS)

# Abas de navegação simples (ideais para tela de celular)
aba_agenda, aba_chamados, aba_novo = st.tabs(["📅 Agenda", "📋 Chamados", "➕ Novo Chamado"])

with aba_agenda:
    st.subheader("Sua Agenda Unificada")
    st.info("Aqui você integrará o componente 'streamlit-calendar' ou visualizará os compromissos do dia.")
    
    # Exemplo simples de lista do dia
    st.write(f"**Compromissos para hoje ({contexto_selecionado}):**")
    st.checkbox("Reunião de Alinhamento - Negócio 1 (14:00)")
    st.checkbox("Entrega do Trabalho - Faculdade (23:59)")

with aba_chamados:
    st.subheader("Quadro de Chamados")
    col1, col2 = st.columns(2)
    with col1:
        status_filtro = st.multiselect("Filtrar Status", ["A Fazer", "Em Andamento", "Concluído"], default=["A Fazer", "Em Andamento"])
    
    # Exemplo de exibição em cards leves
    st.markdown("---")
    st.markdown("### 🔴 A Fazer")
    st.warning("**[Negócio 2]** Enviar proposta do cliente X (Prazo: Hoje)")
    st.markdown("### 🟡 Em Andamento")
    st.info("**[Faculdade]** Escrever capítulo 2 da pesquisa (Prazo: Sexta)")

with aba_novo:
    st.subheader("Criar Novo Chamado / Tarefa")
    with st.form("novo_chamado"):
        titulo = st.text_input("Título do Chamado")
        contexto = st.selectbox("Negócio / Área", CONTEXTOS[1:])
        prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"])
        data_limite = st.date_input("Data de Entrega", datetime.now())
        descricao = st.text_area("Aotações rápidas")
        
        submitted = st.form_submit_button("Salvar Chamado")
        if submitted:
            st.success(f"Chamado '{titulo}' criado em {contexto}!")