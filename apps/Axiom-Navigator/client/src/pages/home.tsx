import { Layout } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PHASES } from "@/lib/data";
import { Link } from "wouter";
import { ArrowRight, Terminal } from "lucide-react";

export default function Home() {
  return (
    <Layout>
      <div className="space-y-16 animate-in fade-in duration-700 slide-in-from-bottom-8">
        <header className="space-y-6 border-b border-border/40 pb-12">
          <div className="flex items-center gap-3 text-primary/60 mb-4">
            <Terminal className="w-5 h-5" />
            <span className="text-xs font-mono tracking-[0.3em] uppercase">System Root Access</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-display font-bold tracking-tight text-primary gold-glow">
            The Iron Chain
            <br />
            Navigator
          </h1>
          <p className="text-2xl text-muted-foreground max-w-3xl leading-relaxed font-serif font-light border-l-2 border-primary/30 pl-6 py-2">
            The canonical interface for the logical reconstruction of reality from first principles. <br/>
            Navigate the spine of truth, from <span className="text-foreground">Ontology</span> to <span className="text-foreground">Unification</span>.
          </p>
        </header>

        <section className="grid md:grid-cols-2 gap-12">
          <div className="space-y-8">
            <div className="space-y-4">
              <h2 className="text-xl font-display font-bold text-foreground border-b border-primary/20 pb-2 inline-block">
                Logical Reconstruction
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed font-serif">
                This system visualizes the <strong>Iron Chain Spine</strong>, a deterministic sequence of 13 axiomatic stages. 
                Traverse the 13 phases of the framework to understand the physics of the system.
              </p>
            </div>
            
            <div className="flex gap-3 flex-wrap">
              <span className="inline-flex items-center px-4 py-1 rounded-sm text-xs font-bold uppercase tracking-widest border border-primary/30 text-primary bg-primary/5">
                Read-Only
              </span>
              <span className="inline-flex items-center px-4 py-1 rounded-sm text-xs font-bold uppercase tracking-widest border border-primary/30 text-primary bg-primary/5">
                Canonical
              </span>
              <span className="inline-flex items-center px-4 py-1 rounded-sm text-xs font-bold uppercase tracking-widest border border-primary/30 text-primary bg-primary/5">
                Spine v3.0
              </span>
            </div>
          </div>

          <Card className="bg-card border border-primary/20 hover:border-primary/50 transition-colors shadow-[0_0_30px_rgba(0,0,0,0.5)]">
            <CardHeader>
              <CardTitle className="font-display text-2xl text-primary tracking-wide">Quick Access</CardTitle>
              <CardDescription className="font-serif italic text-muted-foreground">Jump to critical phases</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3">
              <Link href="/phase/01_Ontology">
                <div className="flex items-center justify-between p-4 rounded-sm border border-border bg-black/20 hover:bg-primary/10 hover:border-primary/50 cursor-pointer transition-all group">
                  <span className="font-display font-bold tracking-wider text-sm group-hover:translate-x-1 transition-transform text-foreground">01_Ontology</span>
                  <ArrowRight className="w-4 h-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
              <Link href="/phase/05_Observer">
                <div className="flex items-center justify-between p-4 rounded-sm border border-border bg-black/20 hover:bg-primary/10 hover:border-primary/50 cursor-pointer transition-all group">
                  <span className="font-display font-bold tracking-wider text-sm group-hover:translate-x-1 transition-transform text-foreground">05_Observer</span>
                  <ArrowRight className="w-4 h-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
              <Link href="/phase/09_Grace">
                <div className="flex items-center justify-between p-4 rounded-sm border border-border bg-black/20 hover:bg-primary/10 hover:border-primary/50 cursor-pointer transition-all group">
                  <span className="font-display font-bold tracking-wider text-sm group-hover:translate-x-1 transition-transform text-foreground">09_Grace</span>
                  <ArrowRight className="w-4 h-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            </CardContent>
          </Card>
        </section>

        <section>
           <h2 className="text-2xl font-display font-bold mb-8 text-foreground flex items-center gap-4">
             <span className="w-8 h-[2px] bg-primary"></span>
             Phase Overview
             <span className="flex-1 h-[1px] bg-border"></span>
           </h2>
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
             {PHASES.map((phase, i) => (
               <Link key={phase} href={`/phase/${phase}`}>
                 <div className="relative border border-border p-8 rounded-sm hover:border-primary hover:bg-primary/5 transition-all duration-300 cursor-pointer h-full flex flex-col group overflow-hidden">
                   <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                     <span className="text-6xl font-display font-bold text-primary">{i + 1}</span>
                   </div>
                   <div className="text-[10px] text-primary mb-3 font-mono tracking-[0.2em] uppercase">Phase {String(i + 1).padStart(2, '0')}</div>
                   <div className="text-xl font-display font-bold text-foreground group-hover:text-primary transition-colors tracking-wide mb-2 uppercase">
                    {phase.split('_')[1]}
                   </div>
                   <div className="mt-auto pt-6 flex items-center text-xs text-muted-foreground font-serif italic group-hover:text-primary/70">
                     View Axioms <ArrowRight className="w-3 h-3 ml-2 group-hover:translate-x-1 transition-transform" />
                   </div>
                 </div>
               </Link>
             ))}
           </div>
        </section>
      </div>
    </Layout>
  );
}

