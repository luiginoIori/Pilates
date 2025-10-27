import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date, time
import sqlite3
import json

# Configuração da página
st.set_page_config(
    page_title="Nova Agenda",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Timezone de Brasília  
def get_brasilia_now():
    """Retorna datetime atual no timezone de Brasília"""
    return datetime.now()

def get_brasilia_today():
    """Retorna date de hoje no timezone de Brasília"""
    return get_brasilia_now().date()

# Função auxiliar para formatar datas no padrão brasileiro
def format_date_br(date_str):
    """Converte data de YYYY-MM-DD para DD/MM/YYYY"""
    if not date_str:
        return ""
    try:
        if isinstance(date_str, str):
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        elif isinstance(date_str, (date, datetime)):
            dt = date_str
        else:
            return date_str
        return dt.strftime('%d/%m/%Y')
    except:
        return date_str

# Classe simulada de banco de dados
class MockDatabase:
    def authenticate_user(self, email, password):
        """Função simulada de autenticação"""
        if email == "admin@pilates.com" and password == "admin123":
            return {"id": 1, "name": "Admin", "type": "master", "email": email}
        elif email == "cliente@pilates.com" and password == "cliente123":
            return {"id": 2, "name": "Cliente Demo", "type": "client", "email": email}
        return None
    
    def get_appointments(self, client_id=None):
        """Retorna appointments simulados"""
        sample_appointments = [
            {"id": 1, "client_id": 2, "date": "2025-10-27", "time": "09:00", "status": "scheduled", "attended": None, "last_equipment_used": "Reformer 1", "day_of_week": 7},
            {"id": 2, "client_id": 2, "date": "2025-10-28", "time": "14:00", "status": "scheduled", "attended": None, "last_equipment_used": "Cadillac 1", "day_of_week": 1},
            {"id": 3, "client_id": 2, "date": "2025-10-25", "time": "09:00", "status": "scheduled", "attended": 1, "last_equipment_used": "Reformer 2", "day_of_week": 5},
            {"id": 4, "client_id": 2, "date": "2025-10-24", "time": "14:00", "status": "scheduled", "attended": 0, "last_equipment_used": "Chair 1", "day_of_week": 4},
        ]
        if client_id:
            return [apt for apt in sample_appointments if apt["client_id"] == client_id]
        return sample_appointments
    
    def get_week_schedule_data_with_details(self, week_start):
        """Retorna dados simulados da grade semanal"""
        return []
    
    def get_clients(self):
        """Retorna clientes simulados"""
        return [
            {"id": 1, "name": "Admin", "email": "admin@pilates.com", "phone": "(11) 99999-0000", "medical_history": "", "data_inicio_contrato": "2025-01-01", "tipo_contrato": "fixo", "sessoes_contratadas": 0, "sessoes_utilizadas": 0, "dias_semana": '{"1": "09:00", "3": "14:00"}', "contrato_ativo": 1},
            {"id": 2, "name": "Cliente Demo", "email": "cliente@pilates.com", "phone": "(11) 99999-1111", "medical_history": "Nenhuma restrição", "data_inicio_contrato": "2025-01-01", "tipo_contrato": "fixo", "sessoes_contratadas": 0, "sessoes_utilizadas": 0, "dias_semana": '{"1": "09:00", "3": "14:00"}', "contrato_ativo": 1},
        ]
    
    def get_client_schedule(self, client_id):
        """Retorna horários fixos do cliente"""
        return [
            {"id": 1, "client_id": client_id, "day_of_week": 1, "time": "09:00", "equipment_name": "Reformer 1"},
            {"id": 2, "client_id": client_id, "day_of_week": 3, "time": "14:00", "equipment_name": "Cadillac 1"},
        ]
    
    def get_equipment(self):
        """Retorna equipamentos simulados"""
        return [
            {"id": 1, "name": "Reformer 1", "description": "Equipamento principal para exercícios de Pilates"},
            {"id": 2, "name": "Cadillac 1", "description": "Mesa com barras e molas para exercícios avançados"},
            {"id": 3, "name": "Chair 1", "description": "Cadeira de Pilates para fortalecimento"},
            {"id": 4, "name": "Barrel 1", "description": "Barril para exercícios de flexibilidade"},
        ]
    
    def get_appointment_by_details(self, client_id, date, time):
        """Busca appointment específico"""
        appointments = self.get_appointments()
        for apt in appointments:
            if apt["client_id"] == client_id and apt["date"] == date and apt["time"] == time:
                return apt
        return None
    
    def mark_attendance(self, appointment_id, attended):
        """Simula marcação de presença"""
        return True
    
    def create_appointment(self, client_id, date, time, sequence_id=None):
        """Simula criação de appointment"""
        return True
    
    def cancel_appointment(self, appointment_id):
        """Simula cancelamento de appointment"""
        return True
    
    def update_appointment_notifications(self, appointment_id, delay_msg, absence_msg):
        """Simula atualização de notificações"""
        return True
    
    def get_all_client_schedules(self):
        """Retorna todos os horários fixos"""
        return []
    
    def create_client_schedule(self, client_id, day_of_week, time):
        """Simula criação de horário fixo"""
        return True
    
    def delete_client_schedule(self, schedule_id):
        """Simula exclusão de horário fixo"""
        return True
    
    def create_recurring_appointments(self, client_id, start_date, days_times, sequence_id, weeks_ahead):
        """Simula criação de appointments recorrentes"""
        return 12  # Número simulado de appointments criados
    
    def get_client_sequences(self, client_id, day_of_week):
        """Retorna sequências do cliente"""
        return [{"id": 1, "name": "Sequência Básica"}]
    
    def gerar_appointments_cliente(self, client_id, dias_horarios):
        """Simula geração de appointments para cliente"""
        return len(dias_horarios) * 12  # Simula 12 appointments por dia selecionado
    
    def delete_equipment(self, equipment_id):
        """Simula exclusão de equipamento"""
        return True
    
    def get_equipment_sequences(self, equipment_id):
        """Retorna sequências de um equipamento"""
        return [
            {"id": 1, "name": "Sequência Básica", "description": "Exercícios básicos"},
            {"id": 2, "name": "Sequência Avançada", "description": "Exercícios avançados"},
        ]
    
    def delete_equipment_sequence(self, sequence_id):
        """Simula exclusão de sequência de equipamento"""
        return True
    
    def get_contas_receber(self, client_id=None):
        """Retorna contas a receber simuladas"""
        sample_contas = [
            {
                "id": 1,
                "client_id": 2,
                "client_name": "Cliente Demo",
                "valor": 300.00,
                "data_vencimento": "2025-11-01",
                "status": "pendente",
                "descricao": "Mensalidade Outubro",
                "data_criacao": "2025-10-01"
            },
            {
                "id": 2,
                "client_id": 2,
                "client_name": "Cliente Demo", 
                "valor": 300.00,
                "data_vencimento": "2025-12-01",
                "status": "pendente",
                "descricao": "Mensalidade Novembro",
                "data_criacao": "2025-11-01"
            }
        ]
        if client_id:
            return [conta for conta in sample_contas if conta["client_id"] == client_id]
        return sample_contas
    
    def get_receitas_pagas(self):
        """Retorna receitas pagas simuladas"""
        return [
            {
                "id": 1,
                "client_id": 2,
                "client_name": "Cliente Demo",
                "valor": 300.00,
                "data_pagamento": "2025-09-15",
                "descricao": "Mensalidade Setembro",
                "metodo_pagamento": "PIX"
            }
        ]
    
    def get_despesas(self):
        """Retorna despesas simuladas"""
        return [
            {
                "id": 1,
                "descricao": "Aluguel do espaço",
                "valor": 1500.00,
                "data": "2025-10-01",
                "categoria": "Aluguel",
                "status": "pago"
            },
            {
                "id": 2,
                "descricao": "Energia elétrica",
                "valor": 200.00,
                "data": "2025-10-15",
                "categoria": "Utilities",
                "status": "pago"
            }
        ]

# Instância global do banco simulado
db = MockDatabase()

def login_page():
    """Página de login"""
    st.set_page_config(
        page_title="Agenda Pilates",
        page_icon="🧘‍♀️",
        layout="wide"
    )
    
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
                    user = db.authenticate_user(email, password)
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
            **Funcionalidades:**
            - Master: Gerencia tudo (clientes, equipamentos, agendamentos)
            - Cliente: Visualiza apenas seus agendamentos e envia notificações
            """)

def logout():
    """Função de logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def check_authentication():
    """Verifica se usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_page()
        st.stop()

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
    
    # Roteamento baseado no tipo de usuário
    if st.session_state.user['type'] == 'master':
        master_dashboard()
    else:
        client_dashboard()
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.title("🧘‍♀️ Agenda Pilates")
    
    with col2:
        if 'user' in st.session_state:
            user_type = "Master" if st.session_state.user['type'] == 'master' else "Cliente"
            st.info(f"👤 {st.session_state.user['name']} ({user_type})")
    
    with col3:
        if st.button("🚪 Sair", use_container_width=True, key="master_logout_btn"):
            logout()
    
    st.markdown("---")
    
    # Roteamento baseado no tipo de usuário
    if st.session_state.user['type'] == 'master':
        master_dashboard()
    else:
        client_dashboard()

def master_dashboard():
    """Dashboard do usuário Master"""
    
    # Verificar notificações não lidas
    import sqlite3
    conn = sqlite3.connect("pilates.db")
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM notifications WHERE is_read = 0')
    unread_count = cursor.fetchone()[0]
    conn.close()
    
    # Balão de notificação
    if unread_count > 0:
        col_title, col_notif = st.columns([3, 1])
        with col_title:
            st.subheader("🔧 Painel do Administrador")
        with col_notif:
            if st.button(f"🔔 {unread_count} Nova{'s' if unread_count > 1 else ''} Notificaç{'ões' if unread_count > 1 else 'ão'}", 
                        type="primary", use_container_width=True):
                st.session_state['show_notifications_popup'] = True
                st.rerun()
    else:
        st.subheader("🔧 Painel do Administrador")
    
    # Popup de Notificações
    if st.session_state.get('show_notifications_popup', False):
        st.markdown("---")
        st.markdown("### 🔔 Notificações Recentes")
        
        conn = sqlite3.connect("pilates.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT n.id, n.client_id, n.client_name, n.type, n.message, n.is_read, n.created_at,
                   u.phone
            FROM notifications n
            LEFT JOIN users u ON n.client_id = u.id
            WHERE n.is_read = 0
            ORDER BY n.created_at DESC
            LIMIT 5
        ''')
        
        recent_notifications = cursor.fetchall()
        conn.close()
        
        if recent_notifications:
            for notif in recent_notifications:
                notif_id, client_id, client_name, notif_type, message, is_read, created_at, phone = notif
                
                from datetime import datetime
                if notif_type == "Falta":
                    icon = "🔴"
                    bg_color = "#ffebee"
                elif notif_type == "Atraso":
                    icon = "🟡"
                    bg_color = "#fff9e6"
                else:
                    icon = "🔵"
                    bg_color = "#e3f2fd"
                
                with st.expander(f"{icon} {notif_type} - {client_name} ({datetime.fromisoformat(created_at).strftime('%d/%m %H:%M')})"):
                    st.write(f"**Mensagem:** {message}")
                    if phone:
                        st.write(f"**Telefone:** {phone}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✅ Marcar como Lida", key=f"popup_read_{notif_id}", use_container_width=True):
                            conn = sqlite3.connect("pilates.db")
                            cursor = conn.cursor()
                            cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🗑️ Limpar", key=f"popup_delete_{notif_id}", use_container_width=True, type="secondary"):
                            conn = sqlite3.connect("pilates.db")
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM notifications WHERE id = ?', (notif_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
            
            col_close, col_all = st.columns(2)
            with col_close:
                if st.button("✖️ Fechar", use_container_width=True):
                    st.session_state['show_notifications_popup'] = False
                    st.rerun()
            with col_all:
                st.info("� Veja todas as notificações na aba 'Notificações'")
        else:
            st.info("Nenhuma notificação não lida")
            if st.button("✖️ Fechar"):
                st.session_state['show_notifications_popup'] = False
                st.rerun()
        
        st.markdown("---")
    
    # Menu de navegação
    default_tab = st.session_state.get('active_tab', 0)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Agendamentos", 
        "👥 Clientes", 
        "🏋️ Equipamentos", 
        "⏰ Horários Fixos",
        "💰 Financeiro",
        "🔔 Notificações",
        "� Histórico de Presença"
    ])
    
    with tab1:
        appointments_tab()
    
    with tab2:
        clients_tab()
    
    with tab3:
        equipment_tab()
    
    with tab4:
        schedules_overview_tab()
    
    with tab5:
        financial_tab()
    
    with tab6:
        notifications_tab()
    
    with tab7:
        attendance_history_tab()

def client_dashboard():
    """Dashboard do cliente"""
    from datetime import datetime, timedelta
    import calendar
    
    user_id = st.session_state.user['id']
    today = get_brasilia_today()
    
    # CSS para reduzir espaços
    st.markdown("""
    <style>
    h2 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .calendar-cell {
        text-align: center;
        padding: 8px;
        border: 1px solid #ddd;
        min-height: 40px;
    }
    .calendar-cell-blue {
        background-color: #90CAF9;
        font-weight: bold;
    }
    .calendar-cell-red {
        background-color: #EF9A9A;
        font-weight: bold;
    }
    .calendar-cell-empty {
        background-color: #f5f5f5;
    }
    .calendar-header {
        text-align: center;
        font-weight: bold;
        padding: 5px;
        background-color: #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Menu lateral para cliente
    st.sidebar.title(f"👤 {st.session_state.user['name']}")
    st.sidebar.markdown("---")
    
    menu_option = st.sidebar.radio(
        "Menu:",
        ["🏠 Página Principal", "📅 Próximas Aulas", "📚 Histórico de Aulas", "� Notificar Instrutor"],
        key="client_menu"
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True, key="client_logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # ===== PÁGINA PRINCIPAL =====
    if menu_option == "🏠 Página Principal":
        st.title("🏠 Bem-vindo ao Agenda Pilates")
        
        # Resumo rápido
        all_appointments = db.get_appointments(client_id=user_id)
        today_str = today.strftime('%Y-%m-%d')
        
        # Próximas aulas (próximos 7 dias)
        seven_days_ahead = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        next_week = [apt for apt in all_appointments 
                    if apt['date'] >= today_str and apt['date'] <= seven_days_ahead 
                    and apt['status'] != 'cancelled']
        
        # Total de presenças
        total_presencas = len([apt for apt in all_appointments if apt.get('attended') == 1])
        total_faltas = len([apt for apt in all_appointments if apt.get('attended') == 0])
        
        # Cards de resumo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Próximas Aulas (7 dias)", len(next_week))
        
        with col2:
            st.metric("✅ Total de Presenças", total_presencas)
        
        with col3:
            st.metric("❌ Total de Faltas", total_faltas)
        
        with col4:
            if total_presencas + total_faltas > 0:
                taxa = (total_presencas / (total_presencas + total_faltas)) * 100
                st.metric("📊 Taxa de Presença", f"{taxa:.1f}%")
            else:
                st.metric("📊 Taxa de Presença", "0%")
        
        st.markdown("---")
        
        # Agendamento de hoje
        today_appointments = [apt for apt in all_appointments if apt['date'] == today_str]
        
        if today_appointments:
            st.success("🎯 **Você tem aula hoje!**")
            for apt in today_appointments:
                st.markdown(f"""
                <div style='padding: 15px; margin: 10px 0; background-color: #e3f2fd; border-left: 5px solid #2196F3; border-radius: 5px;'>
                    <h3 style='margin: 0;'>🕐 {apt['time']}</h3>
                    <p style='margin: 5px 0;'>📍 Equipamento: {apt.get('last_equipment_used', 'Não definido')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📅 Você não tem aula agendada para hoje")
        
        st.markdown("---")
        
        # Próximas 3 aulas
        st.subheader("📆 Suas Próximas Aulas")
        future_apts = [apt for apt in all_appointments 
                      if apt['date'] > today_str and apt['status'] != 'cancelled']
        future_apts.sort(key=lambda x: (x['date'], x['time']))
        
        if future_apts[:3]:
            for apt in future_apts[:3]:
                apt_date = datetime.strptime(apt['date'], '%Y-%m-%d')
                day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][apt_date.weekday()]
                
                st.markdown(f"""
                <div style='padding: 10px; margin: 5px 0; background-color: #f0f8ff; border-left: 4px solid #4CAF50; border-radius: 4px;'>
                    <strong>📅 {format_date_br(apt['date'])}</strong> ({day_name}) às <strong>{apt['time']}</strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Você não tem aulas agendadas. Entre em contato com o instrutor.")
    
    # ===== PRÓXIMAS AULAS =====
    elif menu_option == "📅 Próximas Aulas":
        st.title("📅 Próximas Aulas")
        
        all_appointments = db.get_appointments(client_id=user_id)
        today_str = today.strftime('%Y-%m-%d')
        
        # Filtrar aulas futuras
        future_appointments = [apt for apt in all_appointments 
                              if apt['date'] >= today_str and apt['status'] != 'cancelled']
        future_appointments.sort(key=lambda x: (x['date'], x['time']))
        
        # Filtro de período
        col1, col2 = st.columns(2)
        with col1:
            days_filter = st.selectbox("Período:", [7, 15, 30, 60, 90], index=1, format_func=lambda x: f"Próximos {x} dias")
        
        max_date = (today + timedelta(days=days_filter)).strftime('%Y-%m-%d')
        filtered_appointments = [apt for apt in future_appointments if apt['date'] <= max_date]
        
        st.info(f"📆 Mostrando aulas de {format_date_br(today_str)} até {format_date_br(max_date)}")
        st.success(f"✅ Total: **{len(filtered_appointments)}** aulas agendadas")
        
        if filtered_appointments:
            for apt in filtered_appointments:
                apt_date = datetime.strptime(apt['date'], '%Y-%m-%d')
                day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][apt_date.weekday()]
                equipment = apt.get('last_equipment_used', 'Não definido')
                
                st.markdown(f"""
                <div style='padding: 12px; margin: 6px 0; background-color: #e8f5e9; border-left: 4px solid #4CAF50; border-radius: 4px;'>
                    <strong>📅 {format_date_br(apt['date'])}</strong> ({day_name}) às <strong>🕐 {apt['time']}</strong><br>
                    <small>🏋️ Equipamento: {equipment}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Você não tem aulas agendadas para este período.")
    
    # ===== HISTÓRICO DE AULAS (CALENDÁRIO) =====
    elif menu_option == "📚 Histórico de Aulas":
        st.title("📚 Histórico de Aulas")
        
        # Buscar todos os appointments
        all_appointments = db.get_appointments(client_id=user_id)
        
        # Criar dicionário de datas com status
        appointments_by_date = {}
        for apt in all_appointments:
            if apt.get('attended') is not None:
                appointments_by_date[apt['date']] = apt.get('attended')
        
        # Estatísticas
        total_presencas = len([a for a in all_appointments if a.get('attended') == 1])
        total_faltas = len([a for a in all_appointments if a.get('attended') == 0])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Total de Presenças", total_presencas)
        with col2:
            st.metric("❌ Total de Faltas", total_faltas)
        with col3:
            if total_presencas + total_faltas > 0:
                taxa = (total_presencas / (total_presencas + total_faltas)) * 100
                st.metric("📊 Taxa de Presença", f"{taxa:.1f}%")
            else:
                st.metric("📊 Taxa de Presença", "0%")
        
        st.markdown("---")
        
        # Seletor de mês
        col_mes, col_ano = st.columns(2)
        with col_mes:
            mes_selecionado = st.selectbox("Mês:", list(range(1, 13)), 
                                          index=today.month - 1,
                                          format_func=lambda x: [
                                              "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                                              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                                          ][x-1])
        with col_ano:
            ano_selecionado = st.selectbox("Ano:", list(range(today.year - 1, today.year + 2)), 
                                          index=1)
        
        # Criar calendário
        st.markdown(f"### Calendário - {['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mes_selecionado-1]} {ano_selecionado}")
        
        cal = calendar.monthcalendar(ano_selecionado, mes_selecionado)
        
        # Cabeçalho
        dias_semana_short = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        
        html = '<table style="width:100%; border-collapse: collapse;">'
        html += '<tr>'
        for day in dias_semana_short:
            html += f'<th class="calendar-header">{day}</th>'
        html += '</tr>'
        
        # Dias do mês
        for week in cal:
            html += '<tr>'
            for day in week:
                if day == 0:
                    html += '<td class="calendar-cell calendar-cell-empty"></td>'
                else:
                    date_str = f"{ano_selecionado:04d}-{mes_selecionado:02d}-{day:02d}"
                    
                    if date_str in appointments_by_date:
                        if appointments_by_date[date_str] == 1:
                            cell_class = "calendar-cell-blue"
                            icon = "✓"
                        else:
                            cell_class = "calendar-cell-red"
                            icon = "✗"
                        html += f'<td class="calendar-cell {cell_class}">{day}<br><small>{icon}</small></td>'
                    else:
                        html += f'<td class="calendar-cell">{day}</td>'
            html += '</tr>'
        
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("🔵 **Azul** = Presença | 🔴 **Vermelho** = Falta")
        
        # Lista detalhada do mês
        month_appointments = [apt for apt in all_appointments 
                            if apt['date'].startswith(f"{ano_selecionado:04d}-{mes_selecionado:02d}")
                            and apt.get('attended') is not None]
        month_appointments.sort(key=lambda x: x['date'], reverse=True)
        
        if month_appointments:
            st.markdown("### 📋 Detalhes das Aulas")
            for apt in month_appointments:
                status_icon = "✅" if apt.get('attended') == 1 else "❌"
                status_text = "Presença" if apt.get('attended') == 1 else "Falta"
                bg_color = "#e8f5e9" if apt.get('attended') == 1 else "#ffebee"
                
                st.markdown(f"""
                <div style='padding: 10px; margin: 5px 0; background-color: {bg_color}; border-radius: 4px;'>
                    {status_icon} <strong>{format_date_br(apt['date'])}</strong> às {apt['time']} - {status_text}<br>
                    <small>🏋️ Equipamento: {apt.get('last_equipment_used', 'Não registrado')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ===== PRÓXIMOS AGENDAMENTOS (COM NOTIFICAÇÕES) =====
    # ===== NOTIFICAR INSTRUTOR (COM PRÓXIMOS AGENDAMENTOS) =====
    elif menu_option == "� Notificar Instrutor":
        st.title("� Notificar Instrutor")
        st.info("💡 Aqui você pode notificar o instrutor sobre atrasos ou faltas nos seus próximos agendamentos")
        
        # Mostrar mensagem de sucesso se acabou de enviar
        if st.session_state.get('appointment_notif_sent', False):
            st.success("✅ Notificação enviada ao instrutor!")
            st.session_state.appointment_notif_sent = False
        
        all_appointments = db.get_appointments(client_id=user_id)
        today_str = today.strftime('%Y-%m-%d')
        future_appointments = [apt for apt in all_appointments 
                              if apt['date'] >= today_str and apt['status'] != 'cancelled']
        future_appointments.sort(key=lambda x: (x['date'], x['time']))
        
        if future_appointments:
            for apt in future_appointments[:10]:  # Mostrar próximos 10
                with st.expander(f"📅 {format_date_br(apt['date'])} às {apt['time']}"):
                    st.write(f"**Equipamento:** {apt.get('last_equipment_used', 'Não definido')}")
                    st.markdown("---")
                    
                    # Formulário de notificação
                    with st.form(f"notif_form_{apt['id']}", clear_on_submit=True):
                        st.write("**📢 Notificar Instrutor:**")
                        
                        notif_type = st.radio("Tipo:", ["Atraso", "Falta"], 
                                             key=f"type_{apt['id']}", horizontal=True)
                        notif_msg = st.text_area("Mensagem:", 
                                                key=f"msg_{apt['id']}",
                                                placeholder="Ex: Vou atrasar 15 minutos...",
                                                height=80)
                        
                        submit_apt_notif = st.form_submit_button("📤 Enviar Notificação", use_container_width=True)
                    
                    # Processar fora do form
                    if submit_apt_notif:
                        if notif_msg:
                            delay_msg = notif_msg if notif_type == "Atraso" else None
                            absence_msg = notif_msg if notif_type == "Falta" else None
                            
                            if db.update_appointment_notifications(apt['id'], delay_msg, absence_msg):
                                st.session_state.appointment_notif_sent = True
                                st.rerun()
                            else:
                                st.error("Erro ao enviar notificação")
                        else:
                            st.error("Por favor, escreva uma mensagem")
        else:
            st.info("Você não tem agendamentos futuros")

def appointments_tab():
    """Aba de gerenciamento de agendamentos"""
    from datetime import datetime, timedelta
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📅 Grade de Horários Semanal")
    
    with col2:
        if st.button("➕ Novo Agendamento", use_container_width=True):
            st.session_state.show_appointment_form = True
    
    # CSS para reduzir espaços (sem afetar padding-top global)
    st.markdown("""
    <style>
    h2 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stSelectbox {
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Seleção de semana
    col_week, col_nav = st.columns([3, 2])
    
    with col_week:
        # Inicializar data da semana se não existir
        if 'selected_week_start' not in st.session_state:
            today = get_brasilia_now()
            # Início da semana atual (segunda-feira)
            week_start = today - timedelta(days=today.weekday())
            st.session_state.selected_week_start = week_start.strftime('%Y-%m-%d')

        # Gerar 52 semanas futuras a partir da semana selecionada (inclui a atual)
        current_week = datetime.strptime(st.session_state.selected_week_start, '%Y-%m-%d')
        generated_weeks = []
        for i in range(0, 52):
            wk_start = current_week + timedelta(days=7 * i)
            wk_end = wk_start + timedelta(days=4)
            label = f"Semana de {wk_start.strftime('%d/%m')} a {wk_end.strftime('%d/%m')}"
            generated_weeks.append({'label': label, 'start_date': wk_start.strftime('%Y-%m-%d')})

        # Construir opções de seleção
        week_options = {w['label']: w['start_date'] for w in generated_weeks}

        # Encontrar semana atual selecionada
        current_week_label = next((label for label, date in week_options.items()
                                  if date == st.session_state.selected_week_start),
                                  list(week_options.keys())[0])

        selected_week_label = st.selectbox(
            "Selecionar Semana:",
            options=list(week_options.keys()),
            index=list(week_options.keys()).index(current_week_label)
        )

        if selected_week_label in week_options:
            st.session_state.selected_week_start = week_options[selected_week_label]
    
    with col_nav:
        st.write("**Navegação:**")
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if st.button("⬅️ Semana Anterior", use_container_width=True):
                current_date = datetime.strptime(st.session_state.selected_week_start, '%Y-%m-%d')
                previous_week = current_date - timedelta(days=7)
                st.session_state.selected_week_start = previous_week.strftime('%Y-%m-%d')
                st.rerun()
        
        with col_next:
            if st.button("Próxima Semana ➡️", use_container_width=True):
                current_date = datetime.strptime(st.session_state.selected_week_start, '%Y-%m-%d')
                next_week = current_date + timedelta(days=7)
                st.session_state.selected_week_start = next_week.strftime('%Y-%m-%d')
                st.rerun()
    
    # Mostrar grade de horários da semana selecionada com nomes clicáveis
    schedule_data_raw = db.get_week_schedule_data_with_details(st.session_state.selected_week_start)
    
    # Configurar display da tabela
    if schedule_data_raw:
        st.markdown("**👆 Clique no nome de um cliente para editar**")
        
        # Criar grade com botões clicáveis
        hours = [f"{h:02d}:00" for h in range(6, 21)]
        
        # Obter datas da semana
        from datetime import datetime, timedelta
        start = datetime.strptime(st.session_state.selected_week_start, '%Y-%m-%d')
        week_days = []
        for i in range(5):
            current_date = start + timedelta(days=i)
            day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][i]
            week_days.append({
                'name': day_name,
                'date': current_date.strftime('%d/%m'),
                'day_of_week': i + 1
            })
        
        # CSS para linhas de separação e estilo do checkbox
        st.markdown("""
        <style>
        .stColumn {
            border-right: 1px solid #e0e0e0;
            padding: 2px;
        }
        .stColumn:last-child {
            border-right: none;
        }
        /* Estilizar checkbox - reduzir espaçamento vertical */
        div[data-testid="stCheckbox"] {
            margin-bottom: -15px !important;
            margin-top: -8px !important;
        }
        div[data-testid="stCheckbox"] label {
            padding: 0px !important;
            margin: 0px !important;
            gap: 0px !important;
        }
        div[data-testid="stCheckbox"] label p {
            font-size: 10px !important;
            font-weight: bold !important;
            margin: 0px !important;
            padding: 0px !important;
            line-height: 0.8 !important;
        }
        /* Posicionar texto muito próximo ao checkbox */
        div[data-testid="stCheckbox"] label span[data-testid="stMarkdownContainer"] {
            margin-left: -2px !important;
            padding-left: 0px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Cabeçalho da grade
        header_cols = st.columns([1] + [2]*5)
        with header_cols[0]:
            st.markdown("**Horário**")
        for i, day in enumerate(week_days):
            with header_cols[i+1]:
                st.markdown(f"**{day['name']} {format_date_br(day['date'])}**")
        
        st.markdown("<hr style='margin: 5px 0 2px 0;'>", unsafe_allow_html=True)
        
        # Linhas de horários com separadores
        for idx, hour_data in enumerate(schedule_data_raw):
            # Verificar se a linha tem algum cliente
            has_clients = any(day_data['clients'] for day_data in hour_data['days'])
            
            # Usar altura menor para linhas vazias
            if has_clients:
                cols = st.columns([1] + [2]*5)
            else:
                # Linha vazia - usar container compacto
                st.markdown(f"<div style='padding: 1px 0;'><small><b>{hour_data['time']}</b></small></div>", unsafe_allow_html=True)
                if idx < len(schedule_data_raw) - 1:
                    st.markdown("<hr style='margin: 1px 0; border: 0; border-top: 1px solid #f0f0f0;'>", unsafe_allow_html=True)
                continue
            
            with cols[0]:
                st.markdown(f"**{hour_data['time']}**")
            
            for i, day_data in enumerate(hour_data['days']):
                with cols[i+1]:
                    if day_data['clients']:
                        for client_idx, client_info in enumerate(day_data['clients']):
                            # Buscar informações do tipo de agendamento
                            client_schedules = db.get_client_schedule(client_info['client_id'])
                            schedule_type = "Fixo"  # Padrão
                            
                            # Procurar o tipo correto para este dia/horário
                            for sched in client_schedules:
                                if sched['day_of_week'] == day_data['day_of_week'] and sched['time'] == hour_data['time']:
                                    schedule_type = sched.get('schedule_type', 'Fixo')
                                    break
                            
                            # Buscar agendamento específico para verificar presença
                            appointment = db.get_appointment_by_details(
                                client_info['client_id'], 
                                day_data['date'], 
                                hour_data['time']
                            )
                            
                            # Container para nome + checkboxes (P e F)
                            col_name, col_checks = st.columns([3, 0.5])
                            
                            with col_name:
                                # Ícone baseado no tipo
                                if schedule_type == "Fisioterapia":
                                    icon = "🏥"
                                elif schedule_type == "Aula Experimental":
                                    icon = "🆕"
                                else:
                                    icon = "📅"
                                
                                # Garantir que o nome do cliente seja exibido
                                client_name = client_info.get('client_name', 'Cliente')
                                if not client_name or client_name == 'None':
                                    # Buscar nome do banco se não vier
                                    clients = db.get_clients()
                                    client = next((c for c in clients if c['id'] == client_info['client_id']), None)
                                    client_name = client['name'] if client else 'Cliente'
                                
                                # Botão clicável com o nome do cliente
                                btn_label = f"{icon} {client_name}"
                                if client_info.get('equipment_name'):
                                    btn_label += f" 🏋️"
                                
                                # Chave única: cliente_id + dia + hora + índice do cliente na célula
                                btn_key = f"btn_{client_info['client_id']}_{day_data['day_of_week']}_{hour_data['time'].replace(':', '')}_{client_idx}"
                                
                                if st.button(btn_label, key=btn_key, use_container_width=True):
                                    st.session_state['editing_client_id'] = client_info['client_id']
                                    st.session_state['editing_from_day'] = day_data['day_of_week']
                                    st.session_state['editing_from_time'] = hour_data['time']
                                    st.session_state['editing_is_appointment'] = client_info['has_appointment']
                                    st.session_state['editing_date'] = day_data['date']
                                    st.rerun()
                            
                            # Checkboxes de Presente e Falta (verticais)
                            with col_checks:
                                # Checkbox P (Presente)
                                chk_p_key = f"presente_{client_info['client_id']}_{day_data['date']}_{hour_data['time'].replace(':', '')}_{client_idx}"
                                current_presente = appointment.get('attended') == 1 if appointment else False
                                
                                presente_checked = st.checkbox("**P**", value=current_presente, key=chk_p_key)
                                
                                # Se marcou presente
                                if presente_checked and not current_presente:
                                    if appointment:
                                        db.mark_attendance(appointment['id'], True)
                                    else:
                                        # Criar agendamento e marcar como presente
                                        apt_created = db.create_appointment(
                                            client_info['client_id'],
                                            day_data['date'],
                                            hour_data['time']
                                        )
                                        if apt_created:
                                            new_apt = db.get_appointment_by_details(
                                                client_info['client_id'],
                                                day_data['date'],
                                                hour_data['time']
                                            )
                                            if new_apt:
                                                db.mark_attendance(new_apt['id'], True)
                                    # Limpar qualquer state de edição para forçar recarga
                                    if 'editing_client_id' in st.session_state:
                                        del st.session_state['editing_client_id']
                                    st.rerun()
                                
                                # Se desmarcou presente
                                elif not presente_checked and current_presente and appointment:
                                    db.mark_attendance(appointment['id'], None)
                                    st.rerun()
                                
                                # Checkbox F (Falta)
                                chk_f_key = f"falta_{client_info['client_id']}_{day_data['date']}_{hour_data['time'].replace(':', '')}_{client_idx}"
                                current_falta = appointment.get('attended') == 0 if appointment else False
                                
                                falta_checked = st.checkbox("**F**", value=current_falta, key=chk_f_key)
                                
                                # Se marcou falta
                                if falta_checked and not current_falta:
                                    if appointment:
                                        db.mark_attendance(appointment['id'], False)
                                    else:
                                        # Criar agendamento e marcar como falta
                                        apt_created = db.create_appointment(
                                            client_info['client_id'],
                                            day_data['date'],
                                            hour_data['time']
                                        )
                                        if apt_created:
                                            new_apt = db.get_appointment_by_details(
                                                client_info['client_id'],
                                                day_data['date'],
                                                hour_data['time']
                                            )
                                            if new_apt:
                                                db.mark_attendance(new_apt['id'], False)
                                    # Limpar qualquer state de edição para forçar recarga
                                    if 'editing_client_id' in st.session_state:
                                        del st.session_state['editing_client_id']
                                    st.rerun()
                                
                                # Se desmarcou falta
                                elif not falta_checked and current_falta and appointment:
                                    db.mark_attendance(appointment['id'], None)
                                    st.rerun()
            
            # Linha de separação entre horários com clientes
            if idx < len(schedule_data_raw) - 1:
                st.markdown("<hr style='margin: 2px 0; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
        
        # Formulário de edição (aparece abaixo da grade quando um cliente é selecionado)
        if st.session_state.get('editing_client_id'):
            st.markdown("---")
            st.markdown("---")
            
            client_id = st.session_state['editing_client_id']
            from_day = st.session_state.get('editing_from_day')
            from_time = st.session_state.get('editing_from_time')
            
            # Buscar informações do cliente
            clients = db.get_clients()
            client = next((c for c in clients if c['id'] == client_id), None)
            
            if client:
                st.subheader(f"✏️ Editando: {client['name']}")
                
                # Seção de Controle de Presença
                st.markdown("### ✅ Controle de Presença")
                
                # Verificar se é um dia específico (appointment) ou horário fixo
                editing_date = st.session_state.get('editing_date')
                is_appointment = st.session_state.get('editing_is_appointment', False)
                
                if editing_date:
                    # Buscar o agendamento
                    appointment = db.get_appointment_by_details(client_id, editing_date, from_time)
                    
                    if appointment:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**📅 Data:** {datetime.strptime(editing_date, '%Y-%m-%d').strftime('%d/%m/%Y')}")
                        
                        with col2:
                            st.write(f"**🕐 Horário:** {from_time}")
                        
                        with col3:
                            current_attendance = appointment.get('attended')
                            if current_attendance == 1:
                                st.success("✅ Presença Confirmada")
                            elif current_attendance == 0:
                                st.error("❌ Falta Registrada")
                            else:
                                st.warning("⏳ Presença Não Marcada")
                        
                        # Botões para marcar presença/falta
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button("✅ Marcar Presença", use_container_width=True, type="primary"):
                                if db.mark_attendance(appointment['id'], True):
                                    st.success("Presença marcada!")
                                    time.sleep(0.5)
                                    st.rerun()
                        
                        with col_btn2:
                            if st.button("❌ Marcar Falta", use_container_width=True):
                                if db.mark_attendance(appointment['id'], False):
                                    st.warning("Falta registrada!")
                                    time.sleep(0.5)
                                    st.rerun()
                        
                        with col_btn3:
                            if st.button("🔄 Limpar Marcação", use_container_width=True):
                                if db.mark_attendance(appointment['id'], None):
                                    st.info("Marcação removida!")
                                    time.sleep(0.5)
                                    st.rerun()
                    else:
                        st.info("📋 Não há agendamento específico para este dia. Este é um horário fixo.")
                
                st.markdown("---")
                
                # Mostrar histórico médico
                st.markdown("### 📋 Histórico Médico")
                with st.form("medical_history_form"):
                    medical_history = st.text_area(
                        "Histórico Médico:",
                        value=client.get('medical_history', ''),
                        height=150,
                        help="Informações sobre condições médicas, lesões, limitações, etc."
                    )
                    
                    if st.form_submit_button("💾 Salvar Histórico Médico"):
                        conn = sqlite3.connect("pilates.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE users 
                            SET medical_history = ?
                            WHERE id = ?
                        ''', (medical_history, client_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Histórico médico atualizado!")
                        st.rerun()
                
                st.markdown("---")
                
                # Buscar todos os horários fixos atuais do cliente (necessário em ambos os modos)
                current_schedules = db.get_client_schedule(client_id)
                
                # Verificar se clicou em uma reposição
                is_appointment = st.session_state.get('editing_is_appointment', False)
                editing_date = st.session_state.get('editing_date')
                
                if is_appointment and editing_date:
                    # MODO REPOSIÇÃO - Buscar o agendamento específico
                    st.info(f"📌 Você clicou em uma REPOSIÇÃO do dia {editing_date}")
                    
                    appointments = db.get_appointments()
                    appointment = next((apt for apt in appointments 
                                       if apt['client_id'] == client_id 
                                       and apt['date'] == editing_date 
                                       and apt['time'] == from_time
                                       and apt['status'] != 'cancelled'), None)
                    
                    if appointment:
                        with st.form("edit_appointment_form"):
                            st.write("**Detalhes da Reposição:**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Data:** {datetime.strptime(editing_date, '%Y-%m-%d').strftime('%d/%m/%Y')}")
                                # Garantir que o valor padrão não seja anterior à data mínima
                                current_date = datetime.strptime(editing_date, '%Y-%m-%d').date()
                                default_date = max(current_date, date.today())
                                new_apt_date = st.date_input("Alterar para:", 
                                                             value=default_date,
                                                             min_value=date.today(),
                                                             key="edit_apt_date")
                            
                            with col2:
                                st.write(f"**Horário:** {from_time}")
                                new_apt_time = st.selectbox("Alterar para:", 
                                                           [f"{h:02d}:00" for h in range(6, 21)],
                                                           index=[f"{h:02d}:00" for h in range(6, 21)].index(from_time),
                                                           key="edit_apt_time")
                            
                            with col3:
                                st.write(f"**Status:** {appointment.get('status', 'scheduled')}")
                            
                            st.markdown("---")
                            
                            col_save, col_delete, col_cancel = st.columns(3)
                            
                            with col_save:
                                if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                    # Atualizar agendamento
                                    conn = sqlite3.connect("pilates.db")
                                    cursor = conn.cursor()
                                    
                                    new_day_of_week = new_apt_date.weekday() + 1
                                    
                                    cursor.execute('''
                                        UPDATE appointments 
                                        SET date = ?, time = ?, day_of_week = ?
                                        WHERE id = ?
                                    ''', (new_apt_date.strftime('%Y-%m-%d'), new_apt_time, new_day_of_week, appointment['id']))
                                    
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success("✅ Reposição atualizada!")
                                    del st.session_state['editing_client_id']
                                    del st.session_state['editing_is_appointment']
                                    del st.session_state['editing_date']
                                    st.rerun()
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Excluir Reposição", use_container_width=True, type="secondary"):
                                    if db.cancel_appointment(appointment['id']):
                                        st.success("Reposição excluída!")
                                        del st.session_state['editing_client_id']
                                        del st.session_state['editing_is_appointment']
                                        del st.session_state['editing_date']
                                        st.rerun()
                                    else:
                                        st.error("Erro ao excluir")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                    del st.session_state['editing_client_id']
                                    del st.session_state['editing_is_appointment']
                                    del st.session_state['editing_date']
                                    st.rerun()
                    else:
                        st.warning("Reposição não encontrada")
                        if st.button("⬅️ Voltar"):
                            del st.session_state['editing_client_id']
                            del st.session_state['editing_is_appointment']
                            del st.session_state['editing_date']
                            st.rerun()
                
                else:
                    # MODO HORÁRIO FIXO - Edição normal
                    st.info("📅 Você clicou em um HORÁRIO FIXO")
                
                days_map = {1: "Segunda", 2: "Terça", 3: "Quarta", 4: "Quinta", 5: "Sexta"}
                equipment_list = db.get_equipment()
                equipment_options = {eq['name']: eq['id'] for eq in equipment_list}
                hours_list = [f"{h:02d}:00" for h in range(6, 21)]
                
                # Função para contar clientes em cada dia/horário
                def get_available_slots():
                    """Retorna dicionário com contagem de clientes por dia/horário"""
                    all_schedules = db.get_all_client_schedules()
                    slots_count = {}
                    
                    for day in range(1, 6):  # Segunda a Sexta
                        slots_count[day] = {}
                        for hour in hours_list:
                            # Contar quantos clientes têm horário fixo neste dia/hora
                            count = sum(1 for s in all_schedules 
                                      if s['day_of_week'] == day and s['time'] == hour)
                            slots_count[day][hour] = count
                    
                    return slots_count
                
                def get_available_slots_for_date(target_date):
                    """Retorna dicionário com contagem de clientes para uma data específica"""
                    from datetime import datetime
                    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
                    day_of_week = date_obj.weekday() + 1
                    
                    # Buscar agendamentos confirmados para esta data
                    appointments = db.get_appointments()
                    slots_count = {}
                    
                    for hour in hours_list:
                        # Contar agendamentos confirmados nesta data/hora
                        count = sum(1 for apt in appointments 
                                  if apt['date'] == target_date 
                                  and apt['time'] == hour 
                                  and apt['status'] != 'cancelled')
                        
                        # Também contar horários fixos para este dia da semana (que não têm appointment nesta data)
                        all_schedules = db.get_all_client_schedules()
                        clients_with_apt = {apt['client_id'] for apt in appointments 
                                          if apt['date'] == target_date and apt['time'] == hour}
                        
                        fixed_count = sum(1 for s in all_schedules 
                                        if s['day_of_week'] == day_of_week 
                                        and s['time'] == hour 
                                        and s['client_id'] not in clients_with_apt)
                        
                        slots_count[hour] = count + fixed_count
                    
                    return slots_count
                
                # Obter vagas disponíveis
                available_slots = get_available_slots()
                
                # Inicializar session_state para novos campos se não existir
                if 'show_add_new' not in st.session_state:
                    st.session_state.show_add_new = False
                if 'show_reposicao' not in st.session_state:
                    st.session_state.show_reposicao = False
                
                # Checkboxes para controlar exibição
                st.markdown("---")
                col_opt1, col_opt2 = st.columns(2)
                
                with col_opt1:
                    st.markdown("**➕ Adicionar Novo Horário:**")
                    if st.checkbox("✅ Adicionar mais um dia", key="add_new_check", value=st.session_state.show_add_new):
                        st.session_state.show_add_new = True
                    else:
                        st.session_state.show_add_new = False
                
                with col_opt2:
                    st.markdown("**📌 Criar Reposição:**")
                    if st.checkbox("✅ Reposição (agendamento único)", key="repos_check", value=st.session_state.show_reposicao):
                        st.session_state.show_reposicao = True
                    else:
                        st.session_state.show_reposicao = False
                
                # Campos para ADICIONAR NOVO (aparecem imediatamente)
                new_schedule = None
                if st.session_state.show_add_new:
                    with st.container():
                        st.info("🆕 Preencha os dados do novo horário (máximo 3 clientes por horário):")
                        
                        # Filtrar dias que têm pelo menos um horário disponível
                        available_days = {day: name for day, name in days_map.items() 
                                        if any(available_slots[day][hour] < 3 for hour in hours_list)}
                        
                        if not available_days:
                            st.error("❌ Não há dias/horários disponíveis (todos os horários têm 3 clientes)")
                        else:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                new_day_add = st.selectbox(
                                    "Dia da semana:",
                                    options=list(available_days.keys()),
                                    format_func=lambda x: available_days[x],
                                    key="new_day_add_field"
                                )
                            
                            with col2:
                                # Filtrar horários disponíveis para o dia selecionado
                                available_hours = [hour for hour in hours_list 
                                                 if available_slots[new_day_add][hour] < 3]
                                
                                if not available_hours:
                                    st.warning("⚠️ Nenhum horário disponível neste dia")
                                    new_time_add = None
                                else:
                                    new_time_add = st.selectbox(
                                        f"Horário ({len(available_hours)} disponíveis):",
                                        options=available_hours,
                                        format_func=lambda h: f"{h} ({available_slots[new_day_add][h]}/3)",
                                        key="new_time_add_field"
                                    )
                            
                            with col3:
                                new_equipment_add = st.selectbox(
                                    "Equipamento:",
                                    options=list(equipment_options.keys()),
                                    key="new_eq_add_field"
                                )
                            
                            if new_time_add:
                                new_schedule = {
                                    'day': new_day_add,
                                    'time': new_time_add,
                                    'equipment_id': equipment_options[new_equipment_add]
                                }
                
                # Campos para REPOSIÇÃO (aparecem imediatamente)
                reposicao_data = None
                if st.session_state.show_reposicao:
                    with st.container():
                        st.warning("⚠️ A reposição é um agendamento único e não altera os horários fixos.")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            repos_date = st.date_input("Data:", min_value=date.today(), key="repos_date_field")
                        
                        # Obter vagas para a data selecionada
                        repos_date_str = repos_date.strftime('%Y-%m-%d')
                        repos_slots = get_available_slots_for_date(repos_date_str)
                        available_repos_hours = [hour for hour in hours_list if repos_slots[hour] < 3]
                        
                        with col2:
                            if not available_repos_hours:
                                st.error("❌ Nenhum horário disponível nesta data")
                                repos_time = None
                            else:
                                # Verificar se o cliente já tem reposição nesta data/horário
                                existing_appointments = db.get_appointments()
                                client_appointments_on_date = [
                                    apt for apt in existing_appointments 
                                    if apt['client_id'] == client_id 
                                    and apt['date'] == repos_date_str
                                    and apt['status'] != 'cancelled'
                                ]
                                
                                # Remover horários onde o cliente já tem reposição
                                client_existing_times = {apt['time'] for apt in client_appointments_on_date}
                                available_repos_hours_filtered = [
                                    h for h in available_repos_hours 
                                    if h not in client_existing_times
                                ]
                                
                                if not available_repos_hours_filtered:
                                    st.error("❌ Você já tem reposição em todos os horários disponíveis desta data")
                                    repos_time = None
                                else:
                                    repos_time = st.selectbox(
                                        f"Horário ({len(available_repos_hours_filtered)} disponíveis):",
                                        options=available_repos_hours_filtered,
                                        format_func=lambda h: f"{h} ({repos_slots[h]}/3)",
                                        key="repos_time_field"
                                    )
                        
                        with col3:
                            repos_eq = st.selectbox("Equipamento:", list(equipment_options.keys()), key="repos_eq_field")
                        
                        if repos_time:
                            reposicao_data = {
                                'date': repos_date,
                                'time': repos_time,
                                'equipment_id': equipment_options[repos_eq]
                            }
                
                st.markdown("---")
                
                # FORMULÁRIO apenas para editar horários existentes
                with st.form("edit_client_schedule"):
                    st.write("**📅 Horários Fixos Cadastrados:**")
                    
                    # Mostrar horários existentes com opção de editar ou remover
                    schedules_to_keep = {}
                    
                    for idx, sched in enumerate(current_schedules):
                        st.markdown(f"**📅 {days_map[sched['day_of_week']]} às {sched['time']}** (Fixo)")
                        
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            new_day = st.selectbox(
                                "Dia:",
                                options=list(days_map.keys()),
                                format_func=lambda x: days_map[x],
                                index=list(days_map.keys()).index(sched['day_of_week']),
                                key=f"edit_day_{idx}"
                            )
                        
                        with col2:
                            new_time = st.selectbox(
                                "Horário:",
                                options=hours_list,
                                index=hours_list.index(sched['time']) if sched['time'] in hours_list else 0,
                                key=f"edit_time_{idx}"
                            )
                        
                        with col3:
                            current_eq = sched.get('equipment_name', list(equipment_options.keys())[0])
                            new_equipment = st.selectbox(
                                "Equipamento:",
                                options=list(equipment_options.keys()),
                                index=list(equipment_options.keys()).index(current_eq) if current_eq in equipment_options else 0,
                                key=f"edit_eq_{idx}"
                            )
                        
                        with col4:
                            remove = st.checkbox("🗑️", key=f"remove_{idx}", help="Remover este horário")
                        
                        if not remove:
                            schedules_to_keep[idx] = {
                                'schedule_id': sched['id'],
                                'old_day': sched['day_of_week'],
                                'old_time': sched['time'],
                                'new_day': new_day,
                                'new_time': new_time,
                                'new_equipment_id': equipment_options[new_equipment]
                            }
                        
                        st.divider()
                    
                    # Buscar e mostrar reposições (appointments) do cliente
                    appointments = db.get_appointments()
                    client_appointments = [
                        apt for apt in appointments 
                        if apt['client_id'] == client_id 
                        and apt['status'] != 'cancelled'
                        and apt['date'] >= date.today().strftime('%Y-%m-%d')  # Apenas futuras
                    ]
                    
                    appointments_to_keep = {}  # Inicializar sempre
                    
                    if client_appointments:
                        st.markdown("**📌 Reposições Agendadas:**")
                        
                        appointments_to_keep = {}
                        
                        for apt_idx, apt in enumerate(client_appointments):
                            apt_date = datetime.strptime(apt['date'], '%Y-%m-%d')
                            day_name = days_map.get(apt['day_of_week'], 'Sábado/Domingo')
                            st.markdown(f"**📌 {apt_date.strftime('%d/%m/%Y')} ({day_name}) às {apt['time']}** (Reposição)")
                            
                            col1, col2, col3 = st.columns([2, 2, 1])
                            
                            with col1:
                                new_apt_date = st.date_input(
                                    "Data:",
                                    value=apt_date.date(),
                                    min_value=date.today(),
                                    key=f"edit_apt_date_{apt_idx}_{apt['id']}"
                                )
                            
                            with col2:
                                new_apt_time = st.selectbox(
                                    "Horário:",
                                    options=hours_list,
                                    index=hours_list.index(apt['time']) if apt['time'] in hours_list else 0,
                                    key=f"edit_apt_time_{apt_idx}_{apt['id']}"
                                )
                            
                            with col3:
                                remove_apt = st.checkbox("🗑️", key=f"remove_apt_{apt_idx}_{apt['id']}", help="Excluir esta reposição")
                            
                            if not remove_apt:
                                appointments_to_keep[apt['id']] = {
                                    'old_date': apt['date'],
                                    'old_time': apt['time'],
                                    'new_date': new_apt_date.strftime('%Y-%m-%d'),
                                    'new_time': new_apt_time
                                }
                            
                            st.divider()
                    
                    st.markdown("---")
                    
                    st.markdown("---")
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                            success = True
                            
                            if st.session_state.show_reposicao and reposicao_data:
                                # Verificar se o cliente já tem agendamento neste dia (em qualquer horário)
                                repos_date_str = reposicao_data['date'].strftime('%Y-%m-%d')
                                existing_appointments = db.get_appointments(client_id=client_id)
                                has_appointment_on_date = any(
                                    apt['date'] == repos_date_str and apt['status'] != 'cancelled'
                                    for apt in existing_appointments
                                )
                                
                                if has_appointment_on_date:
                                    st.error(f"❌ Cliente já possui um agendamento no dia {reposicao_data['date'].strftime('%d/%m/%Y')}. Apenas uma aula por dia é permitida.")
                                    success = False
                                else:
                                    # Criar apenas reposição
                                    if db.create_appointment(client_id, repos_date_str, 
                                                            reposicao_data['time'], None):
                                        st.success(f"✅ Reposição criada para {reposicao_data['date'].strftime('%d/%m/%Y')} às {reposicao_data['time']}")
                                        st.session_state.show_reposicao = False
                                    else:
                                        st.error(f"❌ Erro ao criar reposição: O horário {reposicao_data['time']} do dia {reposicao_data['date'].strftime('%d/%m/%Y')} pode estar lotado (máximo 3 clientes)")
                                        success = False
                            elif st.session_state.show_reposicao and not reposicao_data:
                                st.warning("⚠️ Nenhum horário disponível selecionado para a reposição")
                                success = False
                            else:
                                # Processar alterações/exclusões de reposições existentes
                                for apt in client_appointments:
                                    if apt['id'] not in appointments_to_keep:
                                        # Excluir reposição
                                        db.cancel_appointment(apt['id'])
                                    else:
                                        # Verificar se houve alteração
                                        apt_update = appointments_to_keep[apt['id']]
                                        if (apt_update['old_date'] != apt_update['new_date'] or 
                                            apt_update['old_time'] != apt_update['new_time']):
                                            # Atualizar reposição
                                            conn = sqlite3.connect("pilates.db")
                                            cursor = conn.cursor()
                                            new_day_of_week = datetime.strptime(apt_update['new_date'], '%Y-%m-%d').weekday() + 1
                                            cursor.execute('''
                                                UPDATE appointments 
                                                SET date = ?, time = ?, day_of_week = ?
                                                WHERE id = ?
                                            ''', (apt_update['new_date'], apt_update['new_time'], new_day_of_week, apt['id']))
                                            conn.commit()
                                            conn.close()
                                
                                # Atualizar horários fixos
                                # 1. Remover horários desmarcados
                                for idx, sched in enumerate(current_schedules):
                                    if idx not in schedules_to_keep:
                                        db.delete_client_schedule(sched['id'])
                                
                                # 2. Atualizar horários modificados
                                for idx, update_info in schedules_to_keep.items():
                                    if (update_info['old_day'] != update_info['new_day'] or 
                                        update_info['old_time'] != update_info['new_time']):
                                        # Deletar antigo e criar novo
                                        db.delete_client_schedule(update_info['schedule_id'])
                                        db.create_client_schedule(client_id, update_info['new_day'], update_info['new_time'])
                                    
                                    # Atualizar equipamento
                                    conn = sqlite3.connect("pilates.db")
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE client_schedule 
                                        SET equipment_id = ?
                                        WHERE client_id = ? AND day_of_week = ? AND time = ?
                                    ''', (update_info['new_equipment_id'], client_id, 
                                         update_info['new_day'], update_info['new_time']))
                                    conn.commit()
                                    conn.close()
                                
                                # 3. Adicionar novo horário se solicitado
                                if st.session_state.show_add_new and new_schedule:
                                    if db.create_client_schedule(client_id, new_schedule['day'], new_schedule['time']):
                                        # Atualizar equipamento do novo
                                        conn = sqlite3.connect("pilates.db")
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE client_schedule 
                                            SET equipment_id = ?
                                            WHERE client_id = ? AND day_of_week = ? AND time = ?
                                        ''', (new_schedule['equipment_id'], client_id, 
                                             new_schedule['day'], new_schedule['time']))
                                        conn.commit()
                                        conn.close()
                                        st.session_state.show_add_new = False
                                    else:
                                        st.error("Erro ao adicionar novo horário")
                                        success = False
                                
                                if success:
                                    st.success("✅ Horários atualizados com sucesso!")
                            
                            if success:
                                # Limpar estado de edição
                                del st.session_state['editing_client_id']
                                if 'editing_from_day' in st.session_state:
                                    del st.session_state['editing_from_day']
                                if 'editing_from_time' in st.session_state:
                                    del st.session_state['editing_from_time']
                                st.rerun()
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                            del st.session_state['editing_client_id']
                            if 'editing_from_day' in st.session_state:
                                del st.session_state['editing_from_day']
                            if 'editing_from_time' in st.session_state:
                                del st.session_state['editing_from_time']
                            st.rerun()
    else:
        st.info("Nenhum agendamento para esta semana")
    
    # Formulário de novo agendamento
    if st.session_state.get('show_appointment_form', False):
        with st.form("new_appointment"):
            st.subheader("➕ Novo Agendamento")
            
            # Tipo de agendamento
            appointment_type = st.radio(
                "Tipo de Agendamento:",
                ["Único", "Recorrente (Semanal)"],
                horizontal=True
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                clients = db.get_clients()
                client_options = {f"{c['name']} ({c['email']})": c['id'] for c in clients}
                selected_client = st.selectbox("Cliente:", list(client_options.keys()))
                
                if appointment_type == "Único":
                    appointment_date = st.date_input("Data:", min_value=date.today())
                else:
                    start_date = st.date_input("Data de início:", min_value=date.today())
                    weeks_ahead = st.number_input("Criar para quantas semanas:", min_value=1, max_value=52, value=12)
                
            with col2:
                if appointment_type == "Único":
                    hours = [f"{h:02d}:00" for h in range(6, 21)]
                    selected_time = st.selectbox("Horário:", hours)
                    
                    # Carregar sequências para o dia selecionado
                    if 'appointment_date' in locals():
                        day_of_week = appointment_date.weekday() + 1
                        if selected_client:
                            client_id = client_options[selected_client]
                            sequences = db.get_client_sequences(client_id, day_of_week)
                            sequence_options = {"Nenhuma": None}
                            sequence_options.update({seq['name']: seq['id'] for seq in sequences})
                            selected_sequence = st.selectbox("Sequência Personalizada:", list(sequence_options.keys()))
                        else:
                            st.info("Selecione um cliente primeiro")
                else:
                    # Agendamento recorrente - seleção de dias e horários
                    st.write("**Selecione os dias da semana e horários:**")
                    
                    hours = [f"{h:02d}:00" for h in range(6, 21)]
                    days_times = {}
                    
                    days_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
                    for i, day_name in enumerate(days_names, 1):
                        col_day, col_time = st.columns([1, 2])
                        with col_day:
                            if st.checkbox(day_name, key=f"day_{i}"):
                                with col_time:
                                    time = st.selectbox(f"Horário {day_name}:", hours, key=f"time_{i}")
                                    days_times[i] = time
                    
                    # Sequência padrão para os dias selecionados
                    if selected_client and days_times:
                        client_id = client_options[selected_client]
                        # Pegar uma sequência padrão do cliente (primeiro dia)
                        first_day = list(days_times.keys())[0]
                        sequences = db.get_client_sequences(client_id, first_day)
                        sequence_options = {"Nenhuma": None}
                        sequence_options.update({seq['name']: seq['id'] for seq in sequences})
                        selected_sequence = st.selectbox("Sequência Padrão:", list(sequence_options.keys()))
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                if st.form_submit_button("✅ Criar Agendamento", use_container_width=True):
                    if selected_client:
                        client_id = client_options[selected_client]
                        sequence_id = sequence_options[selected_sequence] if 'selected_sequence' in locals() and selected_sequence != "Nenhuma" else None
                        
                        if appointment_type == "Único":
                            if appointment_date and selected_time:
                                # Verificar se o cliente já tem agendamento neste dia
                                date_str = appointment_date.strftime('%Y-%m-%d')
                                existing_appointments = db.get_appointments(client_id=client_id)
                                has_appointment_on_date = any(
                                    apt['date'] == date_str and apt['status'] != 'cancelled'
                                    for apt in existing_appointments
                                )
                                
                                if has_appointment_on_date:
                                    st.error(f"❌ Cliente já possui um agendamento no dia {appointment_date.strftime('%d/%m/%Y')}. Apenas uma aula por dia é permitida.")
                                elif db.create_appointment(client_id, date_str, selected_time, sequence_id):
                                    st.session_state.show_appointment_form = False
                                    st.rerun()
                                else:
                                    st.error("Erro ao criar agendamento. Horário pode estar ocupado.")
                            else:
                                st.error("Preencha todos os campos obrigatórios!")
                        else:
                            if start_date and days_times:
                                created_count = db.create_recurring_appointments(
                                    client_id, 
                                    start_date.strftime('%Y-%m-%d'), 
                                    days_times, 
                                    sequence_id, 
                                    weeks_ahead
                                )
                                if created_count > 0:
                                    st.session_state.show_appointment_form = False
                                    st.rerun()
                                else:
                                    st.error("Erro ao criar agendamentos recorrentes.")
                            else:
                                st.error("Selecione pelo menos um dia da semana!")
                    else:
                        st.error("Selecione um cliente!")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_appointment_form = False
                    st.rerun()

def clients_tab():
    """Aba de gerenciamento de clientes"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("👥 Gerenciar Clientes")
    
    with col2:
        if st.button("➕ Novo Cliente", use_container_width=True):
            st.session_state.show_client_form = True
    
    # Formulário de novo cliente
    if st.session_state.get('show_client_form', False):
        st.subheader("➕ Novo Cliente")
        
        # Seção 1: Dados do cliente (fora do form para coletar antes)
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome completo:", placeholder="Ex: João Silva", key="client_name")
            phone = st.text_input("Telefone:", placeholder="Ex: (11) 99999-9999", key="client_phone")
        
        with col2:
            email = st.text_input("Email:", placeholder="Ex: joao@email.com", key="client_email")
            password = st.text_input("Senha:", type="password", placeholder="Senha para login", key="client_password")
        
        medical_history = st.text_area(
            "Histórico Médico (até 1000 caracteres):", 
            max_chars=1000,
            placeholder="Descreva condições médicas, lesões, limitações...",
            key="client_medical"
        )
        
        st.markdown("---")
        st.subheader("📅 Configurar Contrato e Agendamentos")
        st.info("💡 Configure o tipo de contrato, data de início e dias da semana")
        
        # PASSO 1: Data de início do contrato
        st.write("### 1️⃣ Data de Início do Contrato")
        col_data, col_tipo = st.columns(2)
        
        with col_data:
            data_inicio_contrato = st.date_input(
                "Data de início:",
                value=date.today(),
                min_value=date(2024, 1, 1),
                max_value=date(2030, 12, 31),
                key="data_inicio_contrato",
                help="Data em que o contrato do cliente inicia"
            )
        
        with col_tipo:
            tipo_contrato = st.radio(
                "Tipo de Contrato:",
                ["⭐ Fixo (recorrente)", "📦 Pacote de Sessões"],
                key="tipo_contrato_radio",
                help="Fixo: agendamentos até o fim do ano | Pacote: número limitado de sessões"
            )
        
        # Determinar tipo limpo
        if "Fixo" in tipo_contrato:
            tipo_contrato_clean = "fixo"
        else:
            tipo_contrato_clean = "sessoes"
        
        # Campo de quantidade de sessões (apenas para Pacote)
        sessoes_contratadas = 0
        if tipo_contrato_clean == "sessoes":
            st.write("**Quantidade de Sessões no Pacote:**")
            sessoes_contratadas = st.number_input(
                "Quantas sessões?",
                min_value=1,
                max_value=100,
                value=12,
                key="sessoes_contratadas_input",
                help="Número total de sessões incluídas no pacote"
            )
        
        st.markdown("---")
        
        # PASSO 2: Selecionar DIAS da semana e HORÁRIOS
        st.write("### 2️⃣ Dias da Semana e Horários")
        st.write("**Selecione os dias e defina o horário para cada um:**")
        
        hours = [f"{h:02d}:00" for h in range(6, 21)]
        dias_horarios = {}  # {dia_num: horario}
        dias_nomes = {
            1: ("📅 Segunda-feira", "monday"),
            2: ("📆 Terça-feira", "tuesday"),
            3: ("🗓️ Quarta-feira", "wednesday"),
            4: ("📋 Quinta-feira", "thursday"),
            5: ("� Sexta-feira", "friday")
        }
        
        for dia_num, (dia_label, dia_key) in dias_nomes.items():
            col_check, col_time = st.columns([1, 2])
            
            with col_check:
                dia_selecionado = st.checkbox(dia_label, key=f"check_{dia_key}_new")
            
            with col_time:
                if dia_selecionado:
                    horario = st.selectbox(
                        "Horário:",
                        hours,
                        index=9,  # 15:00 como padrão
                        key=f"time_{dia_key}_new",
                        label_visibility="collapsed"
                    )
                    dias_horarios[dia_num] = horario
                else:
                    st.text_input(
                        "Horário:",
                        value="--:--",
                        disabled=True,
                        key=f"time_{dia_key}_disabled",
                        label_visibility="collapsed"
                    )
        
        dias_semana_selecionados = list(dias_horarios.keys())
        
        # Resumo da configuração
        st.markdown("---")
        
        if dias_semana_selecionados:
            st.success("📋 **Resumo da Configuração:**")
            st.write(f"**Tipo de Contrato:** {tipo_contrato}")
            st.write(f"**Data de Início:** {data_inicio_contrato.strftime('%d/%m/%Y')}")
            
            if tipo_contrato_clean == "sessoes":
                st.write(f"**Sessões Contratadas:** {sessoes_contratadas}")
            
            st.write("**Dias e Horários:**")
            dias_nomes_completos = {
                1: "Segunda-feira", 
                2: "Terça-feira", 
                3: "Quarta-feira", 
                4: "Quinta-feira", 
                5: "Sexta-feira"
            }
            for dia_num in sorted(dias_semana_selecionados):
                st.write(f"  • {dias_nomes_completos[dia_num]} às **{dias_horarios[dia_num]}**")
            
            # Estimativa de agendamentos
            if tipo_contrato_clean == "fixo":
                # Calcular até final do ano
                dias_ate_fim_ano = (date(data_inicio_contrato.year, 12, 31) - data_inicio_contrato).days
                semanas_restantes = dias_ate_fim_ano // 7
                estimativa = len(dias_semana_selecionados) * semanas_restantes
                st.info(f"📊 Estimativa: **~{estimativa} agendamentos** até 31/12/{data_inicio_contrato.year}")
            else:
                st.info(f"📊 Total: **{sessoes_contratadas} agendamentos**")
        else:
            st.warning("⚠️ Selecione pelo menos um dia da semana")
        
        # Formulário apenas para submit
        with st.form("new_client_submit"):
            st.write("")  # Espaçamento
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                if st.form_submit_button("✅ Criar Cliente", use_container_width=True):
                    # Recuperar valores dos campos
                    name = st.session_state.get('client_name', '')
                    phone = st.session_state.get('client_phone', '')
                    email = st.session_state.get('client_email', '')
                    password = st.session_state.get('client_password', '')
                    medical_history = st.session_state.get('client_medical', '')
                    
                    # Validar campos obrigatórios
                    missing_fields = []
                    if not name:
                        missing_fields.append("Nome")
                    if not phone:
                        missing_fields.append("Telefone")
                    if not email:
                        missing_fields.append("Email")
                    if not password:
                        missing_fields.append("Senha")
                    
                    if not missing_fields and len(dias_semana_selecionados) > 0:
                        import json
                        import bcrypt
                        
                        # Criar cliente com os novos campos
                        conn = sqlite3.connect(db.db_path)
                        cursor = conn.cursor()
                        
                        try:
                            # Hash da senha
                            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                            
                            # Preparar dias_semana como JSON com horários: {"1": "08:00", "5": "14:00"}
                            dias_semana_json = json.dumps({str(k): v for k, v in dias_horarios.items()})
                            
                            # Inserir cliente com novos campos
                            cursor.execute("""
                                INSERT INTO users (
                                    name, phone, email, password, medical_history, type,
                                    data_inicio_contrato, tipo_contrato, sessoes_contratadas,
                                    sessoes_utilizadas, dias_semana, contrato_ativo
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                name, phone, email, hashed_password, medical_history, 'client',
                                data_inicio_contrato.strftime('%Y-%m-%d'),
                                tipo_contrato_clean,
                                sessoes_contratadas if tipo_contrato_clean == 'sessoes' else 0,
                                0,  # sessoes_utilizadas começa em 0
                                dias_semana_json,  # {"1": "08:00", "5": "14:00"}
                                1  # contrato_ativo = True
                            ))
                            
                            client_id = cursor.lastrowid
                            conn.commit()
                            conn.close()
                            
                            # Gerar agendamentos automaticamente com horários por dia
                            appointments_created = db.gerar_appointments_cliente(client_id, dias_horarios)
                            
                            success_msg = f"✅ Cliente '{name}' criado com sucesso!"
                            success_msg += f"\n🤖 {appointments_created} agendamento(s) gerado(s) automaticamente!"
                            
                            if tipo_contrato_clean == "sessoes":
                                success_msg += f"\n📦 Pacote: {sessoes_contratadas} sessões (0 utilizadas)"
                            else:
                                success_msg += f"\n⭐ Contrato fixo até 31/12/{data_inicio_contrato.year}"
                            
                            st.success(success_msg)
                            st.session_state.show_client_form = False
                            st.rerun()
                            
                        except Exception as e:
                            conn.rollback()
                            conn.close()
                            if "UNIQUE constraint failed" in str(e):
                                st.error("❌ Erro: Email já está em uso.")
                            else:
                                st.error(f"❌ Erro ao criar cliente: {str(e)}")
                    
                    elif not missing_fields:
                        st.error("⚠️ Selecione pelo menos um dia da semana")
                    else:
                        st.error(f"⚠️ Preencha os seguintes campos obrigatórios: {', '.join(missing_fields)}")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_client_form = False
                    st.rerun()
    
    st.markdown("---")
    
    # Lista de clientes
    clients = db.get_clients()
    
    if clients:
        for client in clients:
            # Obter horários atuais do cliente
            current_schedule = db.get_client_schedule(client['id'])
            current_schedule_dict = {sched['day_of_week']: sched for sched in current_schedule}
            
            with st.expander(f"👤 {client['name']} - {client['email']}"):
                with st.form(f"client_form_{client['id']}"):
                    st.subheader("📋 Informações do Cliente")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Nome completo:", value=client['name'], key=f"name_{client['id']}")
                        edit_phone = st.text_input("Telefone:", value=client['phone'], key=f"phone_{client['id']}")
                    
                    with col2:
                        edit_email = st.text_input("Email:", value=client['email'], key=f"email_{client['id']}")
                        edit_password = st.text_input("Nova senha (deixe em branco para manter):", type="password", key=f"pwd_{client['id']}")
                    
                    edit_medical = st.text_area(
                        "Histórico Médico:", 
                        value=client['medical_history'] or "", 
                        max_chars=1000,
                        key=f"medical_{client['id']}"
                    )
                    
                    st.markdown("---")
                    st.subheader("📅 Configuração de Contrato e Agendamentos")
                    
                    # Parse dos dados atuais
                    import json
                    dados_contrato_atual = {
                        'data_inicio': client.get('data_inicio_contrato'),
                        'tipo': client.get('tipo_contrato'),
                        'sessoes_total': client.get('sessoes_contratadas', 0),
                        'sessoes_usadas': client.get('sessoes_utilizadas', 0),
                        'dias_horarios': {},
                        'ativo': client.get('contrato_ativo', 1)
                    }
                    
                    # Parse dias_semana JSON
                    dias_semana_json = client.get('dias_semana')
                    if dias_semana_json:
                        try:
                            dados = json.loads(dias_semana_json)
                            if isinstance(dados, dict):
                                dados_contrato_atual['dias_horarios'] = {int(k): v for k, v in dados.items()}
                            elif isinstance(dados, list):
                                dados_contrato_atual['dias_horarios'] = {d: "08:00" for d in dados}
                        except:
                            pass
                    
                    # Data de início
                    col_data, col_tipo = st.columns(2)
                    
                    with col_data:
                        data_inicio_edit = st.date_input(
                            "Data de Início do Contrato:",
                            value=datetime.strptime(dados_contrato_atual['data_inicio'], '%Y-%m-%d').date() if dados_contrato_atual['data_inicio'] else date.today(),
                            key=f"data_inicio_edit_{client['id']}"
                        )
                    
                    with col_tipo:
                        tipo_atual = dados_contrato_atual['tipo'] or 'fixo'
                        tipo_index = 0 if tipo_atual == 'fixo' else 1
                        tipo_contrato_edit = st.radio(
                            "Tipo de Contrato:",
                            ["⭐ Fixo (recorrente)", "📦 Pacote de Sessões"],
                            index=tipo_index,
                            key=f"tipo_contrato_edit_{client['id']}"
                        )
                    
                    tipo_contrato_clean_edit = "fixo" if "Fixo" in tipo_contrato_edit else "sessoes"
                    
                    # Sessões contratadas (se pacote)
                    if tipo_contrato_clean_edit == "sessoes":
                        col_sessoes_total, col_sessoes_usadas = st.columns(2)
                        
                        with col_sessoes_total:
                            sessoes_contratadas_edit = st.number_input(
                                "Sessões Contratadas:",
                                min_value=1,
                                max_value=100,
                                value=dados_contrato_atual['sessoes_total'] if dados_contrato_atual['sessoes_total'] > 0 else 12,
                                key=f"sessoes_total_edit_{client['id']}"
                            )
                        
                        with col_sessoes_usadas:
                            st.metric("Sessões Utilizadas", dados_contrato_atual['sessoes_usadas'])
                            sessoes_restantes = sessoes_contratadas_edit - dados_contrato_atual['sessoes_usadas']
                            st.caption(f"📊 Restantes: {sessoes_restantes}")
                    else:
                        sessoes_contratadas_edit = 0
                    
                    # Dias e Horários
                    st.write("**Dias da Semana e Horários:**")
                    
                    hours = [f"{h:02d}:00" for h in range(6, 21)]
                    dias_horarios_edit = {}
                    dias_nomes = {
                        1: ("📅 Segunda-feira", "monday"),
                        2: ("📆 Terça-feira", "tuesday"),
                        3: ("🗓️ Quarta-feira", "wednesday"),
                        4: ("📋 Quinta-feira", "thursday"),
                        5: ("📊 Sexta-feira", "friday")
                    }
                    
                    for dia_num, (dia_label, dia_key) in dias_nomes.items():
                        col_check, col_time = st.columns([1, 2])
                        
                        # Verificar se este dia está nos dados atuais
                        dia_ja_selecionado = dia_num in dados_contrato_atual['dias_horarios']
                        horario_atual = dados_contrato_atual['dias_horarios'].get(dia_num, "15:00")
                        
                        with col_check:
                            dia_selecionado = st.checkbox(
                                dia_label, 
                                value=dia_ja_selecionado,
                                key=f"check_edit_{dia_key}_{client['id']}"
                            )
                        
                        with col_time:
                            if dia_selecionado:
                                try:
                                    time_index = hours.index(horario_atual)
                                except:
                                    time_index = 9
                                
                                horario = st.selectbox(
                                    "Horário:",
                                    hours,
                                    index=time_index,
                                    key=f"time_edit_{dia_key}_{client['id']}",
                                    label_visibility="collapsed"
                                )
                                dias_horarios_edit[dia_num] = horario
                            else:
                                st.text_input(
                                    "Horário:",
                                    value="--:--",
                                    disabled=True,
                                    key=f"time_edit_{dia_key}_disabled_{client['id']}",
                                    label_visibility="collapsed"
                                )
                    
                    # Status do contrato
                    contrato_ativo_edit = st.checkbox(
                        "✅ Contrato Ativo",
                        value=bool(dados_contrato_atual['ativo']),
                        key=f"contrato_ativo_edit_{client['id']}",
                        help="Desmarque para desativar o contrato sem excluir o cliente"
                    )
                    
                    st.markdown("---")
                    st.subheader("💰 Informações Financeiras")
                    st.info("💡 Preencha os campos abaixo. Ao salvar, contas futuras serão criadas/atualizadas automaticamente.")
                    
                    col_fin1, col_fin2, col_fin3 = st.columns(3)
                    
                    with col_fin1:
                        valor_mensalidade = st.number_input(
                            "Valor Mensal (R$):",
                            min_value=0.0,
                            value=0.0,
                            step=10.0,
                            placeholder="Digite o valor",
                            key=f"valor_{client['id']}"
                        )
                    
                    with col_fin2:
                        qtd_sessoes_contratadas = st.number_input(
                            "Quantidade de Sessões:",
                            min_value=0,
                            value=0,
                            step=1,
                            placeholder="Qtd sessões/mês",
                            key=f"qtd_sessoes_{client['id']}"
                        )
                    
                    with col_fin3:
                        qtd_meses_contrato = st.number_input(
                            "Quantidade de Meses:",
                            min_value=0,
                            value=0,
                            step=1,
                            placeholder="Qtd meses",
                            key=f"qtd_meses_contrato_{client['id']}"
                        )
                    
                    col_tipo1, col_tipo2, col_tipo3 = st.columns(3)
                    
                    with col_tipo1:
                        tipo_fisio = st.checkbox(
                            "🏥 Fisioterapia",
                            key=f"fisio_{client['id']}"
                        )
                    
                    with col_tipo2:
                        tipo_pilates = st.checkbox(
                            "🧘 Pilates",
                            key=f"pilates_{client['id']}"
                        )
                    
                    with col_tipo3:
                        recorrente = st.checkbox(
                            "🔄 Recorrente",
                            value=True,
                            key=f"recorrente_{client['id']}",
                            help="Gera contas para os próximos meses automaticamente"
                        )
                    
                    # Data de início do contrato
                    data_inicio_contrato = st.date_input(
                        "Data de Início do Contrato:",
                        value=date.today(),
                        key=f"data_inicio_{client['id']}"
                    )
                    
                    # Informação sobre o que será criado
                    if valor_mensalidade > 0:
                        if tipo_fisio and tipo_pilates:
                            tipo_plano = "Fisioterapia + Pilates"
                        elif tipo_fisio:
                            tipo_plano = "Fisioterapia"
                        elif tipo_pilates:
                            tipo_plano = "Pilates"
                        else:
                            tipo_plano = "Mensalidade"
                        
                        meses_criar = qtd_meses_contrato if qtd_meses_contrato > 0 else (12 if recorrente else 1)
                        st.success(f"📋 Ao salvar: {tipo_plano} | R$ {valor_mensalidade:.2f}/mês | {meses_criar} mês(es) | {qtd_sessoes_contratadas} sessões/mês")
                    
                    st.markdown("---")
                    
                    col_save, col_delete = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                            import json
                            import bcrypt
                            
                            # Atualizar dados do cliente incluindo novos campos
                            conn = sqlite3.connect(db.db_path)
                            cursor = conn.cursor()
                            
                            try:
                                # Preparar dias_semana JSON
                                dias_semana_json_edit = json.dumps({str(k): v for k, v in dias_horarios_edit.items()})
                                
                                if edit_password:
                                    # Se senha fornecida, atualizar com nova senha
                                    hashed = bcrypt.hashpw(edit_password.encode('utf-8'), bcrypt.gensalt())
                                    cursor.execute('''
                                        UPDATE users 
                                        SET name=?, phone=?, email=?, password=?, medical_history=?,
                                            data_inicio_contrato=?, tipo_contrato=?, 
                                            sessoes_contratadas=?, dias_semana=?, contrato_ativo=?
                                        WHERE id=?
                                    ''', (
                                        edit_name, edit_phone, edit_email, hashed, edit_medical,
                                        data_inicio_edit.strftime('%Y-%m-%d'),
                                        tipo_contrato_clean_edit,
                                        sessoes_contratadas_edit if tipo_contrato_clean_edit == 'sessoes' else 0,
                                        dias_semana_json_edit,
                                        1 if contrato_ativo_edit else 0,
                                        client['id']
                                    ))
                                else:
                                    # Atualizar sem mexer na senha
                                    cursor.execute('''
                                        UPDATE users 
                                        SET name=?, phone=?, email=?, medical_history=?,
                                            data_inicio_contrato=?, tipo_contrato=?, 
                                            sessoes_contratadas=?, dias_semana=?, contrato_ativo=?
                                        WHERE id=?
                                    ''', (
                                        edit_name, edit_phone, edit_email, edit_medical,
                                        data_inicio_edit.strftime('%Y-%m-%d'),
                                        tipo_contrato_clean_edit,
                                        sessoes_contratadas_edit if tipo_contrato_clean_edit == 'sessoes' else 0,
                                        dias_semana_json_edit,
                                        1 if contrato_ativo_edit else 0,
                                        client['id']
                                    ))
                                
                                conn.commit()
                                conn.close()
                                
                                # Regenerar appointments com novos horários
                                if dias_horarios_edit:
                                    appointments_created = db.gerar_appointments_cliente(client['id'], dias_horarios_edit)
                                    st.success(f"✅ Cliente atualizado! {appointments_created} agendamentos regenerados.")
                                else:
                                    st.success(f"✅ Cliente atualizado!")
                                
                            except Exception as e:
                                conn.rollback()
                                conn.close()
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                                import traceback
                                traceback.print_exc()
                            
                            # Criar/atualizar contas a receber automaticamente
                            if valor_mensalidade > 0:
                                # Determinar tipo de plano
                                if tipo_fisio and tipo_pilates:
                                    tipo_plano = "Fisioterapia + Pilates"
                                elif tipo_fisio:
                                    tipo_plano = "Fisioterapia"
                                elif tipo_pilates:
                                    tipo_plano = "Pilates"
                                else:
                                    tipo_plano = "Mensalidade"
                                
                                quantidade = qtd_sessoes_contratadas if qtd_sessoes_contratadas > 0 else 1
                                
                                # Verificar se é recorrente
                                is_recorrente = st.session_state.get(f"recorrente_{client['id']}", True)
                                
                                if is_recorrente:
                                    # Criar ou atualizar contas mensais recorrentes
                                    from dateutil.relativedelta import relativedelta
                                    data_base = st.session_state.get(f"data_inicio_{client['id']}", date.today())
                                    meses_criar = qtd_meses_contrato if qtd_meses_contrato > 0 else 12
                                    
                                    # Buscar contas existentes para este cliente
                                    contas_existentes = db.get_contas_receber(client_id=client['id'])
                                    hoje = date.today()
                                    
                                    contas_criadas = 0
                                    contas_atualizadas = 0
                                    
                                    for mes in range(meses_criar):
                                        data_venc = data_base + relativedelta(months=mes)
                                        data_venc_str = data_venc.strftime('%Y-%m-%d')
                                        
                                        # Verificar se já existe uma conta para este mês
                                        conta_existente = next((c for c in contas_existentes if c['data_vencimento'] == data_venc_str), None)
                                        
                                        if conta_existente:
                                            # Se a data já passou, não alterar
                                            if data_venc < hoje:
                                                continue
                                            # Se for futura, atualizar valor e tipo_plano usando SQL direto
                                            try:
                                                conn = sqlite3.connect('pilates.db')
                                                conn.execute('''
                                                    UPDATE contas_receber 
                                                    SET tipo_plano=?, valor=?, quantidade=?
                                                    WHERE id=?
                                                ''', (tipo_plano, valor_mensalidade, quantidade, conta_existente['id']))
                                                conn.commit()
                                                conn.close()
                                                contas_atualizadas += 1
                                            except:
                                                pass
                                        else:
                                            # Criar nova conta
                                            if db.create_conta_receber(
                                                client['id'], tipo_plano, valor_mensalidade, 
                                                quantidade, data_venc_str, 
                                                f"Recorrente - Mês {mes + 1}/{meses_criar}"
                                            ):
                                                contas_criadas += 1
                                    
                                    if contas_criadas > 0 or contas_atualizadas > 0:
                                        msg = []
                                        if contas_criadas > 0:
                                            msg.append(f"{contas_criadas} nova(s)")
                                        if contas_atualizadas > 0:
                                            msg.append(f"{contas_atualizadas} atualizada(s)")
                                        st.success(f"✅ Contas a receber: {' e '.join(msg)}")
                                    elif contas_existentes:
                                        st.info("ℹ️ Todas as contas já existem e estão atualizadas")
                                else:
                                    # Criar conta única
                                    data_venc_str = st.session_state.get(f"data_inicio_{client['id']}", date.today()).strftime('%Y-%m-%d')
                                    
                                    if db.create_conta_receber(
                                        client['id'], tipo_plano, valor_mensalidade, 
                                        quantidade, data_venc_str, 
                                        f"Criado automaticamente via cadastro do cliente"
                                    ):
                                        st.success(f"✅ Conta a receber criada: {tipo_plano}")
                                    else:
                                        st.error("❌ Erro ao criar conta a receber")
                            
                            st.rerun()
                    
                    with col_delete:
                        if st.form_submit_button("🗑️ Excluir Cliente", use_container_width=True, type="secondary"):
                            if db.delete_client(client['id']):
                                st.success("Cliente excluído!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir cliente")
                    
                    # Formulário de edição
                    if st.session_state.get(f'edit_client_form_{client["id"]}', False):
                        with st.form(f"edit_client_{client['id']}"):
                            st.write("**Editar Cliente**")
                            
                            # Dados básicos
                            edit_name = st.text_input("Nome:", value=client['name'], key=f"edit_name_{client['id']}")
                            edit_phone = st.text_input("Telefone:", value=client['phone'], key=f"edit_phone_{client['id']}")
                            edit_email = st.text_input("Email:", value=client['email'], key=f"edit_email_{client['id']}")
                            edit_medical = st.text_area("Histórico Médico:", value=client['medical_history'], 
                                                      max_chars=1000, key=f"edit_medical_{client['id']}")
                            
                            st.markdown("---")
                            st.write("**📅 Editar Horários Fixos**")
                            
                            # Obter horários atuais
                            current_schedule = db.get_client_schedule(client['id'])
                            current_schedule_dict = {sched['day_of_week']: sched['time'] for sched in current_schedule}
                            
                            hours = [f"{h:02d}:00" for h in range(6, 21)]
                            days_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
                            
                            edit_days_selected = {}
                            new_schedule = {}
                            
                            col_edit1, col_edit2, col_edit3 = st.columns(3)
                            
                            with col_edit1:
                                # Segunda e Terça
                                for day_num, day_name in [(1, "Segunda"), (2, "Terça")]:
                                    has_schedule = day_num in current_schedule_dict
                                    edit_days_selected[day_num] = st.checkbox(
                                        f"{day_name}-feira", 
                                        value=has_schedule,
                                        key=f"edit_{day_name.lower()}_{client['id']}"
                                    )
                                    if edit_days_selected[day_num]:
                                        current_time = current_schedule_dict.get(day_num, "09:00")
                                        time_index = hours.index(current_time) if current_time in hours else 0
                                        new_schedule[day_num] = st.selectbox(
                                            f"Horário {day_name}:", 
                                            hours, 
                                            index=time_index,
                                            key=f"edit_{day_name.lower()}_time_{client['id']}"
                                        )
                            
                            with col_edit2:
                                # Quarta e Quinta
                                for day_num, day_name in [(3, "Quarta"), (4, "Quinta")]:
                                    has_schedule = day_num in current_schedule_dict
                                    edit_days_selected[day_num] = st.checkbox(
                                        f"{day_name}-feira", 
                                        value=has_schedule,
                                        key=f"edit_{day_name.lower()}_{client['id']}"
                                    )
                                    if edit_days_selected[day_num]:
                                        current_time = current_schedule_dict.get(day_num, "09:00")
                                        time_index = hours.index(current_time) if current_time in hours else 0
                                        new_schedule[day_num] = st.selectbox(
                                            f"Horário {day_name}:", 
                                            hours, 
                                            index=time_index,
                                            key=f"edit_{day_name.lower()}_time_{client['id']}"
                                        )
                            
                            with col_edit3:
                                # Sexta
                                day_num, day_name = 5, "Sexta"
                                has_schedule = day_num in current_schedule_dict
                                edit_days_selected[day_num] = st.checkbox(
                                    f"{day_name}-feira", 
                                    value=has_schedule,
                                    key=f"edit_{day_name.lower()}_{client['id']}"
                                )
                                if edit_days_selected[day_num]:
                                    current_time = current_schedule_dict.get(day_num, "09:00")
                                    time_index = hours.index(current_time) if current_time in hours else 0
                                    new_schedule[day_num] = st.selectbox(
                                        f"Horário {day_name}:", 
                                        hours, 
                                        index=time_index,
                                        key=f"edit_{day_name.lower()}_time_{client['id']}"
                                    )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    # Atualizar dados do cliente
                                    client_updated = db.update_client(client['id'], edit_name, edit_phone, edit_email, edit_medical)
                                    
                                    # Atualizar horários de forma inteligente
                                    schedule_updated = True
                                    errors = []
                                    
                                    # Obter horários que existem atualmente
                                    current_days = set(current_schedule_dict.keys())
                                    new_days = set(new_schedule.keys())
                                    
                                    # Dias para remover (estavam marcados, agora não estão mais)
                                    days_to_remove = current_days - new_days
                                    
                                    # Dias para adicionar (não estavam marcados, agora estão)
                                    days_to_add = new_days - current_days
                                    
                                    # Dias para atualizar (já existiam e continuam, mas horário pode ter mudado)
                                    days_to_update = current_days & new_days
                                    
                                    # Remover horários desmarcados
                                    for day_num in days_to_remove:
                                        schedule_to_delete = next((s for s in current_schedule if s['day_of_week'] == day_num), None)
                                        if schedule_to_delete:
                                            if not db.delete_client_schedule(schedule_to_delete['id']):
                                                schedule_updated = False
                                                errors.append(f"Erro ao remover dia {day_num}")
                                    
                                    # Adicionar novos horários
                                    for day_num in days_to_add:
                                        result = db.create_client_schedule(client['id'], day_num, new_schedule[day_num])
                                        if not result:
                                            schedule_updated = False
                                            errors.append(f"Erro ao adicionar dia {day_num} às {new_schedule[day_num]}")
                                    
                                    # Atualizar horários existentes (se o horário mudou)
                                    for day_num in days_to_update:
                                        old_time = current_schedule_dict[day_num]
                                        new_time = new_schedule[day_num]
                                        
                                        if old_time != new_time:
                                            # Deletar o antigo e criar novo com novo horário
                                            schedule_to_update = next((s for s in current_schedule if s['day_of_week'] == day_num), None)
                                            if schedule_to_update:
                                                # Deletar o horário antigo
                                                if db.delete_client_schedule(schedule_to_update['id']):
                                                    # Criar novo horário
                                                    result = db.create_client_schedule(client['id'], day_num, new_time)
                                                    if not result:
                                                        schedule_updated = False
                                                        errors.append(f"Erro ao atualizar horário do dia {day_num} para {new_time}")
                                                else:
                                                    schedule_updated = False
                                                    errors.append(f"Erro ao deletar horário antigo do dia {day_num}")
                                    
                                    if client_updated and schedule_updated:
                                        st.success("✅ Cliente e horários atualizados com sucesso!")
                                        st.session_state[f'edit_client_form_{client["id"]}'] = False
                                        st.rerun()
                                    else:
                                        error_msg = "Erro ao atualizar cliente ou horários"
                                        if errors:
                                            error_msg += ":\n" + "\n".join(errors)
                                        st.error(error_msg)
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f'edit_client_form_{client["id"]}'] = False
                                    st.rerun()
    else:
        st.info("Nenhum cliente cadastrado")

def equipment_tab():
    """Aba de gerenciamento de equipamentos"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🏋️ Gerenciar Equipamentos")
    
    with col2:
        if st.button("➕ Novo Equipamento", use_container_width=True):
            st.session_state.show_equipment_form = True
    
    # Formulário de novo equipamento
    if st.session_state.get('show_equipment_form', False):
        with st.form("new_equipment"):
            st.subheader("➕ Novo Equipamento")
            
            name = st.text_input("Nome do equipamento:", placeholder="Ex: Reformer")
            description = st.text_area("Descrição:", placeholder="Descrição opcional do equipamento...")
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                if st.form_submit_button("✅ Criar Equipamento", use_container_width=True):
                    if name:
                        if db.create_equipment(name, description):
                            st.success("Equipamento criado com sucesso!")
                            st.session_state.show_equipment_form = False
                            st.rerun()
                        else:
                            st.error("Erro ao criar equipamento")
                    else:
                        st.error("Nome é obrigatório!")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_equipment_form = False
                    st.rerun()
    
    st.markdown("---")
    
    # Informação sobre equipamentos
    st.info("""
    💡 **Gerenciamento de Equipamentos**
    
    Cada cliente tem um equipamento cadastrado em seu horário fixo. Para variar o equipamento:
    - Use a **Edição Rápida de Clientes** para trocar o equipamento manualmente
    - Configure **sequências de equipamentos** para rotação automática a cada aula
    
    ⚠️ **Unicidade**: Nunca dois clientes podem usar o mesmo equipamento no mesmo horário.
    """)
    
    st.markdown("---")
    
    # Lista de equipamentos
    equipment = db.get_equipment()
    
    if equipment:
        for equip in equipment:
            with st.expander(f"🏋️ {equip['name']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Nome:** {equip['name']}")
                    description = equip.get('description', '')
                    if description:
                        st.write(f"**Descrição:** {description}")
                    else:
                        st.write("**Descrição:** Não informada")
                
                with col2:
                    if st.button(f"✏️ Editar", key=f"edit_equipment_{equip['id']}"):
                        st.session_state[f'edit_equipment_form_{equip["id"]}'] = True
                    
                    if st.button(f"🗑️ Excluir", key=f"delete_equipment_{equip['id']}"):
                        if db.delete_equipment(equip['id']):
                            st.success("Equipamento excluído!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir equipamento")
                
                # Formulário de edição
                if st.session_state.get(f'edit_equipment_form_{equip["id"]}', False):
                    with st.form(f"edit_equipment_{equip['id']}"):
                        st.write("**Editar Equipamento**")
                        
                        edit_name = st.text_input("Nome:", value=equip['name'], key=f"edit_equip_name_{equip['id']}")
                        edit_desc = st.text_area("Descrição:", value=equip['description'], key=f"edit_equip_desc_{equip['id']}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar"):
                                if db.update_equipment(equip['id'], edit_name, edit_desc):
                                    st.success("Equipamento atualizado!")
                                    st.session_state[f'edit_equipment_form_{equip["id"]}'] = False
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar equipamento")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state[f'edit_equipment_form_{equip["id"]}'] = False
                                st.rerun()
    else:
        st.info("Nenhum equipamento cadastrado")

def sequences_tab():
    """Aba de gerenciamento de sequências (templates globais)"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📋 Templates de Sequências (Globais)")
        st.info("💡 **Dica:** Estes são templates que podem ser copiados para criar sequências personalizadas para cada cliente.")
    
    with col2:
        if st.button("➕ Novo Template", use_container_width=True):
            st.session_state.show_sequence_form = True
    
    # Formulário de nova sequência
    if st.session_state.get('show_sequence_form', False):
        with st.form("new_sequence"):
            st.subheader("➕ Novo Template de Sequência")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome do template:", placeholder="Ex: Sequência Iniciante")
                day_options = {
                    "Segunda-feira": 1,
                    "Terça-feira": 2,
                    "Quarta-feira": 3,
                    "Quinta-feira": 4,
                    "Sexta-feira": 5
                }
                selected_day = st.selectbox("Dia da semana:", list(day_options.keys()))
            
            with col2:
                equipment = db.get_equipment()
                if equipment:
                    st.write("**Selecione os equipamentos na ordem desejada:**")
                    selected_equipment = []
                    
                    for equip in equipment:
                        if st.checkbox(f"{equip['name']}", key=f"seq_equip_{equip['id']}"):
                            selected_equipment.append(equip['id'])
                else:
                    st.warning("Cadastre equipamentos primeiro!")
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                if st.form_submit_button("✅ Criar Template", use_container_width=True):
                    if name and selected_day and selected_equipment:
                        day_number = day_options[selected_day]
                        if db.create_equipment_sequence(name, day_number, selected_equipment):
                            st.success("Template criado com sucesso!")
                            st.session_state.show_sequence_form = False
                            st.rerun()
                        else:
                            st.error("Erro ao criar template")
                    else:
                        st.error("Preencha todos os campos e selecione pelo menos um equipamento!")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_sequence_form = False
                    st.rerun()
    
    st.markdown("---")
    
    # Mostrar templates por dia
    days = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
    equipment = db.get_equipment()
    
    for i, day in enumerate(days, 1):
        st.subheader(f"📅 {day}")
        sequences = db.get_equipment_sequences(i)
        
        if sequences:
            for seq in sequences:
                with st.expander(f"📋 {seq['name']} (Template)"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("**Sequência de Equipamentos:**")
                        equipment_names = []
                        for equip_id in seq['equipment_order']:
                            equip = next((e for e in equipment if e['id'] == equip_id), None)
                            if equip:
                                equipment_names.append(equip['name'])
                        
                        if equipment_names:
                            st.write(" → ".join(equipment_names))
                        else:
                            st.write("Equipamentos não encontrados")
                        
                        st.info("💡 Este template pode ser copiado para clientes na aba 'Clientes'")
                    
                    with col2:
                        if st.button(f"🗑️ Excluir", key=f"delete_sequence_{seq['id']}"):
                            if db.delete_equipment_sequence(seq['id']):
                                st.success("Template excluído!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir template")
        else:
            st.info(f"Nenhum template cadastrado para {day}")
        
        st.markdown("---")

def schedules_overview_tab():
    """Aba de visão geral dos horários fixos"""
    
    # CSS para reduzir espaços (sem afetar padding-top global)
    st.markdown("""
    <style>
    h2 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .client-schedule-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
    }
    .schedule-time {
        display: inline-block;
        background-color: #2196F3;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        margin: 3px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("⏰ Horários Fixos dos Clientes")
    
    # Buscar clientes com contratos fixos
    clients = db.get_clients()
    fixed_clients = [c for c in clients if c.get('tipo_contrato') == 'fixo' and c.get('contrato_ativo') == 1]
    
    if not fixed_clients:
        st.info("📋 Nenhum cliente com contrato fixo ativo encontrado.")
        st.write("💡 Configure clientes com contrato fixo na aba **'Clientes'** para visualizar os horários aqui.")
        return
    
    # Tabs: por cliente ou por dia da semana
    tab_view1, tab_view2 = st.tabs(["👤 Por Cliente", "📅 Por Dia da Semana"])
    
    with tab_view1:
        st.markdown("### Lista de Clientes com Horários Fixos")
        
        # Estatísticas no topo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Clientes Fixos Ativos", len(fixed_clients))
        with col2:
            total_horarios = sum(len(c.get('dias_semana', {})) if isinstance(c.get('dias_semana'), dict) else 0 for c in fixed_clients)
            st.metric("⏰ Total de Horários/Semana", total_horarios)
        with col3:
            total_mes = total_horarios * 4
            st.metric("📊 Horários Estimados/Mês", total_mes)
        
        st.markdown("---")
        
        # Mostrar cada cliente
        dias_semana_map = {
            "1": "Segunda",
            "2": "Terça", 
            "3": "Quarta",
            "4": "Quinta",
            "5": "Sexta",
            "6": "Sábado",
            "0": "Domingo"
        }
        
        for client in fixed_clients:
            import json
            dias_semana = client.get('dias_semana', {})
            
            # Converter de string JSON se necessário
            if isinstance(dias_semana, str):
                try:
                    dias_semana = json.loads(dias_semana) if dias_semana else {}
                except:
                    dias_semana = {}
            
            if not dias_semana:
                continue
            
            # Card do cliente
            with st.container():
                st.markdown(f"""
                <div class="client-schedule-card">
                    <h4 style="margin: 0 0 10px 0;">👤 {client['name']}</h4>
                    <p style="margin: 5px 0;"><strong>📞 Telefone:</strong> {client.get('phone', 'Não informado')}</p>
                    <p style="margin: 5px 0;"><strong>📧 Email:</strong> {client.get('email', 'Não informado')}</p>
                    <p style="margin: 5px 0;"><strong>📅 Início do Contrato:</strong> {format_date_br(client.get('data_inicio_contrato', 'Não informado'))}</p>
                    <p style="margin: 5px 0;"><strong>⏰ Horários Semanais:</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar horários organizados
                col_horarios = st.columns(len(dias_semana))
                
                for idx, (dia_num, horario) in enumerate(sorted(dias_semana.items())):
                    with col_horarios[idx]:
                        dia_nome = dias_semana_map.get(dia_num, f"Dia {dia_num}")
                        st.markdown(f"""
                        <div style="text-align: center; padding: 10px; background-color: #e3f2fd; border-radius: 5px;">
                            <div style="font-weight: bold; color: #1976d2;">{dia_nome}</div>
                            <div class="schedule-time">{horario}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
    
    with tab_view2:
        st.markdown("### Horários Organizados por Dia da Semana")
        
        # Organizar horários por dia da semana
        horarios_por_dia = {
            "1": [], "2": [], "3": [], "4": [], "5": []
        }
        
        import json
        for client in fixed_clients:
            dias_semana = client.get('dias_semana', {})
            
            if isinstance(dias_semana, str):
                try:
                    dias_semana = json.loads(dias_semana) if dias_semana else {}
                except:
                    dias_semana = {}
            
            for dia_num, horario in dias_semana.items():
                if dia_num in horarios_por_dia:
                    horarios_por_dia[dia_num].append({
                        'cliente': client['name'],
                        'horario': horario,
                        'telefone': client.get('phone', 'N/A'),
                        'email': client.get('email', 'N/A')
                    })
        
        # Mostrar por dia
        dias_semana_completo = {
            "1": "Segunda-feira",
            "2": "Terça-feira",
            "3": "Quarta-feira",
            "4": "Quinta-feira",
            "5": "Sexta-feira"
        }
        
        for dia_num, dia_nome in dias_semana_completo.items():
            with st.expander(f"� {dia_nome}", expanded=True):
                horarios = horarios_por_dia[dia_num]
                
                if horarios:
                    # Ordenar por horário
                    horarios.sort(key=lambda x: x['horario'])
                    
                    # Mostrar em tabela
                    st.markdown(f"**Total de horários: {len(horarios)}**")
                    
                    for h in horarios:
                        col1, col2, col3 = st.columns([1, 2, 2])
                        
                        with col1:
                            st.markdown(f"<div class='schedule-time'>{h['horario']}</div>", unsafe_allow_html=True)
                        
                        with col2:
                            st.write(f"👤 **{h['cliente']}**")
                        
                        with col3:
                            st.write(f"📞 {h['telefone']}")
                else:
                    st.info(f"Nenhum horário fixo agendado para {dia_nome}")

def notifications_tab():
    """Aba de notificações"""
    st.subheader("🔔 Notificações dos Clientes")
    
    import sqlite3
    from datetime import datetime
    
    # Buscar notificações do banco
    conn = sqlite3.connect("pilates.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.id, n.client_id, n.client_name, n.type, n.message, n.is_read, n.created_at,
               u.phone
        FROM notifications n
        LEFT JOIN users u ON n.client_id = u.id
        ORDER BY n.is_read ASC, n.created_at DESC
    ''')
    
    notifications = cursor.fetchall()
    conn.close()
    
    if notifications:
        for notif in notifications:
            notif_id, client_id, client_name, notif_type, message, is_read, created_at, phone = notif
            
            # Definir cor baseada no tipo
            if notif_type == "Falta":
                icon = "�"
                bg_color = "#ffebee"
            elif notif_type == "Atraso":
                icon = "🟡"
                bg_color = "#fff9e6"
            else:
                icon = "🔵"
                bg_color = "#e3f2fd"
            
            # Indicador de lida/não lida
            read_icon = "✅" if is_read else "🆕"
            
            with st.container():
                st.markdown(f"""
                <div style='padding: 12px; margin: 8px 0; background-color: {bg_color}; 
                            border-left: 4px solid {"#4CAF50" if is_read else "#f44336"}; border-radius: 4px;'>
                    <b>{read_icon} {icon} {notif_type}</b> - {client_name}
                    <br><small>📅 {datetime.fromisoformat(created_at).strftime('%d/%m/%Y %H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.write(f"**Cliente:** {client_name}")
                    if phone:
                        st.write(f"**Telefone:** {phone}")
                
                with col2:
                    with st.expander("📖 Ler mensagem completa"):
                        st.write(message)
                
                with col3:
                    if not is_read:
                        if st.button("✅ Marcar como Lida", key=f"read_{notif_id}", use_container_width=True):
                            conn = sqlite3.connect("pilates.db")
                            cursor = conn.cursor()
                            cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
                            conn.commit()
                            conn.close()
                            st.success("Marcada como lida!")
                            st.rerun()
                    else:
                        st.success("Lida ✓")
                    
                    # Botão para limpar/excluir notificação
                    if st.button("🗑️ Limpar", key=f"delete_{notif_id}", use_container_width=True, type="secondary"):
                        conn = sqlite3.connect("pilates.db")
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM notifications WHERE id = ?', (notif_id,))
                        conn.commit()
                        conn.close()
                        st.success("Notificação removida!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("📭 Nenhuma notificação pendente")

def get_status_text(status):
    """Retorna texto do status em português"""
    status_map = {
        'scheduled': 'Agendado',
        'rescheduled': 'Reagendado',
        'cancelled': 'Cancelado',
        'completed': 'Concluído'
    }
    return status_map.get(status, status)

def get_status_emoji(status):
    """Retorna emoji do status"""
    emoji_map = {
        'scheduled': '✅',
        'rescheduled': '🔄',
        'cancelled': '❌',
        'completed': '✔️'
    }
    return emoji_map.get(status, '❓')

def get_day_name(day_number):
    """Retorna nome do dia da semana"""
    day_map = {
        1: 'Segunda-feira',
        2: 'Terça-feira',
        3: 'Quarta-feira',
        4: 'Quinta-feira',
        5: 'Sexta-feira'
    }
    return day_map.get(day_number, f'Dia {day_number}')

def financial_tab():
    """Aba de gerenciamento financeiro"""
    st.subheader("💰 Gestão Financeira")
    
    # Sub-tabs para cada seção financeira
    fin_tab1, fin_tab2, fin_tab3 = st.tabs([
        "💵 Contas a Receber",
        "💸 Contas a Pagar",
        "📊 Fluxo de Caixa"
    ])
    
    with fin_tab1:
        contas_receber_section()
    
    with fin_tab2:
        contas_pagar_section()
    
    with fin_tab3:
        fluxo_caixa_section()

def contas_receber_section():
    """Seção de contas a receber"""
    st.markdown("### 💵 Contas a Receber")
    
    # Botão para adicionar nova conta
    if 'show_add_receber' not in st.session_state:
        st.session_state.show_add_receber = False
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Mensalidades e Pagamentos dos Clientes**")
    with col2:
        if st.button("➕ Nova Conta", use_container_width=True):
            st.session_state.show_add_receber = not st.session_state.show_add_receber
    
    # Formulário para adicionar nova conta
    if st.session_state.show_add_receber:
        with st.form("form_nova_receber"):
            st.markdown("#### Adicionar Conta a Receber")
            
            # Buscar clientes
            clients = db.get_clients()
            client_options = {f"{c['name']} - {c['phone']}": c['id'] for c in clients}
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_client = st.selectbox("Cliente:", list(client_options.keys()))
                tipo_plano = st.selectbox("Tipo de Plano:", 
                    ["Mensalidade", "Por Sessão", "Pacote", "Fisioterapia"])
                valor = st.number_input("Valor (R$):", min_value=0.0, value=150.0, step=10.0)
            
            with col2:
                quantidade = st.number_input("Quantidade (meses ou sessões):", 
                    min_value=1, value=1, step=1)
                data_vencimento = st.date_input("Data de Vencimento:", 
                    value=date.today())
                observacoes = st.text_area("Observações:", max_chars=200)
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                if st.form_submit_button("💾 Salvar", use_container_width=True):
                    client_id = client_options[selected_client]
                    if db.create_conta_receber(
                        client_id, tipo_plano, valor, quantidade, 
                        data_vencimento.strftime('%Y-%m-%d'), observacoes
                    ):
                        st.success("✅ Conta a receber criada!")
                        st.session_state.show_add_receber = False
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar conta")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_add_receber = False
                    st.rerun()
    
    st.markdown("---")
    
    # Listar contas a receber
    contas = db.get_contas_receber()
    
    if contas:
        # Calcular valores do mês corrente
        from datetime import datetime
        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        # Último dia do mês
        if hoje.month == 12:
            ultimo_dia_mes = date(hoje.year, 12, 31)
        else:
            proximo_mes = date(hoje.year, hoje.month + 1, 1)
            from datetime import timedelta
            ultimo_dia_mes = proximo_mes - timedelta(days=1)
        
        # Filtrar contas do mês corrente
        contas_mes_corrente = [c for c in contas 
                               if primeiro_dia_mes <= datetime.strptime(c['data_vencimento'], '%Y-%m-%d').date() <= ultimo_dia_mes]
        
        valor_receber_mes = sum(c['valor'] for c in contas_mes_corrente if c['status'] == 'pendente')
        valor_recebido_mes = sum(c['valor'] for c in contas_mes_corrente if c['status'] == 'pago')
        
        # Exibir métricas do mês corrente
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("💰 A Receber no Mês Corrente", f"R$ {valor_receber_mes:.2f}")
        with col_m2:
            st.metric("✅ Recebido no Mês Corrente", f"R$ {valor_recebido_mes:.2f}")
        
        st.markdown("---")
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_status = st.selectbox("Filtrar por Status:", 
                ["Todos", "Pendente", "Pago"])
        with col_f2:
            filter_client = st.text_input("Filtrar por Cliente:")
        
        # Aplicar filtros
        contas_filtradas = contas
        if filter_status != "Todos":
            contas_filtradas = [c for c in contas_filtradas 
                              if c['status'].lower() == filter_status.lower()]
        if filter_client:
            contas_filtradas = [c for c in contas_filtradas 
                              if filter_client.lower() in c['client_name'].lower()]
        
        st.markdown(f"**Total de contas: {len(contas_filtradas)}**")
        
        # Exibir contas
        for conta in contas_filtradas:
            from datetime import datetime
            
            status_icon = "✅" if conta['status'] == 'pago' else "⏳"
            bg_color = "#d4edda" if conta['status'] == 'pago' else "#fff3cd"
            
            with st.container():
                st.markdown(f"""
                <div style='padding: 10px; margin: 8px 0; background-color: {bg_color}; 
                            border-left: 4px solid {"#28a745" if conta['status'] == 'pago' else "#ffc107"}; 
                            border-radius: 4px;'>
                    <b>{status_icon} {conta['client_name']}</b> - R$ {conta['valor']:.2f}
                    <br><small>Vencimento: {datetime.strptime(conta['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.write(f"**Tipo:** {conta['tipo_plano']}")
                    st.write(f"**Qtd:** {conta['quantidade']}")
                
                with col2:
                    if conta['status'] == 'pago' and conta['data_pagamento']:
                        st.success(f"Pago em: {datetime.strptime(conta['data_pagamento'], '%Y-%m-%d').strftime('%d/%m/%Y')}")
                    else:
                        st.warning("Pendente")
                
                with col3:
                    # Botão editar
                    if st.button("✏️ Editar", key=f"edit_{conta['id']}", use_container_width=True):
                        st.session_state[f"editing_receber_{conta['id']}"] = True
                        st.rerun()
                
                with col4:
                    if conta['status'] != 'pago':
                        if st.button("💰 Marcar Pago", key=f"pagar_{conta['id']}", use_container_width=True):
                            if db.update_pagamento_receber(conta['id'], date.today().strftime('%Y-%m-%d')):
                                st.success("Pago!")
                                st.rerun()
                    else:
                        if st.button("🗑️", key=f"del_rec_{conta['id']}", use_container_width=True):
                            if db.delete_conta_receber(conta['id']):
                                st.success("Excluído!")
                                st.rerun()
                
                # Formulário de edição
                if st.session_state.get(f"editing_receber_{conta['id']}", False):
                    with st.form(f"form_edit_receber_{conta['id']}"):
                        st.markdown("#### ✏️ Editar Conta")
                        
                        col_e1, col_e2 = st.columns(2)
                        
                        with col_e1:
                            edit_tipo = st.selectbox("Tipo de Plano:", 
                                ["Mensalidade", "Por Sessão", "Pacote", "Fisioterapia", "Fisioterapia + Pilates", "Pilates"],
                                index=["Mensalidade", "Por Sessão", "Pacote", "Fisioterapia", "Fisioterapia + Pilates", "Pilates"].index(conta['tipo_plano']) 
                                    if conta['tipo_plano'] in ["Mensalidade", "Por Sessão", "Pacote", "Fisioterapia", "Fisioterapia + Pilates", "Pilates"] else 0,
                                key=f"edit_tipo_{conta['id']}")
                            edit_valor = st.number_input("Valor (R$):", 
                                min_value=0.0, 
                                value=float(conta['valor']), 
                                step=10.0,
                                key=f"edit_valor_{conta['id']}")
                            edit_qtd = st.number_input("Quantidade:", 
                                min_value=1, 
                                value=conta['quantidade'], 
                                step=1,
                                key=f"edit_qtd_{conta['id']}")
                        
                        with col_e2:
                            edit_venc = st.date_input("Data de Vencimento:",
                                value=datetime.strptime(conta['data_vencimento'], '%Y-%m-%d').date(),
                                key=f"edit_venc_{conta['id']}")
                            edit_status = st.selectbox("Status:",
                                ["pendente", "pago"],
                                index=0 if conta['status'] == 'pendente' else 1,
                                key=f"edit_status_{conta['id']}")
                            
                            if edit_status == 'pago':
                                if conta['data_pagamento']:
                                    default_pag = datetime.strptime(conta['data_pagamento'], '%Y-%m-%d').date()
                                else:
                                    default_pag = date.today()
                                edit_data_pag = st.date_input("Data de Pagamento:",
                                    value=default_pag,
                                    key=f"edit_data_pag_{conta['id']}")
                            else:
                                edit_data_pag = None
                            
                            edit_obs = st.text_area("Observações:",
                                value=conta['observacoes'] or "",
                                max_chars=200,
                                key=f"edit_obs_{conta['id']}")
                        
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.form_submit_button("💾 Salvar", use_container_width=True):
                                # Atualizar conta
                                import sqlite3
                                try:
                                    conn = sqlite3.connect('pilates.db')
                                    if edit_status == 'pago' and edit_data_pag:
                                        conn.execute('''
                                            UPDATE contas_receber 
                                            SET tipo_plano=?, valor=?, quantidade=?, 
                                                data_vencimento=?, status=?, data_pagamento=?, observacoes=?
                                            WHERE id=?
                                        ''', (edit_tipo, edit_valor, edit_qtd, 
                                              edit_venc.strftime('%Y-%m-%d'), edit_status,
                                              edit_data_pag.strftime('%Y-%m-%d'), edit_obs, conta['id']))
                                    else:
                                        conn.execute('''
                                            UPDATE contas_receber 
                                            SET tipo_plano=?, valor=?, quantidade=?, 
                                                data_vencimento=?, status=?, observacoes=?
                                            WHERE id=?
                                        ''', (edit_tipo, edit_valor, edit_qtd, 
                                              edit_venc.strftime('%Y-%m-%d'), edit_status, edit_obs, conta['id']))
                                    conn.commit()
                                    conn.close()
                                    st.success("✅ Conta atualizada!")
                                    st.session_state[f"editing_receber_{conta['id']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar: {e}")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f"editing_receber_{conta['id']}"] = False
                                st.rerun()
                
                if conta['observacoes']:
                    with st.expander("📝 Observações"):
                        st.write(conta['observacoes'])
                
                st.markdown("---")
        
        # Resumo financeiro
        total_pendente = sum(c['valor'] for c in contas_filtradas if c['status'] == 'pendente')
        total_recebido = sum(c['valor'] for c in contas_filtradas if c['status'] == 'pago')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Pendente", f"R$ {total_pendente:.2f}")
        with col2:
            st.metric("✅ Total Recebido", f"R$ {total_recebido:.2f}")
        with col3:
            st.metric("📊 Total Geral", f"R$ {total_pendente + total_recebido:.2f}")
    else:
        st.info("📭 Nenhuma conta a receber cadastrada")

def contas_pagar_section():
    """Seção de contas a pagar"""
    st.markdown("### 💸 Contas a Pagar")
    
    # Botão para adicionar nova conta
    if 'show_add_pagar' not in st.session_state:
        st.session_state.show_add_pagar = False
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Despesas e Contas do Estúdio**")
    with col2:
        if st.button("➕ Nova Despesa", use_container_width=True):
            st.session_state.show_add_pagar = not st.session_state.show_add_pagar
    
    # Formulário para adicionar nova conta
    if st.session_state.show_add_pagar:
        with st.form("form_nova_pagar"):
            st.markdown("#### Adicionar Conta a Pagar")
            
            col1, col2 = st.columns(2)
            
            with col1:
                data_debito = st.date_input("Data do Débito:", value=date.today())
                tipo_debito = st.selectbox("Tipo de Débito:", 
                    ["Aluguel", "Energia", "Água", "Internet", "Equipamento", 
                     "Manutenção", "Salário", "Impostos", "Marketing", "Outros"])
                valor_total = st.number_input("Valor Total (R$):", 
                    min_value=0.0, value=100.0, step=10.0)
                recorrente = st.checkbox("🔄 Recorrente (até Dezembro)", value=False,
                    help="Marca para criar parcelas mensais automaticamente até dezembro do ano atual")
            
            with col2:
                if not recorrente:
                    quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
                    tipo_parcelamento = st.selectbox("Tipo:", 
                        ["mensal", "parcelado"],
                        format_func=lambda x: "Mensal (mesmo valor repetido)" if x == "mensal" 
                                            else "Parcelado (dividir valor)")
                else:
                    # Calcular meses até dezembro
                    meses_ate_dez = 12 - date.today().month + 1
                    st.info(f"📅 Serão criadas {meses_ate_dez} parcelas até Dezembro/{date.today().year}")
                    quantidade = meses_ate_dez
                    tipo_parcelamento = "mensal"
                
                observacoes = st.text_area("Observações:", max_chars=200)
            
            if not recorrente:
                st.info(f"💡 {quantidade} parcela(s) de R$ {(valor_total/quantidade if tipo_parcelamento=='parcelado' else valor_total):.2f}")
            else:
                st.info(f"💡 {quantidade} parcelas mensais de R$ {valor_total:.2f} (recorrente)")
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                if st.form_submit_button("💾 Salvar", use_container_width=True):
                    if db.create_conta_pagar(
                        data_debito.strftime('%Y-%m-%d'), tipo_debito, valor_total,
                        quantidade, tipo_parcelamento, observacoes, recorrente
                    ):
                        st.success("✅ Conta a pagar criada!")
                        st.session_state.show_add_pagar = False
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar conta")
            
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_add_pagar = False
                    st.rerun()
    
    st.markdown("---")
    
    # Listar parcelas a pagar
    parcelas = db.get_parcelas_pagar()
    
    if parcelas:
        # Calcular valores do mês corrente
        from datetime import datetime, timedelta
        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        # Último dia do mês
        if hoje.month == 12:
            ultimo_dia_mes = date(hoje.year, 12, 31)
        else:
            proximo_mes = date(hoje.year, hoje.month + 1, 1)
            ultimo_dia_mes = proximo_mes - timedelta(days=1)
        
        # Filtrar parcelas do mês corrente
        parcelas_mes_corrente = [p for p in parcelas 
                                 if primeiro_dia_mes <= datetime.strptime(p['data_vencimento'], '%Y-%m-%d').date() <= ultimo_dia_mes]
        
        valor_pagar_mes = sum(p['valor'] for p in parcelas_mes_corrente if p['status'] == 'pendente')
        valor_pago_mes = sum(p['valor'] for p in parcelas_mes_corrente if p['status'] == 'pago')
        
        # Exibir métricas do mês corrente
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("💸 A Pagar no Mês Corrente", f"R$ {valor_pagar_mes:.2f}")
        with col_m2:
            st.metric("✅ Pago no Mês Corrente", f"R$ {valor_pago_mes:.2f}")
        
        st.markdown("---")
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_status = st.selectbox("Filtrar por Status:", 
                ["Todos", "Pendente", "Pago"], key="filter_status_pagar")
        with col_f2:
            filter_tipo = st.selectbox("Filtrar por Tipo:", 
                ["Todos"] + ["Aluguel", "Energia", "Água", "Internet", "Equipamento", 
                            "Manutenção", "Salário", "Impostos", "Marketing", "Outros"])
        
        # Aplicar filtros
        parcelas_filtradas = parcelas
        if filter_status != "Todos":
            parcelas_filtradas = [p for p in parcelas_filtradas 
                                if p['status'].lower() == filter_status.lower()]
        if filter_tipo != "Todos":
            parcelas_filtradas = [p for p in parcelas_filtradas 
                                if p['tipo_debito'] == filter_tipo]
        
        st.markdown(f"**Total de parcelas: {len(parcelas_filtradas)}**")
        
        # Exibir parcelas
        for parcela in parcelas_filtradas:
            from datetime import datetime
            
            status_icon = "✅" if parcela['status'] == 'pago' else "⏳"
            bg_color = "#d4edda" if parcela['status'] == 'pago' else "#f8d7da"
            
            with st.container():
                st.markdown(f"""
                <div style='padding: 10px; margin: 8px 0; background-color: {bg_color}; 
                            border-left: 4px solid {"#28a745" if parcela['status'] == 'pago' else "#dc3545"}; 
                            border-radius: 4px;'>
                    <b>{status_icon} {parcela['tipo_debito']}</b> - R$ {parcela['valor']:.2f}
                    <br><small>Vencimento: {datetime.strptime(parcela['data_vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')} 
                    | Parcela {parcela['numero_parcela']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    if parcela['status'] == 'pago' and parcela['data_pagamento']:
                        st.success(f"Pago em: {datetime.strptime(parcela['data_pagamento'], '%Y-%m-%d').strftime('%d/%m/%Y')}")
                    else:
                        st.warning("Pendente")
                
                with col2:
                    # Botão editar
                    if st.button("✏️ Editar", key=f"edit_p_{parcela['id']}", use_container_width=True):
                        st.session_state[f"editing_pagar_{parcela['id']}"] = True
                        st.rerun()
                
                with col3:
                    if parcela['status'] != 'pago':
                        if st.button("💰 Pagar", key=f"pagar_p_{parcela['id']}", use_container_width=True):
                            if db.update_pagamento_pagar(parcela['id'], date.today().strftime('%Y-%m-%d')):
                                st.success("Pago!")
                                st.rerun()
                    else:
                        st.success("✓ Pago")
                
                with col4:
                    if st.button("🗑️", key=f"del_p_{parcela['id']}", use_container_width=True, 
                                help="Excluir esta parcela"):
                        if db.delete_parcela_pagar(parcela['id']):
                            st.success("Parcela excluída!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir parcela")
                
                # Formulário de edição
                if st.session_state.get(f"editing_pagar_{parcela['id']}", False):
                    with st.form(f"form_edit_pagar_{parcela['id']}"):
                        st.markdown("#### ✏️ Editar Parcela")
                        
                        # Buscar informações da conta principal
                        import sqlite3
                        conn = sqlite3.connect('pilates.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT recorrente, data_debito, valor_total
                            FROM contas_pagar 
                            WHERE id=(SELECT conta_pagar_id FROM parcelas_pagar WHERE id=?)
                        ''', (parcela['id'],))
                        conta_info = cursor.fetchone()
                        conn.close()
                        
                        is_recorrente = conta_info[0] if conta_info else 0
                        data_debito_original = conta_info[1] if conta_info else None
                        valor_original = conta_info[2] if conta_info else parcela['valor']
                        
                        col_e1, col_e2 = st.columns(2)
                        
                        with col_e1:
                            edit_tipo_p = st.selectbox("Tipo de Débito:", 
                                ["Aluguel", "Energia", "Água", "Internet", "Equipamento", 
                                 "Manutenção", "Salário", "Impostos", "Marketing", "Outros"],
                                index=["Aluguel", "Energia", "Água", "Internet", "Equipamento", 
                                       "Manutenção", "Salário", "Impostos", "Marketing", "Outros"].index(parcela['tipo_debito']) 
                                    if parcela['tipo_debito'] in ["Aluguel", "Energia", "Água", "Internet", "Equipamento", 
                                                                    "Manutenção", "Salário", "Impostos", "Marketing", "Outros"] else 10,
                                key=f"edit_tipo_p_{parcela['id']}")
                            edit_valor_p = st.number_input("Valor (R$):", 
                                min_value=0.0, 
                                value=float(parcela['valor']), 
                                step=10.0,
                                key=f"edit_valor_p_{parcela['id']}")
                            
                            # Sempre mostrar o checkbox recorrente
                            edit_recorrente = st.checkbox("🔄 Recorrente", 
                                value=bool(is_recorrente), 
                                key=f"edit_recorrente_{parcela['id']}",
                                help="Atualizar todas as parcelas futuras com o novo valor")
                        
                        with col_e2:
                            edit_venc_p = st.date_input("Data de Vencimento:",
                                value=datetime.strptime(parcela['data_vencimento'], '%Y-%m-%d').date(),
                                key=f"edit_venc_p_{parcela['id']}")
                            edit_status_p = st.selectbox("Status:",
                                ["pendente", "pago"],
                                index=0 if parcela['status'] == 'pendente' else 1,
                                key=f"edit_status_p_{parcela['id']}")
                            
                            if edit_status_p == 'pago':
                                if parcela['data_pagamento']:
                                    default_pag_p = datetime.strptime(parcela['data_pagamento'], '%Y-%m-%d').date()
                                else:
                                    default_pag_p = date.today()
                                edit_data_pag_p = st.date_input("Data de Pagamento:",
                                    value=default_pag_p,
                                    key=f"edit_data_pag_p_{parcela['id']}")
                            else:
                                edit_data_pag_p = None
                        
                        if edit_recorrente and edit_valor_p != parcela['valor']:
                            st.warning(f"⚠️ O valor será atualizado para R$ {edit_valor_p:.2f} em todas as parcelas FUTURAS (a partir de hoje)")
                        
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.form_submit_button("💾 Salvar", use_container_width=True):
                                # Atualizar parcela
                                import sqlite3
                                try:
                                    conn = sqlite3.connect('pilates.db')
                                    
                                    # Atualizar tipo_debito, valor_total e recorrente na conta_pagar principal
                                    conn.execute('''
                                        UPDATE contas_pagar 
                                        SET tipo_debito=?, valor_total=?, recorrente=?
                                        WHERE id=(SELECT conta_pagar_id FROM parcelas_pagar WHERE id=?)
                                    ''', (edit_tipo_p, edit_valor_p, 1 if edit_recorrente else 0, parcela['id']))
                                    
                                    # Atualizar parcela atual
                                    if edit_status_p == 'pago' and edit_data_pag_p:
                                        conn.execute('''
                                            UPDATE parcelas_pagar 
                                            SET valor=?, data_vencimento=?, status=?, data_pagamento=?
                                            WHERE id=?
                                        ''', (edit_valor_p, edit_venc_p.strftime('%Y-%m-%d'), 
                                              edit_status_p, edit_data_pag_p.strftime('%Y-%m-%d'), parcela['id']))
                                    else:
                                        conn.execute('''
                                            UPDATE parcelas_pagar 
                                            SET valor=?, data_vencimento=?, status=?, data_pagamento=NULL
                                            WHERE id=?
                                        ''', (edit_valor_p, edit_venc_p.strftime('%Y-%m-%d'), 
                                              edit_status_p, parcela['id']))
                                    
                                    # Se for recorrente e o valor mudou, atualizar parcelas futuras
                                    if edit_recorrente and edit_valor_p != parcela['valor']:
                                        hoje_str = date.today().strftime('%Y-%m-%d')
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE parcelas_pagar 
                                            SET valor=?
                                            WHERE conta_pagar_id=(SELECT conta_pagar_id FROM parcelas_pagar WHERE id=?)
                                            AND data_vencimento > ?
                                            AND id != ?
                                        ''', (edit_valor_p, parcela['id'], hoje_str, parcela['id']))
                                        parcelas_atualizadas = cursor.rowcount
                                    else:
                                        parcelas_atualizadas = 0
                                    
                                    conn.commit()
                                    conn.close()
                                    
                                    if parcelas_atualizadas > 0:
                                        st.success(f"✅ Parcela atualizada! {parcelas_atualizadas} parcelas futuras também foram atualizadas.")
                                    else:
                                        st.success("✅ Parcela atualizada!")
                                    
                                    st.session_state[f"editing_pagar_{parcela['id']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar: {e}")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f"editing_pagar_{parcela['id']}"] = False
                                st.rerun()
                
                st.markdown("---")
        
        # Resumo financeiro
        total_pendente = sum(p['valor'] for p in parcelas_filtradas if p['status'] == 'pendente')
        total_pago = sum(p['valor'] for p in parcelas_filtradas if p['status'] == 'pago')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💸 Total Pendente", f"R$ {total_pendente:.2f}")
        with col2:
            st.metric("✅ Total Pago", f"R$ {total_pago:.2f}")
        with col3:
            st.metric("📊 Total Geral", f"R$ {total_pendente + total_pago:.2f}")
    else:
        st.info("📭 Nenhuma conta a pagar cadastrada")

def fluxo_caixa_section():
    """Seção de fluxo de caixa"""
    st.markdown("### 📊 Fluxo de Caixa")
    
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    # Tabs para visualização diária e mensal
    view_tab1, view_tab2 = st.tabs(["📅 Fluxo Diário", "📊 Fluxo Mensal"])
    
    with view_tab1:
        fluxo_caixa_diario()
    
    with view_tab2:
        fluxo_caixa_mensal()

def fluxo_caixa_diario():
    """Visualização diária do fluxo de caixa"""
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    # Seleção de período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periodo = st.selectbox("Período:", 
            ["Este Mês", "Próximo Mês", "Este Ano", "Personalizado"],
            key="periodo_diario")
    
    hoje = date.today()
    
    if periodo == "Este Mês":
        data_inicio = date(hoje.year, hoje.month, 1)
        data_fim = date(hoje.year, hoje.month, 1) + relativedelta(months=1) - timedelta(days=1)
    elif periodo == "Próximo Mês":
        proximo_mes = hoje + relativedelta(months=1)
        data_inicio = date(proximo_mes.year, proximo_mes.month, 1)
        data_fim = data_inicio + relativedelta(months=1) - timedelta(days=1)
    elif periodo == "Este Ano":
        data_inicio = date(hoje.year, 1, 1)
        data_fim = date(hoje.year, 12, 31)
    else:  # Personalizado
        with col2:
            data_inicio = st.date_input("Data Início:", value=date(hoje.year, hoje.month, 1))
        with col3:
            data_fim = st.date_input("Data Fim:", value=hoje)
    
    if periodo != "Personalizado":
        st.info(f"📅 Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    st.markdown("---")
    
    # Buscar dados
    fluxo = db.get_fluxo_caixa(data_inicio.strftime('%Y-%m-%d'), 
                               data_fim.strftime('%Y-%m-%d'))
    
    # Criar DataFrame para visualização
    import pandas as pd
    
    todas_datas = set(fluxo['receber'].keys()) | set(fluxo['pagar'].keys())
    
    if todas_datas:
        dados = []
        for data_str in sorted(todas_datas):
            receber = fluxo['receber'].get(data_str, 0)
            pagar = fluxo['pagar'].get(data_str, 0)
            saldo = receber - pagar
            
            dados.append({
                'Data': datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y'),
                'A Receber': f"R$ {receber:.2f}",
                'A Pagar': f"R$ {pagar:.2f}",
                'Saldo': f"R$ {saldo:.2f}"
            })
        
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Resumo geral
        total_receber = sum(fluxo['receber'].values())
        total_pagar = sum(fluxo['pagar'].values())
        saldo_periodo = total_receber - total_pagar
        
        st.markdown("---")
        st.markdown("### 💰 Resumo do Período")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💵 Total a Receber", f"R$ {total_receber:.2f}")
        
        with col2:
            st.metric("💸 Total a Pagar", f"R$ {total_pagar:.2f}")
        
        with col3:
            delta_color = "normal" if saldo_periodo >= 0 else "inverse"
            st.metric("📊 Saldo do Período", f"R$ {saldo_periodo:.2f}",
                     delta=f"{'Positivo' if saldo_periodo >= 0 else 'Negativo'}")
        
        # Gráfico
        if len(dados) > 0:
            import plotly.graph_objects as go
            
            datas = [datetime.strptime(d, '%Y-%m-%d') for d in sorted(todas_datas)]
            # Formatar datas para exibição brasileira
            datas_br = [d.strftime('%d/%m') for d in datas]
            receber_vals = [fluxo['receber'].get(d, 0) for d in sorted(todas_datas)]
            pagar_vals = [fluxo['pagar'].get(d, 0) for d in sorted(todas_datas)]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=datas_br,
                y=receber_vals,
                name='A Receber',
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                x=datas_br,
                y=[-v for v in pagar_vals],
                name='A Pagar',
                marker_color='red'
            ))
            
            fig.update_layout(
                title='Fluxo de Caixa',
                xaxis_title='Data',
                yaxis_title='Valor (R$)',
                barmode='relative',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Nenhuma movimentação financeira no período selecionado")

def fluxo_caixa_mensal():
    """Visualização mensal do fluxo de caixa"""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import pandas as pd
    import plotly.graph_objects as go
    
    st.markdown("#### 📊 Resumo Mensal")
    
    # Seleção de ano
    col1, col2 = st.columns([1, 3])
    with col1:
        ano_atual = date.today().year
        ano_selecionado = st.selectbox("Ano:", 
            list(range(ano_atual - 2, ano_atual + 2)), 
            index=2,
            key="ano_mensal")
    
    # Buscar dados de todo o ano
    data_inicio = f"{ano_selecionado}-01-01"
    data_fim = f"{ano_selecionado}-12-31"
    
    fluxo = db.get_fluxo_caixa(data_inicio, data_fim)
    
    # Agrupar por mês
    meses_receber = {}
    meses_pagar = {}
    
    for data_str, valor in fluxo['receber'].items():
        mes = data_str[:7]  # YYYY-MM
        meses_receber[mes] = meses_receber.get(mes, 0) + valor
    
    for data_str, valor in fluxo['pagar'].items():
        mes = data_str[:7]  # YYYY-MM
        meses_pagar[mes] = meses_pagar.get(mes, 0) + valor
    
    # Criar lista de todos os meses do ano
    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    dados_mensais = []
    valores_receber = []
    valores_pagar = []
    valores_saldo = []
    
    for mes_num in range(1, 13):
        mes_str = f"{ano_selecionado}-{mes_num:02d}"
        receber = meses_receber.get(mes_str, 0)
        pagar = meses_pagar.get(mes_str, 0)
        saldo = receber - pagar
        
        dados_mensais.append({
            'Mês': meses_nomes[mes_num - 1],
            'A Receber': f"R$ {receber:.2f}",
            'A Pagar': f"R$ {pagar:.2f}",
            'Saldo': f"R$ {saldo:.2f}"
        })
        
        valores_receber.append(receber)
        valores_pagar.append(pagar)
        valores_saldo.append(saldo)
    
    # Gráfico de barras comparativo
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=meses_nomes,
        y=valores_receber,
        name='A Receber',
        marker_color='#28a745',
        text=[f'R$ {v:.0f}' for v in valores_receber],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        x=meses_nomes,
        y=valores_pagar,
        name='A Pagar',
        marker_color='#dc3545',
        text=[f'R$ {v:.0f}' for v in valores_pagar],
        textposition='outside'
    ))
    
    fig.add_trace(go.Scatter(
        x=meses_nomes,
        y=valores_saldo,
        name='Saldo',
        mode='lines+markers',
        line=dict(color='#007bff', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f'Fluxo de Caixa Mensal - {ano_selecionado}',
        xaxis_title='Mês',
        yaxis_title='Receitas e Despesas (R$)',
        yaxis2=dict(
            title='Saldo (R$)',
            overlaying='y',
            side='right'
        ),
        barmode='group',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de resumo
    st.markdown("---")
    st.markdown("#### 📋 Detalhamento Mensal")
    
    df = pd.DataFrame(dados_mensais)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Totais do ano
    st.markdown("---")
    st.markdown(f"### 💰 Resumo do Ano {ano_selecionado}")
    
    total_receber_ano = sum(valores_receber)
    total_pagar_ano = sum(valores_pagar)
    saldo_ano = total_receber_ano - total_pagar_ano
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💵 Total a Receber", f"R$ {total_receber_ano:.2f}")
    
    with col2:
        st.metric("💸 Total a Pagar", f"R$ {total_pagar_ano:.2f}")
    
    with col3:
        st.metric("📊 Saldo Anual", f"R$ {saldo_ano:.2f}")
    
    with col4:
        media_mensal = saldo_ano / 12
        st.metric("📈 Média Mensal", f"R$ {media_mensal:.2f}")

def attendance_history_tab():
    """Aba de Histórico de Presença"""
    import streamlit as st
    from utils.database import db
    from datetime import datetime, timedelta, date
    import sqlite3
    from collections import defaultdict
    import calendar
    from dateutil.relativedelta import relativedelta
    
    st.title("📊 Histórico de Presença")
    st.markdown("Visualize e edite o histórico de presenças e faltas dos clientes")
    
    # Filtro por cliente
    clients = db.get_clients()
    client_options = ["Todos os clientes"] + [f"{c['name']} ({c['email']})" for c in clients]
    selected_client_str = st.selectbox("🔍 Filtrar por Cliente:", client_options)
    
    if selected_client_str == "Todos os clientes":
        selected_client_id = None
    else:
        # Extrair ID do cliente
        selected_client = next((c for c in clients if f"{c['name']} ({c['email']})" == selected_client_str), None)
        selected_client_id = selected_client['id'] if selected_client else None
    
    st.markdown("---")
    
    # Buscar appointments dos últimos 3 meses até próximos 9 meses (12 meses total)
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    today = get_brasilia_today()
    # 3 meses atrás
    three_months_ago = today - relativedelta(months=3)
    # 9 meses à frente
    nine_months_ahead = today + relativedelta(months=9)
    
    # Query para buscar TODOS os appointments (marcados e não marcados)
    if selected_client_id:
        cursor.execute('''
            SELECT a.id, a.client_id, a.date, a.time, a.attended, u.name as client_name
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            WHERE a.date >= ? AND a.date <= ?
            AND a.client_id = ?
            ORDER BY a.date, a.time
        ''', (three_months_ago.strftime('%Y-%m-%d'), nine_months_ahead.strftime('%Y-%m-%d'), selected_client_id))
    else:
        cursor.execute('''
            SELECT a.id, a.client_id, a.date, a.time, a.attended, u.name as client_name
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            WHERE a.date >= ? AND a.date <= ?
            ORDER BY a.date, a.time
        ''', (three_months_ago.strftime('%Y-%m-%d'), nine_months_ahead.strftime('%Y-%m-%d')))
    
    all_appointments = cursor.fetchall()
    conn.close()
    
    # Filtrar apenas appointments marcados para estatísticas
    marked_appointments = [apt for apt in all_appointments if apt[4] is not None]
    
    # Mostrar estatísticas gerais
    if marked_appointments:
        total = len(marked_appointments)
        presencas = sum(1 for apt in marked_appointments if apt[4] == 1)
        faltas = sum(1 for apt in marked_appointments if apt[4] == 0)
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📋 Total de Registros", total)
        
        with col_stat2:
            st.metric("✅ Presenças", presencas)
        
        with col_stat3:
            st.metric("❌ Faltas", faltas)
        
        with col_stat4:
            taxa = (presencas / total * 100) if total > 0 else 0
            st.metric("📊 Taxa de Presença", f"{taxa:.1f}%")
        
        st.markdown("---")
    
    # Organizar appointments por data para facilitar busca
    appointments_by_date = defaultdict(list)
    for apt in all_appointments:
        apt_id, client_id, date_str, time_str, attended, client_name = apt
        appointments_by_date[date_str].append({
            'id': apt_id,
            'client_id': client_id,
            'client_name': client_name,
            'time': time_str,
            'attended': attended
        })
    
    # Função para criar calendário de um mês
    def create_month_calendar(year, month, appointments_dict):
        # Nome do mês em português
        meses = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        
        st.markdown(f"### {meses[month]} {year}")
        
        # Criar calendário
        cal = calendar.monthcalendar(year, month)
        
        # Cabeçalho dos dias da semana
        dias_semana_short = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        
        # CSS para o calendário
        st.markdown("""
            <style>
            .calendar-cell {
                text-align: center;
                padding: 10px;
                border: 1px solid #ddd;
                min-height: 50px;
                cursor: pointer;
            }
            .calendar-cell-blue {
                background-color: #90CAF9;
                font-weight: bold;
            }
            .calendar-cell-green {
                background-color: #A5D6A7;
                font-weight: bold;
            }
            .calendar-cell-red {
                background-color: #EF9A9A;
                font-weight: bold;
            }
            .calendar-cell-empty {
                background-color: #f0f0f0;
            }
            .calendar-header {
                text-align: center;
                font-weight: bold;
                padding: 5px;
                background-color: #e0e0e0;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Criar tabela HTML para o calendário
        html = '<table style="width:100%; border-collapse: collapse;">'
        
        # Cabeçalho
        html += '<tr>'
        for day in dias_semana_short:
            html += f'<th class="calendar-header">{day}</th>'
        html += '</tr>'
        
        # Dias do mês
        for week in cal:
            html += '<tr>'
            for day in week:
                if day == 0:
                    html += '<td class="calendar-cell calendar-cell-empty"></td>'
                else:
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    
                    # Verificar se há appointments neste dia
                    if date_str in appointments_dict:
                        day_apts = appointments_dict[date_str]
                        
                        # Separar appointments marcados e não marcados
                        presencas_dia = sum(1 for apt in day_apts if apt['attended'] == 1)
                        faltas_dia = sum(1 for apt in day_apts if apt['attended'] == 0)
                        nao_marcados = sum(1 for apt in day_apts if apt['attended'] is None)
                        
                        # Determinar cor:
                        # AZUL = presença (attended=1)
                        # VERMELHO = falta (attended=0)
                        # VERDE = não marcado ainda (attended=NULL)
                        if presencas_dia > 0 and faltas_dia == 0 and nao_marcados == 0:
                            # Só presenças
                            cell_class = "calendar-cell-blue"
                            label = f"{day}<br><small>({presencas_dia}✓)</small>"
                        elif faltas_dia > 0 and presencas_dia == 0 and nao_marcados == 0:
                            # Só faltas
                            cell_class = "calendar-cell-red"
                            label = f"{day}<br><small>({faltas_dia}✗)</small>"
                        elif nao_marcados > 0 and presencas_dia == 0 and faltas_dia == 0:
                            # Só não marcados
                            cell_class = "calendar-cell-green"
                            label = f"{day}<br><small>({nao_marcados}?)</small>"
                        elif presencas_dia > 0 and faltas_dia > 0:
                            # Mix de presenças e faltas - predomina o maior
                            if presencas_dia > faltas_dia:
                                cell_class = "calendar-cell-blue"
                            else:
                                cell_class = "calendar-cell-red"
                            label = f"{day}<br><small>({presencas_dia}✓/{faltas_dia}✗)</small>"
                        elif nao_marcados > 0:
                            # Mix com não marcados - priorizar verde
                            cell_class = "calendar-cell-green"
                            if presencas_dia > 0 or faltas_dia > 0:
                                label = f"{day}<br><small>({presencas_dia}✓/{faltas_dia}✗/{nao_marcados}?)</small>"
                            else:
                                label = f"{day}<br><small>({nao_marcados}?)</small>"
                        else:
                            cell_class = "calendar-cell"
                            label = f"{day}"
                        
                        html += f'<td class="calendar-cell {cell_class}">{label}</td>'
                    else:
                        html += f'<td class="calendar-cell">{day}</td>'
            html += '</tr>'
        
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
        
        # Lista de appointments do mês para edição
        month_dates = [f"{year:04d}-{month:02d}-{day:02d}" for week in cal for day in week if day != 0]
        month_appointments = []
        
        for date_str in sorted(month_dates):
            if date_str in appointments_dict:
                for apt in appointments_dict[date_str]:
                    month_appointments.append((date_str, apt))
        
        if month_appointments:
            with st.expander(f"📝 Editar registros de {meses[month]}", expanded=False):
                for date_str, apt in month_appointments:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        # Atualizar ícone para diferenciar não marcado
                        if apt['attended'] == 1:
                            status_icon = "✅"
                        elif apt['attended'] == 0:
                            status_icon = "❌"
                        else:
                            status_icon = "⏳"  # Não marcado
                        st.write(f"{status_icon} {date_obj.strftime('%d/%m')} - **{apt['client_name']}** - {apt['time']}")
                    
                    with col2:
                        if st.button("✅ P", key=f"p_{apt['id']}_{month}", use_container_width=True):
                            if db.mark_attendance(apt['id'], attended=True):
                                st.success("✓")
                                st.rerun()
                    
                    with col3:
                        if st.button("❌ F", key=f"f_{apt['id']}_{month}", use_container_width=True):
                            if db.mark_attendance(apt['id'], attended=False):
                                st.success("✓")
                                st.rerun()
                    
                    with col4:
                        if st.button("🔄", key=f"c_{apt['id']}_{month}", use_container_width=True):
                            if db.mark_attendance(apt['id'], attended=None):
                                st.success("✓")
                                st.rerun()
    
    # Mostrar legenda de cores
    st.markdown("---")
    st.markdown("### 📖 Legenda")
    col_leg1, col_leg2, col_leg3 = st.columns(3)
    with col_leg1:
        st.markdown("🟦 **Azul** = Presença confirmada")
    with col_leg2:
        st.markdown("🟥 **Vermelho** = Falta registrada")
    with col_leg3:
        st.markdown("🟩 **Verde** = Agendado (não marcado)")
    
    st.markdown("---")
    
    # Criar layout com 12 meses (3 linhas x 4 colunas)
    # 3 meses atrás até 9 meses à frente = 12 meses total
    from dateutil.relativedelta import relativedelta
    
    # Calcular lista de meses para mostrar
    months_to_show = []
    start_month_date = today - relativedelta(months=3)
    
    for i in range(12):
        month_date = start_month_date + relativedelta(months=i)
        months_to_show.append((month_date.year, month_date.month))
    
    # Mostrar em 3 linhas de 4 meses cada
    for row in range(3):
        cols = st.columns(4)
        for col_idx in range(4):
            month_idx = row * 4 + col_idx
            if month_idx < len(months_to_show):
                year, month = months_to_show[month_idx]
                with cols[col_idx]:
                    create_month_calendar(year, month, appointments_by_date)
    
    if not marked_appointments:
        st.info("📭 Nenhum registro de presença/falta encontrado nos últimos 3 meses.")

if __name__ == "__main__":
    main()