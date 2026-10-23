import { Layout } from "@/components/layout";
import { RESEARCH_PAPERS } from "@/lib/research-data";
import { Link } from "wouter";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BookOpen, FileText, Brain, History, Settings, ArrowRight, ShieldCheck, Scale, Search, PenTool, LayoutTemplate, Network, Church, Layers } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function Research() {
  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <BookOpen className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">Deep Dive</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            Research Library
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            The rigorous empirical and theoretical work underpinning the Theophysics framework.
          </p>
        </header>

        <div className="grid gap-8">
          {RESEARCH_PAPERS.map((paper) => {
            let Icon = FileText;
            if (paper.category === "Neuroscience") Icon = Brain;
            if (paper.category === "History") Icon = History;
            if (paper.category === "Methodology") Icon = Settings;
            if (paper.category === "Audit") Icon = Search;
            if (paper.category === "Metrics") Icon = Scale;
            if (paper.category === "Polemic") Icon = PenTool;
            if (paper.category === "Synthesis") Icon = LayoutTemplate;
            if (paper.category === "Study") Icon = BookOpen;
            if (paper.category === "Logic") Icon = Network;
            if (paper.category === "Theology") Icon = Church;
            if (paper.category === "Psychology") Icon = Brain;
            if (paper.category === "Sociology") Icon = Layers;
            if (paper.category === "Defense") Icon = ShieldCheck;

            return (
              <Card key={paper.id} className="bg-card border border-border/50 hover:border-primary/50 transition-all duration-300 group overflow-hidden">
                <CardHeader className="relative pb-2">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 w-fit">
                      <Icon className="w-3 h-3 text-primary" />
                      <span className="text-[10px] font-bold uppercase tracking-widest text-primary">{paper.category}</span>
                    </div>
                    <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest border border-white/10 px-2 py-1 rounded">
                      {paper.status}
                    </div>
                  </div>
                  <CardTitle className="font-display font-bold text-2xl group-hover:text-primary transition-colors">
                    {paper.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <p className="font-serif text-muted-foreground text-lg leading-relaxed">
                    {paper.summary}
                  </p>
                  
                  <div className="max-h-0 group-hover:max-h-[500px] transition-[max-height] duration-700 ease-in-out overflow-hidden opacity-0 group-hover:opacity-100 delay-100">
                    <div className="pt-6 border-t border-border/30 mt-4 prose prose-invert prose-sm max-w-none text-muted-foreground/80">
                      <div className="bg-black/30 p-6 rounded-md border border-white/5 font-mono text-xs leading-relaxed max-h-[300px] overflow-hidden relative">
                         <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80 z-10" />
                        <ReactMarkdown 
                            components={{
                                table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="w-full text-xs border-collapse" {...props} /></div>,
                                thead: ({node, ...props}) => <thead className="bg-white/5 text-primary font-bold uppercase tracking-wider" {...props} />,
                                th: ({node, ...props}) => <th className="p-2 text-left border-b border-white/10" {...props} />,
                                td: ({node, ...props}) => <td className="p-2 border-b border-white/5" {...props} />,
                            }}
                        >
                          {paper.content.substring(0, 1000)}
                        </ReactMarkdown>
                      </div>
                    </div>
                    <div className="mt-4 flex justify-end">
                      <div className="text-xs font-bold text-primary uppercase tracking-widest flex items-center gap-2 cursor-pointer hover:underline">
                        Read Full Paper <ArrowRight className="w-4 h-4" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
