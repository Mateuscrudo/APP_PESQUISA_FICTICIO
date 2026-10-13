import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# FORMATAÇÃO DE DATAS
# =========================================================

def formatar_data(valor):
    """Formata uma data como DD/MM/AAAA, sem alterar o valor no banco."""
    if valor is None or pd.isna(valor):
        return "Não informado"

    try:
        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return "Não informado"

            # Datas do banco em formato ISO: AAAA-MM-DD,
            # com ou sem horário. Preserva a ordem ano/mês/dia.
            if re.match(r"^\d{4}-\d{2}-\d{2}(?:$|[T ])", valor):
                data = pd.to_datetime(
                    valor,
                    format="ISO8601",
                    errors="coerce",
                )
            else:
                # Datas brasileiras: dia/mês/ano, com ou sem horário.
                data = pd.to_datetime(
                    valor,
                    dayfirst=True,
                    errors="coerce",
                )

        elif isinstance(valor, (date, datetime, pd.Timestamp)):
            data = pd.to_datetime(valor, errors="coerce")

        else:
            # Evita interpretar números como timestamps.
            return "Não informado"

        if pd.isna(data):
            return "Não informado"

        return data.strftime("%d/%m/%Y")

    except (ValueError, TypeError, OverflowError):
        return "Não informado"


# =========================================================
# CONFIGURAÇÃO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_ESGOTO = BASE_DIR / "Bases" / "base_esgoto.db"
BASE_LEGADA = BASE_DIR / "Bases" / "historico_visitas.db"


# =========================================================
# MATRÍCULA SELECIONADA
# =========================================================

matricula = st.session_state.get("matricula_consulta")

if not matricula:
    st.warning("⚠️ Nenhuma matrícula foi selecionada.")
    st.stop()

if st.button("⬅️ Voltar para consulta"):
    st.switch_page("EAapp.py")

st.divider()


# =========================================================
# VERIFICAR BASE
# =========================================================

if not BASE_ESGOTO.exists() and not BASE_LEGADA.exists():
    st.error(
        f"❌ Bancos de histórico não encontrados: "
        f"{BASE_ESGOTO} ou {BASE_LEGADA}"
    )
    st.stop()


# =========================================================
# CONSULTAR BANCO
# =========================================================

try:
    historico_agua = pd.DataFrame()
    historico_esgoto = pd.DataFrame()

    if BASE_LEGADA.exists():
        with sqlite3.connect(BASE_LEGADA) as conn:
            historico_agua = pd.read_sql_query(
                """
                SELECT *
                FROM historico_visitas
                WHERE matricula = ?
                ORDER BY data_execucao DESC
                """,
                conn,
                params=(matricula,),
            )

    if BASE_ESGOTO.exists():
        with sqlite3.connect(BASE_ESGOTO) as conn:
            colunas = {
                linha[1]
                for linha in conn.execute(
                    'PRAGMA table_info("historico_visitas")'
                ).fetchall()
            }

            if "Matrícula" in colunas:
                coluna_matricula = '"Matrícula"'
                coluna_data = '"Data"'
            elif "matricula" in colunas:
                coluna_matricula = "matricula"
                coluna_data = "data_execucao"
            else:
                raise ValueError(
                    "A tabela historico_visitas não possui "
                    "uma coluna de matrícula."
                )

            historico_esgoto = pd.read_sql_query(
                f"""
                SELECT *
                FROM historico_visitas
                WHERE {coluna_matricula} = ?
                ORDER BY {coluna_data} DESC
                """,
                conn,
                params=(matricula,),
            )

    # =====================================================
    # TÍTULO
    # =====================================================

    st.title("Histórico da Matrícula")
    st.caption(f"📋 Matrícula: {matricula}")
    st.divider()

    # =====================================================
    # VERIFICAR RESULTADO
    # =====================================================

    if historico_agua.empty and historico_esgoto.empty:
        st.info(
            "Nenhum histórico encontrado para esta matrícula."
        )
        st.stop()

    st.success(
        f"✅ {len(historico_agua) + len(historico_esgoto)} "
        "registro(s) encontrado(s)"
    )

    # =====================================================
    # DUAS COLUNAS
    # =====================================================

    col1, col2 = st.columns(2)

    # =====================================================
    # HISTÓRICO DE ÁGUA
    # =====================================================

    with col1:
        st.subheader("💧 Histórico de Água")

        if historico_agua.empty:
            st.info(
                "Nenhum histórico de água disponível."
            )

        else:
            for i, (_, visita) in enumerate(
                historico_agua.iterrows(),
                start=1,
            ):
                with st.container(border=True):
                    st.markdown(f"### VISITA {i}")

                    st.write(
                        f"**Data:** "
                        f"{formatar_data(visita.get('data_execucao'))}"
                    )

                    st.write(
                        f"**Equipe:** "
                        f"{visita.get('equipe', 'Não informado')}"
                    )

                    st.write(
                        f"**Status Aplicado:** "
                        f"{visita.get('status_aplicado', 'Não informado')}"
                    )

    # =====================================================
    # HISTÓRICO DE ESGOTO
    # =====================================================

    with col2:
        st.subheader("🚰 Histórico de Esgoto")

        if historico_esgoto.empty:
            st.info(
                "Nenhum histórico de esgoto disponível."
            )

        else:
            historico_esgoto = historico_esgoto.rename(
                columns={
                    "Matrícula": "matricula",
                    "Data": "data_execucao",
                    "Agente": "agente",
                    "Origem": "origem",
                    "Status ": "Status",
                }
            )

            for i, (_, visita) in enumerate(
                historico_esgoto.iterrows(),
                start=1,
            ):
                with st.container(border=True):
                    st.markdown(f"### VISITA {i}")

                    st.write(
                        f"**Data:** "
                        f"{formatar_data(visita.get('data_execucao'))}"
                    )

                    st.write(
                        f"**Origem:** "
                        f"{visita.get('origem', 'Não informado')}"
                    )

                    st.write(
                        f"**Agente:** "
                        f"{visita.get('agente', 'Não informado')}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{visita.get('Status', 'Não informado')}"
                    )

# =========================================================
# TRATAMENTO DE ERROS
# =========================================================

except Exception as e:
    st.error(
        "❌ Ocorreu um erro ao consultar o histórico."
    )
    st.exception(e)