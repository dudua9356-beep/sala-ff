from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas e jogadores
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "pagos": []},
    "Sala 2": {"id": "654321", "senha": "fedcba", "pagos": []},
}

ADM_SENHA = "Duduzin321@"

# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        if not nick or not sala:
            return render_template("index.html", salas=salas, erro="Digite nick e escolha a sala.")
        return redirect(url_for("pago", nick=nick, sala=sala))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala:
        return redirect(url_for("home"))

    # Criar pagamento Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala} 🔥",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    payment_id = payment["response"]["id"]

    # Adiciona jogador à lista como NÃO pago
    if not any(j["nick"] == nick for j in salas[sala]["pagos"]):
        salas[sala]["pagos"].append({"nick": nick, "pago": False, "payment_id": payment_id})

    return render_template("pago.html", nick=nick, sala=sala, qr_code=qr_code, payment_id=payment_id)

# Página da sala (ID e senha só aparecem se pago)
@app.route("/sala")
def sala_page():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    jogador = next((j for j in salas[sala]["pagos"] if j["nick"] == nick), None)
    if not jogador or not jogador["pago"]:
        return redirect(url_for("home"))
    return render_template("sala.html", id_sala=salas[sala]["id"], senha=salas[sala]["senha"], nick=nick)

# Painel ADM login
@app.route("/adm", methods=["GET", "POST"])
def adm_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return redirect(url_for("adm_painel"))
        else:
            return render_template("admin_login.html", erro="Senha incorreta.")
    return render_template("admin_login.html")

# Painel ADM principal
@app.route("/adm/painel")
def adm_painel():
    return render_template("admin.html", salas=salas)

# Remover jogador
@app.route("/adm/remover/<sala>/<nick>")
def remover_jogador(sala, nick):
    salas[sala]["pagos"] = [j for j in salas[sala]["pagos"] if j["nick"] != nick]
    return redirect(url_for("adm_painel"))

# Atualizar ID e senha de uma sala
@app.route("/adm/editar_sala", methods=["POST"])
def editar_sala():
    sala = request.form.get("sala")
    id_sala = request.form.get("id_sala")
    senha = request.form.get("senha")
    if sala in salas:
        salas[sala]["id"] = id_sala
        salas[sala]["senha"] = senha
    return redirect(url_for("adm_painel"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
