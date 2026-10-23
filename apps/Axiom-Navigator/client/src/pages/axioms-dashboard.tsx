import { useState } from "react";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { PHASES, AXIOMS } from "@/lib/data";
import { Sidebar } from "@/components/sidebar";
import { ChevronRight, ArrowRight, Circle, Box, Network, FileJson, Eye, Zap, Shield, Binary, Sparkles, Ghost, Scale, Infinity as InfinityIcon, Cpu } from "lucide-react";

const PHASE_ICONS: Record<string, any> = {
  "01_Ontology": Circle,
  "02_Substrate": Box,
  "03_Coherence": Network,
  "04_Compression": FileJson,
  "05_Observer": Eye,
  "06_Collapse": Zap,
  "07_Boundary": Shield,
  "08_Syzygy": Binary,
  "09_Grace": Sparkles,
  "10_Soul": Ghost,
  "11_Morality": Scale,
  "12_Destiny": InfinityIcon,
  "13_Unification": Cpu
};

export default function AxiomsDashboard() {
  const [hoveredPhase, setHoveredPhase] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      <Sidebar />
      <main className="flex-1 ml-64 relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 pointer-events-none" />
        
        <div className="container max-w-7xl mx-auto px-12 py-16 relative z-10">
          <header className="mb-16 text-center max-w-3xl mx-auto">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-5xl md:text-6xl font-display font-bold text-primary mb-6 tracking-tight gold-glow">
                The Axioms
              </h1>
              <p className="text-xl text-muted-foreground font-serif italic leading-relaxed">
                The immutable foundation of the Iron Chain. Thirteen phases of reality, from the first thought to the final unification.
              </p>
            </motion.div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
            {/* Connecting Line (Visual only, tricky to implement perfectly in grid, simpler to imply with order) */}
            
            {PHASES.map((phase, index) => {
              const Icon = PHASE_ICONS[phase];
              const phaseAxioms = AXIOMS.filter(a => a.phase === phase);
              const phaseName = phase.split('_')[1];
              const phaseNum = phase.split('_')[0];
              
              return (
                <Link key={phase} href={`/phase/${phase}`}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05, duration: 0.5 }}
                    onMouseEnter={() => setHoveredPhase(phase)}
                    onMouseLeave={() => setHoveredPhase(null)}
                    className="group relative h-full"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl border border-primary/20" />
                    
                    <div className="relative p-6 h-full border border-white/5 bg-black/40 backdrop-blur-sm rounded-xl hover:border-primary/30 transition-all duration-300 flex flex-col group-hover:translate-y-[-4px] group-hover:shadow-[0_10px_30px_-10px_rgba(212,175,55,0.15)]">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 group-hover:border-primary/50 group-hover:bg-primary/20 transition-all">
                            <Icon className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <div className="text-[10px] font-mono text-primary/50 uppercase tracking-widest">Phase {phaseNum}</div>
                            <h3 className="text-xl font-display font-bold text-foreground group-hover:text-primary transition-colors">{phaseName}</h3>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 text-primary/30 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      
                      {/* Content Preview */}
                      <div className="space-y-2 mb-6 flex-1">
                        {phaseAxioms.slice(0, 3).map((axiom) => (
                          <div key={axiom.id} className="flex items-center gap-2 text-sm text-muted-foreground group-hover:text-muted-foreground/80">
                            <div className="w-1 h-1 rounded-full bg-primary/30" />
                            <span className="line-clamp-1 text-xs font-mono opacity-70">{axiom.title}</span>
                          </div>
                        ))}
                        {phaseAxioms.length > 3 && (
                          <div className="text-[10px] text-primary/40 pl-3 italic">+ {phaseAxioms.length - 3} more axioms</div>
                        )}
                      </div>

                      {/* Progress/Status Indicator */}
                      <div className="w-full bg-white/5 h-0.5 mt-auto rounded-full overflow-hidden">
                        <div className="h-full bg-primary/50 w-full origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-700 ease-out" />
                      </div>
                    </div>
                  </motion.div>
                </Link>
              );
            })}
          </div>
          
          <div className="mt-20 text-center">
            <div className="inline-flex items-center gap-4 px-6 py-3 rounded-full bg-primary/5 border border-primary/10">
              <span className="text-xs font-mono text-primary/70 uppercase tracking-widest">System Status: Coherent</span>
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
