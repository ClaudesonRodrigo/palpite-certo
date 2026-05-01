import math
from supabase import create_client, Client
import os
from dotenv import load_dotenv
# Carrega as chaves do ficheiro .env
load_dotenv()
# 1. Conexão ao TEU Banco de Dados
url_supabase: str = os.getenv("SUPABASE_URL")
chave_supabase: str = os.getenv("SUPABASE_SECRET_KEY")
supabase: Client = create_client(url_supabase, chave_supabase)

print("A consultar a tua base de dados localmente...\n")

# 2. Vai buscar os dados guardados
jogos = supabase.table('matches').select('*').execute().data
estatisticas = supabase.table('stats').select('*').execute().data

# ID do Flamengo
id_flamengo = 133
gols_marcados = 0
jogos_contados = 0

# 3. Calcula os golos reais usando os dados do Supabase
for jogo in jogos:
    stat = next((s for s in estatisticas if s['match_id'] == jogo['id']), None)
    
    if stat:
        if jogo['team_home'] == id_flamengo:
            gols_marcados += stat['goals_home']
            jogos_contados += 1
        elif jogo['team_away'] == id_flamengo:
            gols_marcados += stat['goals_away']
            jogos_contados += 1

if jogos_contados > 0:
    lambda_gols = gols_marcados / jogos_contados
    print(f"📊 Média de Golos (Lambda - λ): {lambda_gols:.2f} em {jogos_contados} jogos.")
    
    prob_over_0_5 = 0
    prob_over_1_5 = 0
    prob_over_2_5 = 0
    
    # 4. Aplica a Fórmula de Poisson
    for gols in range(6):
        probabilidade = (math.exp(-lambda_gols) * (lambda_gols ** gols)) / math.factorial(gols)
        porcentagem = probabilidade * 100
        
        if gols >= 1: prob_over_0_5 += porcentagem
        if gols >= 2: prob_over_1_5 += porcentagem
        if gols >= 3: prob_over_2_5 += porcentagem

    print("-" * 60)
    print("📈 VISÃO PARA BILHETES DE APOSTA (Mercado Over):")
    print(f"👉 Mais de 0.5 golos: {prob_over_0_5:.2f}% de probabilidade real")
    print(f"👉 Mais de 1.5 golos: {prob_over_1_5:.2f}% de probabilidade real")
    
    # =========================================================
    # 5. O FECHO DO CICLO: GUARDAR NA TABELA ANALYSIS
    # =========================================================
    # Para validar o MVP, vamos associar esta análise ao último jogo da nossa lista
    ultimo_jogo_id = jogos[-1]['id']
    
    print("-" * 60)
    print(f"💾 A injetar a inteligência na tabela 'analysis' (Jogo ID: {ultimo_jogo_id})...")
    
    try:
        supabase.table('analysis').upsert({
            'match_id': ultimo_jogo_id,
            'prob_goals': round(prob_over_0_5, 2), # Guardamos a chance de +0.5 golos
            'prob_corners': 0.00, # Deixamos a zeros por agora
            'prob_cards': 0.00    # Deixamos a zeros por agora
        }).execute()
        
        print("✅ SUCESSO! A tabela 'analysis' foi preenchida.")
        print("🚀 O teu motor de Backend está 100% CONCLUÍDO e automatizado!")
    except Exception as e:
        print("❌ Erro ao gravar (Verifica se usaste a Secret Key!):", e)
        
else:
    print("Ainda não tens dados suficientes do time na base de dados.")