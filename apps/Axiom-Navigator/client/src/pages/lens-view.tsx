import { Layout } from "@/components/layout";
import { AXIOMS, Axiom } from "@/lib/data";
import { useRoute, Link } from "wouter";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ArrowRight, Microscope, Atom, Network, BookOpen } from "lucide-react";

type LensType = "Physics" | "Philosophy" | "Systems";

const LENS_CONFIG: Record<LensType, { icon: React.ElementType, description: string, filter: (a: Axiom) => boolean }> = {
  Physics: {
    icon: Atom,
    description: "Axioms related to dynamics, state change, and conservation laws.",
    filter: (a) => a.tags.includes("physics") || a.tags.includes("dynamics") || a.tags.includes("metaphysics")
  },
  Philosophy: {
    icon: BookOpen,
    description: "Epistemological constraints and definitions of truth within the system.",
    filter: (a) => a.tags.includes("epistemology") || a.tags.includes("core") || a.role === "Axiom"
  },
  Systems: {
    icon: Network,
    description: "Cybernetics, feedback loops, and architectural heuristics.",
    filter: (a) => a.tags.includes("systems") || a.tags.includes("cybernetics") || a.tags.includes("complexity")
  }
};

export default function LensView() {
  const [match, params] = useRoute("/lens/:lensId");
  
  if (!match) return null;
  
  const lensId = params.lensId as LensType;
  const config = LENS_CONFIG[lensId];

  if (!config) return null;

  const Icon = config.icon;
  const axioms = AXIOMS.filter(config.filter);

  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="flex flex-col gap-4 pb-8 border-b border-border/40">
          <div className="flex items-center gap-2 text-xs font-mono text-primary/60 uppercase tracking-[0.3em]">
            <Microscope className="w-4 h-4" />
            Curated Lens
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold text-foreground uppercase tracking-wider flex items-center gap-6">
            {lensId} <Icon className="w-12 h-12 text-primary/20" />
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl font-serif italic border-l-2 border-primary/20 pl-4">
            {config.description}
          </p>
        </header>

        <div className="space-y-8">
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-primary/50">Canonical Sequence</h2>
          <div className="relative border-l border-primary/30 ml-4 pl-12 space-y-12 py-4">
            {axioms.map((axiom, index) => (
              <div key={axiom.id} className="relative">
                {/* Timeline node */}
                <div className="absolute -left-[58px] top-2 w-7 h-7 rounded-full bg-background border-2 border-primary text-primary flex items-center justify-center text-[10px] font-bold font-mono shadow-[0_0_10px_rgba(212,175,55,0.4)]">
                  {index + 1}
                </div>
                
                <Link href={`/axiom/${axiom.id}`}>
                  <Card className="group cursor-pointer bg-card border border-border hover:border-primary/50 hover:bg-white/5 transition-all duration-300 rounded-sm">
                    <CardHeader className="py-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4">
                          <span className="font-mono text-xs text-primary/50 font-bold uppercase tracking-widest">{axiom.id}</span>
                          <CardTitle className="font-display text-xl text-foreground group-hover:text-primary transition-colors tracking-wide">
                            {axiom.title}
                          </CardTitle>
                        </div>
                        <ArrowRight className="w-4 h-4 text-primary opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-1" />
                      </div>
                    </CardHeader>
                    <CardContent className="py-2 pb-5 text-lg text-muted-foreground font-serif leading-relaxed line-clamp-2">
                      {axiom.content}
                    </CardContent>
                  </Card>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
