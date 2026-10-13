# APP_PESQUISA_FICTICIO

Cópia independente do aplicativo de consulta de Água, Esgoto e Obra, preparada exclusivamente com dados sintéticos. O APP_MAT_SEARCH interno não foi alterado.

## Executar

Python 3.14 foi usado na validação local.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run EAapp.py
```

Os quatro bancos em Bases já estão incluídos e contêm somente registros inventados. Pesquise `DEM1001`, `DEM1002`, `DEM1003`, `Rua Fictícia` ou `Pessoa Fictícia`. O resultado permite ver Água, Esgoto, Obra, histórico, desenhos de fotos e baixar cards PNG.

## Dados e diferenças da instalação interna

- `gerar_demo.py` cria os quatro bancos e duas imagens locais sem ler arquivos externos; recusa sobrescrever saídas existentes.
- Três pessoas fictícias, matrículas inventadas, telefone `00000000000` e endereços explicitamente fictícios. Não há coordenadas residenciais.
- As fotos são desenhos feitos localmente, exibidos por `pages/Fotos.py`; não há consulta a galerias operacionais.
- Geocodificação desativada nesta cópia. Links de registros são vazios. Não existe integração com serviços de origem ou atualização dos bancos internos.
- Não há senha ou arquivo secrets copiado. A demonstração é aberta por conter somente dados inventados.
- Cards mantêm o download PNG e o link opcional de compartilhamento de texto no WhatsApp. Nada é enviado automaticamente.
- `database.py`, `cards.py` e a página de histórico preservam o código da cópia local; a consulta principal recebeu identificação de demonstração.

## Estrutura

`EAapp.py`, `database.py`, `cards.py`, `pages/`, `Bases/`, `assets/`, `gerar_demo.py`, `tests/`, `requirements.txt`.

## Verificação

```powershell
python -m unittest discover -s tests -v
```

Os testes verificam consultas, busca textual, fotos, cards e navegação com AppTest, sem iniciar servidor. Veja [VALIDACAO.md](VALIDACAO.md) e [origem dos dados](docs/DADOS_FICTICIOS.md).
