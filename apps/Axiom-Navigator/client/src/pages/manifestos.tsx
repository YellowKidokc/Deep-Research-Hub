import { Layout } from "@/components/layout";
import { MANIFESTOS } from "@/lib/manifesto-data";
import { Card, CardContent } from "@/components/ui/card";
import { FileText, AlertTriangle, ShieldCheck } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

export default function Manifestos() {
  return (
    <Layout>
      <div className="space-y-16 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <FileText className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">Core Documentation</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            Manifestos & Proofs
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            The foundational texts establishing Theophysics as a deductively complete framework.
          </p>
        </header>

        <div className="grid gap-16">
          {MANIFESTOS.map((manifesto, index) => (
            <section key={manifesto.id} className="space-y-6 scroll-mt-24" id={manifesto.id}>
              <div className="flex items-center gap-4">
                <span className="text-6xl font-display font-bold text-primary/20">{manifesto.number}</span>
                <div>
                  <h2 className="text-3xl font-display font-bold text-foreground">{manifesto.title}</h2>
                  <p className="text-sm font-mono text-primary uppercase tracking-widest mt-1">{manifesto.subtitle}</p>
                </div>
              </div>
              
              <Card className="bg-card/50 border border-border/50 hover:border-primary/50 transition-all duration-300 group overflow-hidden relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                <CardContent className="p-8 md:p-12 space-y-6 relative z-10">
                  <div className="prose prose-invert max-w-none font-serif text-muted-foreground text-lg leading-relaxed">
                     <ReactMarkdown 
                        components={{
                          h1: ({node, ...props}) => <h1 className="text-2xl font-display font-bold text-foreground mt-8 mb-4 hidden" {...props} />, // Hide h1 as it's the title
                          h2: ({node, ...props}) => <h2 className="text-xl font-display font-bold text-foreground mt-8 mb-4 border-b border-white/10 pb-2" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-lg font-display font-bold text-primary mt-6 mb-3 uppercase tracking-widest" {...props} />,
                          blockquote: ({node, ...props}) => (
                            <div className="border-l-2 border-primary/30 pl-6 py-2 my-8 italic text-primary/80 bg-primary/5 rounded-r-lg" {...props} />
                          ),
                          ul: ({node, ...props}) => <ul className="list-none pl-0 space-y-2 my-6" {...props} />,
                          li: ({node, ...props}) => <li className="pl-4 border-l border-white/10" {...props} />,
                          strong: ({node, ...props}) => <strong className="text-foreground font-semibold" {...props} />,
                          table: ({node, ...props}) => <div className="overflow-x-auto my-8"><table className="w-full text-sm border-collapse" {...props} /></div>,
                          thead: ({node, ...props}) => <thead className="bg-white/5 text-primary font-bold uppercase tracking-wider" {...props} />,
                          th: ({node, ...props}) => <th className="p-3 text-left border-b border-white/10" {...props} />,
                          td: ({node, ...props}) => <td className="p-3 border-b border-white/5" {...props} />,
                        }}
                     >
                       {manifesto.content}
                     </ReactMarkdown>

                     {manifesto.id === "top-down-framework" && (
                        <div className="grid md:grid-cols-3 gap-4 mt-8 not-prose">
                          <div className="flex flex-col gap-3 p-4 rounded bg-white/5 border border-white/5 hover:border-destructive/30 transition-colors">
                            <div className="flex items-center gap-2 text-destructive font-bold text-xs uppercase tracking-wider">
                              <AlertTriangle className="w-4 h-4" />
                              Semantic Collapse
                            </div>
                            <span className="text-sm leading-relaxed text-muted-foreground"><strong>Logos Rejection:</strong> When truth becomes subjective, language loses meaning and tribe formation begins.</span>
                          </div>
                          <div className="flex flex-col gap-3 p-4 rounded bg-white/5 border border-white/5 hover:border-destructive/30 transition-colors">
                            <div className="flex items-center gap-2 text-destructive font-bold text-xs uppercase tracking-wider">
                              <AlertTriangle className="w-4 h-4" />
                              Moral Entropy
                            </div>
                            <span className="text-sm leading-relaxed text-muted-foreground"><strong>Self-Definition:</strong> Closed systems cannot self-correct. Morality fragments into competing preferences.</span>
                          </div>
                          <div className="flex flex-col gap-3 p-4 rounded bg-white/5 border border-white/5 hover:border-destructive/30 transition-colors">
                            <div className="flex items-center gap-2 text-destructive font-bold text-xs uppercase tracking-wider">
                              <AlertTriangle className="w-4 h-4" />
                              Economic Collapse
                            </div>
                            <span className="text-sm leading-relaxed text-muted-foreground"><strong>Fiat Reality:</strong> Value detached from work violates conservation laws, leading to inevitable debt spiral.</span>
                          </div>
                        </div>
                     )}

                     {manifesto.id === "scientific-method-redux" && (
                       <div className="grid md:grid-cols-2 gap-4 mt-8 not-prose">
                          <div className="p-5 bg-secondary/10 rounded border border-border/30 hover:bg-primary/5 transition-colors">
                            <strong className="text-foreground block mb-2 font-display text-lg">Meta-Patterns</strong>
                            <p className="text-sm opacity-80">If the same pattern shows up in Physics and Theology, it's the same Truth.</p>
                          </div>
                          <div className="p-5 bg-secondary/10 rounded border border-border/30 hover:bg-primary/5 transition-colors">
                            <strong className="text-foreground block mb-2 font-display text-lg">Universal Language</strong>
                            <p className="text-sm opacity-80">Information Theory is the code of reality. It explains Atoms and Angels.</p>
                          </div>
                          <div className="p-5 bg-secondary/10 rounded border border-border/30 hover:bg-primary/5 transition-colors">
                            <strong className="text-foreground block mb-2 font-display text-lg">Causal Truth</strong>
                            <p className="text-sm opacity-80">We don't want correlations. We want the Cause.</p>
                          </div>
                          <div className="p-5 bg-secondary/10 rounded border border-border/30 hover:bg-primary/5 transition-colors">
                            <strong className="text-foreground block mb-2 font-display text-lg">Occam's Veto</strong>
                            <p className="text-sm opacity-80">If your theory needs 100 dimensions to work, it's a fiction.</p>
                          </div>
                        </div>
                     )}
                  </div>
                </CardContent>
              </Card>
            </section>
          ))}
        </div>
      </div>
    </Layout>
  );
}
