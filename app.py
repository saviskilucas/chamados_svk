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
        st.info("Nenhum chamado cadastrado para este contexto.")
    else:
        status_opcoes = ["A Fazer", "Em Andamento", "Concluído"]
        status_selecionado = st.multiselect("Filtrar por Status", status_opcoes, default=["A Fazer", "Em Andamento"])
        
        df_filtrado = df_chamados[df_chamados["status"].isin(status_selecionado)]
        
        for _, item in df_filtrado.iterrows():
            com_cor = "🔴" if item['status'] == "A Fazer" else ("🟡" if item['status'] == "Em Andamento" else "🟢")
            
            with st.expander(f"{com_cor} [{item['contexto']}] {item['titulo']} — Prazo: {item['data_entrega']}"):
                st.write(f"**Prioridade:** {item['prioridade']}")
                st.write(f"**Status:** {item['status']}")
                if item['descricao']:
                    st.write(f"**Anotações:** {item['descricao']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if item['status'] != "Concluído":
                        if st.button("✅ Marcar como Concluído", key=f"concluir_{item['id']}"):
                            supabase.table("chamados").update({"status": "Concluído"}).eq("id", item['id']).execute()
                            st.rerun()
                with col2:
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