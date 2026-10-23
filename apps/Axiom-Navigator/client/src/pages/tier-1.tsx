import { Link } from "wouter";
import { Sidebar } from "@/components/sidebar";
import { motion } from "framer-motion";
import { TIER_1_CATEGORIES, SAMPLE_AXIOMS } from "@/lib/tier1-data";
import { 
  Database, 
  ArrowLeft,
  CheckCircle2,
  Clock,
  FileText,
  PlayCircle
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Tier1View() {
  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      <Sidebar />
      <main className="flex-1 ml-64 relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
        
        <div className="container max-w-7xl mx-auto px-12 py-12 relative z-10">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Link href="/horizon">
                <div className="p-2 rounded-full hover:bg-white/5 cursor-pointer transition-colors text-muted-foreground hover:text-primary">
                  <ArrowLeft className="w-5 h-5" />
                </div>
              </Link>
              <div className="flex items-center gap-2 text-xs font-mono text-primary/50 uppercase tracking-widest">
                <Database className="w-4 h-4" />
                <span>System Registry</span>
              </div>
            </div>

            <Link href="/tier-1/walkthrough/AX-001">
              <button className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-lg transition-all border border-primary/20 hover:border-primary/50">
                <PlayCircle className="w-4 h-4" />
                <span className="font-medium text-sm">Start Walkthrough</span>
              </button>
            </Link>
          </div>

          <header className="mb-12">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-4xl font-display font-bold text-foreground mb-4">
                Tier 1: Axiom Chain
              </h1>
              <p className="text-lg text-muted-foreground max-w-3xl leading-relaxed">
                The 188 foundational axioms of Theophysics. This chain moves from Primordial Primitives through Ontological Categories to Divine, Spiritual, and Human nature, culminating in Universal Laws and Eschatology.
              </p>
            </motion.div>
          </header>

          <div className="flex flex-col gap-12">
            {TIER_1_CATEGORIES.map((category, index) => {
              const categoryAxioms = SAMPLE_AXIOMS.filter(a => a.tier === category.id);
              
              return (
                <motion.section 
                  key={category.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.5 }}
                  className="relative"
                >
                  <div className="flex items-start gap-6">
                    {/* Timeline/Connector Line */}
                    <div className="hidden md:flex flex-col items-center mt-2">
                      <div className={cn("w-4 h-4 rounded-full border-2", 
                        category.status === "complete" ? "bg-primary border-primary" : "bg-transparent border-muted-foreground/30"
                      )} />
                      {index !== TIER_1_CATEGORIES.length - 1 && (
                        <div className="w-px h-full bg-white/5 my-2 min-h-[100px]" />
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-4">
                        <div className={cn("w-1 h-8 rounded-full", category.color)} />
                        <div>
                          <h2 className="text-xl font-display font-bold text-foreground">{category.name}</h2>
                          <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground">
                            <span className="bg-white/5 px-2 py-0.5 rounded">{category.range}</span>
                            <span>{category.count} Axioms</span>
                          </div>
                        </div>
                      </div>

                      <p className="text-sm text-muted-foreground mb-6 pl-5 border-l border-white/5">
                        {category.description}
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pl-5">
                        {categoryAxioms.length > 0 ? (
                          categoryAxioms.map((axiom) => (
                            <Link key={axiom.id} href={`/tier-1/walkthrough/${axiom.id}`}>
                              <div 
                                className="group p-4 rounded-lg border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-primary/20 transition-all cursor-pointer h-full flex flex-col"
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-[10px] font-mono text-primary/70">{axiom.id}</span>
                                  {axiom.status === "complete" ? (
                                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                  ) : (
                                    <Clock className="w-3 h-3 text-amber-500/50" />
                                  )}
                                </div>
                                <h3 className="font-medium text-sm text-foreground group-hover:text-primary transition-colors flex-1">{axiom.name}</h3>
                                <div className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground/50 border-t border-white/5 pt-2 flex justify-between items-center">
                                  <span>{axiom.type}</span>
                                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ArrowLeft className="w-3 h-3 rotate-180" />
                                  </div>
                                </div>
                              </div>
                            </Link>
                          ))
                        ) : (
                          <div className="col-span-full p-4 rounded-lg border border-white/5 border-dashed bg-white/[0.01] flex items-center justify-center gap-2 text-muted-foreground/40 text-sm">
                            <FileText className="w-4 h-4" />
                            <span>Axiom data loading...</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.section>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
