import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Configuração da página (otimizada para desktop e mobile)
st.set_page_config(
    page_title="Central de Chamados",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Conexão com o Supabase via Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Estilo para adaptar botões no celular
st.markdown("""
    <style>
    .stButton>button { width: 100%; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

CONTEXTOS = ["Todos", "Negócio 1", "Negócio 2", "Negócio 3", "Negócio 4", "Faculdade", "Pessoal"]

st.title("⚡ Minha Central de Chamados")
contexto_filtro = st.selectbox("🎯 Focar em:", CONTEXTOS)

# Função para buscar dados
def carregar_chamados():
    query = supabase.table("chamados").select("*").order("data_entrega")
    if contexto_filtro != "Todos":
        query = query.eq("contexto", contexto_filtro)
    resposta = query.execute()
    return pd.DataFrame(resposta.data)

df_chamados = carregar_chamados()

aba_chamados, aba_novo = st.tabs(["📋 Chamados", "➕ Novo Chamado"])

# TAB 1: VISUALIZAÇÃO DOS CHAMADOS
with aba_chamados:
    if df_chamados.empty:
        st.info("Nenhum chamado encontrado para este contexto.")
    else:
        # Criando as 3 colunas do Kanban
        col_fazer, col_andamento, col_concluido = st.columns(3)

        # --- COLUNA 1: A FAZER ---
        with col_fazer:
            st.markdown("### 🔴 A Fazer")
            df_fazer = df_chamados[df_chamados["status"] == "A Fazer"]
            
            for _, item in df_fazer.iterrows():
                with st.container(border=True):
                    st.markdown(f"**[{item['contexto']}]** {item['titulo']}")
                    st.caption(f"📅 Prazo: {item['data_entrega']} | 🔥 {item['prioridade']}")
                    if item['descricao']:
                        st.write(item['descricao'])
                    
                    if st.button("Mover ➡️", key=f"fazer_{item['id']}"):
                        supabase.table("chamados").update({"status": "Em Andamento"}).eq("id", item['id']).execute()
                        st.rerun()

        # --- COLUNA 2: EM ANDAMENTO ---
        with col_andamento:
            st.markdown("### 🟡 Em Andamento")
            df_andamento = df_chamados[df_chamados["status"] == "Em Andamento"]
            
            for _, item in df_andamento.iterrows():
                with st.container(border=True):
                    st.markdown(f"**[{item['contexto']}]** {item['titulo']}")
                    st.caption(f"📅 Prazo: {item['data_entrega']} | 🔥 {item['prioridade']}")
                    if item['descricao']:
                        st.write(item['descricao'])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("⬅️", key=f"voltar_{item['id']}"):
                            supabase.table("chamados").update({"status": "A Fazer"}).eq("id", item['id']).execute()
                            st.rerun()
                    with c2:
                        if st.button("✅", key=f"concluir_{item['id']}"):
                            supabase.table("chamados").update({"status": "Concluído"}).eq("id", item['id']).execute()
                            st.rerun()

        # --- COLUNA 3: CONCLUÍDO ---
        with col_concluido:
            st.markdown("### 🟢 Concluído")
            df_concluido = df_chamados[df_chamados["status"] == "Concluído"]
            
            for _, item in df_concluido.iterrows():
                with st.container(border=True):
                    st.markdown(f"~~**[{item['contexto']}]** {item['titulo']}~~")
                    st.caption(f"📅 Concluído")
                    
                    if st.button("🗑️ Excluir", key=f"del_{item['id']}"):
                        supabase.table("chamados").delete().eq("id", item['id']).execute()
                        st.rerun()

# TAB 2: CRIAR NOVO CHAMADO
with aba_novo:
    with st.form("form_novo_chamado", clear_on_submit=True):
        titulo = st.text_input("Título do Chamado *")
        contexto = st.selectbox("Área / Negócio *", CONTEXTOS[1:])
        prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"], value="Média")
        data_limite = st.date_input("Data de Entrega", datetime.now())
        descricao = st.text_area("Anotações e detalhes")
        
        salvar = st.form_submit_button("Salvar Chamado")
        
        if salvar:
            if not titulo:
                st.error("Por favor, informe o título.")
            else:
                novo_dado = {
                    "titulo": titulo,
                    "contexto": contexto,
                    "prioridade": prioridade,
                    "data_entrega": str(data_limite),
                    "descricao": descricao,
                    "status": "A Fazer"
                }
                supabase.table("chamados").insert(novo_dado).execute()
                st.success(f"Chamado '{titulo}' salvo com sucesso!")
                st.rerun()

from streamlit_calendar import calendar

# Criando 3 abas agora: Calendário, Chamados e Novo
aba_agenda, aba_chamados, aba_novo = st.tabs(["📅 Agenda", "📋 Chamados", "➕ Novo Chamado"])

with aba_agenda:
    st.subheader("Visão Mensal / Semanal")
    
    if not df_chamados.empty:
        # Formata os dados do Supabase para o padrão do calendário
        eventos = []
        for _, item in df_chamados.iterrows():
            eventos.append({
                "title": f"[{item['contexto']}] {item['titulo']}",
                "start": item['data_entrega'],
                "end": item['data_entrega'],
                "color": "#ff4b4b" if item['prioridade'] == "Urgente" else "#3788d8"
            })
        
        # Opções de configuração do Google Agenda
        options = {
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek"
            },
        }
        
        calendar(events=eventos, options=options, key="agenda_central")
    else:
        st.info("Nenhum compromisso para exibir no calendário.")