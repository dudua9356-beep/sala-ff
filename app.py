from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mercadopago
import os

app = Flask(__name__)
app.secret_key = "segredo123"

usuarios = {}

# ---------------- RAIZ ----------------
@app.route("/")
def raiz():
    return redirect("/novo")

# ---------------- CRIAR CLIENTE ----------------
@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome")
        senha = request.form.get("senha")
        token = request.form.get("token")

        if not nome or not senha or not token:
            return "Preencha tudo"

        if nome in usuarios:
            return "Cliente já existe"

        usuarios[nome] = {
            "senha": senha,
            "access_token": token,
            "salas": {
                "Sala 1": {"id": "0000", "senha": "0000", "ocupados": 0, "max": 48}
            },
            "jogadores": []
        }

        return f"Cliente criado! 👉 <a href='/{nome}'>Entrar</a>"

    return render_template("criar_cliente.html")

# ---------------- HOME CLIENTE ----------------
@app.route("/<cliente>", methods=["GET", "POST"])
def home(cliente):
    user = usuarios.get(cliente)

    if not user:
        return "Cliente não encontrado"

    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")

        if not nick or sala not in user["salas"]:
            return redirect(f"/{cliente}")

        if user["salas"][sala]["ocupados"] >= user["salas"][sala]["max"]:
            return render_template("index.html", salas=user["salas"], cliente=cliente, erro="Sala cheia")

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

        if nome:
            user["salas"][nome] = {
                "id": id_sala,
                "senha": senha,
                "ocupados": 0,
                "max": 48
            }

    return render_template("painel.html", salas=user["salas"], jogadores=user["jogadores"])

# ---------------- PAGAMENTO ----------------
@app.route("/<cliente>/pago")
def pago(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala = request.args.get("sala")

    sdk = mercadopago.SDK(user["access_token"])

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

# ---------------- SALA ----------------
@app.route("/<cliente>/sala")
def sala(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    jogador = next((j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala_nome), None)

    if not jogador or not jogador["pago"]:
        return redirect(f"/{cliente}")

    sala_info = user["salas"][sala_nome]

    return render_template("sala.html",
        id_sala=sala_info["id"],
        senha=sala_info["senha"],
        nick=nick,
        sala=sala_nome
    )

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]

        for cliente, user in usuarios.items():
            sdk = mercadopago.SDK(user["access_token"])
            payment = sdk.payment().get(payment_id)

            if payment["response"]["status"] == "approved":
                ref = payment["response"].get("external_reference", "")

                if "|" in ref:
                    c, nick, sala = ref.split("|")

                    if c == cliente:
                        for j in user["jogadores"]:
                            if j["nick"] == nick and j["sala"] == sala:
                                if not j["pago"]:
                                    j["pago"] = True
                                    user["salas"][sala]["ocupados"] += 1

    return "ok"
