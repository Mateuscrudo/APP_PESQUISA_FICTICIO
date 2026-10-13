"""Cria bancos e desenhos fictícios sem ler arquivos operacionais."""
from pathlib import Path
from contextlib import closing
import sqlite3
import pandas as pd
from PIL import Image,ImageDraw

def gerar_demo():
    root=Path(__file__).resolve().parent
    bases=root/'Bases';assets=root/'assets'
    names=['base_agua.db','base_esgoto.db','base_obra.db','historico_visitas.db']
    if any((bases/n).exists() for n in names) or any((assets/n).exists() for n in ['demo_agua.png','demo_esgoto.png']):
        raise FileExistsError('Dados fictícios já existem; não serão sobrescritos.')
    bases.mkdir(parents=True,exist_ok=True);assets.mkdir(parents=True,exist_ok=True)
    for name,color,label in [('demo_agua.png','#1479b8','AGUA - IMAGEM FICTICIA'),('demo_esgoto.png','#18856b','ESGOTO - IMAGEM FICTICIA')]:
        image=Image.new('RGB',(640,400),'#eef3f8');draw=ImageDraw.Draw(image)
        draw.rectangle((140,160,500,330),fill=color)
        draw.polygon([(100,160),(320,50),(540,160)],fill='#223a52')
        draw.rectangle((285,230,355,330),fill='#eef3f8')
        draw.text((30,365),label,fill='#223a52');image.save(assets/name)
    agua=[];esgoto=[];obra=[];hist=[]
    for i in range(1,4):
        mat=f'DEM100{i}';nome=f'Pessoa Fictícia {chr(64+i)}';end=f'Rua Fictícia {i}, {i*10}'
        agua.append({'matricula':mat,'endereco':end,'bairro':'Bairro Exemplo',
            'status_adesao':'ADESÃO EXECUTADA','data_adesao':f'2026-10-0{i}',
            'equipe_exec':f'Equipe Fictícia {i}','agente':f'Agente Fictício {i}',
            'nome_cliente':nome,'telefone':'00000000000','quantidade_visitas':i+1,
            'origem_dos_dados':'DEMONSTRAÇÃO','latitude':None,'longitude':None,
            'origem_adesao':'BASE_AG','data_origem_adesao':f'2026-10-0{i}',
            'link_appdeep':None,'registro_appdeep':None})
        esgoto.append({'Matrícula':mat,'Endereço':end,'Nome do Morador':nome,
            'Bairro':'Bairro Exemplo','Data de Execução':f'2026-10-0{i}',
            'Quantidade de Visitas':i,'status':'Adesão executada',
            'Agente Responsável':f'Agente Fictício {i}','Origem dos Dados':'DEMONSTRAÇÃO',
            'origem_adesao':'ROTEIRO','data_origem_adesao':f'2026-10-0{i}',
            'link_appdeep':None,'registro_appdeep':None})
        obra.append({'Número OS':900000+i,'MATRICULA':mat,'PDE':f'PDE-DEMO-{i}',
            'HD_WFM':f'A26LM90000{i}','HD':f'A26LM90000{i}','ORIGEM_HD':'WFM',
            'DATA_EXECUCAO':f'2026-10-0{i} 10:00:00','Endereço':end,'Número':i*10,
            'Complemento':'Casa fictícia','Bairro':'Bairro Exemplo',
            'Notas de Acatamento':f'ADESAO {mat}',
            'Nota Execução/Não Execução':'Execução fictícia',
            'ARQUIVO':'WFM_FICTICIO.xlsx','ABA':'WFM_DEMO'})
        hist.append({'Matrícula':mat,'Data':f'2026-10-0{i}',
            'Origem':'DEMONSTRAÇÃO','Agente':f'Agente Fictício {i}',
            'Status':'Adesão executada','Visitas':1,'Tentativa':'EXECUÇÃO'})
    def banco(name,tables):
        with closing(sqlite3.connect(bases/name)) as con:
            for table,df in tables.items():df.to_sql(table,con,index=False,if_exists='replace')
            con.commit()
    banco('base_agua.db',{'agua':pd.DataFrame(agua),
        'fotos':pd.DataFrame({'matricula':[f'DEM100{i}' for i in range(1,4)],'foto_1':['assets/demo_agua.png']*3})})
    banco('base_esgoto.db',{'base_consolidada':pd.DataFrame(esgoto),
        'fotos_normalizadas':pd.DataFrame({'Matrícula':[f'DEM100{i}' for i in range(1,4)],
            'Origem':['DEMONSTRAÇÃO']*3,'Tipo':['Desenho fictício']*3,'Data do Registro':['2026-10-01']*3,'URL':['assets/demo_esgoto.png']*3}),
        'historico_visitas':pd.DataFrame(hist)})
    banco('base_obra.db',{'adesoes':pd.DataFrame(obra)})
    banco('historico_visitas.db',{'historico_visitas':pd.DataFrame({
        'matricula':[f'DEM100{i}' for i in range(1,4)],'data_execucao':[f'2026-10-0{i}' for i in range(1,4)],
        'equipe':['Equipe Fictícia']*3,'status_aplicado':['Adesão executada']*3})})
    print('Quatro bancos e duas imagens inteiramente fictícios criados.')

if __name__=='__main__':gerar_demo()
