from flask import Flask, jsonify, request
from http import HTTPStatus
from src.controller import simulador


app = Flask(__name__)


@app.route('/jogo/simular', methods=['GET'])
def simular_jogo():
    try:
        qtd_casas = request.args.get("qtd_casas", default=20, type=int)
        jogadores = request.args.get("jogadores", default=4, type=int)
        resultado = simulador(qtd_casas, jogadores)
        return jsonify(resultado), HTTPStatus.OK

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "erro": "Erro interno ao processar simulação"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
