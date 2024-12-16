from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Dados dos queijos
QUEIJOS = {
    "atacado": {
        "brie": 40.00,
        "mozzarella": 25.00,
        "chancliche": 40.00
    },
    "varejo": {
        "brie": 45.00,
        "mozzarella": 28.00,
        "chancliche": 55.00
    }
}

# Estados do usuário
user_state = {"stage": "inicio", "carrinho": [], "tipo": None}

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip().lower()
    response = MessagingResponse()
    message = response.message()

    global user_state

    if user_state["stage"] == "inicio":
        if incoming_msg in ["oi", "menu"]:
            user_state["stage"] = "menu"
            message.body(
                "Seja bem-vindo à Queijaria Belvedere, a primeira queijaria urbana de Maringá!\n"
                "Escolha uma das opções abaixo:\n"
                "1 - Atacado\n"
                "2 - Varejo\n"
                "3 - Falar com atendente"
            )
        else:
            message.body("Digite 'menu' para começar.")

    elif user_state["stage"] == "menu":
        if incoming_msg == "1":
            user_state["tipo"] = "atacado"
            user_state["stage"] = "pedido"
            message.body(
                "A quantidade mínima de cada queijo no atacado é de 6 unidades:\n"
                "- Brie R$40,00 - 125g\n"
                "- Mozzarella R$25,00 - 250g\n"
                "- Chancliche R$40,00 - 125g\n\n"
                "Digite a quantidade e o nome dos queijos, separados por vírgulas.\n"
                "Exemplo: 6 Brie, 8 Mozzarella\n"
                "3 - Falar com atendente"
            )
        elif incoming_msg == "2":
            user_state["tipo"] = "varejo"
            user_state["stage"] = "pedido"
            message.body(
                "Aqui estão os queijos disponíveis para compra unitária:\n"
                "- Brie R$45,00 - 125g\n"
                "- Mozzarella R$28,00 - 250g\n"
                "- Chancliche R$55,00 - 125g\n\n"
                "Digite a quantidade e o nome dos queijos, separados por vírgulas.\n"
                "Exemplo: 2 Brie, 3 Mozzarella\n"
                "3 - Falar com atendente"
            )
        elif incoming_msg == "3":
            user_state = {"stage": "inicio", "carrinho": [], "tipo": None}
            message.body("Um atendente entrará em contato com você em breve. Obrigado!")
        else:
            message.body("Escolha 1 para Atacado, 2 para Varejo ou 3 para falar com atendente.")

    elif user_state["stage"] == "pedido":
        if incoming_msg == "3":
            user_state = {"stage": "inicio", "carrinho": [], "tipo": None}
            message.body("Um atendente entrará em contato com você em breve. Obrigado!")
        else:
            try:
                itens = [item.strip() for item in incoming_msg.split(",")]
                carrinho = []
                for item in itens:
                    qtd, nome = item.split(" ", 1)
                    nome = nome.lower()
                    if nome in QUEIJOS[user_state["tipo"]]:
                        qtd = int(qtd)
                        if user_state["tipo"] == "atacado" and qtd < 6:
                            raise ValueError("Quantidade mínima no atacado é 6 unidades.")
                        carrinho.append((nome, qtd))
                    else:
                        raise ValueError(f"Queijo '{nome}' não encontrado.")
                
                total = sum(qtd * QUEIJOS[user_state["tipo"]][nome] for nome, qtd in carrinho)
                user_state["carrinho"] = carrinho
                user_state["stage"] = "entrega"
                message.body(
                    f"Total do pedido: R$ {total:.2f}\n\n"
                    "Escolha o tipo de entrega:\n"
                    "1 - Maringá e região metropolitana (R$30,00)\n"
                    "2 - Fora de Maringá (frete será calculado por um atendente)\n"
                    "3 - Falar com atendente"
                )
            except ValueError as e:
                message.body(str(e))

    elif user_state["stage"] == "entrega":
        if incoming_msg == "1":
            total = sum(qtd * QUEIJOS[user_state["tipo"]][nome] for nome, qtd in user_state["carrinho"])
            total += 30.00
            user_state["stage"] = "endereco"
            message.body(
                f"Total com frete: R$ {total:.2f}\n\n"
                "Por favor, envie o endereço de entrega no formato:\n"
                "Rua, Número, Complemento (se houver), CEP\n"
                "3 - Falar com atendente"
            )
        elif incoming_msg == "2":
            user_state["stage"] = "endereco"
            message.body(
                "Frete será calculado e enviado posteriormente.\n\n"
                "Por favor, envie o endereço de entrega no formato:\n"
                "Rua, Número, Complemento (se houver), CEP\n"
                "3 - Falar com atendente"
            )
        elif incoming_msg == "3":
            user_state = {"stage": "inicio", "carrinho": [], "tipo": None}
            message.body("Um atendente entrará em contato com você em breve. Obrigado!")
        else:
            message.body("Escolha 1, 2 ou 3 para continuar.")

    elif user_state["stage"] == "endereco":
        if incoming_msg == "3":
            user_state = {"stage": "inicio", "carrinho": [], "tipo": None}
            message.body("Um atendente entrará em contato com você em breve. Obrigado!")
        else:
            message.body(
                "Nome: QUEIJOS BELVEDERE LTDA\n"
                "Chave PIX: 52600588000118\n\n"
                "Por favor, envie o comprovante de pagamento para confirmar o pedido.\n"
                "Prazo de entrega: até 7 dias após o pagamento.\n\n"
                "Obrigado por comprar conosco! Siga-nos no Instagram: @queijariabelvedere"
            )
            user_state = {"stage": "inicio", "carrinho": [], "tipo": None}

    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
