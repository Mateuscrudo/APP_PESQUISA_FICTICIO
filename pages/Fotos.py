from pathlib import Path
import streamlit as st
from database import buscar_fotos_agua, buscar_fotos_esgoto

st.set_page_config(page_title="Fotos fictícias", page_icon="📷", layout="wide")
st.title("Imagens de demonstração")
st.caption("Desenhos locais criados para este exemplo. Nenhuma foto operacional é acessada.")
matricula = st.session_state.get('matricula_consulta')
if st.button('Voltar para consulta'):
    st.switch_page('EAapp.py')
if not matricula:
    st.info('Selecione uma matrícula na consulta.')
    st.stop()
root = Path(__file__).resolve().parent.parent
for titulo, itens in [('Água', buscar_fotos_agua(matricula)), ('Esgoto', buscar_fotos_esgoto(matricula))]:
    st.subheader(titulo)
    for item in itens:
        nome = item.get('url') if isinstance(item,dict) else item
        p = (root / nome).resolve()
        if p.is_relative_to(root / 'assets') and p.is_file():
            st.image(str(p), caption=f'{titulo} — imagem fictícia', width=450)
    if not itens:
        st.info('Nenhuma imagem para esta matrícula.')
