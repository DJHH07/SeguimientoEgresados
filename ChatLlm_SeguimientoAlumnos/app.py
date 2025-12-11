import streamlit as st
from auth import AuthManager
from admin_module import AdminModule
from student_module import StudentModule

# Inicializar componentes
auth = AuthManager()
admin_module = AdminModule()
student_module = StudentModule()

# Configuración inicial
st.set_page_config(page_title="Seguimiento de Egresados - NovaUniversitas", layout="wide")

def main():
    # Si no hay sesión, mostrar login
    if not st.session_state.get("logged_in", False):
        auth.login_page()
    else:
        user = st.session_state.get("user")

        # Barra superior
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar sesión"):
            auth.logout()

        # Redirigir según tipo de usuario
        if user['tipo_usuario'] == "admin":
            admin_module.show_admin_dashboard()
        elif user['tipo_usuario'] == "alumno":
            student_module.show_student_dashboard(user)
        else:
            st.error("Tipo de usuario no reconocido")

if __name__ == "__main__":
    main()