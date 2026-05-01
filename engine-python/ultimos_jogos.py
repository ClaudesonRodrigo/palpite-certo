import requests

url = "https://v3.football.api-sports.io/fixtures?team=127&season=2023"

headers = {
    'x-apisports-key': 'e30f60c41ea64026d24d04bab3124aaf' # Coloque sua chave novamente!
}

print("Buscando jogos e calculando médias...")
response = requests.request("GET", url, headers=headers, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    if data.get('errors'):
        print("⚠️ Erro da API:", data['errors'])
    else:
        # Filtra os jogos encerrados
        jogos_encerrados = [jogo for jogo in data['response'] if jogo['fixture']['status']['short'] in ['FT', 'PEN', 'AET']]
        ultimos_10_jogos = jogos_encerrados[-10:]
        
        # Variáveis para a matemática
        gols_feitos_casa = 0
        jogos_em_casa = 0
        gols_feitos_fora = 0
        jogos_fora = 0

        for jogo in ultimos_10_jogos:
            time_casa = jogo['teams']['home']['name']
            gols_casa = jogo['goals']['home']
            gols_fora = jogo['goals']['away']
            
            # Conta se o Flamengo jogou em casa ou fora e soma os gols
            if time_casa == "Flamengo":
                gols_feitos_casa += gols_casa
                jogos_em_casa += 1
            else:
                gols_feitos_fora += gols_fora
                jogos_fora += 1

        print("\n📊 ESTATÍSTICAS RECENTES DO FLAMENGO (Últimos 10 jogos):")
        print("-" * 50)
        
        if jogos_em_casa > 0:
            media_casa = gols_feitos_casa / jogos_em_casa
            print(f"🏠 Média de Gols Feitos (Em Casa): {media_casa:.2f} por jogo (em {jogos_em_casa} jogos)")
        
        if jogos_fora > 0:
            media_fora = gols_feitos_fora / jogos_fora
            print(f"✈️ Média de Gols Feitos (Fora): {media_fora:.2f} por jogo (em {jogos_fora} jogos)")
        print("-" * 50)
else:
    print(f"❌ Erro na requisição. Código: {response.status_code}")