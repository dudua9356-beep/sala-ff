from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# ID e senha das salas
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef"},
    "Sala 2": {"id": "654321", "senha": "fedcba"},
}

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# SENHA ADM
SENHA_ADM = "Duduzin321@"

# Rota principal do site
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        if not nick or not sala:
            return render_template("index.html", erro="Digite seu nick e escolha a sala.", salas=salas)
        return redirect(url_for("pago", nick=nick, sala=sala))
    return render_template("index.html", salas=salas)

# Página de pagamento (simulada, sem Mercado Pago real aqui)
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala:
        return redirect(url_for("home"))

    # Adiciona jogador à lista (simulação de pagamento)
    if not any(j['nick'] == nick and j['sala'] == sala for j in jogadores_pagaram):
        jogadores_pagaram.append({"nick": nick, "sala": sala, "pago": False})

    # Aqui você poderia gerar QR code real ou código de pagamento
    codigo_pagamento = f"PIX-{nick}-{sala}"

    return render_template("pago.html", nick=nick, sala=sala, codigo=codigo_pagamento)

# Página da sala após pagamento
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    jogador = next((j for j in jogadores_pagaram if j['nick'] == nick and j['sala'] == sala), None)
    if not jogador or not jogador['pago']:
        return redirect(url_for("home"))

    id_sala = salas[sala]['id']
    senha_sala = salas[sala]['senha']

    return render_template("sala.html", nick=nick, id_sala=id_sala, senha_sala=senha_sala)

# Login ADM
@app.route("/adm/login", methods=["GET", "POST"])
def adm_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == SENHA_ADM:
            return redirect(url_for("adm"))
        else:
            erro = "Senha incorreta."
    return render_template("admin_login.html", erro=erro)

# Painel ADM
@app.route("/adm")
def adm():
    return render_template("admin.html", salas=salas, jogadores=jogadores_pagaram)

# Atualizar salas
@app.route("/adm/editar_sala", methods=["POST"])
def editar_sala():
    sala = request.form.get("sala")
    id_novo = request.form.get("id")
    senha_nova = request.form.get("senha")
    if sala in salas:
        salas[sala]['id'] = id_novo
        salas[sala]['senha'] = senha_nova
    return redirect(url_for("adm"))

# Limpar lista de jogadores
@app.route("/adm/limpar_jogadores", methods=["POST"])
def limpar_jogadores():
    global jogadores_pagaram
    jogadores_pagaram = []
    return redirect(url_for("adm"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
