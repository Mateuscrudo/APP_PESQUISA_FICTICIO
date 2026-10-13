import pandas as pd
import streamlit as st  # pyright: ignore[reportMissingImports]
from database import (
    consultar_agua,
    consultar_obra,
    consultar_esgoto,
    consultar_agua_por_endereco
)
from cards import exibir_card
import urllib.parse
import importlib
# Carrega opcionalmente para evitar erro do analisador quando o pacote não
# estiver instalado no ambiente usado pelo editor.
pdk = importlib.import_module("pydeck")


def obter_geocodificador():
    """Retorna o geocodificador quando geopy estiver disponível."""
    try:
        modulo_geopy = importlib.import_module("geopy.geocoders")
        return modulo_geopy.Nominatim
    except (ImportError, AttributeError):
        return None

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="Consulta de Matrícula",
    page_icon="🔎",
    layout="wide"

)

# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>

    .bloco {
        border: 1px solid #666;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .titulo-bloco {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 12px;
    }

    .campo {
        margin-bottom: 6px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TÍTULO
# =========================================================

st.title("🔎 Pesquisa com dados fictícios")
st.info("Demonstração: todos os registros e imagens são inventados. Pesquise DEM1001, DEM1002 ou DEM1003.")


# =========================================================
# GEOCODIFICAÇÃO
# =========================================================

def obter_coordenadas_da_agua(linha):
    """Usa latitude/longitude existentes na base de Água."""

    if linha is None:
        return None, None

    latitude_coluna = next(
        (
            coluna
            for coluna in [
                "latitude",
                "lat",
                "Latitude",
                "LATITUDE",
                "Lat"
            ]
            if coluna in linha.index
        ),
        None
    )

    longitude_coluna = next(
        (
            coluna
            for coluna in [
                "longitude",
                "lon",
                "lng",
                "Longitude",
                "LONGITUDE",
                "Lon",
                "Lng"
            ]
            if coluna in linha.index
        ),
        None
    )

    if latitude_coluna is None or longitude_coluna is None:
        return None, None

    try:

        latitude = pd.to_numeric(
            linha.get(latitude_coluna),
            errors="coerce"
        )

        longitude = pd.to_numeric(
            linha.get(longitude_coluna),
            errors="coerce"
        )

        if pd.isna(latitude) or pd.isna(longitude):
            return None, None

        return float(latitude), float(longitude)

    except (TypeError, ValueError):
        return None, None


@st.cache_data(ttl=60 * 60 * 24 * 30)
def geocodificar_endereco_guaruja(endereco):

    # Endereços inventados não são enviados a serviços de geocodificação.
    return None, None


def obter_localizacao(linha_agua, endereco):

    # 1. PRIORIDADE: coordenadas da Água.
    latitude, longitude = (
        obter_coordenadas_da_agua(
            linha_agua
        )
    )

    if latitude is not None and longitude is not None:
        return latitude, longitude, "Base de Água"

    # 2. FALLBACK: endereço, limitado ao Guarujá.
    latitude, longitude = (
        geocodificar_endereco_guaruja(
            endereco
        )
    )

    if latitude is not None and longitude is not None:
        return latitude, longitude, "Endereço"

    return None, None, None

# =========================================================
# PESQUISA
# =========================================================


valor_inicial = st.session_state.get(
    "matricula_sugerida",
    ""
)

busca = st.text_input(
    "Matrícula, endereço ou nome do morador:",
    value=valor_inicial
)
# =========================================================
# BUSCA POR MATRICULA, NOME OU ENDEREÇO
# =========================================================

matricula = None

if busca:

    busca = busca.strip()

    # -----------------------------------------------------
    # TENTA PRIMEIRO COMO MATRÍCULA
    # -----------------------------------------------------

    resultado_teste = consultar_agua(
        busca
    )

    if not resultado_teste.empty:

        # É uma matrícula válida
        matricula = busca

    else:

        # -------------------------------------------------
        # NÃO É MATRÍCULA → PROCURA PELO ENDEREÇO OU NOME
        # -------------------------------------------------

        resultado_endereco = consultar_agua_por_endereco(
            busca
        )

        if resultado_endereco.empty:

            st.error(
                "❌ Matrícula, endereço ou nome do morador não encontrado."
            )

            st.stop()

        # -------------------------------------------------
        # EXTRAI MATRÍCULAS E NOMES ENCONTRADOS
        # -------------------------------------------------

        resultado_endereco = resultado_endereco.copy()

        def texto_valido(valor, padrao=""):
            if pd.isna(valor):
                return padrao
            texto = str(valor).strip()
            if not texto or texto.lower() in {"nan", "none"}:
                return padrao
            return texto

        resultado_endereco["_matricula_normalizada"] = (
            resultado_endereco["matricula"]
            .map(lambda valor: texto_valido(valor).upper())
        )

        matriculas_encontradas = list(
            dict.fromkeys(
                matricula
                for matricula in resultado_endereco["_matricula_normalizada"]
                if matricula
            )
        )

        coluna_nome = next(
            (
                coluna
                for coluna in ("Nome Cliente", "nome_cliente")
                if coluna in resultado_endereco.columns
            ),
            None,
        )
        if coluna_nome:
            resultado_endereco["_nome_cliente"] = (
                resultado_endereco[coluna_nome].map(texto_valido)
            )
        else:
            resultado_endereco["_nome_cliente"] = ""

        def obter_nome_morador(matricula_opcao):
            registros = resultado_endereco[
                resultado_endereco["_matricula_normalizada"] == matricula_opcao
            ]
            for nome in registros["_nome_cliente"]:
                if nome:
                    return nome
            return "Não informado"

        def obter_endereco_encontrado(matricula_opcao):
            registros = resultado_endereco[
                resultado_endereco["_matricula_normalizada"] == matricula_opcao
            ]
            for coluna in ("Endereço", "endereco"):
                if coluna in registros.columns:
                    for endereco in registros[coluna]:
                        endereco_valido = texto_valido(endereco)
                        if endereco_valido:
                            return endereco_valido
            return texto_valido(busca, "Endereço não informado")

        # -------------------------------------------------
        # UMA ÚNICA MATRÍCULA
        # -------------------------------------------------

        if len(matriculas_encontradas) == 1:

            matricula_encontrada = (
                matriculas_encontradas[0]
            )

            nome_morador = obter_nome_morador(matricula_encontrada)
            endereco_encontrado = obter_endereco_encontrado(matricula_encontrada)

            st.info(
                f"📍 **Matrícula:** {matricula_encontrada}\n\n"
                f"👤 **Morador:** {nome_morador}\n\n"
                f"🏠 **Endereço:** {endereco_encontrado}"
            )

            if st.button(
                "➕ Usar esta matrícula",
                width="stretch"
            ):

                st.session_state[
                    "matricula_sugerida"
                ] = matricula_encontrada

                st.rerun()

            # IMPORTANTE:
            # não continua para Água/Esgoto/Obra
            st.stop()

        # -------------------------------------------------
        # MAIS DE UMA MATRÍCULA
        # -------------------------------------------------

        elif len(matriculas_encontradas) > 1:

            st.warning(
                "⚠️ Encontramos mais de uma matrícula "
                "para esse endereço."
            )

            for matricula_opcao in matriculas_encontradas:

                nome_morador = obter_nome_morador(matricula_opcao)
                endereco_encontrado = obter_endereco_encontrado(matricula_opcao)

                st.write(
                    f"**Matrícula:** {matricula_opcao}  |  "
                    f"**Morador:** {nome_morador}  |  "
                    f"**Endereço:** {endereco_encontrado}"
                )

                if st.button(
                    f"➕ Usar {matricula_opcao}",
                    key=f"mat_{matricula_opcao}",
                    width="stretch"
                ):

                    st.session_state[
                        "matricula_sugerida"
                    ] = matricula_opcao

                    st.rerun()

            # IMPORTANTE:
            # não continua para Água/Esgoto/Obra
            st.stop()

        # -------------------------------------------------
        # ENDEREÇO SEM MATRÍCULA
        # -------------------------------------------------

        else:

            st.warning(
                "⚠️ Endereço encontrado, "
                "mas nenhuma matrícula foi identificada."
            )

            st.stop()
# =========================================================
# PESQUISA
# =========================================================

    # -----------------------------------------------------
    # CONSULTA ÁGUA
    # -----------------------------------------------------

    try:

        resultado_agua = consultar_agua(
            matricula
        )

    except Exception as e:

        st.error(
            "❌ Não foi possível consultar a base de Água."
        )

        resultado_agua = pd.DataFrame()

        


    # -----------------------------------------------------
    # CONSULTA ESGOTO
    # -----------------------------------------------------

    try:

        resultado_esgoto = consultar_esgoto(
            matricula
        )

    except Exception as e:

        st.error(
            f"❌ Erro na consulta de Esgoto: {type(e).__name__}: {e}"
        )

        resultado_esgoto = pd.DataFrame()


    # -----------------------------------------------------
    # CONSULTA OBRA
    # -----------------------------------------------------

    try:

        resultado_obra = consultar_obra(
            matricula
        )

    except Exception as e:

        st.warning(
            "❌ Não foi possível consultar a base de Obra."
        )

        resultado_obra = pd.DataFrame()


    # =====================================================
    # VERIFICAÇÃO
    # =====================================================

    if (
        resultado_agua.empty
        and resultado_esgoto.empty
        and resultado_obra.empty
    ):

        st.error(
            "❌ Matrícula não encontrada."
        )

        st.stop()


    # =====================================================
    # DADOS DA ÁGUA
    # =====================================================

    linha_agua = None

    if not resultado_agua.empty:
        linha_agua = resultado_agua.iloc[0]


    # =====================================================
    # DADOS GERAIS
    # =====================================================

    with st.container(border=True):

        st.subheader("📋 Informações gerais")

        col1, col2 = st.columns([2, 1])

        # -------------------------------------------------
        # INFORMAÇÕES GERAIS
        # -------------------------------------------------

        with col1:

            if linha_agua is not None:

                nome = linha_agua.get(
                    "Nome Cliente",
                    "Não informado"
                )

                endereco = linha_agua.get(
                    "Endereço",
                    "Não informado"
                )

                bairro = linha_agua.get(
                    "Comunidade",
                    "Não informado"
                )
                telefone = linha_agua.get(
                    "Telefone",
                    "Não informado"
                )
                
                st.write(
                    f"**Nome do morador:** {nome}"
                )

                st.write(
                    f"**Endereço:** {endereco}"
                )

                st.write(
                    f"**Bairro:** {bairro}"
                )
                
                st.write(
                    f"**Telefone:** {telefone}"
                )

            elif not resultado_esgoto.empty:

                linha_esgoto = resultado_esgoto.iloc[0]

                nome = linha_esgoto.get(
                    "nome_completo",
                    "Não informado"
                )

                endereco = linha_esgoto.get(
                    "endereco",
                    "Não informado"
                )

                bairro = linha_esgoto.get(
                    "bairro",
                    "Não informado"
                )

                st.write(
                    f"**Nome do morador:** "
                    f"{nome if pd.notna(nome) else 'Não informado'}"
                )

                st.write(
                    f"**Endereço:** "
                    f"{endereco if pd.notna(endereco) else 'Não informado'}"
                )

                st.write(
                    f"**Bairro:** "
                    f"{bairro if pd.notna(bairro) else 'Não informado'}"
                )

        # -------------------------------------------------
        # MINIMAPA
        # -------------------------------------------------

        with col2:

            st.subheader("📍 Localização")

            endereco_mapa = None

            if linha_agua is not None:
                endereco_mapa = linha_agua.get("Endereço")

            if (
                endereco_mapa is None
                or pd.isna(endereco_mapa)
                or str(endereco_mapa).strip() == ""
            ) and not resultado_esgoto.empty:

                linha_esgoto_mapa = resultado_esgoto.iloc[0]
                endereco_mapa = linha_esgoto_mapa.get(
                    "Endereço",
                    linha_esgoto_mapa.get("endereco")
                )

            if (
                endereco_mapa is not None
                and pd.notna(endereco_mapa)
                and str(endereco_mapa).strip() != ""
            ):

                latitude, longitude, origem_mapa = obter_localizacao(
                    linha_agua,
                    endereco_mapa
                )

            

                if latitude is not None and longitude is not None:

                    mapa = pd.DataFrame({
                        "latitude": [latitude],
                        "longitude": [longitude]
                    })

                    camada = pdk.Layer(
                        "ScatterplotLayer",
                        data=mapa,
                        get_position=["longitude", "latitude"],
                        get_radius=0.0001,
                        radius_units="centimeters",
                        pickable=True,
                        get_fill_color=[220, 0, 0, 255],
                        get_line_color=[220, 0, 0, 255],
                        get_line_width=1
                    )

                    deck = pdk.Deck(
                        initial_view_state=pdk.ViewState(
                            latitude=latitude,
                            longitude=longitude,
                            zoom=15,
                            pitch=0
                        ),
                        layers=[camada],
                        map_style="light",
                        tooltip=True
                    )

                    st.pydeck_chart(
                        deck,
                        width="stretch",
                        height=150
                    )

                    endereco_url = urllib.parse.quote(
                        f"{endereco_mapa}, Guarujá, SP, Brasil"
                    )

                    link_google = (
                        "https://example.invalid/maps/"
                        "?api=1"
                        f"&query={endereco_url}"
                    )

                    st.markdown(
                        f"""
                        <a href="{link_google}" target="_blank"
                           style="text-decoration:none;display:block;
                                  text-align:center;padding:8px;
                                  border-radius:6px;border:1px solid #666;">
                            🗺️ Abrir no Google Maps
                        </a>
                        """,
                        unsafe_allow_html=True
                    )

                else:
                    st.info("📍 Não foi possível localizar este endereço.")

            else:
                st.info("📍 Endereço não disponível.")

    # =====================================================
    # ÁGUA + ESGOTO
    # =====================================================

    # Cards usam o mesmo conteúdo na tela, no PNG e no compartilhamento.
    col_agua, col_esgoto = st.columns(2)
    with col_agua:
        exibir_card("Água", matricula, linha_agua)
    with col_esgoto:
        exibir_card("Esgoto", matricula,
                    resultado_esgoto.iloc[0] if not resultado_esgoto.empty else None)

    # =========================================================
    # ACESSAR FOTOS
    # =========================================================

    st.divider()

    st.subheader("📷 Fotos")

    if matricula:
        st.session_state["matricula_consulta"] = matricula

        if st.button(
            "📷 Abrir fotos da matrícula",
            width="stretch"
        ):

            st.switch_page(
                "pages/Fotos.py"
        )
   
    # =====================================================
    # BLOCO OBRA
    # =====================================================

    with st.container(border=True):

        st.subheader("🏗️ Informações de Obra")

        if resultado_obra.empty:

            st.warning(
                "Matrícula não encontrada na base de obra."
            )

        else:

            linha_obra = resultado_obra.iloc[0]

            col1, col2, col3 = st.columns(3)


            with col1:

                pde = linha_obra.get(
                    "PDE"
                )

                if pd.isna(pde):
                    pde_texto = "Não informado"
                elif isinstance(pde, str):
                    pde_texto = pde.strip() or "Não informado"
                    if pde_texto.endswith(".0") and pde_texto[:-2].isdigit():
                        pde_texto = pde_texto[:-2]
                else:
                    pde_texto = str(int(pde)) if float(pde).is_integer() else str(pde)

                st.write(f"**PDE:** {pde_texto}")


            with col2:

                hd = linha_obra.get(
                    "HD"
                )

                st.write(
                    f"**HD:** "
                    f"{hd if pd.notna(hd) else 'Não informado'}"
                )


            with col3:

                aba = linha_obra.get("DATA_EXECUCAO")

                if pd.notna(aba):
                    aba = pd.to_datetime(aba).strftime("%d/%m/%Y")
                else:
                    aba = "Não informado"

                st.write(
                    f"**Data da baixa:** {aba}"
                )

    if st.button("📋 Ver Histórico", width="stretch"):
        st.switch_page("pages/historico.py")
