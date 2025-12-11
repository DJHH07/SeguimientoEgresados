import sqlite3
import bcrypt
from datetime import datetime
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="nova_universitas.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Inicializa todas las tablas de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de usuarios (servicios escolares y alumnos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT UNIQUE,
                password TEXT NOT NULL,
                tipo_usuario TEXT NOT NULL CHECK (tipo_usuario IN ('admin', 'alumno')),
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de carreras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carreras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_carrera TEXT NOT NULL UNIQUE,
                facultad TEXT NOT NULL,
                duracion_semestres INTEGER,
                activa BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de alumnos egresados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alumnos_egresados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                carrera_id INTEGER,
                fecha_ingreso DATE,
                fecha_egreso DATE NOT NULL,
                promedio REAL,
                cedula_profesional TEXT,
                titulo_obtenido BOOLEAN DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (carrera_id) REFERENCES carreras (id),
                FOREIGN KEY (matricula) REFERENCES usuarios (matricula)
            )
        ''')
        
        # Tabla de situación académica actual
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS situacion_academica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL,
                estudia_actualmente BOOLEAN NOT NULL,
                institucion_actual TEXT,
                tipo_estudios TEXT CHECK (tipo_estudios IN ('maestria', 'doctorado', 'especialidad', 'diplomado', 'otro')),
                nombre_programa TEXT,
                fecha_inicio DATE,
                fecha_fin_estimada DATE,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matricula) REFERENCES usuarios (matricula)
            )
        ''')
        
        # Tabla de situación laboral
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS situacion_laboral (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL,
                trabaja_actualmente BOOLEAN NOT NULL,
                empresa TEXT,
                cargo TEXT,
                sector TEXT,
                salario_rango TEXT,
                anos_experiencia INTEGER,
                fecha_inicio_trabajo DATE,
                relacionado_carrera BOOLEAN,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matricula) REFERENCES usuarios (matricula)
            )
        ''')
        
        # Tabla de empresas/bolsas de trabajo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_empresa TEXT NOT NULL,
                sector TEXT,
                descripcion TEXT,
                email_contacto TEXT,
                telefono TEXT,
                sitio_web TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activa BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de ofertas de trabajo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ofertas_trabajo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER,
                titulo_puesto TEXT NOT NULL,
                descripcion TEXT,
                requisitos TEXT,
                salario_ofrecido TEXT,
                modalidad TEXT CHECK (modalidad IN ('presencial', 'remoto', 'hibrido')),
                ubicacion TEXT,
                fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_vencimiento DATE,
                activa BOOLEAN DEFAULT 1,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            )
        ''')
        
        # Tabla de notificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT,
                oferta_id INTEGER,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                leida BOOLEAN DEFAULT 0,
                fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matricula) REFERENCES usuarios (matricula),
                FOREIGN KEY (oferta_id) REFERENCES ofertas_trabajo (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Crear usuario administrador por defecto
        self.create_default_admin()
    
    def create_default_admin(self):
        """Crea un usuario administrador por defecto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un admin
        cursor.execute("SELECT * FROM usuarios WHERE tipo_usuario = 'admin'")
        if cursor.fetchone() is None:
            # Crear admin por defecto
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO usuarios (matricula, password, tipo_usuario, nombre, apellidos, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("ADMIN001", password_hash, "admin", "Servicios", "Escolares", "servicios@novauniversitas.edu"))
            conn.commit()
        
        conn.close()
    
    def hash_password(self, password):
        """Hashea una contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password, hashed):
        """Verifica una contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def authenticate_user(self, matricula, password):
        """Autentica un usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT password, tipo_usuario, nombre, apellidos FROM usuarios WHERE matricula = ? AND activo = 1", (matricula,))
        result = cursor.fetchone()
        conn.close()
        
        if result and self.verify_password(password, result[0]):
            return {
                'matricula': matricula,
                'tipo_usuario': result[1],
                'nombre': result[2],
                'apellidos': result[3]
            }
        return None
    
    def execute_query(self, query, params=None):
        """Ejecuta una consulta SQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            return pd.DataFrame(result, columns=columns) if result else pd.DataFrame()
        else:
            conn.commit()
            conn.close()
            return cursor.rowcount