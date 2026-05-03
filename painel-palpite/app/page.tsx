import { createClient } from '@supabase/supabase-js'

interface AnalysisItem {
  prob_goals: number;
  prob_over_1_5: number;
  prob_over_2_5: number;
  prob_btts: number;
  matches: {
    date: string;
    team_home: { name: string };
    team_away: { name: string };
  };
}

export const dynamic = 'force-dynamic'

export default async function Dashboard() {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )

  // Refatoração Senior para garantir o Join e buscar todas as projeções de IA
  const { data, error } = await supabase
    .from('analysis')
    .select(`
      prob_goals,
      prob_over_1_5,
      prob_over_2_5,
      prob_btts,
      matches!inner (
        date,
        team_home:teams!team_home ( name ),
        team_away:teams!team_away ( name )
      )
    `)

  const analyses = data as unknown as AnalysisItem[] | null;

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-10 font-mono">
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-6 rounded-lg max-w-2xl">
          <h2 className="font-bold text-xl mb-2">🚨 ERRO DE SCHEMA DETECTADO</h2>
          <p className="text-sm opacity-80 mb-4">O Banco de Dados não reconheceu o relacionamento ou as novas colunas.</p>
          <code className="block bg-black/50 p-3 rounded text-xs">{error.message}</code>
          <p className="mt-4 text-xs text-slate-400 italic">Dica: Verifique se rodou o comando SQL para adicionar as colunas prob_over_1_5, prob_over_2_5 e prob_btts.</p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-slate-900 text-white p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        
        <header className="mb-10 text-center">
          <div className="inline-block bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest mb-4 border border-green-500/30">
            SISTEMA OMNICHANNEL ATIVO
          </div>
          <h1 className="text-5xl font-black text-white mb-2 font-mono tracking-tighter">
            PALPITE<span className="text-green-500">CERTO</span>
          </h1>
          <p className="text-slate-500 text-xs uppercase tracking-[0.4em] font-light">
            Data Science & Software Architecture
          </p>
        </header>

        <div className="bg-slate-800/50 backdrop-blur-md rounded-2xl border border-slate-700/50 overflow-hidden shadow-2xl">
          <table className="w-full text-left border-separate border-spacing-0">
            <thead>
              <tr className="bg-slate-700/30 text-slate-400 text-[10px] uppercase tracking-widest">
                <th className="p-6 font-bold border-b border-slate-700 w-1/4">Data</th>
                <th className="p-6 font-bold border-b border-slate-700 text-center w-2/4">Confronto</th>
                <th className="p-6 font-bold border-b border-slate-700 text-right w-1/4">Projeções Poisson (IA)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {analyses && analyses.length > 0 ? (
                analyses.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-800/80 transition-all group cursor-default">
                    <td className="p-6 text-slate-400 text-sm font-mono italic">
                      {new Date(item.matches.date).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="p-6 text-center">
                      <div className="flex items-center justify-center gap-6">
                        <span className="text-base font-semibold group-hover:text-white text-slate-300 transition-colors uppercase">{item.matches.team_home.name}</span>
                        <div className="bg-slate-700 h-px w-8 relative">
                          <div className="absolute inset-0 bg-green-500 scale-x-0 group-hover:scale-x-100 transition-transform origin-left"></div>
                        </div>
                        <span className="text-base font-semibold group-hover:text-white text-slate-300 transition-colors uppercase">{item.matches.team_away.name}</span>
                      </div>
                    </td>
                    <td className="p-6 text-right">
                      {/* Grid de Métricas de Alta Performance */}
                      <div className="flex justify-end gap-2">
                        
                        <div className="bg-slate-900/60 border border-slate-700 rounded-md p-2 w-16 flex flex-col items-center justify-center group-hover:border-green-500/30 transition-colors">
                          <span className="text-sm font-black text-green-400 font-mono">{item.prob_goals.toFixed(0)}%</span>
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-wider mt-1">O0.5</span>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-700 rounded-md p-2 w-16 flex flex-col items-center justify-center group-hover:border-green-500/30 transition-colors">
                          <span className="text-sm font-black text-emerald-400 font-mono">{item.prob_over_1_5.toFixed(0)}%</span>
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-wider mt-1">O1.5</span>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-700 rounded-md p-2 w-16 flex flex-col items-center justify-center group-hover:border-green-500/30 transition-colors">
                          <span className="text-sm font-black text-teal-400 font-mono">{item.prob_over_2_5.toFixed(0)}%</span>
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-wider mt-1">O2.5</span>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-700 rounded-md p-2 w-16 flex flex-col items-center justify-center group-hover:border-purple-500/30 transition-colors">
                          <span className="text-sm font-black text-purple-400 font-mono">{item.prob_btts.toFixed(0)}%</span>
                          <span className="text-[8px] text-slate-500 font-bold uppercase tracking-wider mt-1">BTTS</span>
                        </div>

                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="p-32 text-center">
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-8 h-8 border-2 border-slate-700 border-t-green-500 rounded-full animate-spin"></div>
                      <p className="text-slate-600 font-mono text-sm tracking-widest uppercase">Aguardando Injeção de Dados via Python...</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <footer className="mt-12 flex justify-between items-center text-slate-600 text-[9px] uppercase tracking-[0.3em] font-mono border-t border-slate-800/50 pt-8">
          <div className="flex items-center gap-3">
            <div className="h-1.5 w-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse"></div>
            Production Environment
          </div>
          <div className="hover:text-slate-400 transition-colors">
            Dev: Carioca do Bugio • Engine: Atlas Develop
          </div>
        </footer>
      </div>
    </main>
  )
}