import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { PHASES, type Phase, AXIOMS } from "@/lib/data";
import { ChevronRight, Circle, Box, Cpu, FileJson, Eye, Zap, Shield, Binary, Sparkles, Ghost, Scale, Infinity as InfinityIcon, Network, Microscope, FileText, Users, BookOpen, Layers, Anchor, Database } from "lucide-react";

const PHASE_ICONS: Record<Phase, React.ElementType> = {
  "01_Ontology": Circle,
  "02_Substrate": Box,
  "03_Coherence": Network,
  "04_Compression": FileJson,
  "05_Observer": Eye,
  "06_Collapse": Zap,
  "07_Boundary": Shield,
  "08_Syzygy": Binary,
  "09_Grace": Sparkles,
  "10_Soul": Ghost,
  "11_Morality": Scale,
  "12_Destiny": InfinityIcon,
  "13_Unification": Cpu
};

const LENSES = ["Theology", "Physics", "Philosophy", "Systems"];

export function Sidebar() {
  const [location] = useLocation();

  return (
    <div className="w-64 border-r border-sidebar-border bg-sidebar h-screen flex flex-col fixed left-0 top-0 z-10 overflow-hidden">
      <div className="p-8 border-b border-sidebar-border shrink-0">
        <Link href="/">
          <div className="group cursor-pointer">
            <h1 className="font-display font-bold text-2xl tracking-widest text-primary gold-glow transition-opacity group-hover:opacity-80">
              Iron Chain
            </h1>
            <div className="h-0.5 w-12 bg-primary mt-2 mb-2 group-hover:w-full transition-all duration-500"></div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-medium">
              Navigator v3.2
            </p>
          </div>
        </Link>
      </div>
      
      <div className="flex-1 overflow-y-auto py-8 scrollbar-thin">
        {/* Tools Section */}
        <div className="px-6 mb-4 text-[10px] font-bold text-primary/50 uppercase tracking-[0.2em]">
          Tools & Research
        </div>
        <nav className="space-y-1 px-4 mb-10">
          <Link href="/horizon">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location.includes("/horizon") || location.includes("/tier-1")
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <Database className={cn("w-4 h-4", location.includes("/horizon") || location.includes("/tier-1") ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Horizon Academia</span>
            </div>
          </Link>
          <Link href="/logos-papers">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location.includes("/logos-paper")
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <FileText className={cn("w-4 h-4", location.includes("/logos-paper") ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Logos Papers</span>
            </div>
          </Link>
          <Link href="/metrics">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location === "/metrics"
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <Scale className={cn("w-4 h-4", location === "/metrics" ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Metrics & Sim</span>
            </div>
          </Link>
          <Link href="/manifestos">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location === "/manifestos"
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <FileText className={cn("w-4 h-4", location === "/manifestos" ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Manifestos</span>
            </div>
          </Link>
          <Link href="/map">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location === "/map"
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <Network className={cn("w-4 h-4", location === "/map" ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Axiom Map</span>
            </div>
          </Link>
          <Link href="/generations">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location.includes("/generations")
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <Users className={cn("w-4 h-4", location.includes("/generations") ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">The Generations</span>
            </div>
          </Link>
          <Link href="/synthesis">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location === "/synthesis"
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <Layers className={cn("w-4 h-4", location === "/synthesis" ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Synthesis</span>
            </div>
          </Link>
          <Link href="/research">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
              location === "/research"
                ? "text-primary bg-primary/10 border-l-2 border-primary" 
                : "text-muted-foreground hover:text-primary hover:bg-white/5 hover:pl-5 border-l-2 border-transparent"
            )}>
              <BookOpen className={cn("w-4 h-4", location === "/research" ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
              <span className="tracking-wide">Research Library</span>
            </div>
          </Link>
        </nav>

        {/* Lenses Section - Moved Up */}
        <div className="px-6 mb-4 text-[10px] font-bold text-primary/50 uppercase tracking-[0.2em] flex items-center gap-2">
          Lenses
        </div>
        <nav className="space-y-1 px-4 mb-10">
          {LENSES.map((lens) => {
            const isActive = location.includes(`/lens/${lens}`);
            return (
              <Link key={lens} href={`/lens/${lens}`}>
                <div className={cn(
                  "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group",
                  isActive 
                    ? "text-primary bg-primary/10 border-r-2 border-primary" 
                    : "text-muted-foreground hover:text-primary hover:bg-white/5"
                )}>
                  <Microscope className={cn("w-4 h-4", isActive ? "text-primary" : "text-muted-foreground group-hover:text-primary")} />
                  <span className="tracking-wide">{lens}</span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* The Axioms Section (formerly The Chain) */}
        <div className="px-6 mb-4 text-[10px] font-bold text-primary/50 uppercase tracking-[0.2em]">
          The Axioms
        </div>
        
        {/* Axioms Dashboard Link */}
        <nav className="space-y-1 px-4 mb-4">
          <Link href="/axioms">
            <div className={cn(
              "flex items-center gap-3 px-3 py-3 text-sm font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group bg-primary/5 hover:bg-primary/10 border border-primary/10 hover:border-primary/30",
              location === "/axioms"
                ? "text-primary border-primary/50 shadow-[0_0_10px_rgba(212,175,55,0.1)]" 
                : "text-primary/80"
            )}>
              <Anchor className="w-4 h-4" />
              <span className="tracking-wide font-bold">Axiom Dashboard</span>
            </div>
          </Link>
        </nav>

        {/* Phase List */}
        <nav className="space-y-1 px-4 mb-10 pl-8 border-l border-primary/10 ml-6">
          {PHASES.map((phase) => {
            const Icon = PHASE_ICONS[phase];
            const isActive = location.includes(`/phase/${phase}`) || 
                             AXIOMS.filter(a => a.phase === phase).some(a => location === `/axiom/${a.id}`);
            
            return (
              <Link key={phase} href={`/phase/${phase}`}>
                <div className={cn(
                  "flex items-center gap-3 px-3 py-2 text-xs font-serif font-medium rounded-sm cursor-pointer transition-all duration-300 group relative overflow-hidden",
                  isActive 
                    ? "text-primary" 
                    : "text-muted-foreground hover:text-primary hover:translate-x-1"
                )}>
                  <span className="opacity-50 text-[10px] w-4">{phase.split('_')[0]}</span>
                  <span className="tracking-wide uppercase">{phase.split('_')[1]}</span>
                </div>
              </Link>
            );
          })}
        </nav>

      </div>

      <div className="p-6 border-t border-sidebar-border shrink-0 bg-background/50 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(212,175,55,0.8)]"></div>
          <span className="text-xs font-serif text-primary tracking-widest uppercase">System Online</span>
        </div>
        <p className="text-[10px] text-muted-foreground font-mono opacity-50">Immutable • Read-Only</p>
      </div>
    </div>
  );
}
