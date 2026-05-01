import requests
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Configurações do Supabase (A Fundação)
# ATENÇÃO: Substitua a URL abaixo pela Project URL que está no painel do seu Supabase
url_supabase: str = os.getenv("SUPABASE_URL")
chave_supabase: str = os.getenv("SUPABASE_SECRET_KEY")
supabase: Client = create_client(url_supabase, chave_supabase)

# 2. Configurações da API-Football (A Extração)
url_api = "https://v3.football.api-sports.io/fixtures?team=133&season=2024"
headers = {
    'x-apisports-key': os.getenv("API_FOOTBALL_KEY")
}

print("Buscando dados na API-Football (última vez para esses jogos!)...")
response = requests.request("GET", url_api, headers=headers, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    # 1. O nosso Rastreador de Erros
    if data.get('errors'):
        print("\n🕵️ Achamos o culpado! A API bloqueou a busca pelo seguinte motivo:")
        print(data['errors'])
        print("-" * 50)
    elif not data.get('response'):
        print("\n⚠️ A API não enviou nenhum erro, mas a lista de jogos veio vazia!")
        print("-" * 50)
    else:
        # 2. Se tudo estiver OK, ele faz a injeção
        jogos_encerrados = [jogo for jogo in data['response'] if jogo['fixture']['status']['short'] in ['FT', 'PEN', 'AET']]
        ultimos_10_jogos = jogos_encerrados[-10:]
        
        print(f"✅ {len(ultimos_10_jogos)} jogos prontos. Injetando no banco de dados Supabase...")
        
        for jogo in ultimos_10_jogos:
            match_id = jogo['fixture']['id']
            data_jogo = jogo['fixture']['date']
            
            equipa_casa_id = jogo['teams']['home']['id']
            equipa_casa_nome = jogo['teams']['home']['name']
            equipa_fora_id = jogo['teams']['away']['id']
            equipa_fora_nome = jogo['teams']['away']['name']
            
            gols_casa = jogo['goals']['home']
            gols_fora = jogo['goals']['away']

            supabase.table('teams').upsert({'id': equipa_casa_id, 'name': equipa_casa_nome}).execute()
            supabase.table('teams').upsert({'id': equipa_fora_id, 'name': equipa_fora_nome}).execute()

            supabase.table('matches').upsert({
                'id': match_id,
                'team_home': equipa_casa_id,
                'team_away': equipa_fora_id,
                'date': data_jogo
            }).execute()

            supabase.table('stats').upsert({
                'match_id': match_id,
                'goals_home': gols_casa,
                'goals_away': gols_fora
            }).execute()

        print("🎉 Sucesso Absoluto! Os jogos e estatísticas estão blindados no seu banco de dados.")
else:
    print(f"❌ Erro na requisição. Código: {response.status_code}")