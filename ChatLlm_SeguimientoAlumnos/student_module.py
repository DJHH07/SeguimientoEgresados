import streamlit as st
import pandas as pd
from database import DatabaseManager
from datetime import datetime, date

class StudentModule:
    def __init__(self):
        self.db = DatabaseManager()

    def show_student_dashboard(self, user):
        """Dashboard principal del estudiante"""
        # Verificar si es el primer login (contraseña = matrícula)
        if self.is_first_login(user['matricula']):
            self.force_password_change(user)
            return

        st.title(f"🎓 Bienvenido, {user['nombre']} {user['apellidos']}")
        st.write(f"**Matrícula:** {user['matricula']}")

        # Sidebar con opciones
        st.sidebar.title("Mi Portal")

        menu_options = [
            "📊 Mi Dashboard",
            "👤 Mi Perfil",
            "🎓 Situación Académica",
            "💼 Situación Laboral",
            "📧 Mis Notificaciones",
            "💼 Ofertas de Trabajo",
            "🔐 Cambiar Contraseña"
        ]

        # Inicializar opción por defecto si no existe
        if "student_menu_selection" not in st.session_state:
            st.session_state.student_menu_selection = "📊 Mi Dashboard"

        # Determinar el índice inicial basado en la selección guardada
        default_index = 0
        if st.session_state.student_menu_selection in menu_options:
            default_index = menu_options.index(st.session_state.student_menu_selection)

        # Usar radio buttons en lugar de selectbox
        option = st.sidebar.radio(
            "Seleccione una opción:",
            menu_options,
            index=default_index,
            key="sidebar_menu_radio"
        )

        # Solo actualizar si cambió la selección
        if option != st.session_state.student_menu_selection:
            st.session_state.student_menu_selection = option
            st.rerun()

        if option == "📊 Mi Dashboard":
            self.show_personal_dashboard(user['matricula'])
        elif option == "👤 Mi Perfil":
            self.show_profile(user['matricula'])
        elif option == "🎓 Situación Académica":
            self.manage_academic_situation(user['matricula'])
        elif option == "💼 Situación Laboral":
            self.manage_work_situation(user['matricula'])
        elif option == "📧 Mis Notificaciones":
            self.show_notifications(user['matricula'])
        elif option == "💼 Ofertas de Trabajo":
            self.show_job_offers(user['matricula'])
        elif option == "🔐 Cambiar Contraseña":
            self.change_password(user['matricula'])

    def is_first_login(self, matricula):
        """Verifica si es el primer login (contraseña = matrícula)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE matricula = ?", (matricula,))
        result = cursor.fetchone()
        conn.close()

        if result:
            # Verificar si la contraseña actual es igual a la matrícula
            return self.db.verify_password(matricula, result[0])
        return False

    def force_password_change(self, user):
        """Fuerza el cambio de contraseña en el primer login"""
        st.warning("🔐 **Primer Acceso Detectado**")
        st.info("Por seguridad, debe cambiar su contraseña antes de continuar.")
        st.subheader("Cambio de Contraseña Obligatorio")

        with st.form("force_password_change"):
            st.write(f"**Usuario:** {user['nombre']} {user['apellidos']}")
            st.write(f"**Matrícula:** {user['matricula']}")

            new_password = st.text_input("Nueva Contraseña", type="password", help="Mínimo 6 caracteres")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")

            submit = st.form_submit_button("Cambiar Contraseña")

            if submit:
                if len(new_password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                elif new_password != confirm_password:
                    st.error("Las contraseñas no coinciden")
                elif new_password == user['matricula']:
                    st.error("La nueva contraseña no puede ser igual a su matrícula")
                else:
                    try:
                        # Actualizar contraseña
                        new_password_hash = self.db.hash_password(new_password)
                        query = "UPDATE usuarios SET password = ? WHERE matricula = ?"
                        self.db.execute_query(query, (new_password_hash, user['matricula']))
                        st.success("¡Contraseña cambiada exitosamente!")
                        st.info("Ahora puede acceder a todas las funciones del sistema.")
                        # Pequeña pausa y recargar
                        import time
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al cambiar contraseña: {str(e)}")

    def show_personal_dashboard(self, matricula):
        """Dashboard personal del estudiante"""
        st.subheader("📊 Mi Dashboard Personal")

        # Obtener información básica del egresado
        graduate_info = self.db.execute_query('''
            SELECT ae.*, c.nombre_carrera, c.facultad
            FROM alumnos_egresados ae
            LEFT JOIN carreras c ON ae.carrera_id = c.id
            WHERE ae.matricula = ?
        ''', (matricula,))

        if graduate_info.empty:
            st.error("No se encontró información de egreso. Contacte a Servicios Escolares.")
            return

        grad_data = graduate_info.iloc[0]

        # Información básica en cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Carrera", grad_data['nombre_carrera'])

        with col2:
            st.metric("Promedio", f"{grad_data['promedio']:.2f}" if grad_data['promedio'] else "N/A")

        with col3:
            años_egresado = datetime.now().year - pd.to_datetime(grad_data['fecha_egreso']).year
            st.metric("Años de Egreso", años_egresado)

        with col4:
            # Contar notificaciones no leídas
            notifications = self.db.execute_query(
                "SELECT COUNT(*) as count FROM notificaciones WHERE matricula = ? AND leida = 0",
                (matricula,)
            )
            unread_count = notifications.iloc[0]['count'] if not notifications.empty else 0
            st.metric("Notificaciones", unread_count)

        # Resumen de situación actual
        st.subheader("📋 Resumen de Situación Actual")

        col1, col2 = st.columns(2)

        with col1:
            st.write("### 🎓 Situación Académica")
            academic = self.db.execute_query(
                "SELECT * FROM situacion_academica WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
                (matricula,)
            )

            if not academic.empty:
                acad_data = academic.iloc[0]
                if acad_data['estudia_actualmente']:
                    st.success("✅ Estudiando actualmente")
                    st.write(f"**Institución:** {acad_data['institucion_actual']}")
                    st.write(f"**Programa:** {acad_data['nombre_programa']}")
                else:
                    st.info("📚 No estudia actualmente")
            else:
                st.warning("⚠️ Información académica pendiente de actualizar")

            if st.button("Actualizar Información Académica", key="btn_academic"):
                st.session_state.student_menu_selection = "🎓 Situación Académica"
                st.rerun()

        with col2:
            st.write("### 💼 Situación Laboral")
            work = self.db.execute_query(
                "SELECT * FROM situacion_laboral WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
                (matricula,)
            )

            if not work.empty:
                work_data = work.iloc[0]
                if work_data['trabaja_actualmente']:
                    st.success("✅ Trabajando actualmente")
                    st.write(f"**Empresa:** {work_data['empresa']}")
                    st.write(f"**Cargo:** {work_data['cargo']}")
                else:
                    st.info("💼 No trabaja actualmente")
            else:
                st.warning("⚠️ Información laboral pendiente de actualizar")

            if st.button("Actualizar Información Laboral", key="btn_work"):
                st.session_state.student_menu_selection = "💼 Situación Laboral"
                st.rerun()

        # Ofertas de trabajo recientes
        st.subheader("💼 Ofertas de Trabajo Recientes")
        recent_offers = self.db.execute_query('''
            SELECT ot.titulo_puesto, e.nombre_empresa, ot.modalidad, ot.fecha_publicacion
            FROM ofertas_trabajo ot
            JOIN empresas e ON ot.empresa_id = e.id
            WHERE ot.activa = 1
            ORDER BY ot.fecha_publicacion DESC
            LIMIT 5
        ''')

        if not recent_offers.empty:
            for _, offer in recent_offers.iterrows():
                with st.expander(f"🏢 {offer['titulo_puesto']} - {offer['nombre_empresa']}"):
                    st.write(f"**Modalidad:** {offer['modalidad']}")
                    st.write(f"**Publicado:** {offer['fecha_publicacion']}")
        else:
            st.info("No hay ofertas de trabajo disponibles actualmente")

    def show_profile(self, matricula):
        """Mostrar y editar perfil del estudiante"""
        st.subheader("👤 Mi Perfil")

        # Obtener información completa
        profile = self.db.execute_query('''
            SELECT ae.*, c.nombre_carrera, c.facultad, u.email as user_email, u.telefono as user_telefono
            FROM alumnos_egresados ae
            LEFT JOIN carreras c ON ae.carrera_id = c.id
            LEFT JOIN usuarios u ON ae.matricula = u.matricula
            WHERE ae.matricula = ?
        ''', (matricula,))

        if profile.empty:
            st.error("No se pudo cargar la información del perfil")
            return

        prof_data = profile.iloc[0]

        tab1, tab2 = st.tabs(["Ver Perfil", "Editar Información"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.write("### 📋 Información Personal")
                st.write(f"**Matrícula:** {prof_data['matricula']}")
                st.write(f"**Nombre:** {prof_data['nombre']} {prof_data['apellidos']}")
                st.write(f"**Email:** {prof_data['user_email'] or prof_data['email'] or 'No registrado'}")
                st.write(f"**Teléfono:** {prof_data['user_telefono'] or prof_data['telefono'] or 'No registrado'}")

            with col2:
                st.write("### 🎓 Información Académica")
                st.write(f"**Carrera:** {prof_data['nombre_carrera']}")
                st.write(f"**Facultad:** {prof_data['facultad']}")
                st.write(f"**Fecha de Egreso:** {prof_data['fecha_egreso']}")
                st.write(f"**Promedio:** {prof_data['promedio']}")
                st.write(f"**Cédula Profesional:** {prof_data['cedula_profesional'] or 'No registrada'}")
                st.write(f"**Título Obtenido:** {'Sí' if prof_data['titulo_obtenido'] else 'No'}")

        with tab2:
            st.write("### ✏️ Actualizar Información de Contacto")

            with st.form("update_profile"):
                email = st.text_input("Email", value=prof_data['user_email'] or prof_data['email'] or "")
                telefono = st.text_input("Teléfono", value=prof_data['user_telefono'] or prof_data['telefono'] or "")

                # Información adicional que puede actualizar
                st.write("### 📜 Información Académica Adicional")
                cedula_profesional = st.text_input("Cédula Profesional", value=prof_data['cedula_profesional'] or "")
                titulo_obtenido = st.checkbox("Título Obtenido", value=bool(prof_data['titulo_obtenido']))

                submit = st.form_submit_button("Actualizar Información")

                if submit:
                    try:
                        # Actualizar tabla usuarios
                        self.db.execute_query(
                            "UPDATE usuarios SET email = ?, telefono = ? WHERE matricula = ?",
                            (email, telefono, matricula)
                        )

                        # Actualizar tabla alumnos_egresados
                        self.db.execute_query('''
                            UPDATE alumnos_egresados
                            SET email = ?, telefono = ?, cedula_profesional = ?, titulo_obtenido = ?
                            WHERE matricula = ?
                        ''', (email, telefono, cedula_profesional, titulo_obtenido, matricula))

                        st.success("¡Información actualizada exitosamente!")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar información: {str(e)}")

    def manage_academic_situation(self, matricula):
        """Gestionar situación académica actual"""
        st.subheader("🎓 Mi Situación Académica Actual")

        # Mostrar situación actual
        current_academic = self.db.execute_query(
            "SELECT * FROM situacion_academica WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
            (matricula,)
        )

        if not current_academic.empty:
            st.write("### 📋 Situación Actual")
            acad_data = current_academic.iloc[0]
            if acad_data['estudia_actualmente']:
                st.success("✅ Estudiando actualmente")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Institución:** {acad_data['institucion_actual']}")
                    st.write(f"**Tipo de estudios:** {acad_data['tipo_estudios']}")
                with col2:
                    st.write(f"**Programa:** {acad_data['nombre_programa']}")
                    st.write(f"**Última actualización:** {acad_data['fecha_actualizacion']}")
            else:
                st.info("📚 No estudia actualmente")
                st.write(f"**Última actualización:** {acad_data['fecha_actualizacion']}")

        st.write("### ✏️ Actualizar Situación Académica")

        # Inicializar session state para el radio button con key único
        session_key = f'estudia_actualmente_{matricula}'
        if session_key not in st.session_state:
            if not current_academic.empty:
                st.session_state[session_key] = "Sí" if current_academic.iloc[0]['estudia_actualmente'] else "No"
            else:
                st.session_state[session_key] = "No"

        # Radio button FUERA del formulario
        estudia_actualmente = st.radio(
            "¿Estudia actualmente?",
            ["Sí", "No"],
            key=f"radio_estudia_{matricula}",
            index=0 if st.session_state[session_key] == "Sí" else 1
        )

        # Actualizar session state
        st.session_state[session_key] = estudia_actualmente

        # Ahora el formulario con campos condicionales
        with st.form("academic_situation"):
            if estudia_actualmente == "Sí":
                st.write("#### 📚 Información de Estudios Actuales")
                
                institucion_actual = st.text_input(
                    "Institución donde estudia*",
                    value=current_academic.iloc[0]['institucion_actual'] if not current_academic.empty and current_academic.iloc[0]['institucion_actual'] else ""
                )

                tipo_estudios = st.selectbox(
                    "Tipo de estudios*",
                    ["maestria", "doctorado", "especialidad", "diplomado", "otro"],
                    index=["maestria", "doctorado", "especialidad", "diplomado", "otro"].index(
                        current_academic.iloc[0]['tipo_estudios']
                    ) if not current_academic.empty and current_academic.iloc[0]['tipo_estudios'] else 0
                )

                nombre_programa = st.text_input(
                    "Nombre del programa*",
                    value=current_academic.iloc[0]['nombre_programa'] if not current_academic.empty and current_academic.iloc[0]['nombre_programa'] else ""
                )

                col1, col2 = st.columns(2)
                with col1:
                    fecha_inicio = st.date_input(
                        "Fecha de inicio",
                        value=pd.to_datetime(current_academic.iloc[0]['fecha_inicio']).date() if not current_academic.empty and current_academic.iloc[0]['fecha_inicio'] else date.today()
                    )
                with col2:
                    fecha_fin_estimada = st.date_input(
                        "Fecha estimada de finalización",
                        value=pd.to_datetime(current_academic.iloc[0]['fecha_fin_estimada']).date() if not current_academic.empty and current_academic.iloc[0]['fecha_fin_estimada'] else date.today()
                    )

                # Preguntas adicionales
                st.write("#### 📝 Información Adicional")
                modalidad_estudios = st.selectbox(
                    "Modalidad de estudios",
                    ["Presencial", "En línea", "Mixta"]
                )

                beca_apoyo = st.radio("¿Cuenta con beca o apoyo económico?", ["Sí", "No"], key="beca_radio")

                if beca_apoyo == "Sí":
                    tipo_beca = st.text_input("Tipo de beca o apoyo")

                tiempo_dedicacion = st.selectbox(
                    "Tiempo de dedicación",
                    ["Tiempo completo", "Tiempo parcial", "Fines de semana"]
                )

            else:
                # Si no estudia, preguntar razones
                st.write("#### 📝 Información sobre no estudiar actualmente")
                
                razon_no_estudia = st.selectbox(
                    "Principal razón por la que no estudia",
                    [
                        "Enfocado en trabajo",
                        "Razones económicas",
                        "Razones familiares",
                        "No encontré programa de interés",
                        "Tomando un descanso",
                        "Otro"
                    ]
                )

                planes_futuros = st.radio(
                    "¿Planea estudiar en el futuro?",
                    ["Sí, en los próximos 6 meses", "Sí, en el próximo año", "Sí, pero no tengo fecha definida", "No"],
                    key="planes_futuros_radio"
                )

                if "Sí" in planes_futuros:
                    area_interes = st.text_input("¿En qué área le gustaría estudiar?")

            submit = st.form_submit_button("Actualizar Situación Académica")

            if submit:
                try:
                    if estudia_actualmente == "Sí":
                        if not all([institucion_actual, tipo_estudios, nombre_programa]):
                            st.error("Por favor complete todos los campos obligatorios (*)")
                            return

                        query = '''
                            INSERT INTO situacion_academica 
                            (matricula, estudia_actualmente, institucion_actual, tipo_estudios, 
                             nombre_programa, fecha_inicio, fecha_fin_estimada)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        '''
                        self.db.execute_query(query, (
                            matricula,
                            True,
                            institucion_actual,
                            tipo_estudios,
                            nombre_programa,
                            fecha_inicio,
                            fecha_fin_estimada
                        ))
                    else:
                        query = '''
                            INSERT INTO situacion_academica 
                            (matricula, estudia_actualmente)
                            VALUES (?, ?)
                        '''
                        self.db.execute_query(query, (matricula, False))

                    st.success("¡Situación académica actualizada exitosamente!")
                    # Limpiar session state
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {str(e)}")

    def manage_work_situation(self, matricula):
        """Gestionar situación laboral actual"""
        st.subheader("💼 Mi Situación Laboral Actual")

        # Mostrar situación actual
        current_work = self.db.execute_query(
            "SELECT * FROM situacion_laboral WHERE matricula = ? ORDER BY fecha_actualizacion DESC LIMIT 1",
            (matricula,)
        )

        if not current_work.empty:
            st.write("### 📋 Situación Actual")
            work_data = current_work.iloc[0]
            if work_data['trabaja_actualmente']:
                st.success("✅ Trabajando actualmente")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Empresa:** {work_data['empresa']}")
                    st.write(f"**Cargo:** {work_data['cargo']}")
                    st.write(f"**Sector:** {work_data['sector']}")
                with col2:
                    st.write(f"**Años de experiencia:** {work_data['anos_experiencia']}")
                    st.write(f"**Relacionado con carrera:** {'Sí' if work_data['relacionado_carrera'] else 'No'}")
                    st.write(f"**Última actualización:** {work_data['fecha_actualizacion']}")
            else:
                st.info("💼 No trabaja actualmente")
                st.write(f"**Última actualización:** {work_data['fecha_actualizacion']}")

        st.write("### ✏️ Actualizar Situación Laboral")

        # Inicializar session state para el radio button con key único
        session_key = f'trabaja_actualmente_{matricula}'
        if session_key not in st.session_state:
            if not current_work.empty:
                st.session_state[session_key] = "Sí" if current_work.iloc[0]['trabaja_actualmente'] else "No"
            else:
                st.session_state[session_key] = "No"

        # Radio button FUERA del formulario
        trabaja_actualmente = st.radio(
            "¿Trabaja actualmente?",
            ["Sí", "No"],
            key=f"radio_trabaja_{matricula}",
            index=0 if st.session_state[session_key] == "Sí" else 1
        )

        # Actualizar session state
        st.session_state[session_key] = trabaja_actualmente

        # Ahora el formulario con campos condicionales
        with st.form("work_situation"):
            if trabaja_actualmente == "Sí":
                st.write("#### 💼 Información Laboral Actual")
                
                col1, col2 = st.columns(2)

                with col1:
                    empresa = st.text_input(
                        "Nombre de la empresa*",
                        value=current_work.iloc[0]['empresa'] if not current_work.empty and current_work.iloc[0]['empresa'] else ""
                    )

                    cargo = st.text_input(
                        "Cargo/Puesto*",
                        value=current_work.iloc[0]['cargo'] if not current_work.empty and current_work.iloc[0]['cargo'] else ""
                    )

                    sector = st.selectbox(
                        "Sector*",
                        [
                            "Tecnología", "Salud", "Educación", "Finanzas", "Manufactura",
                            "Servicios", "Gobierno", "Construcción", "Comercio", "Otro"
                        ],
                        index=0 if current_work.empty else max(0, [
                            "Tecnología", "Salud", "Educación", "Finanzas", "Manufactura",
                            "Servicios", "Gobierno", "Construcción", "Comercio", "Otro"
                        ].index(current_work.iloc[0]['sector']) if current_work.iloc[0]['sector'] in [
                            "Tecnología", "Salud", "Educación", "Finanzas", "Manufactura",
                            "Servicios", "Gobierno", "Construcción", "Comercio", "Otro"
                        ] else 0)
                    )

                with col2:
                    salario_rango = st.selectbox(
                        "Rango salarial (mensual)",
                        [
                            "Menos de $10,000",
                            "$10,000 - $20,000",
                            "$20,000 - $30,000",
                            "$30,000 - $50,000",
                            "$50,000 - $75,000",
                            "Más de $75,000"
                        ]
                    )

                    anos_experiencia = st.number_input(
                        "Años de experiencia en esta empresa",
                        min_value=0,
                        max_value=50,
                        value=int(current_work.iloc[0]['anos_experiencia']) if not current_work.empty and current_work.iloc[0]['anos_experiencia'] else 0
                    )

                    fecha_inicio_trabajo = st.date_input(
                        "Fecha de inicio en la empresa",
                        value=pd.to_datetime(current_work.iloc[0]['fecha_inicio_trabajo']).date() if not current_work.empty and current_work.iloc[0]['fecha_inicio_trabajo'] else date.today()
                    )

                relacionado_carrera = st.radio(
                    "¿Su trabajo está relacionado con su carrera?",
                    ["Sí", "No"],
                    key="relacionado_radio",
                    index=0 if not current_work.empty and current_work.iloc[0]['relacionado_carrera'] else 1
                )

                # Preguntas adicionales
                st.write("#### 📝 Información Adicional")
                
                modalidad_trabajo = st.selectbox(
                    "Modalidad de trabajo",
                    ["Presencial", "Remoto", "Híbrido"]
                )

                tipo_contrato = st.selectbox(
                    "Tipo de contrato",
                    ["Tiempo completo", "Tiempo parcial", "Por proyecto", "Freelance", "Prácticas"]
                )

                satisfaccion_trabajo = st.select_slider(
                    "Nivel de satisfacción con su trabajo actual",
                    options=["Muy insatisfecho", "Insatisfecho", "Neutral", "Satisfecho", "Muy satisfecho"],
                    value="Satisfecho"
                )

                busca_otro_trabajo = st.radio(
                    "¿Está buscando otro trabajo actualmente?",
                    ["Sí", "No"],
                    key="busca_trabajo_radio"
                )

            else:
                # Si no trabaja
                st.write("#### 📝 Información sobre situación laboral")
                
                razon_no_trabaja = st.selectbox(
                    "Principal razón por la que no trabaja",
                    [
                        "Buscando trabajo",
                        "Estudiando tiempo completo",
                        "Razones familiares",
                        "Razones de salud",
                        "Emprendiendo negocio propio",
                        "Tomando un descanso",
                        "Otro"
                    ]
                )

                tiempo_buscando = st.selectbox(
                    "¿Cuánto tiempo lleva buscando trabajo?",
                    [
                        "No estoy buscando",
                        "Menos de 1 mes",
                        "1-3 meses",
                        "3-6 meses",
                        "6-12 meses",
                        "Más de 1 año"
                    ]
                )

                experiencia_previa = st.radio(
                    "¿Ha trabajado anteriormente?",
                    ["Sí", "No"],
                    key="experiencia_previa_radio"
                )

                if experiencia_previa == "Sí":
                    ultimo_trabajo = st.text_input("Último trabajo/empresa")
                    tiempo_ultimo_trabajo = st.text_input("¿Cuánto tiempo trabajó ahí?")

            submit = st.form_submit_button("Actualizar Situación Laboral")

            if submit:
                try:
                    if trabaja_actualmente == "Sí":
                        if not all([empresa, cargo, sector]):
                            st.error("Por favor complete todos los campos obligatorios (*)")
                            return

                        query = '''
                            INSERT INTO situacion_laboral 
                            (matricula, trabaja_actualmente, empresa, cargo, sector, 
                             salario_rango, anos_experiencia, fecha_inicio_trabajo, relacionado_carrera)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        '''
                        self.db.execute_query(query, (
                            matricula,
                            True,
                            empresa,
                            cargo,
                            sector,
                            salario_rango,
                            anos_experiencia,
                            fecha_inicio_trabajo,
                            relacionado_carrera == "Sí"
                        ))
                    else:
                        query = '''
                            INSERT INTO situacion_laboral 
                            (matricula, trabaja_actualmente)
                            VALUES (?, ?)
                        '''
                        self.db.execute_query(query, (matricula, False))

                    st.success("¡Situación laboral actualizada exitosamente!")
                    # Limpiar session state
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {str(e)}")

    def show_notifications(self, matricula):
        """Mostrar notificaciones del estudiante"""
        st.subheader("📧 Mis Notificaciones")

        # Obtener notificaciones
        notifications = self.db.execute_query('''
            SELECT n.*, ot.titulo_puesto, e.nombre_empresa
            FROM notificaciones n
            LEFT JOIN ofertas_trabajo ot ON n.oferta_id = ot.id
            LEFT JOIN empresas e ON ot.empresa_id = e.id
            WHERE n.matricula = ?
            ORDER BY n.fecha_envio DESC
        ''', (matricula,))

        if notifications.empty:
            st.info("📭 No tienes notificaciones")
            return

        # Tabs para notificaciones leídas y no leídas
        unread = notifications[notifications['leida'] == 0]
        read = notifications[notifications['leida'] == 1]

        tab1, tab2 = st.tabs([f"📬 No Leídas ({len(unread)})", f"📭 Leídas ({len(read)})"])

        with tab1:
            if not unread.empty:
                for _, notif in unread.iterrows():
                    with st.expander(f"🔔 {notif['titulo']}", expanded=True):
                        st.write(f"**Fecha:** {notif['fecha_envio']}")
                        st.write(f"**Mensaje:** {notif['mensaje']}")
                        if notif['oferta_id']:
                            st.write(f"**Oferta relacionada:** {notif['titulo_puesto']} - {notif['nombre_empresa']}")
                        if st.button(f"Marcar como leída", key=f"read_{notif['id']}"):
                            self.db.execute_query(
                                "UPDATE notificaciones SET leida = 1 WHERE id = ?",
                                (notif['id'],)
                            )
                            st.rerun()
            else:
                st.info("✅ No tienes notificaciones pendientes")

        with tab2:
            if not read.empty:
                for _, notif in read.iterrows():
                    with st.expander(f"📖 {notif['titulo']}"):
                        st.write(f"**Fecha:** {notif['fecha_envio']}")
                        st.write(f"**Mensaje:** {notif['mensaje']}")
                        if notif['oferta_id']:
                            st.write(f"**Oferta relacionada:** {notif['titulo_puesto']} - {notif['nombre_empresa']}")
            else:
                st.info("No tienes notificaciones leídas")

        # Botón para marcar todas como leídas
        if not unread.empty:
            if st.button("📖 Marcar todas como leídas"):
                self.db.execute_query(
                    "UPDATE notificaciones SET leida = 1 WHERE matricula = ? AND leida = 0",
                    (matricula,)
                )
                st.success("Todas las notificaciones han sido marcadas como leídas")
                import time
                time.sleep(1)
                st.rerun()

    def show_job_offers(self, matricula):
        """Mostrar ofertas de trabajo disponibles"""
        st.subheader("💼 Ofertas de Trabajo Disponibles")

        # Filtros
        col1, col2, col3 = st.columns(3)

        with col1:
            modalidad_filter = st.selectbox(
                "Filtrar por modalidad",
                ["Todas", "presencial", "remoto", "hibrido"],
                key="filter_modalidad_job"
            )

        with col2:
            # Obtener sectores únicos
            sectors = self.db.execute_query('''
                SELECT DISTINCT e.sector
                FROM empresas e
                JOIN ofertas_trabajo ot ON e.id = ot.empresa_id
                WHERE ot.activa = 1 AND e.sector IS NOT NULL
            ''')
            sector_options = ["Todos"] + (sectors['sector'].tolist() if not sectors.empty else [])
            sector_filter = st.selectbox("Filtrar por sector", sector_options, key="filter_sector_job")

        with col3:
            fecha_filter = st.selectbox(
                "Filtrar por fecha",
                ["Todas", "Última semana", "Último mes", "Últimos 3 meses"],
                key="filter_fecha_job"
            )

        # Construir query con filtros
        base_query = '''
            SELECT ot.*, e.nombre_empresa, e.sector, e.email_contacto
            FROM ofertas_trabajo ot
            JOIN empresas e ON ot.empresa_id = e.id
            WHERE ot.activa = 1
        '''
        params = []

        if modalidad_filter != "Todas":
            base_query += " AND ot.modalidad = ?"
            params.append(modalidad_filter)

        if sector_filter != "Todos":
            base_query += " AND e.sector = ?"
            params.append(sector_filter)

        if fecha_filter != "Todas":
            if fecha_filter == "Última semana":
                base_query += " AND ot.fecha_publicacion >= date('now', '-7 days')"
            elif fecha_filter == "Último mes":
                base_query += " AND ot.fecha_publicacion >= date('now', '-1 month')"
            elif fecha_filter == "Últimos 3 meses":
                base_query += " AND ot.fecha_publicacion >= date('now', '-3 months')"

        base_query += " ORDER BY ot.fecha_publicacion DESC"

        offers = self.db.execute_query(base_query, params if params else None)

        if offers.empty:
            st.info("📭 No hay ofertas de trabajo que coincidan con los filtros seleccionados")
            return

        st.write(f"**{len(offers)} ofertas encontradas**")

        # Mostrar ofertas
        for _, offer in offers.iterrows():
            with st.expander(f"🏢 {offer['titulo_puesto']} - {offer['nombre_empresa']}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Empresa:** {offer['nombre_empresa']}")
                    st.write(f"**Sector:** {offer['sector']}")
                    st.write(f"**Modalidad:** {offer['modalidad']}")
                    st.write(f"**Ubicación:** {offer['ubicacion'] or 'No especificada'}")

                with col2:
                    st.write(f"**Salario:** {offer['salario_ofrecido'] or 'No especificado'}")
                    st.write(f"**Publicado:** {offer['fecha_publicacion']}")
                    st.write(f"**Vence:** {offer['fecha_vencimiento'] or 'No especificado'}")
                    st.write(f"**Contacto:** {offer['email_contacto']}")

                if offer['descripcion']:
                    st.write("**Descripción:**")
                    st.write(offer['descripcion'])

                if offer['requisitos']:
                    st.write("**Requisitos:**")
                    st.write(offer['requisitos'])

                # Botón para mostrar interés
                # if st.button(f"💌 Mostrar Interés", key=f"interest_{offer['id']}"):
                #     try:
                #         admin_notification = f"El egresado {matricula} mostró interés en la oferta: {offer['titulo_puesto']} de {offer['nombre_empresa']}"
                #         self.db.execute_query('''
                #             INSERT INTO notificaciones (matricula, titulo, mensaje, oferta_id)
                #             VALUES (?, ?, ?, ?)
                #         ''', ("ADMIN001", "Interés en Oferta de Trabajo", admin_notification, offer['id']))
                #         st.success("✅ Se ha notificado tu interés en esta oferta a Servicios Escolares")
                #     except Exception as e:
                #         st.error(f"Error al enviar notificación: {str(e)}")

    def change_password(self, matricula):
        """Cambiar contraseña del usuario"""
        st.subheader("🔐 Cambiar Contraseña")

        with st.form("change_password"):
            current_password = st.text_input("Contraseña Actual", type="password")
            new_password = st.text_input("Nueva Contraseña", type="password", help="Mínimo 6 caracteres")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")

            submit = st.form_submit_button("Cambiar Contraseña")

            if submit:
                if not all([current_password, new_password, confirm_password]):
                    st.error("Por favor complete todos los campos")
                elif len(new_password) < 6:
                    st.error("La nueva contraseña debe tener al menos 6 caracteres")
                elif new_password != confirm_password:
                    st.error("Las contraseñas nuevas no coinciden")
                elif new_password == matricula:
                    st.error("La nueva contraseña no puede ser igual a su matrícula")
                else:
                    # Verificar contraseña actual
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT password FROM usuarios WHERE matricula = ?", (matricula,))
                    result = cursor.fetchone()
                    conn.close()

                    if result and self.db.verify_password(current_password, result[0]):
                        try:
                            # Actualizar contraseña
                            new_password_hash = self.db.hash_password(new_password)
                            self.db.execute_query(
                                "UPDATE usuarios SET password = ? WHERE matricula = ?",
                                (new_password_hash, matricula)
                            )
                            st.success("¡Contraseña cambiada exitosamente!")
                        except Exception as e:
                            st.error(f"Error al cambiar contraseña: {str(e)}")
                    else:
                        st.error("La contraseña actual es incorrecta")