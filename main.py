import streamlit as st
from utils.database import db
from datetime import datetime, date
import sqlite3
import bcrypt
import time
from zoneinfo import ZoneInfo

# Timezone de Brasília
BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

# Funções auxiliares para timezone de Brasília
def get_brasilia_now():
    """Retorna datetime atual no timezone de Brasília"""
    return datetime.now(BRASILIA_TZ)

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
    
    # Configurar página principal
    st.set_page_config(
        page_title="Agenda Pilates",
        page_icon="🧘‍♀️",
        layout="wide"
    )
    
    # CSS global para cabeçalho
    st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header com informações do usuário
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

def client_dashboard():
    """Dashboard do cliente - placeholder for now"""
    st.info("Área do cliente em desenvolvimento")
    if st.button("Voltar"):
        st.session_state.clear()
        st.rerun()

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
                        st.write(f"📞 Telefone: {phone}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✅ Marcar como lida", key=f"mark_read_{notif_id}"):
                            conn = sqlite3.connect("pilates.db")
                            cursor = conn.cursor()
                            cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
        else:
            st.info("Nenhuma notificação não lida")
        
        if st.button("❌ Fechar", key="close_notif_popup"):
            st.session_state['show_notifications_popup'] = False
            st.rerun()
        
        st.markdown("---")
    
    # Tabs para o master
    tabs = st.tabs(["� Agendamentos", "👥 Clientes", "🏋️ Equipamentos", "⏰ Horários", "💰 Financeiro", "� Análises"])
    
    with tabs[0]:
        appointments_tab()
    
    with tabs[1]:
        clients_tab()
    
    with tabs[2]:
        equipment_tab()
    
    with tabs[3]:
        schedules_overview_tab()
    
    with tabs[4]:
        financial_tab()
    
    with tabs[5]:
        attendance_history_tab()

def appointments_tab():
    """Aba de gerenciamento de agendamentos com seletor de data"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    import sqlite3
    
    # Preparar lista de equipamentos para os selectboxes
    equipment_list = db.get_equipment() if hasattr(db, 'get_equipment') else []
    equipment_options = ['N/A'] + [e['name'] for e in equipment_list] if equipment_list else ['N/A']
    
    # Seletor de data simples
    st.markdown("### 📋 Grade de Horários Diária")
    selected_date = st.date_input(
        "📅 Selecione o Dia:",
        value=get_brasilia_today(),
        key="selected_date_input"
    )
    
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    day_name = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 
                'Sexta-feira', 'Sábado', 'Domingo'][selected_date.weekday()]
    
    st.info(f"📅 {day_name} - {selected_date.strftime('%d/%m/%Y')}")

    # Buscar todos os appointments do dia selecionado
    conn = sqlite3.connect("pilates.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.client_id, a.time, a.attended, a.equipamento, a.observacao,
               u.name as client_name
        FROM appointments a
        JOIN users u ON a.client_id = u.id
        WHERE a.date = ?
        ORDER BY a.time
    ''', (selected_date_str,))
    
    appointments_today = cursor.fetchall()
    conn.close()
    
    # Organizar por horário
    appointments_by_hour = defaultdict(list)
    for apt in appointments_today:
        apt_id, client_id, time_str, attended, equipamento, observacao, client_name = apt
        hour = time_str.split(':')[0]
        appointments_by_hour[hour].append({
            'id': apt_id,
            'client_id': client_id,
            'client_name': client_name,
            'time': time_str,
            'attended': attended,
            'equipamento': equipamento or 'N/A',
            'observacao': observacao or ''
        })
    
    # Exibir grade de 6:00 às 20:00
    st.markdown("---")
    hours = [f"{h:02d}:00" for h in range(6, 21)]
    
    for hour in hours:
        hour_key = hour.split(':')[0]
        clients_in_hour = appointments_by_hour.get(hour_key, [])
        
        if clients_in_hour:
            st.markdown(f"### 🕐 {hour}")
            
            for apt in clients_in_hour:
                col_name, col_equip, col_pf, col_actions = st.columns([2, 1.5, 1, 0.5])
                
                with col_name:
                    # Nome clicável para editar
                    if st.button(
                        f"👤 {apt['client_name']}",
                        key=f"btn_name_{apt['id']}",
                        help="Clique para editar horário/equipamento"
                    ):
                        st.session_state.editing_appointment_id = apt['id']
                        st.session_state.show_edit_appointment_form = True
                
                with col_equip:
                    # Selectbox de equipamento com salvamento automático
                    current_equip = apt['equipamento'] if apt['equipamento'] in equipment_options else 'N/A'
                    current_idx = equipment_options.index(current_equip)
                    
                    new_equipment = st.selectbox(
                        "🏋️",
                        options=equipment_options,
                        index=current_idx,
                        key=f"equip_select_{apt['id']}",
                        label_visibility="collapsed"
                    )
                    
                    # Se mudou, salvar automaticamente
                    if new_equipment != apt['equipamento']:
                        conn = sqlite3.connect("pilates.db")
                        cursor = conn.cursor()
                        cursor.execute(
                            'UPDATE appointments SET equipamento = ? WHERE id = ?',
                            (new_equipment, apt['id'])
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()
            
            with col_pf:
                # Checkboxes P e F em linha
                col_p, col_f = st.columns(2)
                with col_p:
                    p_checked = apt['attended'] == 1
                    if st.checkbox(
                        "P",
                        value=p_checked,
                        key=f"p_{apt['id']}",
                        help="Presença"
                    ):
                        if not p_checked:
                            # Marcar presença
                            db.mark_attendance(apt['id'], True, apt['observacao'], apt['equipamento'])
                            st.rerun()
                
                with col_f:
                    f_checked = apt['attended'] == 0
                    if st.checkbox(
                        "F",
                        value=f_checked,
                        key=f"f_{apt['id']}",
                        help="Falta"
                    ):
                        if not f_checked:
                            # Marcar falta
                            db.mark_attendance(apt['id'], False, apt['observacao'], apt['equipamento'])
                            st.rerun()
            
            with col_actions:
                # Indicador visual do status
                if apt['attended'] == 1:
                    st.success("✅")
                elif apt['attended'] == 0:
                    st.error("❌")
                else:
                    st.warning("⏳")
            
            st.markdown("---")
        else:
            # Exibir horário vazio
            st.markdown(f"**🕐 {hour}** - _Sem agendamentos_")
    
    # Formulário de edição (modal)
    if st.session_state.get('show_edit_appointment_form', False):
        st.markdown("---")
        st.markdown("### ✏️ Editar Agendamento")
        
        editing_apt_id = st.session_state.get('editing_appointment_id')
        
        # Buscar dados do appointment
        conn = sqlite3.connect("pilates.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.client_id, a.date, a.time, a.equipamento, a.observacao,
                   u.name as client_name
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            WHERE a.id = ?
        ''', (editing_apt_id,))
        
        apt_data = cursor.fetchone()
        conn.close()
        
        if apt_data:
            apt_id, client_id, apt_date, apt_time, apt_equip, apt_obs, client_name = apt_data

            st.info(f"**Cliente:** {client_name}")

            col_date, col_time = st.columns(2)
            with col_date:
                new_date = st.date_input(
                    "Nova Data:",
                    value=datetime.strptime(apt_date, '%Y-%m-%d').date(),
                    key="edit_apt_date"
                )

            with col_time:
                time_options = [f"{h:02d}:00" for h in range(6, 21)]
                current_time_idx = time_options.index(apt_time) if apt_time in time_options else 0
                new_time = st.selectbox(
                    "Novo Horário:",
                    options=time_options,
                    index=current_time_idx,
                    key="edit_apt_time"
                )

            # Seletor de equipamento
            equipment_list = db.get_equipment() if hasattr(db, 'get_equipment') else []
            equipment_options = [e['name'] for e in equipment_list] if equipment_list else []

            if equipment_options:
                current_equip_idx = equipment_options.index(apt_equip) if apt_equip in equipment_options else 0
                new_equipment = st.selectbox(
                    "Equipamento:",
                    options=equipment_options,
                    index=current_equip_idx,
                    key="edit_apt_equipment"
                )
            else:
                new_equipment = apt_equip

            # Observação
            new_obs = st.text_area(
                "Observação:",
                value=apt_obs or '',
                height=80,
                key="edit_apt_obs"
            )

            col_save, col_cancel = st.columns(2)

            with col_save:
                if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                    # Verificar mudanças
                    mudou_data = new_date.strftime('%Y-%m-%d') != apt_date
                    mudou_horario = new_time != apt_time
                    mudou_equip = new_equipment != apt_equip
                    mudou_obs = new_obs != (apt_obs or '')

                    if mudou_data or mudou_horario:
                        # Atualizar data e horário
                        conn = sqlite3.connect("pilates.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE appointments
                            SET date = ?, time = ?, equipamento = ?, observacao = ?
                            WHERE id = ?
                        ''', (new_date.strftime('%Y-%m-%d'), new_time, new_equipment, new_obs, apt_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Horário atualizado!")
                    elif mudou_equip or mudou_obs:
                        # Atualizar apenas equipamento/observação
                        conn = sqlite3.connect("pilates.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE appointments
                            SET equipamento = ?, observacao = ?
                            WHERE id = ?
                        ''', (new_equipment, new_obs, apt_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Equipamento/observação atualizado!")
                    else:
                        st.info("ℹ️ Nenhuma alteração detectada")

                    time.sleep(0.5)
                    st.session_state.show_edit_appointment_form = False
                    st.rerun()

            with col_cancel:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_edit_appointment_form = False
                    st.rerun()
    
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
    editing_date = st.session_state.get('editing_date')
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
                            # Sempre permitir edição do horário, independente do checkbox
                            try:
                                time_index = hours.index(horario_atual)
                            except:
                                time_index = 9
                            
                            horario = st.selectbox(
                                "Horário:",
                                hours,
                                index=time_index,
                                key=f"time_edit_{dia_key}_{client['id']}",
                                label_visibility="collapsed",
                                help=f"Horário para {dia_label}" if not dia_selecionado else None
                            )
                            
                            # Sempre salvar o horário no dicionário, mas só usar se dia estiver selecionado
                            if dia_selecionado:
                                dias_horarios_edit[dia_num] = horario
                    
                    # Status do contrato
                    contrato_ativo_edit = st.checkbox(
                        "✅ Contrato Ativo",
                        value=bool(dados_contrato_atual['ativo']),
                        key=f"contrato_ativo_edit_{client['id']}",
                        help="Desmarque para desativar o contrato sem excluir o cliente"
                    )
                    
                    st.markdown("---")
                    st.subheader("💰 Valor Mensal")
                    
                    # Buscar valor mensal do cliente nas contas mais recentes
                    contas_cliente = db.get_contas_receber(client_id=client['id'])
                    valor_atual = 0.0
                    
                    if contas_cliente:
                        # Pegar o valor da conta mais recente para mostrar como valor atual
                        conta_recente = max(contas_cliente, key=lambda x: x['data_vencimento'])
                        valor_atual = conta_recente['valor']
                        st.info(f"💵 Valor mensal atual: **R$ {valor_atual:.2f}**")
                    else:
                        st.info("💵 Nenhum valor mensal definido ainda")
                    
                    st.markdown("---")
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
                    
                        # Exibir bloco de presença/equipamento/observação apenas se appointment e from_time existirem
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
                    if equip['description']:
                        st.write(f"**Descrição:** {equip['description']}")
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
            # Buscar clientes para o filtro
            clients = db.get_clients()
            client_filter_options = ["Todos"] + [f"{c['name']} - {c['phone']}" for c in clients]
            
            # Usar filtro automático se veio da seção de clientes
            default_filter = st.session_state.get('filter_client_financeiro', '')
            default_index = 0  # "Todos" por padrão
            if default_filter:
                # Procurar o cliente correspondente
                for i, option in enumerate(client_filter_options):
                    if default_filter.lower() in option.lower():
                        default_index = i
                        break
            
            selected_client_filter = st.selectbox("Filtrar por Cliente:", 
                client_filter_options, index=default_index)
            
            # Limpar filtro automático após usar
            if 'filter_client_financeiro' in st.session_state:
                del st.session_state.filter_client_financeiro
        
        # Aplicar filtros
        contas_filtradas = contas
        if filter_status != "Todos":
            contas_filtradas = [c for c in contas_filtradas 
                              if c['status'].lower() == filter_status.lower()]
        if selected_client_filter != "Todos":
            # Extrair o nome do cliente da opção selecionada (antes do " - ")
            client_name = selected_client_filter.split(" - ")[0]
            contas_filtradas = [c for c in contas_filtradas 
                              if client_name.lower() in c['client_name'].lower()]
        
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
