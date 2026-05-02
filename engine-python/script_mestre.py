import requests
import os
import math
from dotenv import load_dotenv
import time 
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. SETUP INICIAL E CONEXÕES
# ==========================================
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))
headers = {'x-apisports-key': os.getenv("API_FOOTBALL_KEY")}

# ==========================================
# 2. FUNÇÕES DO MOTOR (OTIMIZADAS)
# ==========================================
def buscar_jogos_do_dia(league_id, season):
    """Busca a temporada inteira e separa 5 jogos na memória (Sem ferir as regras da API)"""
    
    # Pedimos TODOS os jogos de 2024. A API permite isso no plano grátis!
    url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}"
    print(f"🔍 [1/3] Fazendo download da temporada inteira de {season}...")
    
    resposta_bruta = requests.get(url, headers=headers).json()
    
    if resposta_bruta.get('errors'):
        print("\n🚨 ERRO NA API (BUSCAR JOGOS):", resposta_bruta['errors'])
        return []
        
    todos_os_jogos = resposta_bruta.get('response', [])
    
    # O nosso Python assume o controle: pegamos 5 jogos do meio do campeonato para testar
    if len(todos_os_jogos) > 5:
        jogos_simulados = todos_os_jogos[100:105] # Pega 5 jogos a partir do jogo 100
        print(f"✅ Download concluído! O Python separou {len(jogos_simulados)} confrontos para análise.")
        return jogos_simulados
        
    return todos_os_jogos

def extrair_historico_lote(teams_ids, season):
    """Baixa o histórico com sistema Anti-Bloqueio (Rate Limit) e Timeouts"""
    print(f"📦 [2/3] Baixando histórico de {len(teams_ids)} times (Com sistema Anti-Bloqueio)...")
    
    teams_batch = []
    matches_batch = []
    stats_batch = []
    
    total_times = len(teams_ids)
    
    for index, team_id in enumerate(teams_ids, 1):
        print(f"   ⏳ [{index}/{total_times}] Extraindo dados do Time ID {team_id}...")
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&season={season}"
        
        try:
            # O timeout=10 impede que o script fique travado para sempre
            resposta = requests.get(url, headers=headers, timeout=10).json()
            
            if resposta.get('errors'):
                print(f"   🚨 Erro da API para o Time {team_id}: {resposta['errors']}")
                continue

            jogos = resposta.get('response', [])
            jogos_encerrados = [j for j in jogos if j['fixture']['status']['short'] in ['FT', 'PEN', 'AET']]
            ultimos_10 = jogos_encerrados[-10:]
            
            for j in ultimos_10:
                m_id = j['fixture']['id']
                teams_batch.append({'id': j['teams']['home']['id'], 'name': j['teams']['home']['name']})
                teams_batch.append({'id': j['teams']['away']['id'], 'name': j['teams']['away']['name']})
                matches_batch.append({'id': m_id, 'team_home': j['teams']['home']['id'], 'team_away': j['teams']['away']['id'], 'date': j['fixture']['date']})
                if j['goals']['home'] is not None:
                    stats_batch.append({'match_id': m_id, 'goals_home': j['goals']['home'], 'goals_away': j['goals']['away']})
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Falha de conexão ao tentar baixar o Time {team_id}. Ignorando...")
        
        # A MAGIA ACONTECE AQUI: Faz o script dormir 1.5 segundos para enganar o bloqueio da API
        time.sleep(1.5)

    # Limpando duplicatas de times para evitar erros no banco
    teams_batch = list({t['id']: t for t in teams_batch}.values())
    matches_batch = list({m['id']: m for m in matches_batch}.values())
    stats_batch = list({s['match_id']: s for s in stats_batch}.values())

    print(f"⚡ Disparando lote para o Supabase: {len(teams_batch)} times, {len(matches_batch)} jogos...")
    if teams_batch: supabase.table('teams').upsert(teams_batch).execute()
    if matches_batch: supabase.table('matches').upsert(matches_batch).execute()
    if stats_batch: supabase.table('stats').upsert(stats_batch).execute()

def calcular_poisson_lote(jogos_hoje):
    """Baixa o banco de dados UMA VEZ e calcula tudo na memória RAM"""
    print(f"🧠 [3/3] Calculando Inteligência Poisson para todos os jogos...")
    
    # Faz apenas UMA requisição ao Supabase para puxar tudo
    stats = supabase.table('stats').select('*').execute().data or []
    matches = supabase.table('matches').select('*').execute().data or []
    
    analysis_batch = []

    for jogo in jogos_hoje:
        match_id = jogo['fixture']['id']
        home_id = jogo['teams']['home']['id']
        away_id = jogo['teams']['away']['id']
        
        def obter_media_ataque(team_id):
            gols = 0; contagem = 0
            for m in matches:
                s = next((x for x in stats if x['match_id'] == m['id']), None)
                if s:
                    if m['team_home'] == team_id: gols += s['goals_home']; contagem += 1
                    elif m['team_away'] == team_id: gols += s['goals_away']; contagem += 1
            return gols / contagem if contagem > 0 else 0.1

        lambda_home = obter_media_ataque(home_id)
        lambda_away = obter_media_ataque(away_id)
        lambda_jogo = lambda_home + lambda_away

        def poisson(lmbd, x): return (math.exp(-lmbd) * (lmbd**x)) / math.factorial(x)

        prob_0_gols = poisson(lambda_jogo, 0)
        prob_1_gol = poisson(lambda_jogo, 1)
        prob_2_gols = poisson(lambda_jogo, 2)

        prob_over_0_5 = (1 - prob_0_gols) * 100
        prob_over_1_5 = (1 - (prob_0_gols + prob_1_gol)) * 100
        prob_over_2_5 = (1 - (prob_0_gols + prob_1_gol + prob_2_gols)) * 100
        prob_ambas_marcam = ((1 - poisson(lambda_home, 0)) * (1 - poisson(lambda_away, 0))) * 100

        analysis_batch.append({
            'match_id': match_id,
            'prob_goals': round(prob_over_0_5, 2),
            'prob_over_1_5': round(prob_over_1_5, 2),
            'prob_over_2_5': round(prob_over_2_5, 2),
            'prob_btts': round(prob_ambas_marcam, 2)
        })

    # Envia todos os resultados para o banco de uma vez só!
    if analysis_batch:
        supabase.table('analysis').upsert(analysis_batch).execute()

# ==========================================
# 3. EXECUÇÃO PRINCIPAL
# ==========================================
print("🤖 Iniciando Motor V2 (Modo Turbo - Bulk Operations)...")
ID_LIGA = 71
SEASON = 2024

jogos_hoje = buscar_jogos_do_dia(ID_LIGA, SEASON)

if not jogos_hoje:
    print("📅 Nenhum jogo encontrado ou erro na API.")
else:
    # 1. Pega os IDs únicos de todos os times que vão jogar
    times_ids = set()
    matches_do_dia = [] # 🚨 NOVA LISTA PARA GUARDAR OS JOGOS DE HOJE
    
    for jogo in jogos_hoje:
        times_ids.add(jogo['teams']['home']['id'])
        times_ids.add(jogo['teams']['away']['id'])
        
        # 🚨 Prepara o "jogo de hoje" para ser guardado no banco
        matches_do_dia.append({
            'id': jogo['fixture']['id'], 
            'team_home': jogo['teams']['home']['id'], 
            'team_away': jogo['teams']['away']['id'], 
            'date': jogo['fixture']['date']
        })
    
    # 2. Executa a extração em lote do Histórico
    extrair_historico_lote(times_ids, SEASON)
    
    # 🚨 2.5 SALVA OS JOGOS DE HOJE NO BANCO ANTES DA ANÁLISE (A CORREÇÃO DO ERRO)
    print(f"📌 Garantindo a existência de {len(matches_do_dia)} confrontos base no Supabase...")
    supabase.table('matches').upsert(matches_do_dia).execute()
    
    # 3. Executa o cálculo matemático em lote
    calcular_poisson_lote(jogos_hoje)

    print("\n🎉 Sucesso Absoluto! Banco de dados alimentado na velocidade da luz. ⚡")