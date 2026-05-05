from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mercadopago
import os

app = Flask(__name__)
app.secret_key = "segredo123"

ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# 🔥 CLIENTES
usuarios = {
    "eduardo": {
        "senha": "123",
        "salas": {
            "Sala 1": {"id": "123456", "senha": "abcdef", "ocupados": 0, "max": 49}
        },
        "jogadores": []
    }
}

# ✅ ROTA RAIZ (corrige teu erro)
@app.route("/")
def raiz():
    return redirect("/eduardo")

# ---------------- HOME ----------------
@app.route("/<cliente>", methods=["GET", "POST"])
def home(cliente):
    user = usuarios.get(cliente)
    if not user:
        return "Cliente não encontrado"

    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        return redirect(url_for("pago", cliente=cliente, nick=nick, sala=sala))

    return render_template("index.html", salas=user["salas"], cliente=cliente)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        senha = request.form.get("senha")

        if user in usuarios and usuarios[user]["senha"] == senha:
            session["user"] = user
            return redirect("/painel")

    return render_template("login.html")

# ---------------- PAINEL ----------------
@app.route("/painel", methods=["GET", "POST"])
def painel():
    if "user" not in session:
        return redirect("/login")

    user = usuarios[session["user"]]

    if request.method == "POST":
        nome = request.form.get("nome")
        id_sala = request.form.get("id")
        senha = request.form.get("senha")

        user["salas"][nome] = {
            "id": id_sala,
            "senha": senha,
            "ocupados": 0,
            "max": 49
        }

    return render_template("painel.html", salas=user["salas"], jogadores=user["jogadores"])

# ---------------- PAGAMENTO ----------------
@app.route("/<cliente>/pago")
def pago(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala = request.args.get("sala")

    payment_data = {
        "transaction_amount": 6.0,
        "payment_method_id": "pix",
        "external_reference": f"{cliente}|{nick}|{sala}",
        "notification_url": "https://sala-ff-2.onrender.com/webhook",
        "payer": {"email": f"{nick}@teste.com"}
    }

    payment = sdk.payment().create(payment_data)

    qr = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    code = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"]

    user["jogadores"].append({"nick": nick, "sala": sala, "pago": False})

    return render_template("pago.html", qr_code=qr, qr_code_text=code, nick=nick, sala=sala, cliente=cliente)

# ---------------- STATUS ----------------
@app.route("/<cliente>/status")
def status(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala = request.args.get("sala")

    jogador = next((j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala), None)

    return jsonify({"pago": jogador["pago"] if jogador else False})

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data.get("type") == "payment":
        payment_id = data["data"]["id"]
        payment = sdk.payment().get(payment_id)

        if payment["response"]["status"] == "approved":
            ref = payment["response"]["external_reference"]
            cliente, nick, sala = ref.split("|")

            user = usuarios[cliente]

            for j in user["jogadores"]:
                if j["nick"] == nick and j["sala"] == sala:
                    j["pago"] = True
                    user["salas"][sala]["ocupados"] += 1

    return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()
