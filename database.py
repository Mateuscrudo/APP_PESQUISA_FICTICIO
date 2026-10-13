
from pathlib import Path
import sqlite3
import pandas as pd


# =========================================================
# CONFIGURAÇÃO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_DIR = BASE_DIR / "Bases"

DB_AGUA = DB_DIR / "base_agua.db"
DB_ESGOTO = DB_DIR / "base_esgoto.db"
DB_OBRA = DB_DIR / "base_obra.db"


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def normalizar_matricula(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip().upper()


def consultar_sqlite(caminho_db, tabela):

    if not caminho_db.exists():
        raise FileNotFoundError(
            f"Banco não encontrado: {caminho_db}"
        )

    with sqlite3.connect(caminho_db) as conn:

        return pd.read_sql_query(
            f'SELECT * FROM "{tabela}"',
            conn
        )


def consultar_fotos_matricula(caminho_db, tabela, coluna, matricula):
    if not caminho_db.exists():
        return pd.DataFrame()
    # Identificadores são constantes internas; matrícula é um parâmetro.
    query = (
        f'SELECT * FROM "{tabela}" '
        f'WHERE UPPER(TRIM(CAST("{coluna}" AS TEXT))) = ?'
    )
    with sqlite3.connect(caminho_db) as conn:
        return pd.read_sql_query(
            query, conn, params=(normalizar_matricula(matricula),)
        )


def buscar_fotos_agua(matricula):

    if not DB_AGUA.exists():
        return []

    df = consultar_fotos_matricula(
        DB_AGUA, "fotos", "matricula", matricula
    )

    if df.empty:
        return []

    df["matricula"] = (
        df["matricula"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    resultado = df[
        df["matricula"] ==
        normalizar_matricula(matricula)
    ]

    fotos = []

    for i in range(1, 8):

        coluna = f"foto_{i}"

        if coluna not in resultado.columns:
            continue

        for valor in resultado[coluna]:

            if pd.notna(valor):

                url = str(valor).strip()

                if url:
                    fotos.append(url)

    return fotos[:7]


def buscar_fotos_esgoto(matricula):

    if not DB_ESGOTO.exists():
        return []

    df = consultar_fotos_matricula(
        DB_ESGOTO, "fotos_normalizadas", "Matrícula", matricula
    )

    if df.empty:
        return []

    df["Matrícula"] = (
        df["Matrícula"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    resultado = df[
        df["Matrícula"] ==
        normalizar_matricula(matricula)
    ].copy()

    if resultado.empty:
        return []

    fotos = []

    for _, linha in resultado.iterrows():

        url = linha.get("URL")
        tipo = linha.get("Tipo")

        if pd.isna(url):
            continue

        url = str(url).strip()

        if not url:
            continue

        if pd.isna(tipo):
            tipo = "Foto"

        tipo = str(tipo).strip()

        fotos.append({
            "tipo": tipo,
            "url": url
        })

    # Esgoto pode ter até 30 fotos
    return fotos[:30]


def adicionar_colunas_fotos(df, fotos, limite=7):

    if df.empty:
        return df

    # Garante que as colunas possam receber objetos/dicionários
    for i in range(1, limite + 1):

        coluna = f"foto_{i}"

        if coluna not in df.columns:
            df[coluna] = None

        df[coluna] = df[coluna].astype(object)

    # Se não houver fotos, retorna normalmente
    if not fotos:
        return df

    # Como a consulta normalmente retorna uma única matrícula,
    # usamos o primeiro registro.
    indice = df.index[0]

    for i, foto in enumerate(
        fotos[:limite],
        start=1
    ):

        coluna = f"foto_{i}"

        # .at permite armazenar dicionários dentro da célula
        df.at[indice, coluna] = foto

    return df

# =========================================================
# ÁGUA
# =========================================================

def consultar_agua(matricula):

    matricula = normalizar_matricula(matricula)

    df = consultar_sqlite(
        DB_AGUA,
        "agua"
    )

    if df.empty:
        return df

    df["matricula"] = (
        df["matricula"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    resultado = df[
        df["matricula"] == matricula
    ].copy()

    if resultado.empty:
        return resultado

    # -----------------------------------------------------
    # ADAPTAÇÃO PARA O APP
    # -----------------------------------------------------

    resultado = resultado.rename(
        columns={
            "matricula": "Matrícula",
            "endereco": "Endereço",
            "bairro": "Comunidade",
            "status_adesao": "Status Adesão",
            "data_adesao": "Data Adesão",
            "equipe_exec": "Equipe Exec.",
            "agente": "Agente",
            "nome_cliente": "Nome Cliente",
            "telefone": "Telefone",
            "quantidade_visitas": "Quantidade de Visitas",
            "origem_dos_dados": "Origem dos Dados",
        }
    )

    # -----------------------------------------------------
    # FOTOS
    # -----------------------------------------------------

    fotos = buscar_fotos_agua(matricula)

    resultado = adicionar_colunas_fotos(
        resultado,
        fotos
    )

    return resultado


# =========================================================
# ESGOTO
# =========================================================

def consultar_esgoto(matricula):

    matricula = normalizar_matricula(matricula)

    df = consultar_sqlite(
        DB_ESGOTO,
        "Base_Consolidada"
    )

    if df.empty:
        return df

    df["Matrícula"] = (
        df["Matrícula"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    resultado = df[
        df["Matrícula"] == matricula
    ].copy()

    if resultado.empty:
        return resultado

    # -----------------------------------------------------
    # ADAPTAÇÃO PARA O APP
    # -----------------------------------------------------

    resultado = resultado.rename(
        columns={
            "Matrícula": "matricula",
            "Endereço": "endereco",
            "Nome do Morador": "nome_completo",
            "Bairro": "bairro",
            "Data de Execução": "data_execucao_roteiro",
            "Quantidade de Visitas": "quantidade_visitas",
            "status": "Status do Registro",
            "Agente Responsável": "agente_appdeep",
            "Origem dos Dados": "origem_dos_dados",
        }
    )

    # -----------------------------------------------------
    # FOTOS
    # -----------------------------------------------------

    fotos = buscar_fotos_esgoto(matricula)

    resultado = adicionar_colunas_fotos(
        resultado,
        fotos,
        limite=30
    )

    return resultado


# =========================================================
# OBRA
# =========================================================

def consultar_obra(matricula):

    matricula = normalizar_matricula(matricula)

    df = consultar_sqlite(
        DB_OBRA,
        "adesoes"
    )

    if df.empty:
        return df

    df["MATRICULA"] = (
        df["MATRICULA"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    resultado = df[
        df["MATRICULA"] == matricula
    ].copy()

    return resultado

def consultar_agua_por_endereco(busca):
    """Pesquisa parte do endereço ou do nome do cliente na base de água."""
    import unicodedata

    def normalizar_texto(valor):
        if valor is None:
            return ""
        texto = unicodedata.normalize("NFKD", str(valor))
        texto = "".join(
            caractere for caractere in texto
            if not unicodedata.combining(caractere)
        )
        return " ".join(texto.casefold().split())

    termo = normalizar_texto(busca)
    if not termo:
        return pd.DataFrame()

    if not DB_AGUA.exists():
        raise FileNotFoundError(f"Banco não encontrado: {DB_AGUA}")

    with sqlite3.connect(DB_AGUA) as conn:
        conn.create_function("NORMALIZAR_TEXTO", 1, normalizar_texto)
        return pd.read_sql_query(
            """
            SELECT *
            FROM agua
            WHERE instr(NORMALIZAR_TEXTO(endereco), ?) > 0
               OR instr(NORMALIZAR_TEXTO(nome_cliente), ?) > 0
            """,
            conn,
            params=(termo, termo),
        )
