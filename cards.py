"""Cards com um único modelo para tela, imagem e texto compartilhado."""
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode, urlsplit
import re
import pandas as pd

LARGURA_PNG = 900

def texto(value, default="Não informado"):
    if value is None or pd.isna(value):
        return default
    value = str(value).strip()
    return value if value and value.casefold() not in {"nan", "none", "nat"} else default

def data(value):
    if value is None or pd.isna(value) or isinstance(value, (float, int)):
        return "Não informado"
    value = str(value).strip()
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=not bool(re.match(r"^\d{4}-", value)))
    return parsed.strftime("%d/%m/%Y") if pd.notna(parsed) else "Não informado"

def url_valida(value):
    value = texto(value, "")
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in {"http", "https"} and parsed.hostname else None
    except ValueError:
        return None

def campos_card(tipo, matricula, row):
    campos = [("Matrícula", texto(matricula))]
    if row is None:
        return campos + [("Situação", "Matrícula não encontrada nesta base")]
    agua = tipo == "Água"
    campos += [
        ("Status adesão", texto(row.get("Status Adesão" if agua else "Status do Registro"))),
        ("Data adesão" if agua else "Data execução",
         data(row.get("Data Adesão" if agua else "data_execucao_roteiro"))),
        ("Agente", texto(row.get("Agente") if agua and texto(row.get("origem_adesao"), "") == "APPDEEP"
                         else row.get("Equipe Exec." if agua else "agente_appdeep"))),
        ("Quantidade de visitas", texto(row.get("Quantidade de Visitas" if agua else "quantidade_visitas"))),
        ("Origem da adesão", texto(row.get("origem_adesao"), "Não rastreada nesta versão da base")),
        ("Data do registro de origem", data(row.get("data_origem_adesao"))),
    ]
    link = url_valida(row.get("link_appdeep"))
    if texto(row.get("origem_adesao"), "") == "APPDEEP" and link:
        campos.append(("APPDEEP", link))
    return campos

def texto_card(tipo, campos):
    return f"Informações {tipo}\n" + "\n".join(f"{k}: {v}" for k, v in campos)

def whatsapp_url(tipo, campos):
    return "https://wa.me/?" + urlencode({"text": texto_card(tipo, campos)})

def gerar_png(tipo, campos):
    from PIL import Image, ImageDraw, ImageFont
    def fonte(size):
        for candidate in [str(Path(__file__).parent / "fonts/DejaVuSans.ttf"),
                          "DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                pass
        return ImageFont.load_default(size=size)
    regular, title = fonte(26), fonte(36)
    draw = ImageDraw.Draw(Image.new("RGB", (LARGURA_PNG, 1)))
    lines = []
    # Quebra por pixels, inclusive URLs e palavras longas, preservando cada caractere.
    for label, value in campos:
        for paragraph in f"{label}: {value}".split("\n"):
            line = ""
            for char in paragraph:
                if line and draw.textlength(line + char, font=regular) > LARGURA_PNG - 88:
                    lines.append(line)
                    line = ""
                line += char
            lines.append(line)
        lines.append("")
    height = 116 + len(lines) * 38 + 28
    img = Image.new("RGB", (LARGURA_PNG, height), "#f4f7fb")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((12, 12, LARGURA_PNG - 13, height - 13), radius=22,
                           fill="white", outline="#bac9db", width=2)
    draw.text((44, 34), f"Informações {tipo}", font=title, fill="#153e68")
    for i, line in enumerate(lines):
        draw.text((44, 110 + i * 38), line, font=regular, fill="#243448")
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

def exibir_card(tipo, matricula, row):
    import streamlit as st
    campos = campos_card(tipo, matricula, row)
    with st.container(border=True, width=450, height="content"):
        st.subheader(f"Informações {tipo}")
        for label, value in campos:
            if label == "APPDEEP":
                st.link_button("Abrir registro no APPDEEP", value)
            else:
                st.text(f"{label}: {value}")
        png = gerar_png(tipo, campos)
        safe = re.sub(r"[^\w-]", "_", str(matricula))
        st.download_button("Baixar card PNG", png, file_name=f"{tipo}_{safe}.png",
                           mime="image/png", key=f"png_{tipo}_{matricula}", on_click="ignore")
        st.link_button("Compartilhar texto no WhatsApp", whatsapp_url(tipo, campos))
        st.caption("O WhatsApp recebe texto e link. Para enviar a imagem, baixe o PNG e anexe na conversa.")
