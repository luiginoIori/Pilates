import sqlite3
import bcrypt
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Optional, Union
from zoneinfo import ZoneInfo

# Timezone de Brasília
BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

def get_brasilia_now():
    """Retorna datetime atual no timezone de Brasília"""
    return datetime.now(BRASILIA_TZ)

def get_brasilia_today():
    """Retorna date de hoje no timezone de Brasília"""
    return get_brasilia_now().date()

class Database:
    def __init__(self, db_path: str = "pilates.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'client',
                medical_history TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de equipamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sequências de equipamentos (templates globais)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                equipment_order TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sequências personalizadas por cliente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                equipment_order TEXT NOT NULL,
                current_position INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de horários fixos por cliente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                time TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users (id),
                UNIQUE(client_id, day_of_week, time)
            )
        ''')
        
        # Tabela de agendamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                client_sequence_id INTEGER,
                last_equipment_used TEXT,
                status TEXT DEFAULT 'scheduled',
                delay_notification TEXT,
                absence_notification TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users (id),
                FOREIGN KEY (client_sequence_id) REFERENCES client_sequences (id)
            )
        ''')
        
        # Tabela de notificações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de contas a receber
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contas_receber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                tipo_plano TEXT NOT NULL,
                valor REAL NOT NULL,
                quantidade INTEGER,
                data_vencimento TEXT NOT NULL,
                data_pagamento TEXT,
                status TEXT DEFAULT 'pendente',
                observacoes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de contas a pagar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contas_pagar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_debito TEXT NOT NULL,
                tipo_debito TEXT NOT NULL,
                valor_total REAL NOT NULL,
                quantidade INTEGER DEFAULT 1,
                tipo_parcelamento TEXT DEFAULT 'mensal',
                status TEXT DEFAULT 'pendente',
                observacoes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de parcelas de contas a pagar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parcelas_pagar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conta_pagar_id INTEGER NOT NULL,
                numero_parcela INTEGER NOT NULL,
                data_vencimento TEXT NOT NULL,
                valor REAL NOT NULL,
                data_pagamento TEXT,
                status TEXT DEFAULT 'pendente',
                FOREIGN KEY (conta_pagar_id) REFERENCES contas_pagar (id)
            )
        ''')
        
        conn.commit()
        
        # Migrar banco existente se necessário
        self.migrate_database()
        
        # Criar usuário master padrão se não existir
        self.create_default_master()
        
        # Criar equipamentos padrão se não existirem
        self.create_default_equipment()
        
        conn.close()
    
    def migrate_database(self):
        """Migra banco de dados existente para nova estrutura"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verificar se coluna client_sequence_id existe
            cursor.execute("PRAGMA table_info(appointments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'client_sequence_id' not in columns:
                # Adicionar nova coluna se não existir
                cursor.execute('ALTER TABLE appointments ADD COLUMN client_sequence_id INTEGER')
                
                # Migrar dados da coluna antiga se existir
                if 'equipment_sequence_id' in columns:
                    cursor.execute('''
                        UPDATE appointments 
                        SET client_sequence_id = equipment_sequence_id 
                        WHERE equipment_sequence_id IS NOT NULL
                    ''')
                
                conn.commit()
                print("Banco de dados migrado com sucesso!")
            
            # Verificar se coluna current_position existe na tabela client_sequences
            cursor.execute("PRAGMA table_info(client_sequences)")
            seq_columns = [col[1] for col in cursor.fetchall()]
            
            if 'current_position' not in seq_columns:
                cursor.execute('ALTER TABLE client_sequences ADD COLUMN current_position INTEGER DEFAULT 0')
                conn.commit()
                print("Coluna current_position adicionada!")
            
            # Verificar se coluna is_recurring existe na tabela appointments
            if 'is_recurring' not in columns:
                cursor.execute('ALTER TABLE appointments ADD COLUMN is_recurring INTEGER DEFAULT 0')
                conn.commit()
                print("Coluna is_recurring adicionada!")
            
            # Verificar se coluna equipment_id existe na tabela client_schedule
            cursor.execute("PRAGMA table_info(client_schedule)")
            schedule_columns = [col[1] for col in cursor.fetchall()]
            
            if 'equipment_id' not in schedule_columns:
                cursor.execute('ALTER TABLE client_schedule ADD COLUMN equipment_id INTEGER')
                conn.commit()
                print("Coluna equipment_id adicionada na tabela client_schedule!")
            
            # Verificar se coluna schedule_type existe na tabela client_schedule
            if 'schedule_type' not in schedule_columns:
                cursor.execute("ALTER TABLE client_schedule ADD COLUMN schedule_type TEXT DEFAULT 'Fixo'")
                conn.commit()
                print("Coluna schedule_type adicionada na tabela client_schedule!")
            
            # Verificar se coluna sessions_count existe na tabela client_schedule
            if 'sessions_count' not in schedule_columns:
                cursor.execute('ALTER TABLE client_schedule ADD COLUMN sessions_count INTEGER DEFAULT 0')
                conn.commit()
                print("Coluna sessions_count adicionada na tabela client_schedule!")
            
            # Verificar e adicionar coluna attended na tabela appointments
            cursor.execute("PRAGMA table_info(appointments)")
            appointments_columns = [col[1] for col in cursor.fetchall()]
            
            if 'attended' not in appointments_columns:
                cursor.execute('ALTER TABLE appointments ADD COLUMN attended INTEGER DEFAULT NULL')
                conn.commit()
                print("Coluna attended adicionada na tabela appointments!")
            
            # Verificar e adicionar coluna recorrente na tabela contas_pagar
            cursor.execute("PRAGMA table_info(contas_pagar)")
            contas_pagar_columns = [col[1] for col in cursor.fetchall()]
            
            if 'recorrente' not in contas_pagar_columns:
                cursor.execute('ALTER TABLE contas_pagar ADD COLUMN recorrente INTEGER DEFAULT 0')
                conn.commit()
                print("Coluna recorrente adicionada na tabela contas_pagar!")

            # Backfill: atribuir equipamento onde estiver NULL para horários ativos
            try:
                cursor.execute('''
                    SELECT id, client_id, day_of_week, time
                    FROM client_schedule
                    WHERE is_active = 1 AND (equipment_id IS NULL OR equipment_id = '')
                ''')
                rows = cursor.fetchall()
                for sched_id, client_id, day_of_week, time in rows:
                    eq_id = self.assign_equipment_to_client(client_id, day_of_week, time)
                    if eq_id:
                        cursor.execute('UPDATE client_schedule SET equipment_id = ? WHERE id = ?', (eq_id, sched_id))
                conn.commit()
            except Exception as e:
                print(f"Backfill equipment_id falhou: {e}")
            
        except sqlite3.OperationalError as e:
            # Tabela pode não existir ainda, isso é normal
            print(f"⚠️ Migração: {e}")
        
        conn.close()
        
    def create_default_master(self):
        """Cria usuário master padrão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se já existe um usuário master
        cursor.execute("SELECT id FROM users WHERE type = 'master'")
        if cursor.fetchone() is None:
            master_password = bcrypt.hashpw('master123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (name, phone, email, password, type) 
                VALUES (?, ?, ?, ?, ?)
            ''', ('Master Admin', '(11) 99999-9999', 'master@pilates.com', master_password, 'master'))
            conn.commit()
            
        conn.close()
    
    def create_default_equipment(self):
        """Cria equipamentos padrão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Lista de equipamentos padrão
        default_equipment = [
            ('Cavalo', 'Equipamento de Pilates'),
            ('Cadilak', 'Equipamento de Pilates'),
            ('Chase', 'Equipamento de Pilates'),
            ('Solo', 'Exercícios no solo')
        ]
        
        # Verificar se já existem equipamentos
        cursor.execute("SELECT COUNT(*) FROM equipment")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Inserir equipamentos padrão
            cursor.executemany('''
                INSERT INTO equipment (name, description) 
                VALUES (?, ?)
            ''', default_equipment)
            conn.commit()
            print("✅ Equipamentos padrão criados!")
            
        conn.close()

    # MÉTODOS DE USUÁRIO
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Autentica usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            stored_password = user[4]
            # Se a senha armazenada é bytes, use diretamente; se é string, faça encode
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return {
                    'id': user[0],
                    'name': user[1],
                    'phone': user[2],
                    'email': user[3],
                    'type': user[5],
                    'medical_history': user[6]
                }
        return None
    
    def create_client(self, name: str, phone: str, email: str, password: str, medical_history: str = "") -> bool:
        """Cria novo cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (name, phone, email, password, type, medical_history) 
                VALUES (?, ?, ?, ?, 'client', ?)
            ''', (name, phone, email, hashed_password, medical_history))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_clients(self) -> List[Dict]:
        """Retorna lista de clientes com todos os campos incluindo os novos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, phone, email, password, type, medical_history, created_at,
                   data_inicio_contrato, tipo_contrato, sessoes_contratadas, 
                   sessoes_utilizadas, dias_semana, contrato_ativo
            FROM users 
            WHERE type = "client" 
            ORDER BY name
        ''')
        clients = cursor.fetchall()
        
        conn.close()
        
        return [{
            'id': client[0],
            'name': client[1],
            'phone': client[2],
            'email': client[3],
            'medical_history': client[6] or '',
            'created_at': client[7],
            'data_inicio_contrato': client[8],
            'tipo_contrato': client[9],
            'sessoes_contratadas': client[10] or 0,
            'sessoes_utilizadas': client[11] or 0,
            'dias_semana': client[12],
            'contrato_ativo': client[13]
        } for client in clients]
    
    def update_client(self, client_id: int, name: str, phone: str, email: str, medical_history: str = "") -> bool:
        """Atualiza dados do cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET name = ?, phone = ?, email = ?, medical_history = ? 
                WHERE id = ? AND type = 'client'
            ''', (name, phone, email, medical_history, client_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def delete_client(self, client_id: int) -> bool:
        """Exclui cliente e todos os dados relacionados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Excluir agendamentos do cliente
            cursor.execute('DELETE FROM appointments WHERE client_id = ?', (client_id,))
            
            # Excluir horários fixos do cliente
            cursor.execute('DELETE FROM client_schedule WHERE client_id = ?', (client_id,))
            
            # Excluir sequências personalizadas do cliente
            cursor.execute('DELETE FROM client_sequences WHERE client_id = ?', (client_id,))
            
            # Excluir o cliente
            cursor.execute('DELETE FROM users WHERE id = ? AND type = "client"', (client_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir cliente: {e}")
            return False

    # MÉTODOS DE EQUIPAMENTOS
    def create_equipment(self, name: str, description: str = "") -> bool:
        """Cria novo equipamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO equipment (name, description) VALUES (?, ?)', (name, description))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_equipment(self) -> List[Dict]:
        """Retorna lista de equipamentos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM equipment ORDER BY name')
        equipment = cursor.fetchall()
        
        conn.close()
        
        return [{
            'id': equip[0],
            'name': equip[1],
            'description': equip[2] or '',
            'created_at': equip[3]
        } for equip in equipment]
    
    def update_equipment(self, equipment_id: int, name: str, description: str = "") -> bool:
        """Atualiza equipamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE equipment SET name = ?, description = ? WHERE id = ?', 
                         (name, description, equipment_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def delete_equipment(self, equipment_id: int) -> bool:
        """Exclui equipamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM equipment WHERE id = ?', (equipment_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    # MÉTODOS DE SEQUÊNCIAS DE EQUIPAMENTOS (TEMPLATES GLOBAIS)
    def create_equipment_sequence(self, name: str, day_of_week: int, equipment_order: List[int]) -> bool:
        """Cria sequência de equipamentos (template global)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            equipment_order_json = json.dumps(equipment_order)
            
            cursor.execute('''
                INSERT INTO equipment_sequences (name, day_of_week, equipment_order) 
                VALUES (?, ?, ?)
            ''', (name, day_of_week, equipment_order_json))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_equipment_sequences(self, day_of_week: int = None) -> List[Dict]:
        """Retorna sequências de equipamentos (templates globais)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if day_of_week:
            cursor.execute('SELECT * FROM equipment_sequences WHERE day_of_week = ? ORDER BY name', (day_of_week,))
        else:
            cursor.execute('SELECT * FROM equipment_sequences ORDER BY day_of_week, name')
        
        sequences = cursor.fetchall()
        conn.close()
        
        import json
        result = []
        for seq in sequences:
            equipment_order = json.loads(seq[3])
            result.append({
                'id': seq[0],
                'name': seq[1],
                'day_of_week': seq[2],
                'equipment_order': equipment_order,
                'created_at': seq[4]
            })
        
        return result
    
    def delete_equipment_sequence(self, sequence_id: int) -> bool:
        """Exclui sequência de equipamentos (template global)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM equipment_sequences WHERE id = ?', (sequence_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    # MÉTODOS DE SEQUÊNCIAS PERSONALIZADAS POR CLIENTE
    def create_client_sequence(self, client_id: int, name: str, day_of_week: int, equipment_order: List[int]) -> bool:
        """Cria sequência personalizada para cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            equipment_order_json = json.dumps(equipment_order)
            
            cursor.execute('''
                INSERT INTO client_sequences (client_id, name, day_of_week, equipment_order) 
                VALUES (?, ?, ?, ?)
            ''', (client_id, name, day_of_week, equipment_order_json))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_client_sequences(self, client_id: int, day_of_week: int = None) -> List[Dict]:
        """Retorna sequências personalizadas do cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM client_sequences WHERE client_id = ? AND is_active = 1'
        params = [client_id]
        
        if day_of_week:
            query += ' AND day_of_week = ?'
            params.append(day_of_week)
        
        query += ' ORDER BY day_of_week, name'
        
        cursor.execute(query, params)
        sequences = cursor.fetchall()
        conn.close()
        
        import json
        result = []
        for seq in sequences:
            equipment_order = json.loads(seq[4])
            # Verificar se current_position existe (compatibilidade com versões antigas)
            current_position = seq[5] if len(seq) > 6 else 0
            is_active = seq[6] if len(seq) > 7 else seq[5]
            created_at = seq[7] if len(seq) > 8 else seq[6]
            
            result.append({
                'id': seq[0],
                'client_id': seq[1],
                'name': seq[2],
                'day_of_week': seq[3],
                'equipment_order': equipment_order,
                'current_position': current_position,
                'is_active': is_active,
                'created_at': created_at
            })
        
        return result
    
    def update_client_sequence(self, sequence_id: int, name: str, day_of_week: int, equipment_order: List[int]) -> bool:
        """Atualiza sequência personalizada do cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            equipment_order_json = json.dumps(equipment_order)
            
            cursor.execute('''
                UPDATE client_sequences 
                SET name = ?, day_of_week = ?, equipment_order = ? 
                WHERE id = ?
            ''', (name, day_of_week, equipment_order_json, sequence_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def delete_client_sequence(self, sequence_id: int) -> bool:
        """Remove sequência personalizada do cliente (soft delete)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE client_sequences SET is_active = 0 WHERE id = ?', (sequence_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def copy_template_to_client(self, client_id: int, template_id: int, custom_name: str = None) -> bool:
        """Copia template global para sequência personalizada do cliente"""
        try:
            # Buscar template
            template = self.get_equipment_sequences()
            template_data = next((t for t in template if t['id'] == template_id), None)
            
            if not template_data:
                return False
            
            name = custom_name or f"{template_data['name']} (Personalizada)"
            
            return self.create_client_sequence(
                client_id=client_id,
                name=name,
                day_of_week=template_data['day_of_week'],
                equipment_order=template_data['equipment_order']
            )
        except:
            return False
    
    def get_next_equipment_for_client(self, client_id: int, day_of_week: int) -> Dict:
        """Retorna o próximo equipamento na rotação para o cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar sequência do cliente para este dia
            cursor.execute('''
                SELECT id, equipment_order, current_position 
                FROM client_sequences 
                WHERE client_id = ? AND day_of_week = ? AND is_active = 1
                LIMIT 1
            ''', (client_id, day_of_week))
            
            sequence = cursor.fetchone()
            
            if not sequence:
                conn.close()
                return {'equipment_id': None, 'equipment_name': 'Nenhuma sequência configurada'}
            
            sequence_id, equipment_order_json, current_position = sequence
            
            import json
            equipment_order = json.loads(equipment_order_json)
            
            if not equipment_order:
                conn.close()
                return {'equipment_id': None, 'equipment_name': 'Sequência vazia'}
            
            # Obter equipamento atual na rotação
            current_equipment_id = equipment_order[current_position % len(equipment_order)]
            
            # Buscar nome do equipamento
            cursor.execute('SELECT name FROM equipment WHERE id = ?', (current_equipment_id,))
            equipment_result = cursor.fetchone()
            equipment_name = equipment_result[0] if equipment_result else 'Equipamento não encontrado'
            
            conn.close()
            
            return {
                'sequence_id': sequence_id,
                'equipment_id': current_equipment_id,
                'equipment_name': equipment_name,
                'position': current_position,
                'total_equipment': len(equipment_order)
            }
            
        except Exception as e:
            return {'equipment_id': None, 'equipment_name': f'Erro: {str(e)}'}
    
    def advance_equipment_rotation(self, client_id: int, day_of_week: int) -> bool:
        """Avança para o próximo equipamento na rotação"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar sequência atual
            cursor.execute('''
                SELECT id, equipment_order, current_position 
                FROM client_sequences 
                WHERE client_id = ? AND day_of_week = ? AND is_active = 1
                LIMIT 1
            ''', (client_id, day_of_week))
            
            sequence = cursor.fetchone()
            
            if not sequence:
                conn.close()
                return False
            
            sequence_id, equipment_order_json, current_position = sequence
            
            import json
            equipment_order = json.loads(equipment_order_json)
            
            if not equipment_order:
                conn.close()
                return False
            
            # Avançar posição (ciclo)
            new_position = (current_position + 1) % len(equipment_order)
            
            # Atualizar posição no banco
            cursor.execute('''
                UPDATE client_sequences 
                SET current_position = ? 
                WHERE id = ?
            ''', (new_position, sequence_id))
            
            conn.commit()
            conn.close()
            return True
            
        except:
            return False
    
    def set_equipment_position(self, client_id: int, day_of_week: int, equipment_id: int) -> bool:
        """Define equipamento específico como atual e reinicia ciclo a partir dele"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar sequência atual
            cursor.execute('''
                SELECT id, equipment_order 
                FROM client_sequences 
                WHERE client_id = ? AND day_of_week = ? AND is_active = 1
                LIMIT 1
            ''', (client_id, day_of_week))
            
            sequence = cursor.fetchone()
            
            if not sequence:
                conn.close()
                return False
            
            sequence_id, equipment_order_json = sequence
            
            import json
            equipment_order = json.loads(equipment_order_json)
            
            # Encontrar posição do equipamento especificado
            try:
                new_position = equipment_order.index(equipment_id)
            except ValueError:
                # Equipamento não está na sequência
                conn.close()
                return False
            
            # Atualizar posição no banco
            cursor.execute('''
                UPDATE client_sequences 
                SET current_position = ? 
                WHERE id = ?
            ''', (new_position, sequence_id))
            
            conn.commit()
            conn.close()
            return True
            
        except:
            return False

    # MÉTODOS DE HORÁRIOS FIXOS POR CLIENTE
    def create_client_schedule(self, client_id: int, day_of_week: int, time: str, schedule_type: str = "Fixo", sessions_count: int = 0) -> bool:
        """Adiciona horário fixo para cliente com atribuição automática de equipamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se já existe um horário para este cliente neste dia/hora (ativo ou inativo)
            cursor.execute('''
                SELECT id, is_active FROM client_schedule 
                WHERE client_id = ? AND day_of_week = ? AND time = ?
            ''', (client_id, day_of_week, time))
            
            existing = cursor.fetchone()
            
            if existing:
                schedule_id, is_active = existing
                if is_active == 1:
                    # Já existe e está ativo - atualizar tipo e sessões
                    cursor.execute('''
                        UPDATE client_schedule 
                        SET schedule_type = ?, sessions_count = ?
                        WHERE id = ?
                    ''', (schedule_type, sessions_count, schedule_id))
                    conn.commit()
                    conn.close()
                    return True
                else:
                    # Existe mas está inativo - REATIVAR!
                    cursor.execute('''
                        UPDATE client_schedule 
                        SET is_active = 1, schedule_type = ?, sessions_count = ?
                        WHERE id = ?
                    ''', (schedule_type, sessions_count, schedule_id))
                    conn.commit()
                    conn.close()
                    return True
            
            # Não existe - criar novo
            # Atribuir equipamento automaticamente
            equipment_id = self.assign_equipment_to_client(client_id, day_of_week, time)
            
            cursor.execute('''
                INSERT INTO client_schedule (client_id, day_of_week, time, equipment_id, is_active, schedule_type, sessions_count) 
                VALUES (?, ?, ?, ?, 1, ?, ?)
            ''', (client_id, day_of_week, time, equipment_id, schedule_type, sessions_count))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError as e:
            # Horário já existe para este cliente
            print(f"IntegrityError ao criar horário: {e}")
            return False
        except Exception as e:
            print(f"Erro ao criar horário: {e}")
            return False
    
    def get_client_schedule(self, client_id: int) -> List[Dict]:
        """Retorna horários fixos do cliente com informação de equipamento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cs.*, e.name as equipment_name
            FROM client_schedule cs
            LEFT JOIN equipment e ON cs.equipment_id = e.id
            WHERE cs.client_id = ? AND cs.is_active = 1 
            ORDER BY cs.day_of_week, cs.time
        ''', (client_id,))
        
        schedules = cursor.fetchall()
        conn.close()
        
        return [{
            'id': sched[0],
            'client_id': sched[1],
            'day_of_week': sched[2],
            'time': sched[3],
            'is_active': sched[4],
            'created_at': sched[5],
            'equipment_id': sched[6],
            'equipment_name': sched[7] if len(sched) > 7 else None
        } for sched in schedules]
    
    def update_client_schedule(self, client_id: int, schedules: List[Dict]) -> bool:
        """Atualiza todos os horários fixos do cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remover horários existentes (soft delete)
            cursor.execute('UPDATE client_schedule SET is_active = 0 WHERE client_id = ?', (client_id,))
            
            # Adicionar novos horários
            for schedule in schedules:
                cursor.execute('''
                    INSERT INTO client_schedule (client_id, day_of_week, time) 
                    VALUES (?, ?, ?)
                ''', (client_id, schedule['day_of_week'], schedule['time']))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def delete_client_schedule(self, schedule_id: int) -> bool:
        """Remove horário fixo específico (soft delete)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE client_schedule SET is_active = 0 WHERE id = ?', (schedule_id,))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def assign_equipment_to_client(self, client_id: int, day_of_week: int, time: str) -> Optional[int]:
        """
        Atribui automaticamente um equipamento ao cliente baseado em rotação e conflito de horário.
        - Rotação: equipamentos alternam entre os dias/horários do mesmo cliente, voltando ao 1º quando acabar a lista.
        - Conflito: no mesmo dia/horário, clientes diferentes não podem usar o mesmo equipamento.
        Retorna o ID do equipamento atribuído.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obter todos os equipamentos disponíveis
            cursor.execute('SELECT id FROM equipment ORDER BY id')
            all_equipment = [row[0] for row in cursor.fetchall()]
            
            if not all_equipment:
                conn.close()
                return None
            
            total_equipment = len(all_equipment)

            # Calcular offset de rotação baseado na quantidade de horários já configurados para o cliente
            cursor.execute('''
                SELECT COUNT(*) FROM client_schedule
                WHERE client_id = ? AND is_active = 1
            ''', (client_id,))
            client_schedule_count = cursor.fetchone()[0]

            rotation_offset = client_schedule_count % total_equipment if total_equipment > 0 else 0

            # Gerar ordem de preferência rotacionada para este cliente
            rotated_order = all_equipment[rotation_offset:] + all_equipment[:rotation_offset]

            # Obter equipamentos já em uso nesse dia e horário por outros clientes
            cursor.execute('''
                SELECT DISTINCT cs.equipment_id
                FROM client_schedule cs
                WHERE cs.day_of_week = ? 
                AND cs.time = ?
                AND cs.client_id != ?
                AND cs.is_active = 1
                AND cs.equipment_id IS NOT NULL
            ''', (day_of_week, time, client_id))
            
            used_equipment = [row[0] for row in cursor.fetchall()]
            
            # Escolher o primeiro equipamento da ordem rotacionada que não esteja em uso
            selected_equipment = None
            for eq in rotated_order:
                if eq not in used_equipment:
                    selected_equipment = eq
                    break

            # Se todos estão em uso neste slot, escolher o primeiro da ordem rotacionada
            if selected_equipment is None:
                selected_equipment = rotated_order[0]
            
            conn.close()
            return selected_equipment
            
        except Exception as e:
            print(f"Erro ao atribuir equipamento: {e}")
            conn.close()
            return None
    
    def get_all_client_schedules(self) -> List[Dict]:
        """Retorna todos os horários fixos de todos os clientes com equipamentos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cs.*, u.name as client_name, u.phone as client_phone, e.name as equipment_name
            FROM client_schedule cs
            JOIN users u ON cs.client_id = u.id
            LEFT JOIN equipment e ON cs.equipment_id = e.id
            WHERE cs.is_active = 1
            ORDER BY cs.day_of_week, cs.time, u.name
        ''')
        
        schedules = cursor.fetchall()
        conn.close()
        
        # Estrutura: id(0), client_id(1), day_of_week(2), time(3), is_active(4), created_at(5),
        # equipment_id(6), schedule_type(7), sessions_count(8), 
        # JOINs: client_name(9), client_phone(10), equipment_name(11)
        return [{
            'id': sched[0],
            'client_id': sched[1],
            'day_of_week': sched[2],
            'time': sched[3],
            'is_active': sched[4],
            'created_at': sched[5],
            'equipment_id': sched[6] if len(sched) > 6 else None,
            'schedule_type': sched[7] if len(sched) > 7 else 'Fixo',
            'sessions_count': sched[8] if len(sched) > 8 else 0,
            'client_name': sched[9] if len(sched) > 9 else None,
            'client_phone': sched[10] if len(sched) > 10 else None,
            'equipment_name': sched[11] if len(sched) > 11 else None
        } for sched in schedules]
    
    def rotate_equipment_daily(self) -> Dict:
        """
        Rotaciona equipamentos de um dia para outro, mantendo unicidade no mesmo horário.
        Para cada horário, os clientes trocam de equipamento em rotação circular.
        
        Exemplo:
        Dia 1: A=Cavalo, B=Cadilak, C=Chase
        Dia 2: A=Cadilak, B=Chase, C=Cavalo (rotação)
        Dia 3: A=Chase, B=Cavalo, C=Cadilak (rotação)
        
        Retorna estatísticas da rotação.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        changes_made = 0
        
        try:
            # Para cada dia da semana
            for target_day in range(1, 6):  # 1=Segunda até 5=Sexta
                # Buscar todos os horários distintos neste dia
                cursor.execute('''
                    SELECT DISTINCT time
                    FROM client_schedule
                    WHERE day_of_week = ? AND is_active = 1
                    ORDER BY time
                ''', (target_day,))
                
                times = [row[0] for row in cursor.fetchall()]
                
                for time in times:
                    # Buscar todos os clientes neste horário
                    cursor.execute('''
                        SELECT cs.id, cs.client_id, cs.equipment_id, u.name
                        FROM client_schedule cs
                        JOIN users u ON cs.client_id = u.id
                        WHERE cs.day_of_week = ? AND cs.time = ? AND cs.is_active = 1
                        ORDER BY u.name
                    ''', (target_day, time))
                    
                    clients = cursor.fetchall()
                    
                    if len(clients) <= 1:
                        continue  # Não há rotação para fazer se só tem 1 cliente
                    
                    # Obter equipamentos disponíveis
                    cursor.execute('SELECT id FROM equipment ORDER BY id')
                    all_equipment = [row[0] for row in cursor.fetchall()]
                    
                    if len(all_equipment) < len(clients):
                        print(f"Aviso: Não há equipamentos suficientes para {len(clients)} clientes")
                        continue
                    
                    # Calcular rotação baseada no dia da semana
                    # Cada dia avança uma posição na rotação
                    rotation_offset = (target_day - 1) % len(all_equipment)
                    
                    # Criar lista rotacionada de equipamentos para este dia
                    rotated_equipment = all_equipment[rotation_offset:] + all_equipment[:rotation_offset]
                    
                    # Atribuir equipamentos aos clientes mantendo unicidade
                    for idx, (schedule_id, client_id, current_eq, client_name) in enumerate(clients):
                        # Cada cliente recebe um equipamento diferente da lista rotacionada
                        new_equipment_id = rotated_equipment[idx % len(rotated_equipment)]
                        
                        if new_equipment_id != current_eq:
                            cursor.execute('''
                                UPDATE client_schedule
                                SET equipment_id = ?
                                WHERE id = ?
                            ''', (new_equipment_id, schedule_id))
                            changes_made += 1
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro na rotação de equipamentos: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return {
            'changes_made': changes_made,
            'status': 'success' if changes_made >= 0 else 'error'
        }
    
    def check_and_fix_equipment_conflicts(self) -> Dict:
        """
        Verifica se há conflitos de equipamento (mesmo equipamento, mesmo dia/hora, clientes diferentes)
        e corrige automaticamente reatribuindo equipamentos.
        Retorna um dicionário com estatísticas dos conflitos encontrados e corrigidos.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conflicts_found = []
        conflicts_fixed = 0
        
        try:
            # Buscar todos os horários ativos agrupados por dia/hora
            cursor.execute('''
                SELECT cs.day_of_week, cs.time, cs.equipment_id, 
                       GROUP_CONCAT(cs.id || ':' || cs.client_id || ':' || u.name, '|') as clients
                FROM client_schedule cs
                JOIN users u ON cs.client_id = u.id
                WHERE cs.is_active = 1 AND cs.equipment_id IS NOT NULL
                GROUP BY cs.day_of_week, cs.time, cs.equipment_id
                HAVING COUNT(*) > 1
            ''')
            
            conflicts = cursor.fetchall()
            
            for day_of_week, time, equipment_id, clients_str in conflicts:
                # Parsear clientes
                clients_data = []
                for client in clients_str.split('|'):
                    parts = client.split(':')
                    clients_data.append({
                        'schedule_id': int(parts[0]),
                        'client_id': int(parts[1]),
                        'name': parts[2]
                    })
                
                conflicts_found.append({
                    'day': day_of_week,
                    'time': time,
                    'equipment_id': equipment_id,
                    'clients': [c['name'] for c in clients_data]
                })
                
                # Corrigir: manter o primeiro, reatribuir os outros
                for i, client_data in enumerate(clients_data):
                    if i == 0:
                        continue  # Manter o primeiro com equipamento atual
                    
                    # Reatribuir equipamento para os demais
                    new_equipment_id = self.assign_equipment_to_client(
                        client_data['client_id'], 
                        day_of_week, 
                        time
                    )
                    
                    if new_equipment_id and new_equipment_id != equipment_id:
                        cursor.execute('''
                            UPDATE client_schedule 
                            SET equipment_id = ? 
                            WHERE id = ?
                        ''', (new_equipment_id, client_data['schedule_id']))
                        conflicts_fixed += 1
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao verificar conflitos: {e}")
        finally:
            conn.close()
        
        return {
            'conflicts_found': len(conflicts_found),
            'conflicts_fixed': conflicts_fixed,
            'details': conflicts_found
        }
    
    def generate_weekly_appointments(self, start_date: str, end_date: str) -> bool:
        """Gera agendamentos automáticos baseados nos horários fixos dos clientes"""
        try:
            from datetime import datetime, timedelta
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar todos os horários fixos
            schedules = self.get_all_client_schedules()
            
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            current_date = start
            while current_date <= end:
                day_of_week = current_date.weekday() + 1  # 1=Segunda
                
                # Buscar horários fixos para este dia
                day_schedules = [s for s in schedules if s['day_of_week'] == day_of_week]
                
                for schedule in day_schedules:
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # Verificar se já existe agendamento
                    cursor.execute('''
                        SELECT COUNT(*) FROM appointments 
                        WHERE client_id = ? AND date = ? AND time = ? AND status != 'cancelled'
                    ''', (schedule['client_id'], date_str, schedule['time']))
                    
                    if cursor.fetchone()[0] == 0:
                        # Buscar sequência personalizada do cliente para este dia
                        client_sequences = self.get_client_sequences(schedule['client_id'], day_of_week)
                        sequence_id = client_sequences[0]['id'] if client_sequences else None
                        
                        # Criar agendamento
                        cursor.execute('''
                            INSERT INTO appointments (client_id, date, time, day_of_week, client_sequence_id) 
                            VALUES (?, ?, ?, ?, ?)
                        ''', (schedule['client_id'], date_str, schedule['time'], day_of_week, sequence_id))
                
                current_date += timedelta(days=1)
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

    # MÉTODOS DE AGENDAMENTOS
    def create_appointment(self, client_id: int, date: str, time: str, client_sequence_id: int = None, is_recurring: bool = False) -> bool:
        """Cria novo agendamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calcular dia da semana
            from datetime import datetime
            appointment_date = datetime.strptime(date, '%Y-%m-%d')
            day_of_week = appointment_date.weekday() + 1  # Streamlit usa 1=Segunda
            
            # Verificar se o cliente já tem agendamento nesta data/hora
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE client_id = ? AND date = ? AND time = ? AND status != 'cancelled'
            ''', (client_id, date, time))
            client_has_appointment = cursor.fetchone()[0]
            
            if client_has_appointment > 0:
                conn.close()
                print(f"Cliente já tem reposição nesta data/hora")
                return False
            
            # Verificar quantos clientes já estão agendados neste dia/hora
            # 1. Contar agendamentos confirmados
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE date = ? AND time = ? AND status != 'cancelled'
            ''', (date, time))
            confirmed_appointments = cursor.fetchone()[0]
            
            # 2. Contar horários fixos (que não têm agendamento nesta data)
            cursor.execute('''
                SELECT COUNT(*) FROM client_schedule cs
                WHERE cs.day_of_week = ? AND cs.time = ? AND cs.is_active = 1
                AND cs.client_id NOT IN (
                    SELECT client_id FROM appointments 
                    WHERE date = ? AND time = ? AND status != 'cancelled'
                )
            ''', (day_of_week, time, date, time))
            fixed_without_appointment = cursor.fetchone()[0]
            
            total_clients = confirmed_appointments + fixed_without_appointment
            
            # Verificar limite de 3 clientes
            if total_clients >= 3:
                conn.close()
                print(f"Horário lotado: {total_clients} clientes já agendados")
                return False  # Horário lotado (3 clientes)
            
            cursor.execute('''
                INSERT INTO appointments (client_id, date, time, day_of_week, client_sequence_id, is_recurring) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, date, time, day_of_week, client_sequence_id, 1 if is_recurring else 0))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao criar agendamento: {e}")
            return False

    def create_recurring_appointments(self, client_id: int, start_date: str, days_times: dict, client_sequence_id: int = None, weeks_ahead: int = 12) -> int:
        """Cria agendamentos recorrentes para várias semanas
        
        Args:
            client_id: ID do cliente
            start_date: Data de início (YYYY-MM-DD)
            days_times: Dict {day_of_week: time} ex: {1: "09:00", 3: "14:00"}
            client_sequence_id: ID da sequência do cliente
            weeks_ahead: Quantas semanas à frente criar
        
        Returns:
            Número de agendamentos criados
        """
        try:
            from datetime import datetime, timedelta
            
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            created_count = 0
            
            # Para cada semana até weeks_ahead
            for week in range(weeks_ahead):
                week_start = start_date_obj + timedelta(weeks=week)
                
                # Para cada dia da semana selecionado
                for day_of_week, time in days_times.items():
                    # Calcular a data específica
                    days_to_add = (day_of_week - 1) - week_start.weekday()
                    if days_to_add < 0:
                        days_to_add += 7
                    
                    appointment_date = week_start + timedelta(days=days_to_add)
                    
                    # Pular se a data/hora já passou
                    now = get_brasilia_now()
                    appointment_datetime = datetime.combine(appointment_date.date(), datetime.strptime(time, '%H:%M').time())
                    
                    if appointment_datetime <= now:
                        continue
                    
                    # Criar agendamento se não existir
                    if self.create_appointment(
                        client_id, 
                        appointment_date.strftime('%Y-%m-%d'), 
                        time, 
                        client_sequence_id, 
                        is_recurring=True
                    ):
                        created_count += 1
            
            return created_count
        except Exception as e:
            print(f"Erro ao criar agendamentos recorrentes: {e}")
            return 0
    
    def get_appointments(self, client_id: int = None, date_filter: str = None) -> List[Dict]:
        """Retorna lista de agendamentos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna client_sequence_id existe
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'client_sequence_id' in columns:
            # Nova estrutura com client_sequence_id
            query = '''
                SELECT a.*, u.name as client_name, u.phone as client_phone, 
                       cs.name as sequence_name
                FROM appointments a
                JOIN users u ON a.client_id = u.id
                LEFT JOIN client_sequences cs ON a.client_sequence_id = cs.id
            '''
        else:
            # Estrutura antiga com equipment_sequence_id
            query = '''
                SELECT a.*, u.name as client_name, u.phone as client_phone, 
                       es.name as sequence_name
                FROM appointments a
                JOIN users u ON a.client_id = u.id
                LEFT JOIN equipment_sequences es ON a.equipment_sequence_id = es.id
            '''
        
        params = []
        
        conditions = []
        if client_id:
            conditions.append('a.client_id = ?')
            params.append(client_id)
        
        if date_filter:
            conditions.append('a.date = ?')
            params.append(date_filter)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY a.date, a.time'
        
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        
        conn.close()
        
        # Adaptar retorno baseado na estrutura
        # Verificar quais colunas existem
        has_is_recurring = 'is_recurring' in columns
        has_attended = 'attended' in columns
        
        if 'client_sequence_id' in columns:
            if has_is_recurring and has_attended:
                # Estrutura completa: id(0), client_id(1), date(2), time(3), day_of_week(4), 
                # client_sequence_id(5), last_equipment_used(6), status(7), 
                # delay_notification(8), absence_notification(9), created_at(10), 
                # is_recurring(11), attended(12), [JOINs: client_name(13), client_phone(14), sequence_name(15)]
                return [{
                    'id': apt[0],
                    'client_id': apt[1],
                    'date': apt[2],
                    'time': apt[3],
                    'day_of_week': apt[4],
                    'client_sequence_id': apt[5],
                    'last_equipment_used': apt[6],
                    'status': apt[7],
                    'delay_notification': apt[8],
                    'absence_notification': apt[9],
                    'created_at': apt[10],
                    'is_recurring': apt[11],
                    'attended': apt[12],
                    'client_name': apt[13] if len(apt) > 13 else None,
                    'client_phone': apt[14] if len(apt) > 14 else None,
                    'sequence_name': apt[15] if len(apt) > 15 else None
                } for apt in appointments]
            elif has_attended:
                # Com attended mas sem is_recurring
                return [{
                    'id': apt[0],
                    'client_id': apt[1],
                    'date': apt[2],
                    'time': apt[3],
                    'day_of_week': apt[4],
                    'client_sequence_id': apt[5],
                    'last_equipment_used': apt[6],
                    'status': apt[7],
                    'delay_notification': apt[8],
                    'absence_notification': apt[9],
                    'created_at': apt[10],
                    'attended': apt[11],
                    'client_name': apt[12] if len(apt) > 12 else None,
                    'client_phone': apt[13] if len(apt) > 13 else None,
                    'sequence_name': apt[14] if len(apt) > 14 else None
                } for apt in appointments]
            else:
                # Schema antigo sem attended
                return [{
                    'id': apt[0],
                    'client_id': apt[1],
                    'date': apt[2],
                    'time': apt[3],
                    'day_of_week': apt[4],
                    'client_sequence_id': apt[5],
                    'last_equipment_used': apt[6],
                    'status': apt[7],
                    'delay_notification': apt[8],
                    'absence_notification': apt[9],
                    'created_at': apt[10],
                    'client_name': apt[11],
                    'client_phone': apt[12],
                    'sequence_name': apt[13] if len(apt) > 13 else None,
                    'attended': None
                } for apt in appointments]
        else:
            # Estrutura antiga com equipment_sequence_id
            return [{
                'id': apt[0],
                'client_id': apt[1],
                'date': apt[2],
                'time': apt[3],
                'day_of_week': apt[4],
                'equipment_sequence_id': apt[5],
                'client_sequence_id': apt[5],  # Usar o mesmo valor para compatibilidade
                'last_equipment_used': apt[6],
                'status': apt[7],
                'delay_notification': apt[8],
                'absence_notification': apt[9],
                'created_at': apt[10],
                'client_name': apt[11],
                'client_phone': apt[12],
                'sequence_name': apt[13],
                'attended': apt[14] if len(apt) > 14 else None
            } for apt in appointments]
    
    def update_appointment_notifications(self, appointment_id: int, delay_notification: str = None, 
                                       absence_notification: str = None) -> bool:
        """Atualiza notificações do agendamento e cria registro de notificação"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Atualizar campos de notificação no appointment
            cursor.execute('''
                UPDATE appointments 
                SET delay_notification = ?, absence_notification = ? 
                WHERE id = ?
            ''', (delay_notification, absence_notification, appointment_id))
            
            # Buscar informações do appointment para criar notificação
            cursor.execute('''
                SELECT a.client_id, u.name, u.phone, a.date, a.time
                FROM appointments a
                JOIN users u ON a.client_id = u.id
                WHERE a.id = ?
            ''', (appointment_id,))
            
            apt_info = cursor.fetchone()
            
            if apt_info:
                client_id, client_name, client_phone, apt_date, apt_time = apt_info
                
                # Criar mensagem de notificação
                message = ""
                notification_type = ""
                
                if delay_notification:
                    notification_type = "delay"
                    message = f"Atraso notificado para {apt_date} às {apt_time}: {delay_notification}"
                elif absence_notification:
                    notification_type = "absence"
                    message = f"Falta notificada para {apt_date} às {apt_time}: {absence_notification}"
                
                if message:
                    # Inserir notificação na tabela notifications
                    now = get_brasilia_now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    cursor.execute('''
                        INSERT INTO notifications (client_id, client_name, type, message, is_read, created_at)
                        VALUES (?, ?, ?, ?, 0, ?)
                    ''', (client_id, client_name, notification_type, message, now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar notificações: {e}")
            return False
    
    def update_appointment_equipment(self, appointment_id: int, last_equipment_used: str) -> bool:
        """Atualiza último equipamento usado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE appointments 
                SET last_equipment_used = ? 
                WHERE id = ?
            ''', (last_equipment_used, appointment_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def reschedule_appointment(self, appointment_id: int, new_date: str, new_time: str) -> bool:
        """Reagenda compromisso"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se novo horário está disponível
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE date = ? AND time = ? AND status != 'cancelled' AND id != ?
            ''', (new_date, new_time, appointment_id))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # Horário ocupado
            
            # Calcular novo dia da semana
            from datetime import datetime
            appointment_date = datetime.strptime(new_date, '%Y-%m-%d')
            day_of_week = appointment_date.weekday() + 1
            
            cursor.execute('''
                UPDATE appointments 
                SET date = ?, time = ?, day_of_week = ?, status = 'rescheduled' 
                WHERE id = ?
            ''', (new_date, new_time, day_of_week, appointment_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def cancel_appointment(self, appointment_id: int) -> bool:
        """Cancela agendamento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE appointments SET status = "cancelled" WHERE id = ?', (appointment_id,))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_notifications(self) -> List[Dict]:
        """Retorna agendamentos com notificações"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.name as client_name, u.phone as client_phone 
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            WHERE (a.delay_notification IS NOT NULL AND a.delay_notification != '') 
               OR (a.absence_notification IS NOT NULL AND a.absence_notification != '')
            ORDER BY a.date DESC, a.time DESC
        ''')
        
        notifications = cursor.fetchall()
        conn.close()
        
        return [{
            'id': notif[0],
            'client_id': notif[1],
            'date': notif[2],
            'time': notif[3],
            'delay_notification': notif[8],
            'absence_notification': notif[9],
            'client_name': notif[11],
            'client_phone': notif[12]
        } for notif in notifications]
    
    def get_schedule_data(self) -> pd.DataFrame:
        """Retorna dados para visualização da grade de horários com horários fixos"""
        appointments = self.get_appointments()
        client_schedules = self.get_all_client_schedules()
        
        # Criar DataFrame para visualização
        schedule_data = []
        
        # Horários de 6h às 20h
        hours = [f"{h:02d}:00" for h in range(6, 21)]
        days = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
        
        for hour in hours:
            row = {'Horário': hour}
            for i, day in enumerate(days, 1):
                # Procurar agendamento confirmado para este dia/hora
                appointment = next((apt for apt in appointments 
                                  if apt['time'] == hour and apt['day_of_week'] == i 
                                  and apt['status'] != 'cancelled'), None)
                
                if appointment:
                    row[day] = f"✅ {appointment['client_name']}"
                else:
                    # Procurar horário fixo (mas sem agendamento específico)
                    fixed_schedule = next((sched for sched in client_schedules 
                                         if sched['time'] == hour and sched['day_of_week'] == i), None)
                    
                    if fixed_schedule:
                        row[day] = f"📅 {fixed_schedule['client_name']} (Fixo)"
                    else:
                        row[day] = ""
            
            schedule_data.append(row)
        
        return pd.DataFrame(schedule_data)
    
    def get_week_schedule_data(self, start_date: str) -> pd.DataFrame:
        """Retorna dados da grade de horários para uma semana específica"""
        from datetime import datetime, timedelta
        
        appointments = self.get_appointments()
        client_schedules = self.get_all_client_schedules()
        
        # Normalizar hora para formato HH:MM
        def norm_time(t: str) -> str:
            try:
                return t.strip()[:5]
            except Exception:
                return t
        
        # Converter start_date para objeto datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Criar DataFrame para visualização da semana
        schedule_data = []
        
        # Horários de 6h às 20h
        hours = [f"{h:02d}:00" for h in range(6, 21)]
        
        for hour in hours:
            row = {'Horário': hour}
            
            # Para cada dia da semana (Segunda a Sexta)
            for i in range(5):  # 0 = Segunda, 1 = Terça, etc.
                current_date = start + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                day_of_week = current_date.weekday() + 1  # 1 = Segunda, 2 = Terça, ..., 5 = Sexta
                day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][i]
                # Criar coluna com dia e data
                column_name = f"{day_name} {current_date.strftime('%d/%m')}"
                
                # Procurar TODOS os agendamentos confirmados para este dia/hora/data
                day_appointments = [apt for apt in appointments 
                                  if norm_time(apt['time']) == norm_time(hour) 
                                  and apt['date'] == date_str 
                                  and apt['status'] != 'cancelled']
                
                # Coletar IDs dos clientes que já têm appointment
                clients_with_appointments = {apt['client_id'] for apt in day_appointments}
                
                # Procurar horários fixos para este dia/hora (incluindo os que têm appointment)
                fixed_schedules = [sched for sched in client_schedules 
                                 if norm_time(sched['time']) == norm_time(hour) 
                                 and sched['day_of_week'] == day_of_week]
                
                # Montar lista de clientes para exibir
                client_list = []
                
                # Adicionar clientes com appointments
                for apt in day_appointments:
                    client_sched = next((s for s in client_schedules 
                                       if s['client_id'] == apt['client_id'] 
                                       and s['day_of_week'] == day_of_week
                                       and norm_time(s['time']) == norm_time(hour)), None)
                    
                    if client_sched and client_sched.get('equipment_name'):
                        client_list.append(f"✅ {apt['client_name']} 🏋️{client_sched['equipment_name']}")
                    else:
                        client_list.append(f"✅ {apt['client_name']}")
                
                # Adicionar clientes com horário fixo mas SEM appointment ainda
                for sched in fixed_schedules:
                    if sched['client_id'] not in clients_with_appointments:
                        if sched.get('equipment_name'):
                            client_list.append(f"📅 {sched['client_name']} 🏋️{sched['equipment_name']}")
                        else:
                            client_list.append(f"📅 {sched['client_name']}")
                
                # Se tem algum cliente (com ou sem appointment), mostrar
                if client_list:
                    # Usar <br> para quebra de linha HTML (funciona melhor no Streamlit)
                    row[column_name] = "<br>".join(client_list)
                else:
                    row[column_name] = ""
            
            schedule_data.append(row)
        
        return pd.DataFrame(schedule_data)
    
    def get_weeks_with_appointments(self, start_date: str, end_date: str) -> List[Dict]:
        """Retorna semanas que contêm agendamentos no período"""
        from datetime import datetime, timedelta
        
        appointments = self.get_appointments()
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Encontrar todas as semanas no período
        weeks = []
        current = start
        
        while current <= end:
            # Início da semana (segunda-feira)
            week_start = current - timedelta(days=current.weekday())
            week_end = week_start + timedelta(days=4)  # Sexta-feira
            
            # Verificar se há agendamentos nesta semana
            week_appointments = [apt for apt in appointments 
                               if week_start.strftime('%Y-%m-%d') <= apt['date'] <= week_end.strftime('%Y-%m-%d')
                               and apt['status'] != 'cancelled']
            
            weeks.append({
                'start_date': week_start.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
                'week_label': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                'appointments_count': len(week_appointments),
                'has_appointments': len(week_appointments) > 0
            })
            
            current += timedelta(days=7)
        
        return weeks
    
    def get_week_schedule_data_with_details(self, start_date: str) -> List[Dict]:
        """Retorna dados detalhados da grade de horários com appointments por data"""
        from datetime import datetime, timedelta
        
        # Buscar apenas appointments (sistema novo baseado em datas)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calcular range de datas (segunda a sexta da semana)
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = start + timedelta(days=4)  # Segunda a Sexta
        
        # Buscar appointments da semana
        cursor.execute('''
            SELECT a.id, a.client_id, a.date, a.time, a.day_of_week, 
                   a.status, a.attended, u.name as client_name
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            WHERE a.date >= ? AND a.date <= ?
            AND a.status != 'cancelled'
            AND a.attended IS NULL
            ORDER BY a.date, a.time
        ''', (start_date, end.strftime('%Y-%m-%d')))
        
        appointments = cursor.fetchall()
        conn.close()
        
        # Normalizar hora para formato HH:MM
        def norm_time(t: str) -> str:
            try:
                return t.strip()[:5]
            except Exception:
                return t
        
        # Horários de 6h às 20h
        hours = [f"{h:02d}:00" for h in range(6, 21)]
        
        schedule_details = []
        
        for hour in hours:
            hour_data = {
                'time': hour,
                'days': []
            }
            
            # Para cada dia da semana (Segunda a Sexta)
            for i in range(5):  # 0 = Segunda, 1 = Terça, etc.
                current_date = start + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                day_of_week = current_date.weekday() + 1  # 1 = Segunda, ..., 5 = Sexta
                day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][i]
                
                day_data = {
                    'date': date_str,
                    'day_of_week': day_of_week,
                    'day_name': day_name,
                    'clients': []
                }
                
                # Procurar appointments para este dia/hora específicos
                for apt in appointments:
                    apt_date = apt[2]
                    apt_time = norm_time(apt[3])
                    
                    if apt_date == date_str and apt_time == norm_time(hour):
                        # Appointment encontrado para esta data/hora
                        client_info = {
                            'client_id': apt[1],
                            'client_name': apt[7],
                            'appointment_id': apt[0],
                            'status': apt[5],
                            'attended': apt[6],
                            'has_appointment': True,
                            'equipment_name': None  # Pode adicionar lógica de equipamento depois se necessário
                        }
                        day_data['clients'].append(client_info)
                
                hour_data['days'].append(day_data)
            
            schedule_details.append(hour_data)
        
        return schedule_details
    
    def mark_attendance(self, appointment_id: int, attended: bool = None) -> bool:
        """Marca presença ou falta em um agendamento
        
        Args:
            appointment_id: ID do agendamento
            attended: True para presença, False para falta, None para limpar
        
        Returns:
            True se marcado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if attended is None:
                value = None
            else:
                value = 1 if attended else 0
            
            cursor.execute('''
                UPDATE appointments 
                SET attended = ? 
                WHERE id = ?
            ''', (value, appointment_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao marcar presença: {e}")
            return False
    
    def get_appointment_by_details(self, client_id: int, date: str, time: str) -> Optional[Dict]:
        """Busca um agendamento específico por detalhes
        
        Args:
            client_id: ID do cliente
            date: Data no formato YYYY-MM-DD
            time: Hora no formato HH:MM
        
        Returns:
            Dict com dados do agendamento ou None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, client_id, date, time, attended, status
                FROM appointments
                WHERE client_id = ? AND date = ? AND time = ?
                ORDER BY id DESC
                LIMIT 1
            ''', (client_id, date, time))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'client_id': row[1],
                    'date': row[2],
                    'time': row[3],
                    'attended': row[4],
                    'status': row[5]
                }
            return None
        except Exception as e:
            print(f"Erro ao buscar agendamento: {e}")
            return None
    
    # ==================== MÉTODOS FINANCEIROS ====================
    
    def create_conta_receber(self, client_id: int, tipo_plano: str, valor: float, 
                            quantidade: int, data_vencimento: str, observacoes: str = "") -> bool:
        """Cria uma conta a receber para um cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO contas_receber (client_id, tipo_plano, valor, quantidade, 
                                           data_vencimento, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, tipo_plano, valor, quantidade, data_vencimento, observacoes))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao criar conta a receber: {e}")
            return False
    
    def get_contas_receber(self, client_id: int = None) -> List[Dict]:
        """Busca contas a receber, opcionalmente filtradas por cliente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if client_id:
                cursor.execute('''
                    SELECT cr.*, u.name as client_name
                    FROM contas_receber cr
                    JOIN users u ON cr.client_id = u.id
                    WHERE cr.client_id = ?
                    ORDER BY cr.data_vencimento
                ''', (client_id,))
            else:
                cursor.execute('''
                    SELECT cr.*, u.name as client_name
                    FROM contas_receber cr
                    JOIN users u ON cr.client_id = u.id
                    ORDER BY cr.data_vencimento
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            contas = []
            for row in rows:
                contas.append({
                    'id': row[0],
                    'client_id': row[1],
                    'tipo_plano': row[2],
                    'valor': row[3],
                    'quantidade': row[4],
                    'data_vencimento': row[5],
                    'data_pagamento': row[6],
                    'status': row[7],
                    'observacoes': row[8],
                    'created_at': row[9],
                    'client_name': row[10]
                })
            return contas
        except Exception as e:
            print(f"Erro ao buscar contas a receber: {e}")
            return []
    
    def update_pagamento_receber(self, conta_id: int, data_pagamento: str) -> bool:
        """Marca uma conta a receber como paga"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE contas_receber 
                SET data_pagamento = ?, status = 'pago'
                WHERE id = ?
            ''', (data_pagamento, conta_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar pagamento: {e}")
            return False
    
    def delete_conta_receber(self, conta_id: int) -> bool:
        """Exclui uma conta a receber"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM contas_receber WHERE id = ?', (conta_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir conta a receber: {e}")
            return False
    
    def create_conta_pagar(self, data_debito: str, tipo_debito: str, valor_total: float,
                          quantidade: int, tipo_parcelamento: str, observacoes: str = "", 
                          recorrente: bool = False) -> bool:
        """Cria uma conta a pagar e suas parcelas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Se for recorrente, ajustar quantidade para até dezembro
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            data_inicial = datetime.strptime(data_debito, '%Y-%m-%d')
            
            if recorrente:
                # Calcular meses até dezembro do ano atual
                meses_ate_dezembro = 12 - data_inicial.month + 1
                quantidade = meses_ate_dezembro
            
            # Inserir conta principal
            cursor.execute('''
                INSERT INTO contas_pagar (data_debito, tipo_debito, valor_total, quantidade,
                                         tipo_parcelamento, observacoes, recorrente)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data_debito, tipo_debito, valor_total, quantidade, tipo_parcelamento, observacoes, 
                  1 if recorrente else 0))
            
            conta_id = cursor.lastrowid
            
            # Criar parcelas
            valor_parcela = valor_total / quantidade if tipo_parcelamento == 'parcelado' else valor_total
            
            for i in range(quantidade):
                if tipo_parcelamento == 'mensal' or recorrente:
                    data_vencimento = data_inicial + relativedelta(months=i)
                    valor_atual = valor_total
                else:  # parcelado
                    data_vencimento = data_inicial + relativedelta(months=i)
                    valor_atual = valor_parcela
                
                cursor.execute('''
                    INSERT INTO parcelas_pagar (conta_pagar_id, numero_parcela, data_vencimento, valor)
                    VALUES (?, ?, ?, ?)
                ''', (conta_id, i + 1, data_vencimento.strftime('%Y-%m-%d'), valor_atual))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao criar conta a pagar: {e}")
            return False
    
    def get_contas_pagar(self) -> List[Dict]:
        """Busca todas as contas a pagar"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM contas_pagar ORDER BY data_debito DESC')
            rows = cursor.fetchall()
            conn.close()
            
            contas = []
            for row in rows:
                contas.append({
                    'id': row[0],
                    'data_debito': row[1],
                    'tipo_debito': row[2],
                    'valor_total': row[3],
                    'quantidade': row[4],
                    'tipo_parcelamento': row[5],
                    'status': row[6],
                    'observacoes': row[7],
                    'created_at': row[8],
                    'recorrente': row[9] if len(row) > 9 else 0
                })
            return contas
        except Exception as e:
            print(f"Erro ao buscar contas a pagar: {e}")
            return []
    
    def get_parcelas_pagar(self, conta_id: int = None) -> List[Dict]:
        """Busca parcelas de contas a pagar"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if conta_id:
                cursor.execute('''
                    SELECT pp.*, cp.tipo_debito
                    FROM parcelas_pagar pp
                    JOIN contas_pagar cp ON pp.conta_pagar_id = cp.id
                    WHERE pp.conta_pagar_id = ?
                    ORDER BY pp.numero_parcela
                ''', (conta_id,))
            else:
                cursor.execute('''
                    SELECT pp.*, cp.tipo_debito
                    FROM parcelas_pagar pp
                    JOIN contas_pagar cp ON pp.conta_pagar_id = cp.id
                    ORDER BY pp.data_vencimento
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            parcelas = []
            for row in rows:
                parcelas.append({
                    'id': row[0],
                    'conta_pagar_id': row[1],
                    'numero_parcela': row[2],
                    'data_vencimento': row[3],
                    'valor': row[4],
                    'data_pagamento': row[5],
                    'status': row[6],
                    'tipo_debito': row[7]
                })
            return parcelas
        except Exception as e:
            print(f"Erro ao buscar parcelas: {e}")
            return []
    
    def update_pagamento_pagar(self, parcela_id: int, data_pagamento: str) -> bool:
        """Marca uma parcela como paga"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE parcelas_pagar 
                SET data_pagamento = ?, status = 'pago'
                WHERE id = ?
            ''', (data_pagamento, parcela_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar pagamento: {e}")
            return False
    
    def delete_conta_pagar(self, conta_id: int) -> bool:
        """Exclui uma conta a pagar e suas parcelas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM parcelas_pagar WHERE conta_pagar_id = ?', (conta_id,))
            cursor.execute('DELETE FROM contas_pagar WHERE id = ?', (conta_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir conta a pagar: {e}")
            return False
    
    def delete_parcela_pagar(self, parcela_id: int) -> bool:
        """Exclui uma parcela específica. Se for a última, exclui a conta também."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar conta_pagar_id antes de excluir
            cursor.execute('SELECT conta_pagar_id FROM parcelas_pagar WHERE id = ?', (parcela_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            conta_pagar_id = result[0]
            
            # Excluir a parcela
            cursor.execute('DELETE FROM parcelas_pagar WHERE id = ?', (parcela_id,))
            
            # Verificar se ainda existem outras parcelas
            cursor.execute('SELECT COUNT(*) FROM parcelas_pagar WHERE conta_pagar_id = ?', (conta_pagar_id,))
            count = cursor.fetchone()[0]
            
            # Se não houver mais parcelas, excluir a conta principal também
            if count == 0:
                cursor.execute('DELETE FROM contas_pagar WHERE id = ?', (conta_pagar_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir parcela: {e}")
            return False
    
    def get_fluxo_caixa(self, data_inicio: str, data_fim: str) -> Dict:
        """Gera relatório de fluxo de caixa para um período, incluindo projeção de contas recorrentes"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contas a receber no período (incluindo as já cadastradas)
            cursor.execute('''
                SELECT data_vencimento, SUM(valor) as total
                FROM contas_receber
                WHERE data_vencimento BETWEEN ? AND ?
                GROUP BY data_vencimento
            ''', (data_inicio, data_fim))
            
            receber = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Buscar contas a receber recorrentes para projetar até dezembro
            # Usar apenas a conta mais recente de cada cliente/tipo para evitar duplicação
            # Pegar a conta com a última data de vencimento para cada client_id + tipo_plano
            cursor.execute('''
                WITH todas_contas_recorrentes AS (
                    -- Contas marcadas como Recorrente
                    SELECT DISTINCT client_id, tipo_plano
                    FROM contas_receber
                    WHERE observacoes LIKE '%Recorrente%'
                    
                    UNION
                    
                    -- Contas com 3 ou mais registros do mesmo tipo
                    SELECT c2.client_id, c2.tipo_plano
                    FROM contas_receber c2
                    GROUP BY c2.client_id, c2.tipo_plano
                    HAVING COUNT(*) >= 3
                )
                SELECT cr.client_id, cr.tipo_plano, cr.valor, cr.quantidade, cr.data_vencimento as ultima_data
                FROM contas_receber cr
                INNER JOIN todas_contas_recorrentes tcr 
                    ON cr.client_id = tcr.client_id 
                    AND cr.tipo_plano = tcr.tipo_plano
                WHERE cr.data_vencimento = (
                    SELECT MAX(cr2.data_vencimento)
                    FROM contas_receber cr2
                    WHERE cr2.client_id = cr.client_id
                    AND cr2.tipo_plano = cr.tipo_plano
                )
            ''')
            
            contas_recorrentes = cursor.fetchall()
            
            # Projetar contas recorrentes até dezembro do ano final
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            dezembro = datetime(data_fim_obj.year, 12, 31)
            
            for conta in contas_recorrentes:
                client_id, tipo_plano, valor, quantidade, ultima_data = conta
                
                # Começar a partir do mês seguinte à última data cadastrada
                ultima_data_obj = datetime.strptime(ultima_data, '%Y-%m-%d')
                mes_atual = ultima_data_obj + relativedelta(months=1)
                
                # Projetar mensalmente até dezembro
                while mes_atual <= dezembro:
                    data_str = mes_atual.strftime('%Y-%m-%d')
                    
                    # Verificar se está no período solicitado
                    if data_inicio <= data_str <= data_fim:
                        # Verificar se JÁ EXISTE uma conta cadastrada para este cliente/tipo neste mês
                        ano_mes = data_str[:7]  # YYYY-MM
                        cursor.execute('''
                            SELECT COUNT(*) FROM contas_receber
                            WHERE client_id=? AND tipo_plano=? 
                            AND strftime('%Y-%m', data_vencimento) = ?
                        ''', (client_id, tipo_plano, ano_mes))
                        
                        # Só adicionar projeção se NÃO existir conta cadastrada neste mês
                        if cursor.fetchone()[0] == 0:
                            receber[data_str] = receber.get(data_str, 0) + valor
                    
                    mes_atual = mes_atual + relativedelta(months=1)
            
            # Parcelas a pagar no período (incluindo as já cadastradas)
            cursor.execute('''
                SELECT data_vencimento, SUM(valor) as total
                FROM parcelas_pagar
                WHERE data_vencimento BETWEEN ? AND ?
                GROUP BY data_vencimento
            ''', (data_inicio, data_fim))
            
            pagar = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Buscar contas a pagar recorrentes para projetar até dezembro
            cursor.execute('''
                SELECT cp.id, cp.tipo_debito, cp.valor_total, cp.data_debito,
                       (SELECT MAX(pp.data_vencimento) FROM parcelas_pagar pp WHERE pp.conta_pagar_id = cp.id) as ultima_parcela
                FROM contas_pagar cp
                WHERE cp.recorrente = 1
            ''')
            
            contas_pagar_recorrentes = cursor.fetchall()
            
            for conta_pagar in contas_pagar_recorrentes:
                cp_id, tipo_debito, valor_total, data_debito, ultima_parcela = conta_pagar
                
                # Se já existem parcelas, começar após a última. Senão, começar na data de débito
                if ultima_parcela:
                    data_inicial_obj = datetime.strptime(ultima_parcela, '%Y-%m-%d')
                    mes_atual = data_inicial_obj + relativedelta(months=1)
                else:
                    data_inicial_obj = datetime.strptime(data_debito, '%Y-%m-%d')
                    mes_atual = data_inicial_obj
                
                # Projetar mensalmente até dezembro
                while mes_atual <= dezembro:
                    data_str = mes_atual.strftime('%Y-%m-%d')
                    
                    # Verificar se está no período solicitado
                    if data_inicio <= data_str <= data_fim:
                        # Verificar se JÁ EXISTE uma parcela cadastrada para esta conta neste mês
                        ano_mes = data_str[:7]  # YYYY-MM
                        cursor.execute('''
                            SELECT COUNT(*) FROM parcelas_pagar
                            WHERE conta_pagar_id=? 
                            AND strftime('%Y-%m', data_vencimento) = ?
                        ''', (cp_id, ano_mes))
                        
                        # Só adicionar projeção se NÃO existir parcela cadastrada neste mês
                        if cursor.fetchone()[0] == 0:
                            pagar[data_str] = pagar.get(data_str, 0) + valor_total
                    
                    mes_atual = mes_atual + relativedelta(months=1)
            
            conn.close()
            
            return {
                'receber': receber,
                'pagar': pagar
            }
        except Exception as e:
            print(f"Erro ao gerar fluxo de caixa: {e}")
            import traceback
            traceback.print_exc()
            return {'receber': {}, 'pagar': {}}
    
    def gerar_appointments_cliente(self, client_id: int, dias_horarios: dict = None) -> int:
        """
        Gera appointments automaticamente para um cliente baseado em:
        - data_inicio_contrato
        - tipo_contrato ('fixo' ou 'sessoes')
        - sessoes_contratadas
        - dias_semana (JSON object: {"1": "08:00", "5": "14:00"} = Segunda 08h e Sexta 14h)
        
        Args:
            client_id: ID do cliente
            dias_horarios: Dicionário opcional {dia_num: horario} para sobrescrever
        
        Returns:
            Número de appointments criados
        """
        import json
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar dados do cliente
            cursor.execute('''
                SELECT data_inicio_contrato, tipo_contrato, sessoes_contratadas,
                       dias_semana, sessoes_utilizadas, contrato_ativo
                FROM users WHERE id = ?
            ''', (client_id,))
            
            dados = cursor.fetchone()
            
            if not dados:
                conn.close()
                return 0
            
            data_inicio_str, tipo, sessoes_total, dias_semana_json, sessoes_usadas, ativo = dados
            
            # Verificar se contrato está ativo
            if not ativo:
                conn.close()
                return 0
            
            # Parse data de início
            if not data_inicio_str:
                conn.close()
                return 0
                
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            
            # Parse dias da semana e horários
            # Novo formato: {"1": "08:00", "5": "14:00"}
            # Formato antigo (compatibilidade): [1, 5]
            if not dias_semana_json:
                conn.close()
                return 0
            
            dias_horarios_map = {}
            if dias_horarios:
                # Usar dicionário fornecido
                dias_horarios_map = {int(k): v for k, v in dias_horarios.items()}
            else:
                # Carregar do banco
                try:
                    data = json.loads(dias_semana_json)
                    if isinstance(data, dict):
                        # Novo formato: {"1": "08:00", "5": "14:00"}
                        dias_horarios_map = {int(k): v for k, v in data.items()}
                    elif isinstance(data, list):
                        # Formato antigo: [1, 5] - usar horário padrão
                        dias_horarios_map = {dia: "08:00" for dia in data}
                except:
                    conn.close()
                    return 0
            
            if not dias_horarios_map:
                conn.close()
                return 0
            
            # Definir data final baseado no tipo de contrato
            if tipo == 'fixo':
                # Cliente fixo: gerar appointments por 1 ano (ilimitado, renovado automaticamente)
                # Gerar 52 semanas à frente da data atual
                data_fim = get_brasilia_today() + timedelta(days=365)
            else:
                # Cliente sessões: gerar apenas as sessões restantes
                sessoes_restantes = (sessoes_total or 0) - (sessoes_usadas or 0)
                if sessoes_restantes <= 0:
                    conn.close()
                    return 0
                # Máximo 6 meses no futuro
                data_fim = data_inicio + timedelta(days=180)
            
            # Deletar appointments futuros existentes (não marcados)
            hoje = get_brasilia_today().strftime('%Y-%m-%d')
            cursor.execute('''
                DELETE FROM appointments
                WHERE client_id = ? AND date >= ? AND attended IS NULL
            ''', (client_id, hoje))
            
            # Iterar pelas datas e criar appointments
            current_date = data_inicio if data_inicio >= get_brasilia_today() else get_brasilia_today()
            appointments_criados = 0
            
            while current_date <= data_fim:
                # Verificar se é um dos dias da semana do cliente (1=Segunda, 5=Sexta)
                weekday = current_date.weekday() + 1  # Python: 0=Segunda, converte para 1=Segunda
                
                if weekday in dias_horarios_map:
                    # Pegar horário específico para este dia
                    horario = dias_horarios_map[weekday]
                    
                    # Verificar se já existe appointment para este dia
                    date_str = current_date.strftime('%Y-%m-%d')
                    cursor.execute('''
                        SELECT id FROM appointments
                        WHERE client_id = ? AND date = ? AND status != 'cancelled'
                    ''', (client_id, date_str))
                    
                    if not cursor.fetchone():
                        # Criar appointment com horário específico do dia
                        cursor.execute('''
                            INSERT INTO appointments 
                            (client_id, date, time, day_of_week, status, created_at)
                            VALUES (?, ?, ?, ?, 'scheduled', datetime('now'))
                        ''', (client_id, date_str, horario, weekday))
                        
                        appointments_criados += 1
                        
                        # Se tipo sessões, parar ao atingir o limite
                        if tipo == 'sessoes' and appointments_criados >= (sessoes_total - sessoes_usadas):
                            break
                
                current_date += timedelta(days=1)
            
            conn.commit()
            conn.close()
            
            return appointments_criados
            
        except Exception as e:
            print(f"Erro ao gerar appointments: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def marcar_sessao_utilizada(self, client_id: int) -> bool:
        """Incrementa o contador de sessões utilizadas quando marca presença"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET sessoes_utilizadas = sessoes_utilizadas + 1
                WHERE id = ?
            ''', (client_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao marcar sessão utilizada: {e}")
            return False

# Instância global do banco
db = Database()