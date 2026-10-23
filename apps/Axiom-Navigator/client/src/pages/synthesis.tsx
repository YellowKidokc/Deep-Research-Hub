import { Layout } from "@/components/layout";
import { Link } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { RESEARCH_PAPERS } from "@/lib/research-data";
import { ArrowRight, Brain, Scale, Shield, Network, Zap, Church, BookOpen, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Synthesis() {
  const domains = [
    {
      id: "logic",
      title: "Logic",
      subtitle: "The Informational Ground",
      icon: Network,
      color: "text-blue-400",
      description: "Truth is not invented; it is discovered. Logic is the architecture of the Divine Mind.",
      papers: RESEARCH_PAPERS.filter(p => p.category === "Logic")
    },
    {
      id: "science",
      title: "Science",
      subtitle: "The Methodology",
      icon: Zap,
      color: "text-amber-400",
      description: "Restoring the 'Why' to scientific inquiry to heal the fragmentation of modern physics.",
      papers: RESEARCH_PAPERS.filter(p => ["Methodology", "Audit", "Polemic", "Synthesis"].includes(p.category))
    },
    {
      id: "psychology",
      title: "Psychology",
      subtitle: "The Consequence",
      icon: Brain,
      color: "text-purple-400",
      description: "Mental health collapse is an entropy problem. The soul requires connection to the Logos to function.",
      papers: RESEARCH_PAPERS.filter(p => p.category === "Psychology")
    },
    {
      id: "theology",
      title: "Theology",
      subtitle: "The Source",
      icon: Church,
      color: "text-rose-400",
      description: "Not a separate domain, but the root system. Thermodynamics and Grace are the same law.",
      papers: RESEARCH_PAPERS.filter(p => p.category === "Theology")
    },
    {
        id: "sociology",
        title: "Sociology",
        subtitle: "The Application",
        icon: Layers,
        color: "text-emerald-400",
        description: "Moral decay is not opinion; it is social entropy. Justice is a physical property of the universe.",
        papers: RESEARCH_PAPERS.filter(p => p.category === "Sociology")
    }
  ];

  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <Layers className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">The Unified Field</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            Cross-Domain Synthesis
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            Mapping the isomorphism of Truth across Logic, Science, Psychology, and Theology.
          </p>
        </header>

        <div className="grid gap-16">
          {domains.map((domain) => (
            <section key={domain.id} className="space-y-8">
              <div className="flex items-center gap-4 mb-8">
                <div className={cn("p-4 rounded-full bg-white/5 border border-white/10", domain.color)}>
                  <domain.icon className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-3xl font-display font-bold text-foreground">{domain.title}</h2>
                  <p className="text-sm font-mono text-primary uppercase tracking-widest mt-1">{domain.subtitle}</p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-card to-card/50 border border-border/50 col-span-full md:col-span-1">
                  <CardContent className="p-8 h-full flex flex-col justify-center">
                    <p className="font-serif text-xl italic leading-relaxed text-muted-foreground">
                      "{domain.description}"
                    </p>
                  </CardContent>
                </Card>

                {domain.papers.map((paper) => (
                  <Link key={paper.id} href="/research">
                    <Card className="bg-card/30 border border-border/30 hover:border-primary/50 hover:bg-white/5 transition-all duration-300 h-full cursor-pointer group">
                      <CardContent className="p-6 flex flex-col h-full">
                        <div className="mb-4">
                           <span className={cn("text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded border border-white/10", domain.color)}>
                             {paper.category}
                           </span>
                        </div>
                        <h3 className="font-display font-bold text-lg mb-2 group-hover:text-primary transition-colors">
                          {paper.title}
                        </h3>
                        <p className="text-sm text-muted-foreground flex-grow">
                          {paper.summary}
                        </p>
                        <div className="mt-4 flex justify-end">
                            <ArrowRight className="w-4 h-4 text-primary/50 group-hover:text-primary transition-colors" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </Layout>
  );
}
