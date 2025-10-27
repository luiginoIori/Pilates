import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date, time

# Configuração da página
st.set_page_config(
    page_title="Nova Agenda",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simulação de banco de dados simples
def authenticate_user(email, password):
    """Função simulada de autenticação"""
    # Login padrão para demo
    if email == "admin@pilates.com" and password == "admin123":
        return {"id": 1, "name": "Admin", "type": "master", "email": email}
    elif email == "cliente@pilates.com" and password == "cliente123":
        return {"id": 2, "name": "Cliente Demo", "type": "client", "email": email}
    return None

def login_page():
    """Página de login"""
    st.title("🧘‍♀️ Agenda Pilates")
    st.markdown("---")
    
    # Centralize login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="digite seu email")
            password = st.text_input("Senha", type="password", placeholder="digite sua senha")
            
            login_button = st.form_submit_button("Entrar", use_container_width=True)
            
            if login_button:
                if email and password:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Email ou senha incorretos!")
                else:
                    st.error("Por favor, preencha todos os campos!")
        
        # Informações de login padrão
        with st.expander("ℹ️ Informações de Login"):
            st.info("""            
            **Logins de demonstração:**
            - Admin: admin@pilates.com / admin123
            - Cliente: cliente@pilates.com / cliente123
            
            **Funcionalidades:**
            - Master: Gerencia tudo (clientes, equipamentos, agendamentos)
            - Cliente: Visualiza apenas seus agendamentos
            """)

def logout():
    """Função de logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def show_home():
    """Página inicial"""
    st.header("🏠 Bem-vindo à Nova Agenda")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Eventos Hoje",
            value="5",
            delta="2"
        )
    
    with col2:
        st.metric(
            label="Eventos Esta Semana",
            value="23",
            delta="-1"
        )
    
    with col3:
        st.metric(
            label="Total de Eventos",
            value="156",
            delta="12"
        )
    
    st.markdown("---")
    
    # Resumo do dia
    st.subheader("📋 Resumo do Dia")
    today = datetime.now().strftime("%d/%m/%Y")
    st.write(f"**Data:** {today}")
    
    # Eventos próximos (exemplo)
    st.subheader("⏰ Próximos Eventos")
    events_data = {
        "Horário": ["09:00", "14:30", "16:00"],
        "Evento": ["Aula de Pilates", "Fisioterapia", "Aula Experimental"],
        "Status": ["Confirmado", "Pendente", "Confirmado"]
    }
    df = pd.DataFrame(events_data)
    st.dataframe(df, use_container_width=True)

def show_agenda():
    """Página da agenda"""
    st.header("📅 Agenda")
    
    # Formulário para adicionar evento
    with st.expander("➕ Adicionar Novo Evento"):
        with st.form("new_event"):
            col1, col2 = st.columns(2)
            
            with col1:
                event_title = st.text_input("Título do Evento")
                event_date = st.date_input("Data", value=date.today())
            
            with col2:
                event_time = st.time_input("Horário", value=time(9, 0))
                event_type = st.selectbox("Tipo", ["Pilates", "Fisioterapia", "Aula Experimental", "Outro"])
            
            event_description = st.text_area("Descrição")
            
            submitted = st.form_submit_button("Adicionar Evento")
            
            if submitted:
                st.success(f"Evento '{event_title}' adicionado com sucesso!")
    
    # Lista de eventos
    st.subheader("📋 Eventos Agendados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_date = st.date_input("Filtrar por data", value=date.today())
    with col2:
        filter_type = st.selectbox("Filtrar por tipo", ["Todos", "Pilates", "Fisioterapia", "Aula Experimental", "Outro"])
    with col3:
        filter_status = st.selectbox("Filtrar por status", ["Todos", "Confirmado", "Pendente", "Cancelado"])
    
    # Exemplo de dados de eventos
    sample_events = {
        "Data": ["27/10/2025", "27/10/2025", "28/10/2025", "29/10/2025"],
        "Horário": ["09:00", "14:30", "10:00", "15:00"],
        "Título": ["João Silva", "Maria Santos", "Pedro Costa", "Ana Lima"],
        "Tipo": ["Pilates", "Fisioterapia", "Aula Experimental", "Pilates"],
        "Status": ["Confirmado", "Pendente", "Confirmado", "Confirmado"]
    }
    
    df_events = pd.DataFrame(sample_events)
    st.dataframe(df_events, use_container_width=True)

def show_reports():
    """Página de relatórios"""
    st.header("📊 Relatórios")
    
    # Gráfico de eventos por tipo
    st.subheader("Eventos por Tipo")
    event_types = ["Pilates", "Fisioterapia", "Aula Experimental", "Outro"]
    event_counts = [45, 30, 15, 10]
    
    fig = px.pie(
        values=event_counts,
        names=event_types,
        title="Distribuição de Eventos por Tipo"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de eventos por mês
    st.subheader("Eventos por Mês")
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    events_per_month = [20, 25, 30, 28, 35, 40]
    
    fig_bar = px.bar(
        x=months,
        y=events_per_month,
        title="Número de Eventos por Mês",
        labels={"x": "Mês", "y": "Número de Eventos"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def show_settings():
    """Página de configurações"""
    st.header("⚙️ Configurações")
    
    with st.expander("🎨 Personalização"):
        theme = st.selectbox("Tema", ["Claro", "Escuro", "Auto"])
        language = st.selectbox("Idioma", ["Português", "English", "Español"])
        timezone = st.selectbox("Fuso Horário", ["GMT-3 (Brasília)", "GMT-5 (Nova York)", "GMT+0 (Londres)"])
    
    with st.expander("📧 Notificações"):
        email_notifications = st.checkbox("Notificações por email", value=True)
        push_notifications = st.checkbox("Notificações push", value=True)
        reminder_time = st.selectbox("Lembrete antes do evento", ["5 min", "15 min", "30 min", "1 hora"])
    
    with st.expander("🔒 Privacidade"):
        share_calendar = st.checkbox("Permitir compartilhamento do calendário")
        public_events = st.checkbox("Eventos públicos visíveis")
    
    if st.button("💾 Salvar Configurações"):
        st.success("Configurações salvas com sucesso!")

def show_simple_dashboard():
    """Dashboard simplificado"""
    st.sidebar.title("Menu")
    page = st.sidebar.selectbox(
        "Escolha uma opção:",
        ["Home", "Agenda", "Relatórios", "Configurações"]
    )
    
    if page == "Home":
        show_home()
    elif page == "Agenda":
        show_agenda()
    elif page == "Relatórios":
        show_reports()
    elif page == "Configurações":
        show_settings()

def main():
    """Função principal"""
    # Inicializar session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Verificar autenticação
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Header com informações do usuário
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.title("🧘‍♀️ Agenda Pilates")
    
    with col2:
        if 'user' in st.session_state:
            user_type = "Master" if st.session_state.user['type'] == 'master' else "Cliente"
            st.info(f"👤 {st.session_state.user['name']} ({user_type})")
    
    with col3:
        if st.button("🚪 Sair", use_container_width=True, key="logout_btn"):
            logout()
    
    st.markdown("---")
    
    # Mostrar dashboard simples
    show_simple_dashboard()

if __name__ == "__main__":
    main()