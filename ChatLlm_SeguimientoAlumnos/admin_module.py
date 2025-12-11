import streamlit as st
import pandas as pd
from database import DatabaseManager
from datetime import datetime, date

class AdminModule:
    def __init__(self):
        self.db = DatabaseManager()
    
    def show_admin_dashboard(self):
        """Dashboard principal del administrador"""
        st.title("🏛️ Panel de Administración - Servicios Escolares")
        
        # Sidebar con opciones
        st.sidebar.title("Opciones de Administración")
        option = st.sidebar.selectbox("Seleccione una opción:", [
            "📊 Dashboard Principal",
            "👨‍🎓 Gestión de Alumnos Egresados", 
            "🔍 Búsqueda de Alumnos",
            "📝 Registro de Nuevos Egresados",
            "🎓 Gestión de Carreras",
            "🏢 Gestión de Empresas",
            "💼 Gestión de Ofertas de Trabajo",
            "📧 Gestión de Notificaciones",
            "👥 Gestión de Usuarios"
        ])
        
        if option == "📊 Dashboard Principal":
            self.show_dashboard_stats()
        elif option == "👨‍🎓 Gestión de Alumnos Egresados":
            self.manage_graduates()
        elif option == "🔍 Búsqueda de Alumnos":
            self.search_students()
        elif option == "📝 Registro de Nuevos Egresados":
            self.register_new_graduate()
        elif option == "🎓 Gestión de Carreras":
            self.manage_careers()
        elif option == "🏢 Gestión de Empresas":
            self.manage_companies()
        elif option == "💼 Gestión de Ofertas de Trabajo":
            self.manage_job_offers()
        elif option == "📧 Gestión de Notificaciones":
            self.manage_notifications()
        elif option == "👥 Gestión de Usuarios":
            self.manage_users()
    
    def show_dashboard_stats(self):
        """Muestra estadísticas del dashboard"""
        st.subheader("📊 Estadísticas Generales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Total de egresados
        total_graduates = self.db.execute_query("SELECT COUNT(*) as total FROM alumnos_egresados")
        with col1:
            st.metric("Total Egresados", total_graduates.iloc[0]['total'] if not total_graduates.empty else 0)
        
        # Egresados activos (con cuenta)
        active_users = self.db.execute_query("SELECT COUNT(*) as total FROM usuarios WHERE tipo_usuario = 'alumno' AND activo = 1")
        with col2:
            st.metric("Usuarios Activos", active_users.iloc[0]['total'] if not active_users.empty else 0)
        
        # Empresas registradas
        companies = self.db.execute_query("SELECT COUNT(*) as total FROM empresas WHERE activa = 1")
        with col3:
            st.metric("Empresas Registradas", companies.iloc[0]['total'] if not companies.empty else 0)
        
        # Ofertas activas
        job_offers = self.db.execute_query("SELECT COUNT(*) as total FROM ofertas_trabajo WHERE activa = 1")
        with col4:
            st.metric("Ofertas Activas", job_offers.iloc[0]['total'] if not job_offers.empty else 0)
        
        # Gráficos adicionales
        st.subheader("📈 Estadísticas por Carrera")
        career_stats = self.db.execute_query('''
            SELECT c.nombre_carrera, COUNT(ae.id) as total_egresados
            FROM carreras c
            LEFT JOIN alumnos_egresados ae ON c.id = ae.carrera_id
            GROUP BY c.id, c.nombre_carrera
            ORDER BY total_egresados DESC
        ''')
        
        if not career_stats.empty:
            st.bar_chart(career_stats.set_index('nombre_carrera'))
    
    def manage_graduates(self):
        """Gestión CRUD de alumnos egresados"""
        st.subheader("👨‍🎓 Gestión de Alumnos Egresados")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Ver Todos", "Crear", "Actualizar", "Eliminar"])
        
        with tab1:
            self.view_all_graduates()
        
        with tab2:
            self.create_graduate()
        
        with tab3:
            self.update_graduate()
        
        with tab4:
            self.delete_graduate()
    
    def view_all_graduates(self):
        """Ver todos los egresados"""
        st.write("### Lista de Todos los Egresados")
        
        graduates = self.db.execute_query('''
            SELECT ae.matricula, ae.nombre, ae.apellidos, ae.email, 
                   c.nombre_carrera, ae.fecha_egreso, ae.promedio
            FROM alumnos_egresados ae
            LEFT JOIN carreras c ON ae.carrera_id = c.id
            ORDER BY ae.fecha_egreso DESC
        ''')
        
        if not graduates.empty:
            st.dataframe(graduates, use_container_width=True)
        else:
            st.info("No hay egresados registrados")
    
    def create_graduate(self):
        """Crear nuevo egresado"""
        st.write("### Registrar Nuevo Egresado")
        
        with st.form("create_graduate"):
            col1, col2 = st.columns(2)
            
            with col1:
                matricula = st.text_input("Matrícula*")
                nombre = st.text_input("Nombre*")
                apellidos = st.text_input("Apellidos*")
                email = st.text_input("Email")
                telefono = st.text_input("Teléfono")
            
            with col2:
                # Obtener carreras
                carreras = self.db.execute_query("SELECT id, nombre_carrera FROM carreras WHERE activa = 1")
                if not carreras.empty:
                    carrera_options = dict(zip(carreras['nombre_carrera'], carreras['id']))
                    carrera_selected = st.selectbox("Carrera*", list(carrera_options.keys()))
                    carrera_id = carrera_options[carrera_selected]
                else:
                    st.error("No hay carreras registradas. Registre una carrera primero.")
                    return
                
                fecha_ingreso = st.date_input("Fecha de Ingreso")
                fecha_egreso = st.date_input("Fecha de Egreso*")
                promedio = st.number_input("Promedio", min_value=0.0, max_value=10.0, step=0.1)
                cedula_profesional = st.text_input("Cédula Profesional")
                titulo_obtenido = st.checkbox("Título Obtenido")
            
            submit = st.form_submit_button("Registrar Egresado")
            
            if submit:
                if matricula and nombre and apellidos and fecha_egreso:
                    try:
                        # Insertar en alumnos_egresados
                        query = '''
                            INSERT INTO alumnos_egresados 
                            (matricula, nombre, apellidos, email, telefono, carrera_id, 
                             fecha_ingreso, fecha_egreso, promedio, cedula_profesional, titulo_obtenido)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        '''
                        self.db.execute_query(query, (
                            matricula, nombre, apellidos, email, telefono, carrera_id,
                            fecha_ingreso, fecha_egreso, promedio, cedula_profesional, titulo_obtenido
                        ))
                        
                        # Crear usuario para login (contraseña temporal = matrícula)
                        password_hash = self.db.hash_password(matricula)
                        user_query = '''
                            INSERT INTO usuarios (matricula, password, tipo_usuario, nombre, apellidos, email, telefono)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        '''
                        self.db.execute_query(user_query, (
                            matricula, password_hash, 'alumno', nombre, apellidos, email, telefono
                        ))
                        
                        st.success(f"¡Egresado {nombre} {apellidos} registrado exitosamente!")
                        st.info(f"Contraseña temporal: {matricula}")
                        
                    except Exception as e:
                        st.error(f"Error al registrar egresado: {str(e)}")
                else:
                    st.error("Por favor complete los campos obligatorios (*)")
    
    def update_graduate(self):
        """Actualizar egresado existente"""
        st.write("### Actualizar Información de Egresado")
        
        # Buscar egresado
        matricula_search = st.text_input("Ingrese la matrícula del egresado a actualizar:")
        
        if matricula_search:
            graduate = self.db.execute_query(
                "SELECT * FROM alumnos_egresados WHERE matricula = ?", 
                (matricula_search,)
            )
            
            if not graduate.empty:
                grad_data = graduate.iloc[0]
                
                with st.form("update_graduate"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nombre = st.text_input("Nombre", value=grad_data['nombre'])
                        apellidos = st.text_input("Apellidos", value=grad_data['apellidos'])
                        email = st.text_input("Email", value=grad_data['email'] or "")
                        telefono = st.text_input("Teléfono", value=grad_data['telefono'] or "")
                    
                    with col2:
                        promedio = st.number_input("Promedio", value=float(grad_data['promedio'] or 0), min_value=0.0, max_value=10.0, step=0.1)
                        cedula_profesional = st.text_input("Cédula Profesional", value=grad_data['cedula_profesional'] or "")
                        titulo_obtenido = st.checkbox("Título Obtenido", value=bool(grad_data['titulo_obtenido']))
                    
                    submit = st.form_submit_button("Actualizar")
                    
                    if submit:
                        try:
                            query = '''
                                UPDATE alumnos_egresados 
                                SET nombre=?, apellidos=?, email=?, telefono=?, 
                                    promedio=?, cedula_profesional=?, titulo_obtenido=?
                                WHERE matricula=?
                            '''
                            self.db.execute_query(query, (
                                nombre, apellidos, email, telefono, promedio, 
                                cedula_profesional, titulo_obtenido, matricula_search
                            ))
                            st.success("¡Información actualizada exitosamente!")
                        except Exception as e:
                            st.error(f"Error al actualizar: {str(e)}")
            else:
                st.error("No se encontró ningún egresado con esa matrícula")
    
    def delete_graduate(self):
        """Eliminar egresado"""
        st.write("### Eliminar Egresado")
        st.warning("⚠️ Esta acción eliminará permanentemente al egresado del sistema")
        
        matricula_delete = st.text_input("Ingrese la matrícula del egresado a eliminar:")
        
        if matricula_delete:
            graduate = self.db.execute_query(
                "SELECT nombre, apellidos FROM alumnos_egresados WHERE matricula = ?", 
                (matricula_delete,)
            )
            
            if not graduate.empty:
                grad_data = graduate.iloc[0]
                st.write(f"**Egresado encontrado:** {grad_data['nombre']} {grad_data['apellidos']}")
                
                if st.button("🗑️ Confirmar Eliminación", type="secondary"):
                    try:
                        # Eliminar de todas las tablas relacionadas
                        self.db.execute_query("DELETE FROM notificaciones WHERE matricula = ?", (matricula_delete,))
                        self.db.execute_query("DELETE FROM situacion_laboral WHERE matricula = ?", (matricula_delete,))
                        self.db.execute_query("DELETE FROM situacion_academica WHERE matricula = ?", (matricula_delete,))
                        self.db.execute_query("DELETE FROM usuarios WHERE matricula = ?", (matricula_delete,))
                        self.db.execute_query("DELETE FROM alumnos_egresados WHERE matricula = ?", (matricula_delete,))
                        
                        st.success("¡Egresado eliminado exitosamente!")
                    except Exception as e:
                        st.error(f"Error al eliminar: {str(e)}")
            else:
                st.error("No se encontró ningún egresado con esa matrícula")
    
    def search_students(self):
        """Búsqueda avanzada de estudiantes"""
        st.subheader("🔍 Búsqueda de Alumnos Egresados")
        
        search_type = st.radio("Buscar por:", ["Matrícula", "Nombre", "Carrera"])
        
        if search_type == "Matrícula":
            matricula = st.text_input("Ingrese la matrícula:")
            if matricula:
                self.show_student_details(matricula)
        
        elif search_type == "Nombre":
            nombre = st.text_input("Ingrese el nombre o apellido:")
            if nombre:
                results = self.db.execute_query('''
                    SELECT ae.matricula, ae.nombre, ae.apellidos, c.nombre_carrera, ae.fecha_egreso
                    FROM alumnos_egresados ae
                    LEFT JOIN carreras c ON ae.carrera_id = c.id
                    WHERE ae.nombre LIKE ? OR ae.apellidos LIKE ?
                ''', (f'%{nombre}%', f'%{nombre}%'))
                
                if not results.empty:
                    st.dataframe(results)
                else:
                    st.info("No se encontraron resultados")
        
        elif search_type == "Carrera":
            carreras = self.db.execute_query("SELECT DISTINCT nombre_carrera FROM carreras WHERE activa = 1")
            if not carreras.empty:
                carrera = st.selectbox("Seleccione la carrera:", carreras['nombre_carrera'].tolist())
                
                results = self.db.execute_query('''
                    SELECT ae.matricula, ae.nombre, ae.apellidos, ae.fecha_egreso, ae.promedio
                    FROM alumnos_egresados ae
                    JOIN carreras c ON ae.carrera_id = c.id
                    WHERE c.nombre_carrera = ?
                    ORDER BY ae.fecha_egreso DESC
                ''', (carrera,))
                
                if not results.empty:
                    st.dataframe(results)
                else:
                    st.info("No se encontraron egresados para esta carrera")
    
    def show_student_details(self, matricula):
        """Muestra detalles completos de un estudiante"""
        # Información básica
        graduate = self.db.execute_query('''
            SELECT ae.*, c.nombre_carrera, c.facultad
            FROM alumnos_egresados ae
            LEFT JOIN carreras c ON ae.carrera_id = c.id
            WHERE ae.matricula = ?
        ''', (matricula,))
        
        if graduate.empty:
            st.error("No se encontró ningún egresado con esa matrícula")
            return
        
        grad_data = graduate.iloc[0]
        
        st.success(f"**Egresado encontrado:** {grad_data['nombre']} {grad_data['apellidos']}")
        
        # Tabs con información detallada
        tab1, tab2, tab3 = st.tabs(["📋 Información Básica", "🎓 Situación Académica", "💼 Situación Laboral"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Matrícula:** {grad_data['matricula']}")
                st.write(f"**Nombre:** {grad_data['nombre']} {grad_data['apellidos']}")
                st.write(f"**Email:** {grad_data['email'] or 'No registrado'}")
                st.write(f"**Teléfono:** {grad_data['telefono'] or 'No registrado'}")
            
            with col2:
                st.write(f"**Carrera:** {grad_data['nombre_carrera']}")
                st.write(f"**Facultad:** {grad_data['facultad']}")
                st.write(f"**Fecha de Egreso:** {grad_data['fecha_egreso']}")
                st.write(f"**Promedio:** {grad_data['promedio']}")
                st.write(f"**Cédula:** {grad_data['cedula_profesional'] or 'No registrada'}")
        
        with tab2:
            academic = self.db.execute_query(
                "SELECT * FROM situacion_academica WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
                (matricula,)
            )
            
            if not academic.empty:
                acad_data = academic.iloc[0]
                if acad_data['estudia_actualmente']:
                    st.write(f"**Estudia actualmente:** Sí")
                    st.write(f"**Institución:** {acad_data['institucion_actual']}")
                    st.write(f"**Tipo de estudios:** {acad_data['tipo_estudios']}")
                    st.write(f"**Programa:** {acad_data['nombre_programa']}")
                else:
                    st.write("**Estudia actualmente:** No")
            else:
                st.info("No hay información académica registrada")
        
        with tab3:
            laboral = self.db.execute_query(
                "SELECT * FROM situacion_laboral WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
                (matricula,)
            )
            
            if not laboral.empty:
                lab_data = laboral.iloc[0]
                if lab_data['trabaja_actualmente']:
                    st.write(f"**Trabaja actualmente:** Sí")
                    st.write(f"**Empresa:** {lab_data['empresa']}")
                    st.write(f"**Cargo:** {lab_data['cargo']}")
                    st.write(f"**Sector:** {lab_data['sector']}")
                    st.write(f"**Años de experiencia:** {lab_data['anos_experiencia']}")
                else:
                    st.write("**Trabaja actualmente:** No")
            else:
                st.info("No hay información laboral registrada")
    
    def register_new_graduate(self):
        """Registro rápido de nuevos egresados"""
        st.subheader("📝 Registro Rápido de Egresados")
        st.info("Use esta sección para registrar rápidamente nuevos egresados")
        
        # Reutilizar la función de crear egresado
        self.create_graduate()
    
    def manage_careers(self):
        """Gestión de carreras"""
        st.subheader("🎓 Gestión de Carreras")
        
        tab1, tab2 = st.tabs(["Ver Carreras", "Agregar/Editar"])
        
        with tab1:
            careers = self.db.execute_query("SELECT * FROM carreras ORDER BY nombre_carrera")
            if not careers.empty:
                st.dataframe(careers)
            else:
                st.info("No hay carreras registradas")
        
        with tab2:
            with st.form("career_form"):
                nombre_carrera = st.text_input("Nombre de la Carrera*")
                facultad = st.text_input("Facultad*")
                duracion_semestres = st.number_input("Duración (semestres)", min_value=1, max_value=20, value=8)
                activa = st.checkbox("Carrera Activa", value=True)
                
                submit = st.form_submit_button("Agregar Carrera")
                
                if submit and nombre_carrera and facultad:
                    try:
                        query = '''
                            INSERT INTO carreras (nombre_carrera, facultad, duracion_semestres, activa)
                            VALUES (?, ?, ?, ?)
                        '''
                        self.db.execute_query(query, (nombre_carrera, facultad, duracion_semestres, activa))
                        st.success("¡Carrera agregada exitosamente!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    def manage_companies(self):
        """Gestión de empresas"""
        st.subheader("🏢 Gestión de Empresas")
        
        companies = self.db.execute_query("SELECT * FROM empresas ORDER BY fecha_registro DESC")
        if not companies.empty:
            st.dataframe(companies)
        else:
            st.info("No hay empresas registradas")
    
    def manage_job_offers(self):
        """Gestión de ofertas de trabajo"""
        st.subheader("💼 Gestión de Ofertas de Trabajo")
        
        tab1, tab2 = st.tabs(["Ver Ofertas", "Crear Oferta"])
        
        with tab1:
            offers = self.db.execute_query('''
                SELECT ot.*, e.nombre_empresa
                FROM ofertas_trabajo ot
                JOIN empresas e ON ot.empresa_id = e.id
                ORDER BY ot.fecha_publicacion DESC
            ''')
            if not offers.empty:
                st.dataframe(offers)
            else:
                st.info("No hay ofertas registradas")
        
        with tab2:
            companies = self.db.execute_query("SELECT id, nombre_empresa FROM empresas WHERE activa = 1")
            if not companies.empty:
                with st.form("job_offer_form"):
                    company_options = dict(zip(companies['nombre_empresa'], companies['id']))
                    empresa_selected = st.selectbox("Empresa", list(company_options.keys()))
                    empresa_id = company_options[empresa_selected]
                    
                    titulo_puesto = st.text_input("Título del Puesto*")
                    descripcion = st.text_area("Descripción del Puesto")
                    requisitos = st.text_area("Requisitos")
                    salario_ofrecido = st.text_input("Salario Ofrecido")
                    modalidad = st.selectbox("Modalidad", ["presencial", "remoto", "hibrido"])
                    ubicacion = st.text_input("Ubicación")
                    fecha_vencimiento = st.date_input("Fecha de Vencimiento")
                    
                    submit = st.form_submit_button("Crear Oferta")
                    
                    if submit and titulo_puesto:
                        try:
                            query = '''
                                INSERT INTO ofertas_trabajo 
                                (empresa_id, titulo_puesto, descripcion, requisitos, 
                                 salario_ofrecido, modalidad, ubicacion, fecha_vencimiento)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            '''
                            self.db.execute_query(query, (
                                empresa_id, titulo_puesto, descripcion, requisitos,
                                salario_ofrecido, modalidad, ubicacion, fecha_vencimiento
                            ))
                            st.success("¡Oferta creada exitosamente!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                st.warning("No hay empresas registradas. Registre una empresa primero.")
    
    def manage_notifications(self):
        """Gestión de notificaciones"""
        st.subheader("📧 Gestión de Notificaciones")
        
        # Enviar notificación masiva
        with st.form("mass_notification"):
            st.write("### Enviar Notificación Masiva")
            titulo = st.text_input("Título de la Notificación*")
            mensaje = st.text_area("Mensaje*")
            
            # Filtros para destinatarios
            filter_type = st.selectbox("Enviar a:", [
                "Todos los egresados",
                "Por carrera específica",
                "Por año de egreso"
            ])
            
            if filter_type == "Por carrera específica":
                carreras = self.db.execute_query("SELECT DISTINCT nombre_carrera FROM carreras")
                if not carreras.empty:
                    carrera_filter = st.selectbox("Carrera:", carreras['nombre_carrera'].tolist())
            elif filter_type == "Por año de egreso":
                año_filter = st.number_input("Año de egreso:", min_value=2000, max_value=2024, value=2023)
            
            submit = st.form_submit_button("Enviar Notificación")
            
            if submit and titulo and mensaje:
                try:
                    # Obtener destinatarios según filtro
                    if filter_type == "Todos los egresados":
                        recipients = self.db.execute_query("SELECT matricula FROM usuarios WHERE tipo_usuario = 'alumno'")
                    elif filter_type == "Por carrera específica":
                        recipients = self.db.execute_query('''
                            SELECT u.matricula FROM usuarios u
                            JOIN alumnos_egresados ae ON u.matricula = ae.matricula
                            JOIN carreras c ON ae.carrera_id = c.id
                            WHERE c.nombre_carrera = ?
                        ''', (carrera_filter,))
                    else:  # Por año
                        recipients = self.db.execute_query('''
                            SELECT u.matricula FROM usuarios u
                            JOIN alumnos_egresados ae ON u.matricula = ae.matricula
                            WHERE strftime('%Y', ae.fecha_egreso) = ?
                        ''', (str(año_filter),))
                    
                    # Enviar notificaciones
                    for _, recipient in recipients.iterrows():
                        query = '''
                            INSERT INTO notificaciones (matricula, titulo, mensaje)
                            VALUES (?, ?, ?)
                        '''
                        self.db.execute_query(query, (recipient['matricula'], titulo, mensaje))
                    
                    st.success(f"¡Notificación enviada a {len(recipients)} egresados!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    def manage_users(self):
        """Gestión de usuarios del sistema"""
        st.subheader("👥 Gestión de Usuarios")
        
        users = self.db.execute_query('''
            SELECT matricula, nombre, apellidos, email, tipo_usuario, activo, fecha_registro
            FROM usuarios
            ORDER BY fecha_registro DESC
        ''')
        
        if not users.empty:
            st.dataframe(users)
            
            # Activar/Desactivar usuarios
            st.write("### Activar/Desactivar Usuario")
            matricula_toggle = st.text_input("Matrícula del usuario:")
            if matricula_toggle:
                user = self.db.execute_query("SELECT * FROM usuarios WHERE matricula = ?", (matricula_toggle,))
                if not user.empty:
                    current_status = bool(user.iloc[0]['activo'])
                    new_status = not current_status
                    
                    if st.button(f"{'Desactivar' if current_status else 'Activar'} Usuario"):
                        self.db.execute_query("UPDATE usuarios SET activo = ? WHERE matricula = ?", (new_status, matricula_toggle))
                        st.success(f"Usuario {'activado' if new_status else 'desactivado'} exitosamente")
                        st.rerun()
        else:
            st.info("No hay usuarios registrados")