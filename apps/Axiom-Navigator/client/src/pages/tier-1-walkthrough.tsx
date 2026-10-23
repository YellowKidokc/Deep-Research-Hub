import { useState, useEffect } from "react";
import { Link, useLocation } from "wouter";
import { Sidebar } from "@/components/sidebar";
import { motion, AnimatePresence } from "framer-motion";
import { FULL_AXIOMS, TIER_1_CATEGORIES } from "@/lib/tier1-data";
import { 
  ArrowLeft, 
  ArrowRight, 
  BookOpen, 
  CheckCircle2, 
  AlertCircle,
  HelpCircle,
  Network,
  List,
  Database
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Tier1Walkthrough({ params }: { params: { axiomId: string } }) {
  const [location, setLocation] = useLocation();
  const currentId = params.axiomId || "AX-001";
  
  const currentIndex = FULL_AXIOMS.findIndex(a => a.id === currentId);
  const currentAxiom = FULL_AXIOMS[currentIndex];
  
  // Handlers for navigation
  const goToNext = () => {
    if (currentIndex < FULL_AXIOMS.length - 1) {
      setLocation(`/tier-1/walkthrough/${FULL_AXIOMS[currentIndex + 1].id}`);
    }
  };

  const goToPrev = () => {
    if (currentIndex > 0) {
      setLocation(`/tier-1/walkthrough/${FULL_AXIOMS[currentIndex - 1].id}`);
    }
  };

  const category = TIER_1_CATEGORIES.find(c => c.id === currentAxiom.tier);

  // If axiom not found
  if (!currentAxiom) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Axiom Not Found</h1>
          <Link href="/tier-1">
            <span className="text-primary hover:underline cursor-pointer">Return to Index</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      <Sidebar />
      <main className="flex-1 ml-64 relative overflow-hidden flex flex-col">
        {/* Background Elements */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
        
        {/* Top Navigation Bar */}
        <div className="border-b border-white/5 bg-background/50 backdrop-blur-md sticky top-0 z-20 px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/tier-1">
              <div className="p-2 rounded-full hover:bg-white/5 cursor-pointer transition-colors text-muted-foreground hover:text-primary" title="Back to Index">
                <List className="w-5 h-5" />
              </div>
            </Link>
            <div className="h-6 w-px bg-white/10" />
            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground">Axiom Walkthrough</span>
              <span className="text-sm font-display font-bold">{currentAxiom.id}: {currentAxiom.name}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={goToPrev}
              disabled={currentIndex === 0}
              className="p-2 rounded-lg border border-white/10 hover:border-primary/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:bg-white/5"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-mono text-muted-foreground w-20 text-center">
              {currentIndex + 1} / {FULL_AXIOMS.length}
            </span>
            <button 
              onClick={goToNext}
              disabled={currentIndex === FULL_AXIOMS.length - 1}
              className="p-2 rounded-lg border border-white/10 hover:border-primary/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:bg-white/5"
            >
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-8 py-12">
            
            {/* Category Header */}
            <div className="flex items-center gap-3 mb-8">
              <div className={cn("w-2 h-2 rounded-full", category?.color || "bg-primary")} />
              <span className="text-xs font-mono uppercase tracking-widest text-primary/70">
                {category?.name || "Unknown Tier"}
              </span>
              <span className="text-xs text-muted-foreground/50">•</span>
              <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                {currentAxiom.type} Type
              </span>
            </div>

            {/* Main Title & Statement */}
            <motion.div
              key={currentAxiom.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-12"
            >
              <h1 className="text-5xl font-display font-bold text-foreground mb-6 leading-tight">
                {currentAxiom.name}
              </h1>
              
              {currentAxiom.content ? (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-8 mb-8 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
                  <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground mb-4">Formal Statement</h3>
                  <p className="text-xl md:text-2xl font-serif italic text-primary/90 leading-relaxed">
                    "{currentAxiom.content.formal_statement}"
                  </p>
                </div>
              ) : (
                <div className="p-8 border border-dashed border-white/10 rounded-xl bg-white/[0.01] mb-8">
                  <div className="flex flex-col items-center justify-center text-center py-8">
                    <Database className="w-8 h-8 text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground">Detailed content for this axiom is being generated.</p>
                    <p className="text-xs text-muted-foreground/50 mt-2 font-mono">Template: {currentAxiom.status}</p>
                  </div>
                </div>
              )}

              {/* Explanatory Content */}
              {currentAxiom.content && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <div className="lg:col-span-2 space-y-8">
                    <section>
                      <h3 className="flex items-center gap-2 text-lg font-bold mb-4 text-foreground/90">
                        <BookOpen className="w-4 h-4 text-primary" />
                        The Explanation
                      </h3>
                      <p className="text-lg text-muted-foreground leading-relaxed">
                        {currentAxiom.content.description}
                      </p>
                    </section>

                    <section>
                      <h3 className="flex items-center gap-2 text-lg font-bold mb-4 text-foreground/90">
                        <Network className="w-4 h-4 text-blue-400" />
                        Key Analogy
                      </h3>
                      <div className="pl-4 border-l-2 border-blue-500/20">
                        <p className="text-muted-foreground italic">
                          {currentAxiom.content.analogy}
                        </p>
                      </div>
                    </section>

                    {currentAxiom.content.dependencies && (
                      <section className="pt-8 border-t border-white/5">
                        <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground block mb-4">Builds Upon</span>
                        <div className="flex flex-wrap gap-2">
                          {currentAxiom.content.dependencies.map(dep => (
                            <Link key={dep} href={`/tier-1/walkthrough/${dep}`}>
                              <span className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-xs font-mono cursor-pointer transition-colors">
                                {dep}
                              </span>
                            </Link>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>

                  <div className="lg:col-span-1 space-y-6">
                    <div className="bg-black/20 border border-white/5 rounded-xl p-6">
                      <h3 className="flex items-center gap-2 text-sm font-bold mb-4 text-amber-400">
                        <HelpCircle className="w-4 h-4" />
                        The Core Question
                      </h3>
                      <p className="text-sm font-medium leading-relaxed">
                        {currentAxiom.content.question}
                      </p>
                    </div>

                    <div className="bg-black/20 border border-white/5 rounded-xl p-6">
                      <h3 className="flex items-center gap-2 text-sm font-bold mb-4 text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                        Common Objections
                      </h3>
                      <div className="space-y-4">
                        {currentAxiom.content.objections?.map((obj, i) => (
                          <div key={i} className="text-sm">
                            <p className="font-medium text-red-300/80 mb-1">"{obj.objection}"</p>
                            <p className="text-muted-foreground pl-3 border-l border-white/10 text-xs leading-relaxed">
                              {obj.response}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}
