import { Layout } from "@/components/layout";
import MasterEquationSimulator from "@/components/master-equation-simulator";
import FruitsScorer from "@/components/fruits-scorer";
import { Link } from "wouter";
import { ArrowRight, Activity, Scale, Info } from "lucide-react";

export default function Metrics() {
  return (
    <Layout>
      <div className="space-y-16 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <Scale className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">System Metrics</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            Coherence Metrics
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            Operational tools for measuring and simulating system coherence.
            <br />
            <span className="text-primary/70 text-lg italic">"Entropy ↑ as Coherence ↓"</span>
          </p>
        </header>

        <section className="space-y-12">
          
          {/* Simulator Section */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display font-bold text-foreground flex items-center gap-3">
                <Activity className="w-6 h-6 text-primary" />
                The Master Equation
              </h2>
              <div className="px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-xs font-mono text-primary/80">
                SIMULATION V1.0
              </div>
            </div>
            <p className="text-muted-foreground font-serif max-w-2xl">
              Simulate the trajectory of any system based on its internal entropy (Sin), external input (Grace), and reception capacity (Faith). 
              See the mathematical inevitability of collapse in closed systems.
            </p>
            <MasterEquationSimulator />
          </div>

          <div className="w-full h-px bg-border/30 my-16"></div>

          {/* Scorer Section */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display font-bold text-foreground flex items-center gap-3">
                <Scale className="w-6 h-6 text-primary" />
                Fruits of the Spirit Scorer
              </h2>
              <div className="px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-xs font-mono text-primary/80">
                ANALYSIS V1.0
              </div>
            </div>
            <p className="text-muted-foreground font-serif max-w-2xl">
              A text analysis engine that evaluates documents for "Structural Coherence Invariants" (The 12 Fruits). 
              Determine if a manifesto, policy, or theory is generative (Coherent) or extractive (Entropic).
            </p>
            <FruitsScorer />
          </div>

        </section>
      </div>
    </Layout>
  );
}
