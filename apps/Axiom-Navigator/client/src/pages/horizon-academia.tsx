import { Link } from "wouter";
import { Sidebar } from "@/components/sidebar";
import { motion } from "framer-motion";
import { 
  Library, 
  Scroll, 
  Database, 
  Brain, 
  Microscope, 
  Network,
  ArrowRight,
  ShieldCheck,
  FileText
} from "lucide-react";

export default function HorizonAcademia() {
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
              <div className="flex items-center justify-center gap-2 mb-4">
                <div className="h-[1px] w-12 bg-primary/50" />
                <span className="text-xs font-mono text-primary uppercase tracking-[0.3em]">Horizon Academia</span>
                <div className="h-[1px] w-12 bg-primary/50" />
              </div>
              <h1 className="text-5xl md:text-6xl font-display font-bold text-primary mb-6 tracking-tight gold-glow">
                The Academy
              </h1>
              <p className="text-xl text-muted-foreground font-serif italic leading-relaxed">
                "Academia only solve problems in Tier 1." <br/>
                The rigorous study of the 188-Axiom Chain and the foundational mathematics of Theophysics.
              </p>
            </motion.div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
            <Link href="/tier-1">
              <motion.div 
                whileHover={{ y: -5 }}
                className="group relative overflow-hidden rounded-xl border border-primary/20 bg-black/40 backdrop-blur-sm p-8 cursor-pointer hover:border-primary/50 transition-all duration-300"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-6 border border-primary/20 group-hover:border-primary/50">
                    <Database className="w-6 h-6 text-primary" />
                  </div>
                  <h2 className="text-2xl font-display font-bold text-foreground mb-2 group-hover:text-primary transition-colors">Tier 1: The Axiom Chain</h2>
                  <p className="text-muted-foreground mb-6 line-clamp-2">
                    Access the complete 188-Axiom structure, spanning from Primordial Primitives to Eschatological Laws.
                  </p>
                  <div className="flex items-center gap-2 text-xs font-mono text-primary uppercase tracking-wider">
                    Explore Database <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </motion.div>
            </Link>

            <Link href="/research">
              <motion.div 
                whileHover={{ y: -5 }}
                className="group relative overflow-hidden rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-8 cursor-pointer hover:border-primary/30 transition-all duration-300"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mb-6 border border-blue-500/20 group-hover:border-blue-500/50">
                    <Library className="w-6 h-6 text-blue-400" />
                  </div>
                  <h2 className="text-2xl font-display font-bold text-foreground mb-2 group-hover:text-blue-400 transition-colors">Research Library</h2>
                  <p className="text-muted-foreground mb-6 line-clamp-2">
                    Deep dive into the Logos Papers, Manifestos, and supporting research documents.
                  </p>
                  <div className="flex items-center gap-2 text-xs font-mono text-blue-400 uppercase tracking-wider">
                    View Documents <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </motion.div>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-lg border border-white/5 bg-white/5 backdrop-blur-sm">
              <ShieldCheck className="w-8 h-8 text-emerald-500 mb-4" />
              <h3 className="font-display font-bold text-lg mb-2">Validation Protocols</h3>
              <p className="text-sm text-muted-foreground">Rigorous testing of axioms against empirical data and theological consistency.</p>
            </div>
            
            <div className="p-6 rounded-lg border border-white/5 bg-white/5 backdrop-blur-sm">
              <Network className="w-8 h-8 text-amber-500 mb-4" />
              <h3 className="font-display font-bold text-lg mb-2">Dependency Mapping</h3>
              <p className="text-sm text-muted-foreground">Visualizing the causal chains between axioms, laws, and observable reality.</p>
            </div>

            <div className="p-6 rounded-lg border border-white/5 bg-white/5 backdrop-blur-sm">
              <Microscope className="w-8 h-8 text-purple-500 mb-4" />
              <h3 className="font-display font-bold text-lg mb-2">Falsification Tests</h3>
              <p className="text-sm text-muted-foreground">Scientific methodology applied to spiritual claims to ensure robustness.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
