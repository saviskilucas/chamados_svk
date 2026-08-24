import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from streamlit_calendar import calendar

st.set_page_config(page_title="Central", layout="wide", initial_sidebar_state="collapsed")

# Estilo ultra-minimalista
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 2px; padding: 2px; height: auto; }
    div[data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
CONTEXTOS = ["Todos", "Negócio 1", "Negócio 2", "Negócio 3", "Negócio 4", "Faculdade", "Pessoal"]
CORES = {"Padrão": "#ffffff", "Cinza": "#f0f0f0", "Azul": "#e6f0fa", "Verde": "#e6ffe6", "Amarelo": "#ffffcc", "Vermelho": "#ffe6e6"}

def carregar_chamados():
    try:
        query = supabase.table("chamados").select("*").order("ordem", desc=False)
        if contexto_filtro != "Todos":
            query = query.eq("contexto", contexto_filtro)
        resposta = query.execute()
        return pd.DataFrame(resposta.data)
    except Exception:
        return pd.DataFrame()

# Topo simples
col_titulo, col_filtro = st.columns([3, 1])
with col_titulo:
    st.title("Central")
with col_filtro:
    contexto_filtro = st.selectbox("Contexto", CONTEXTOS, label_visibility="collapsed")

df_chamados = carregar_chamados()

aba_kanban, aba_calendario = st.tabs(["Kanban", "Calendario"])

# --- KANBAN DIRECTO ---
with aba_kanban:
    col_fazer, col_andamento, col_concluido = st.columns(3)
    
    colunas_status = [
        ("A Fazer", col_fazer),
        ("Em Andamento", col_andamento),
        ("Concluído", col_concluido)
    ]

    for status, col in colunas_status:
        with col:
            st.subheader(status)
            
            # Criar tarefa direta na coluna
            with st.popover("+ Adicionar"):
                with st.form(f"form_quick_{status}", clear_on_submit=True):
                    quick_titulo = st.text_input("Título")
                    quick_ctx = st.selectbox("Contexto", CONTEXTOS[1:])
                    quick_data = st.date_input("Prazo", datetime.now())
                    if st.form_submit_button("Criar"):
                        if quick_titulo:
                            supabase.table("chamados").insert({
                                "titulo": quick_titulo,
                                "contexto": quick_ctx,
                                "data_entrega": str(quick_data),
                                "status": status,
                                "ordem": 0,
                                "cor": "#ffffff"
                            }).execute()
                            st.rerun()

            if not df_chamados.empty:
                df_col = df_chamados[df_chamados["status"] == status]
                
                for idx, item in df_col.reset_index(drop=True).iterrows():
                    cor_card = item.get("cor", "#ffffff") if item.get("cor") else "#ffffff"
                    
                    with st.container(border=True):
                        # Fundo personalizado
                        st.markdown(f"<div style='background-color: {cor_card}; padding: 4px; border-radius: 4px;'><b>[{item['contexto']}]</b> {item['titulo']}</div>", unsafe_allow_html=True)
                        st.caption(f"Prazo: {item['data_entrega']}")
                        
                        # Ações minimalistas do card
                        c_mudar, c_subir, c_descer, c_cor = st.columns([2, 1, 1, 1])
                        
                        # Mover de coluna
                        with c_mudar:
                            destinos = [s for s, _ in colunas_status if s != status]
                            novo_st = st.selectbox("Mover", destinos, key=f"st_{item['id']}", index=None, placeholder="Mover...", label_visibility="collapsed")
                            if novo_st:
                                supabase.table("chamados").update({"status": novo_st}).eq("id", item['id']).execute()
                                st.rerun()

                        # Reordenar (Cima/Baixo)
                        with c_subir:
                            if st.button("↑", key=f"up_{item['id']}"):
                                supabase.table("chamados").update({"ordem": item.get("ordem", 0) - 1}).eq("id", item['id']).execute()
                                st.rerun()
                        with c_descer:
                            if st.button("↓", key=f"down_{item['id']}"):
                                supabase.table("chamados").update({"ordem": item.get("ordem", 0) + 1}).eq("id", item['id']).execute()
                                st.rerun()

                        # Alterar Cor
                        with c_cor:
                            with st.popover("🎨"):
                                nova_cor_nome = st.radio("Cor", list(CORES.keys()), key=f"c_{item['id']}")
                                if st.button("OK", key=f"btn_c_{item['id']}"):
                                    supabase.table("chamados").update({"cor": CORES[nova_cor_nome]}).eq("id", item['id']).execute()
                                    st.rerun()

# --- CALENDÁRIO ---
with aba_calendario:
    if not df_chamados.empty:
        eventos = [{"title": f"[{item['contexto']}] {item['titulo']}", "start": item['data_entrega'], "end": item['data_entrega']} for _, item in df_chamados.iterrows()]
        calendar(events=eventos, options={"initialView": "dayGridMonth"}, key="agenda_minimal")