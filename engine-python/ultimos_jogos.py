import requests
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. CARREGAR AS CONFIGURAÇÕES (O Cofre)
load_dotenv()

url_supabase: str = os.getenv("SUPABASE_URL")
chave_supabase: str = os.getenv("SUPABASE_SECRET_KEY")
api_key: str = os.getenv("API_FOOTBALL_KEY")

# Inicializa o cliente do Supabase
supabase: Client = create_client(url_supabase, chave_supabase)

# 2. CONFIGURAÇÕES DA API (Extração Dinâmica)
# Por agora deixamos o Palmeiras (121), mas podes mudar aqui para qualquer ID
id_time = 133 
url_api = f"https://v3.football.api-sports.io/fixtures?team={id_time}&season=2024"

headers = {
    'x-apisports-key': api_key
}

print(f"🚀 Iniciando extração de dados para o Time ID: {id_time}...")
response = requests.request("GET", url_api, headers=headers, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    if data.get('errors'):
        print("❌ Erro da API:", data['errors'])
    else:
        # Filtra apenas jogos que já terminaram
        jogos_encerrados = [jogo for jogo in data['response'] if jogo['fixture']['status']['short'] in ['FT', 'PEN', 'AET']]
        ultimos_10_jogos = jogos_encerrados[-10:]
        
        print(f"✅ {len(ultimos_10_jogos)} jogos encontrados. Injetando no Supabase...")
        
        for jogo in ultimos_10_jogos:
            match_id = jogo['fixture']['id']
            data_jogo = jogo['fixture']['date']
            
            # Dados das Equipas
            casa_id = jogo['teams']['home']['id']
            casa_nome = jogo['teams']['home']['name']
            fora_id = jogo['teams']['away']['id']
            fora_nome = jogo['teams']['away']['name']
            
            # Golos
            gols_casa = jogo['goals']['home']
            gols_fora = jogo['goals']['away']

            # Injeção nas Tabelas (Upsert evita duplicados)
            supabase.table('teams').upsert({'id': casa_id, 'name': casa_nome}).execute()
            supabase.table('teams').upsert({'id': fora_id, 'name': fora_nome}).execute()

            supabase.table('matches').upsert({
                'id': match_id,
                'team_home': casa_id,
                'team_away': fora_id,
                'date': data_jogo
            }).execute()

            supabase.table('stats').upsert({
                'match_id': match_id,
                'goals_home': gols_casa,
                'goals_away': gols_fora
            }).execute()

        print("🎉 Sucesso Absoluto! Dados blindados no banco.")
else:
    print(f"❌ Falha na conexão: Status {response.status_code}")