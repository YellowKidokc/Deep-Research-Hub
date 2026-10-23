import { Layout } from "@/components/layout";
import { getAxiomsByPhase, Phase, getNextPhase, getPrevPhase } from "@/lib/data";
import { useRoute, Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, BookOpen, Shield, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  Canonical: "text-emerald-400 border-emerald-400/30 bg-emerald-400/5",
  Provisional: "text-amber-400 border-amber-400/30 bg-amber-400/5",
  Theoretical: "text-blue-400 border-blue-400/30 bg-blue-400/5",
  Derived: "text-purple-400 border-purple-400/30 bg-purple-400/5",
  Deprecated: "text-slate-500 border-slate-500/30 bg-slate-500/5 line-through opacity-70",
};

export default function PhaseView() {
  const [match, params] = useRoute("/phase/:phaseId");
  
  if (!match) return null;
  
  const phase = params.phaseId as Phase;
  const axioms = getAxiomsByPhase(phase);
  
  const prevPhase = getPrevPhase(phase);
  const nextPhase = getNextPhase(phase);

  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="flex flex-col gap-4 pb-8 border-b border-border/40">
          <div className="flex justify-between items-start">
             <div>
                <div className="text-xs font-mono text-primary/60 uppercase tracking-[0.3em]">
                  Phase Collection
                </div>
                <h1 className="text-5xl md:text-6xl font-display font-bold text-foreground uppercase tracking-wider mt-2">
                  {phase.split('_')[1]}
                  <span className="text-primary/20 ml-4 text-4xl">{phase.split('_')[0]}</span>
                </h1>
             </div>
             
             {/* Phase Navigation */}
             <div className="flex items-center gap-2">
               {prevPhase && (
                 <Link href={`/phase/${prevPhase}`}>
                   <div className="p-2 rounded-full border border-border hover:border-primary/50 hover:bg-primary/10 cursor-pointer transition-all" title={`Previous: ${prevPhase}`}>
                     <ChevronLeft className="w-5 h-5 text-muted-foreground hover:text-primary" />
                   </div>
                 </Link>
               )}
               {nextPhase && (
                 <Link href={`/phase/${nextPhase}`}>
                   <div className="p-2 rounded-full border border-border hover:border-primary/50 hover:bg-primary/10 cursor-pointer transition-all" title={`Next: ${nextPhase}`}>
                     <ChevronRight className="w-5 h-5 text-muted-foreground hover:text-primary" />
                   </div>
                 </Link>
               )}
             </div>
          </div>
          
          <p className="text-xl text-muted-foreground max-w-2xl font-serif italic border-l-2 border-primary/20 pl-4">
            Axioms defined within the {phase.split('_')[1]} phase representing a distinct stage of logical reconstruction.
          </p>
        </header>

        <div className="grid gap-6">
          {axioms.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-border rounded-sm bg-black/20">
              <p className="text-muted-foreground font-serif italic text-lg">No axioms defined for this phase yet.</p>
            </div>
          ) : (
            axioms.map((axiom) => (
              <Link key={axiom.id} href={`/axiom/${axiom.id}`}>
                <Card className="group cursor-pointer bg-card border border-border hover:border-primary/50 transition-all duration-300 rounded-sm overflow-hidden relative">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary/0 group-hover:bg-primary transition-all duration-300"></div>
                  <CardHeader className="pb-3 pt-6 pl-8">
                    <div className="flex justify-between items-start">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-mono text-xs text-primary/70 font-bold tracking-widest uppercase">
                            {axiom.id}
                          </span>
                          <Badge variant="outline" className={cn("text-[10px] px-2 py-0.5 h-auto font-mono uppercase tracking-wider rounded-sm", STATUS_COLORS[axiom.status] || "")}>
                            {axiom.status}
                          </Badge>
                        </div>
                        <CardTitle className="font-display text-2xl group-hover:text-primary transition-colors tracking-wide">
                          {axiom.title}
                        </CardTitle>
                      </div>
                      <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all mr-2" />
                    </div>
                  </CardHeader>
                  <CardContent className="pl-8">
                    <p className="text-muted-foreground line-clamp-2 leading-relaxed font-serif text-lg">
                      {axiom.content}
                    </p>
                  </CardContent>
                  <CardFooter className="pt-2 pb-6 pl-8 flex gap-6 text-xs text-muted-foreground uppercase tracking-widest font-bold opacity-60">
                    <div className="flex items-center gap-2">
                      <Shield className="w-3 h-3" />
                      {axiom.authority}
                    </div>
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-3 h-3" />
                      {axiom.role}
                    </div>
                  </CardFooter>
                </Card>
              </Link>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}

