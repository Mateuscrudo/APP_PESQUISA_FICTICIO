from pathlib import Path
import unittest
import database
from cards import campos_card,gerar_png
from streamlit.testing.v1 import AppTest

class AppDemoTests(unittest.TestCase):
    def test_consultas_e_fotos(self):
        for mat in ['DEM1001','DEM1002','DEM1003']:
            self.assertEqual(len(database.consultar_agua(mat)),1)
            self.assertEqual(len(database.consultar_esgoto(mat)),1)
            self.assertEqual(len(database.consultar_obra(mat)),1)
            self.assertEqual(database.buscar_fotos_agua(mat),['assets/demo_agua.png'])
        self.assertEqual(len(database.consultar_agua_por_endereco('Pessoa Ficticia')),3)
        self.assertTrue(database.consultar_agua('INEXISTENTE').empty)

    def test_card_png(self):
        row=database.consultar_agua('DEM1001').iloc[0]
        self.assertTrue(gerar_png('Água',campos_card('Água','DEM1001',row)).startswith(b'\x89PNG'))

    def test_pesquisa_historico_e_fotos(self):
        root=Path(__file__).resolve().parents[1]
        at=AppTest.from_file(str(root/'EAapp.py'),default_timeout=20).run()
        self.assertFalse(at.exception)
        at.text_input[0].set_value('DEM1001').run()
        self.assertFalse(at.exception)
        self.assertFalse(at.error)
        at.session_state['matricula_consulta']='DEM1001'
        at.switch_page('pages/historico.py').run()
        self.assertFalse(at.exception)
        self.assertFalse(at.error)
        at.switch_page('pages/Fotos.py').run()
        self.assertFalse(at.exception)
        self.assertFalse(at.error)

if __name__=='__main__':unittest.main()
