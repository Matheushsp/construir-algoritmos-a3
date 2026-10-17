
import os
import requests
from dotenv import load_dotenv

# Carrega o token do arquivo .env
load_dotenv()

token = os.getenv("SPTRANS_TOKEN")

if not token:
    print("Erro: token não encontrado no arquivo .env")
else:
    try:
        resposta = requests.post(
            "https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar",
            params={"token": token},
            timeout=30
        )

        resposta.raise_for_status()
        print("Autenticado:", resposta.json())

    except requests.RequestException as erro:
        print("Erro na conexão com a API:", erro)
