import { Layout } from "@/components/layout";
import { GENERATIONS, getNarrative } from "@/lib/narrative-data";
import { Link, useRoute } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { ChevronRight, Clock, Users, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

export default function Generations({ params }: { params?: { narrativeId?: string } }) {
  const [match, paramsFromRoute] = useRoute("/generations/:narrativeId");
  const narrativeId = params?.narrativeId || paramsFromRoute?.narrativeId || GENERATIONS[0].id;
  const activeNarrative = getNarrative(narrativeId);

  if (!activeNarrative) return <div>Narrative not found</div>;

  const currentIndex = GENERATIONS.findIndex(g => g.id === narrativeId);
  const nextNarrative = GENERATIONS[currentIndex + 1];
  const prevNarrative = GENERATIONS[currentIndex - 1];

  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-2 text-primary/60 mb-2">
            <Users className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">Longitudinal Narrative</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold tracking-tight text-primary gold-glow">
            The Generations
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            A six-part case study tracing the trajectory of American coherence through a single bloodline (1900–2025).
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          {/* Navigation Sidebar */}
          <div className="lg:col-span-3 space-y-4">
            <div className="text-xs font-bold text-primary/50 uppercase tracking-[0.2em] mb-4">
              Timeline
            </div>
            {GENERATIONS.map((gen) => (
              <Link key={gen.id} href={`/generations/${gen.id}`}>
                <div className={cn(
                  "group cursor-pointer p-4 rounded-sm border transition-all duration-300 relative overflow-hidden",
                  gen.id === narrativeId 
                    ? "bg-primary/10 border-primary text-primary" 
                    : "bg-card/30 border-transparent hover:bg-white/5 hover:border-primary/30 text-muted-foreground"
                )}>
                  <div className="text-xs font-mono mb-1 opacity-70">{gen.year}</div>
                  <div className="font-display font-bold text-sm tracking-wide">{gen.subtitle}</div>
                  <div className="text-[10px] uppercase tracking-widest mt-2 opacity-50 group-hover:opacity-100 transition-opacity">
                    {gen.title}
                  </div>
                  
                  {gen.id === narrativeId && (
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-9 space-y-8">
            <Card className="bg-card border-border/50 overflow-hidden relative group">
              {/* Image Banner */}
              <div className="h-64 w-full bg-black/50 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent z-10" />
                <div className="absolute inset-0 flex items-end p-8 z-20">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 bg-primary text-black font-bold text-xs tracking-widest uppercase">
                        {activeNarrative.year}
                      </span>
                      <span className="text-primary/80 font-mono text-xs uppercase tracking-widest">
                        {activeNarrative.title}
                      </span>
                    </div>
                    <h2 className="text-4xl font-display font-bold text-white shadow-black drop-shadow-lg">
                      {activeNarrative.subtitle}
                    </h2>
                  </div>
                </div>
                {/* Abstract texture for image placeholder */}
                <div className="absolute inset-0 opacity-20 bg-[url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center grayscale mix-blend-overlay" />
              </div>

              <CardContent className="p-8 md:p-12">
                <div className="prose prose-invert max-w-none font-serif text-lg leading-relaxed text-muted-foreground">
                  <ReactMarkdown>{activeNarrative.content}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>

            {/* Footer Navigation */}
            <div className="flex justify-between items-center pt-8 border-t border-border/30">
              {prevNarrative ? (
                <Link href={`/generations/${prevNarrative.id}`}>
                  <div className="flex items-center gap-3 text-muted-foreground hover:text-primary transition-colors cursor-pointer group">
                    <ChevronRight className="w-5 h-5 rotate-180 group-hover:-translate-x-1 transition-transform" />
                    <div className="text-right">
                      <div className="text-[10px] uppercase tracking-widest opacity-50">Previous</div>
                      <div className="font-display font-bold">{prevNarrative.subtitle}</div>
                    </div>
                  </div>
                </Link>
              ) : <div />}

              {nextNarrative ? (
                <Link href={`/generations/${nextNarrative.id}`}>
                  <div className="flex items-center gap-3 text-muted-foreground hover:text-primary transition-colors cursor-pointer group">
                    <div className="text-right">
                      <div className="text-[10px] uppercase tracking-widest opacity-50">Next</div>
                      <div className="font-display font-bold">{nextNarrative.subtitle}</div>
                    </div>
                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>
              ) : <div />}
            </div>
          </div>

        </div>
      </div>
    </Layout>
  );
}
