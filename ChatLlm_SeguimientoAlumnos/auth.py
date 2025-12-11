import streamlit as st
from database import DatabaseManager

class AuthManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def login_page(self):
        """Página de login principal"""
        st.title("🎓 Sistema de Seguimiento de Egresados - NovaUniversitas")
        
        # Tabs para diferentes tipos de login
        tab1, tab2, tab3 = st.tabs(["👨‍🎓 Alumnos Egresados", "👨‍💼 Servicios Escolares", "🏢 Empresas"])
        
        with tab1:
            self.student_login()
        
        with tab2:
            self.admin_login()
        
        with tab3:
            self.company_registration()
    
    def student_login(self):
        """Login para alumnos egresados"""
        st.subheader("Acceso para Alumnos Egresados")
        
        with st.form("student_login"):
            matricula = st.text_input("Matrícula: 0121010030")
            password = st.text_input("Contraseña 01210100", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                if matricula and password:
                    user = self.db.authenticate_user(matricula, password)
                    if user and user['tipo_usuario'] == 'alumno':
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.success("¡Bienvenido!")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas o usuario no autorizado")
                else:
                    st.error("Por favor complete todos los campos")
    
    def admin_login(self):
        """Login para servicios escolares"""
        st.subheader("Acceso para Servicios Escolares")
        
        with st.form("admin_login"):
            matricula = st.text_input("Usuario: ADMIN001")
            password = st.text_input("Contraseña: admin123", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                if matricula and password:
                    user = self.db.authenticate_user(matricula, password)
                    if user and user['tipo_usuario'] == 'admin':
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.success("¡Bienvenido Administrador!")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                else:
                    st.error("Por favor complete todos los campos")
    
    def company_registration(self):
        """Registro para empresas"""
        st.subheader("Registro de Empresas - Bolsa de Trabajo")
        
        with st.form("company_registration"):
            st.write("Registre su empresa para publicar ofertas de trabajo")
            
            nombre_empresa = st.text_input("Nombre de la Empresa*")
            sector = st.selectbox("Sector", [
                "Tecnología", "Salud", "Educación", "Finanzas", 
                "Manufactura", "Servicios", "Gobierno", "Otro"
            ])
            descripcion = st.text_area("Descripción de la Empresa")
            email_contacto = st.text_input("Email de Contacto*")
            telefono = st.text_input("Teléfono")
            sitio_web = st.text_input("Sitio Web")
            
            submit = st.form_submit_button("Registrar Empresa")
            
            if submit:
                if nombre_empresa and email_contacto:
                    try:
                        query = '''
                            INSERT INTO empresas (nombre_empresa, sector, descripcion, email_contacto, telefono, sitio_web)
                            VALUES (?, ?, ?, ?, ?, ?)
                        '''
                        self.db.execute_query(query, (nombre_empresa, sector, descripcion, email_contacto, telefono, sitio_web))
                        st.success("¡Empresa registrada exitosamente! Pronto nos pondremos en contacto.")
                    except Exception as e:
                        st.error(f"Error al registrar empresa: {str(e)}")
                else:
                    st.error("Por favor complete los campos obligatorios (*)")
    
    def logout(self):
        """Cerrar sesión"""
        for key in ['user', 'logged_in']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    def is_logged_in(self):
        """Verifica si hay una sesión activa"""
        return st.session_state.get('logged_in', False)
    
    def get_current_user(self):
        """Obtiene el usuario actual"""
        return st.session_state.get('user', None)
    