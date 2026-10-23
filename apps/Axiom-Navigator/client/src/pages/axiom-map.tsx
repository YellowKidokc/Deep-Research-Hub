import { Layout } from "@/components/layout";
import AxiomDependencyGraph from "@/components/axiom-dependency-graph";
import FalsificationMatrix from "@/components/falsification-matrix";
import { Link } from "wouter";
import { Network, ShieldAlert, GitBranch } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function AxiomMap() {
  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <Network className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">Structural Architecture</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            Axiom Map
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            The logical skeleton of the argument. Trace dependencies from primitives to conclusions, 
            and identify the "Kill Switches" that would falsify the entire system.
          </p>
        </header>

        <Tabs defaultValue="dependency" className="space-y-8">
          <TabsList className="bg-secondary/20 border border-white/10 p-1">
            <TabsTrigger value="dependency" className="gap-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
              <GitBranch className="w-4 h-4" />
              Dependency Chain
            </TabsTrigger>
            <TabsTrigger value="falsification" className="gap-2 data-[state=active]:bg-destructive/20 data-[state=active]:text-destructive">
              <ShieldAlert className="w-4 h-4" />
              Falsification Matrix
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dependency" className="space-y-6 focus-visible:outline-none">
            <div className="flex justify-between items-end mb-4">
               <div>
                <h2 className="text-2xl font-display font-bold">The Iron Chain</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Click any node to reveal its logical ancestors (blue) and descendants (red).
                </p>
               </div>
               <div className="text-xs font-mono text-primary/50 uppercase tracking-widest border border-primary/20 px-3 py-1 rounded-full">
                 Tier 0 → Tier 6
               </div>
            </div>
            <AxiomDependencyGraph />
          </TabsContent>

          <TabsContent value="falsification" className="space-y-6 focus-visible:outline-none">
            <div className="flex justify-between items-end mb-4">
               <div>
                <h2 className="text-2xl font-display font-bold text-destructive">Kill Switches</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  The explicit conditions that would disprove the framework.
                </p>
               </div>
            </div>
            <FalsificationMatrix />
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
