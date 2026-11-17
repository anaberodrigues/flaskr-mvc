import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


def salvar_imagem(arquivo):
    """Valida e salva a imagem em static/uploads/. Devolve o nome do arquivo,
    ou None se nenhum arquivo foi enviado. Levanta ValueError se for inválido."""
    if arquivo is None or arquivo.filename == "":
        return None

    nome = secure_filename(arquivo.filename)
    if "." not in nome or nome.rsplit(".", 1)[1].lower() not in EXTENSOES_PERMITIDAS:
        raise ValueError("Formato inválido. Use png, jpg, jpeg, gif ou webp.")

    nome_final = f"{uuid.uuid4().hex}_{nome}"
    arquivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nome_final))
    return nome_final


def remover_imagem(nome):
    """Apaga o arquivo físico, se existir."""
    if not nome:
        return
    caminho = os.path.join(current_app.config["UPLOAD_FOLDER"], nome)
    if os.path.exists(caminho):
        os.remove(caminho)