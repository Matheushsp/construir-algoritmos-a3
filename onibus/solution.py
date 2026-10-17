
import os
import requests
import folium
from dotenv import load_dotenv

# Configuração
load_dotenv()

TOKEN = os.getenv("SPTRANS_TOKEN")
BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"

sessao = requests.Session()


def consultar(endpoint, parametros=None):
    """Consulta um endpoint da API Olho Vivo."""
    url = f"{BASE_URL}/{endpoint}"

    resposta = sessao.get(
        url,
        params=parametros,
        timeout=30
    )

    resposta.raise_for_status()
    return resposta.json()


def main():
    # 1. Verifica o token
    if not TOKEN:
        print("Erro: token não encontrado no arquivo .env.")
        return

    # 2. Autentica na API
    resposta = sessao.post(
        f"{BASE_URL}/Login/Autenticar",
        params={"token": TOKEN},
        timeout=30
    )

    resposta.raise_for_status()

    if resposta.json() is not True:
        print("Falha na autenticação da API.")
        return

    print("Autenticação realizada!")

    # 3. Procura a linha com mais paradas disponíveis
    termos_busca = ["Lapa", "Pinheiros", "Paulista"]

    linha = None
    codigo = None
    paradas = []
    codigos_testados = set()

    for termo in termos_busca:
        print(f"Procurando linhas: {termo}")

        linhas = consultar(
            "Linha/Buscar",
            {"termosBusca": termo}
        )

        for candidata in linhas[:15]:
            codigo_teste = candidata.get("cl")

            if not codigo_teste or codigo_teste == 2506:
                continue

            if codigo_teste in codigos_testados:
                continue

            codigos_testados.add(codigo_teste)

            resultado = consultar(
                "Parada/BuscarParadasPorLinha",
                {"codigoLinha": codigo_teste}
            )

            if resultado and len(resultado) > len(paradas):
                linha = candidata
                codigo = codigo_teste
                paradas = resultado

    if linha is None:
        print("Nenhuma linha com paradas disponíveis foi encontrada.")
        return

    print(
        f"Linha selecionada: {linha.get('lt', '')} - "
        f"{linha.get('tp', '')} / {linha.get('ts', '')}"
    )
    print(f"Total de paradas: {len(paradas)}")

    # 4. Busca os veículos da linha
    dados = consultar(
        "Posicao/Linha",
        {"codigoLinha": codigo}
    )

    onibus = dados.get("vs", []) if isinstance(dados, dict) else []
    print(f"Total de veículos retornados: {len(onibus)}")

    # 5. Cria a lista de coordenadas válidas
    coordenadas = []

    for parada in paradas:
        latitude = parada.get("py")
        longitude = parada.get("px")

        if latitude is not None and longitude is not None:
            coordenadas.append([latitude, longitude])

    for veiculo in onibus:
        latitude = veiculo.get("py")
        longitude = veiculo.get("px")

        if latitude is not None and longitude is not None:
            coordenadas.append([latitude, longitude])

    if not coordenadas:
        print("Nenhuma coordenada válida foi encontrada.")
        return

    # 6. Cria o mapa próximo à região dos dados
    mapa = folium.Map(
        location=[-23.506, -46.706],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # Enquadra as paradas e os ônibus na visualização inicial
    mapa.fit_bounds(coordenadas, padding=[30, 30])

    
# Marcador do local de estudo, conforme o exemplo do professor
    folium.Marker(
    location=[-22.8773542, -47.2280647],
    popup=folium.Popup(
        "Estudo aqui!",
        max_width=100
    ),
    tooltip="Local de estudo",
    icon=folium.Icon(
        color="blue",
        icon="info-sign"
    )
).add_to(mapa)


    # 7. Adiciona as paradas em vermelho
    for parada in paradas:
        latitude = parada.get("py")
        longitude = parada.get("px")

        if latitude is None or longitude is None:
            continue

        nome = parada.get("np", "Parada de ônibus")
        endereco = parada.get("ed", "")

        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(
                f"Parada: {nome}<br>Endereço: {endereco}",
                max_width=250
            ),
            tooltip=nome,
            icon=folium.Icon(
                color="red",
                icon="info-sign"
            )
        ).add_to(mapa)

    # 8. Adiciona os ônibus em azul
    for veiculo in onibus:
        latitude = veiculo.get("py")
        longitude = veiculo.get("px")

        if latitude is None or longitude is None:
            continue

        prefixo = veiculo.get("p", "Não informado")

        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(
                f"Ônibus: {prefixo}<br>"
                f"Linha: {linha.get('lt', '')}",
                max_width=250
            ),
            tooltip=f"Ônibus {prefixo}",
            icon=folium.Icon(
                color="blue",
                icon="info-sign"
            )
        ).add_to(mapa)

    # 9. Salva o arquivo HTML na pasta do projeto
    pasta = os.path.dirname(os.path.abspath(__file__))
    arquivo_saida = os.path.join(pasta, "mapa_onibus.html")

    mapa.save(arquivo_saida)

    print(f"Mapa criado: {arquivo_saida}")
    print("Acesse http://localhost:8000/mapa_onibus.html")
    print("Se o servidor local ainda não estiver ativo, execute:")
    print("py -m http.server 8000")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as erro:
        print(f"Erro na comunicação com a API: {erro}")
    except (ValueError, KeyError, TypeError) as erro:
        print(f"Erro ao processar os dados: {erro}")
