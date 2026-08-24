import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from streamlit_calendar import calendar

# Configuração da página
st.set_page_config(
    page_title="Central de Tarefas",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo minimalista CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 4px; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# Conexão com Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

CONTEXTOS = ["Todos", "Negócio 1", "Negócio 2", "Negócio 3", "Negócio 4", "Faculdade", "Pessoal"]

# Cabeçalho limpo
st.title("Central de Tarefas")
contexto_filtro = st.selectbox("Filtrar contexto:", CONTEXTOS)

# Buscar dados
def carregar_chamados():
    try:
        query = supabase.table("chamados").select("*").order("data_entrega")
        if contexto_filtro != "Todos":
            query = query.eq("contexto", contexto_filtro)
        resposta = query.execute()
        return pd.DataFrame(resposta.data)
    except Exception:
        return pd.DataFrame()

df_chamados = carregar_chamados()

# Estrutura de Navegação em Menus Separados
aba_kanban, aba_calendario, aba_novo = st.tabs(["Kanban", "Calendario", "Novo Chamado"])

# MENU 1: KANBAN
with aba_kanban:
    if df_chamados.empty:
        st.info("Nenhuma tarefa encontrada.")
    else:
        col_fazer, col_andamento, col_concluido = st.columns(3)

        # A Fazer
        with col_fazer:
            st.subheader("A Fazer")
            df_fazer = df_chamados[df_chamados["status"] == "A Fazer"]
            for _, item in df_fazer.iterrows():
                with st.container(border=True):
                    st.markdown(f"**[{item['contexto']}]** {item['titulo']}")
                    st.caption(f"Prazo: {item['data_entrega']} | Prioridade: {item['prioridade']}")
                    if item['descricao']:
                        st.text(item['descricao'])
                    
                    if st.button("Iniciar ->", key=f"fazer_{item['id']}"):
                        supabase.table("chamados").update({"status": "Em Andamento"}).eq("id", item['id']).execute()
                        st.rerun()

        # Em Andamento
        with col_andamento:
            st.subheader("Em Andamento")
            df_andamento = df_chamados[df_chamados["status"] == "Em Andamento"]
            for _, item in df_andamento.iterrows():
                with st.container(border=True):
                    st.markdown(f"**[{item['contexto']}]** {item['titulo']}")
                    st.caption(f"Prazo: {item['data_entrega']} | Prioridade: {item['prioridade']}")
                    if item['descricao']:
                        st.text(item['descricao'])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("<- Voltar", key=f"voltar_{item['id']}"):
                            supabase.table("chamados").update({"status": "A Fazer"}).eq("id", item['id']).execute()
                            st.rerun()
                    with c2:
                        if st.button("Concluir", key=f"concluir_{item['id']}"):
                            supabase.table("chamados").update({"status": "Concluído"}).eq("id", item['id']).execute()
                            st.rerun()

        # Concluído
        with col_concluido:
            st.subheader("Concluído")
            df_concluido = df_chamados[df_chamados["status"] == "Concluído"]
            for _, item in df_concluido.iterrows():
                with st.container(border=True):
                    st.markdown(f"~~[{item['contexto']}] {item['titulo']}~~")
                    st.caption(f"Status: Finalizado")
                    
                    if st.button("Excluir", key=f"del_{item['id']}"):
                        supabase.table("chamados").delete().eq("id", item['id']).execute()
                        st.rerun()

# MENU 2: CALENDÁRIO SEPARADO
with aba_calendario:
    if not df_chamados.empty:
        eventos = []
        for _, item in df_chamados.iterrows():
            eventos.append({
                "title": f"[{item['contexto']}] {item['titulo']}",
                "start": item['data_entrega'],
                "end": item['data_entrega'],
                "color": "#4a4a4a" if item['status'] == "Concluído" else "#1f77b4"
            })
        
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
        st.info("Sem eventos para o calendário.")

# MENU 3: NOVO CHAMADO
with aba_novo:
    with st.form("form_novo_chamado", clear_on_submit=True):
        titulo = st.text_input("Título *")
        contexto = st.selectbox("Contexto *", CONTEXTOS[1:])
        prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"], value="Média")
        data_limite = st.date_input("Data Limite", datetime.now())
        descricao = st.text_area("Descrição")
        
        salvar = st.form_submit_button("Criar Tarefa")
        
        if salvar:
            if not titulo:
                st.error("Informe o título.")
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
                st.rerun()