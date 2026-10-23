import { Layout } from "@/components/layout";
import { getAxiom, getDownstreamDependencies, getUpstreamDependencies } from "@/lib/data";
import { useRoute, Link } from "wouter";
import ReactMarkdown from "react-markdown";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, GitCommitVertical, ArrowDown, ArrowUp, Share2, AlertTriangle, Sigma, Info, Key } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AxiomView() {
  const [match, params] = useRoute("/axiom/:axiomId");
  
  if (!match) return null;
  
  const axiom = getAxiom(params.axiomId);
  
  if (!axiom) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[50vh] gap-6 text-center">
          <h1 className="text-4xl font-display font-bold text-destructive">Void State Encountered</h1>
          <p className="text-muted-foreground font-serif text-xl">The requested axiom does not exist within the current causal chain.</p>
          <Link href="/">
             <span className="text-primary hover:underline cursor-pointer font-mono uppercase tracking-widest text-sm">Return to Protocol Root</span>
          </Link>
        </div>
      </Layout>
    );
  }

  const upstream = getUpstreamDependencies(axiom.id);
  const downstream = getDownstreamDependencies(axiom.id);

  return (
    <Layout>
      <div className="space-y-12 animate-in fade-in duration-700 slide-in-from-bottom-4">
        
        {/* Breadcrumb / Back */}
        <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-muted-foreground uppercase">
          <Link href={`/phase/${axiom.phase}`}>
            <span className="hover:text-primary cursor-pointer flex items-center gap-1 transition-colors">
              <ArrowLeft className="w-3 h-3" /> Back to {axiom.phase.split('_')[1]}
            </span>
          </Link>
          <span className="opacity-30 text-primary">/</span>
          <span className="text-primary">{axiom.id}</span>
        </div>

        {/* Header */}
        <header className="space-y-6 border-b border-border/40 pb-8">
          <div className="flex flex-wrap gap-3 items-center">
            <Badge variant="outline" className="rounded-sm px-3 py-1 font-mono text-[10px] uppercase tracking-widest border-primary/30 text-primary bg-primary/5">
              {axiom.phase.split('_')[1]}
            </Badge>
            <Badge variant="secondary" className="rounded-sm px-3 py-1 font-mono text-[10px] uppercase tracking-widest">
              {axiom.role}
            </Badge>
            <Badge variant={axiom.status === "Canonical" ? "default" : "outline"} className="rounded-sm px-3 py-1 font-mono text-[10px] uppercase tracking-widest">
              {axiom.status}
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-display font-bold leading-tight text-foreground tracking-wide">
            {axiom.title}
          </h1>
        </header>

        <div className="grid lg:grid-cols-3 gap-16 pt-4">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-12">
            
            {/* Mathematical Form - Prominent Display */}
            {axiom.mathematical_form && (
              <div className="p-6 bg-black/40 border border-primary/30 rounded-sm shadow-[0_0_20px_rgba(212,175,55,0.05)]">
                <div className="flex items-center gap-2 mb-3 text-xs font-mono uppercase tracking-widest text-primary/60">
                   <Sigma className="w-4 h-4" /> Mathematical Form
                </div>
                <div className="font-serif text-2xl md:text-3xl text-primary italic text-center py-4">
                  {axiom.mathematical_form}
                </div>
              </div>
            )}

            <div className="prose prose-invert prose-lg max-w-none font-serif leading-loose text-xl text-muted-foreground/90">
              <ReactMarkdown 
                components={{
                  strong: ({node, ...props}) => <span className="text-primary font-bold" {...props} />,
                  p: ({node, ...props}) => <p className="mb-6" {...props} />
                }}
              >
                {axiom.content}
              </ReactMarkdown>
            </div>

            {/* Justification Block */}
            {axiom.justification && (
              <div className="bg-secondary/20 border-l-2 border-primary p-6 rounded-r-sm">
                <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-3 flex items-center gap-2">
                  <Key className="w-4 h-4" /> Justification
                </h3>
                <p className="text-muted-foreground italic font-serif">
                  {axiom.justification}
                </p>
              </div>
            )}

            {/* Collapse Test Block */}
            {axiom.collapse_test && (
              <div className="bg-destructive/10 border border-destructive/20 p-6 rounded-sm">
                <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-destructive mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Collapse Condition
                </h3>
                <p className="text-destructive/80 font-serif">
                  {axiom.collapse_test}
                </p>
              </div>
            )}
            
            <div className="pt-8 border-t border-border/40">
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-6 flex items-center gap-2">
                <span className="w-2 h-2 bg-primary rounded-full"></span>
                Axiomatic Metadata
              </h3>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-8 text-sm border border-border/50 p-8 rounded-sm bg-black/20 backdrop-blur-sm">
                <div>
                  <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Authority</dt>
                  <dd className="font-display font-bold text-lg text-foreground">{axiom.authority}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Role</dt>
                  <dd className="font-display font-bold text-lg text-foreground">{axiom.role}</dd>
                </div>
                <div>
                   <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Tier</dt>
                   <dd className="font-mono text-lg text-primary">{axiom.tier}</dd>
                </div>
                <div>
                   <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Collapse Radius</dt>
                   <dd className="font-display font-bold text-lg text-foreground">{axiom.collapse_radius}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-3">Tags</dt>
                  <dd className="flex gap-2 flex-wrap">
                    {axiom.tags.map(tag => (
                      <span key={tag} className="border border-border hover:border-primary/50 bg-secondary/30 px-3 py-1 rounded-sm text-xs text-muted-foreground uppercase tracking-wider transition-colors cursor-default">
                        #{tag}
                      </span>
                    ))}
                  </dd>
                </div>
                <div>
                   <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Phase</dt>
                   <dd className="font-display font-bold text-lg text-foreground">{axiom.phase.split('_')[1]}</dd>
                </div>
                <div>
                   <dt className="text-xs text-muted-foreground uppercase tracking-widest mb-2">UUID</dt>
                   <dd className="font-mono text-xs text-muted-foreground break-all">{axiom.uuid || axiom.id}</dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Sidebar / Context */}
          <div className="space-y-10">
            <div className="border border-border/50 rounded-sm p-6 bg-secondary/10 relative overflow-hidden backdrop-blur-sm">
               <div className="absolute top-0 right-0 p-4 opacity-5">
                 <Share2 className="w-32 h-32" />
               </div>
               
               <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-8 flex items-center gap-2">
                 <GitCommitVertical className="w-4 h-4" />
                 Causal Chain
               </h3>

               <div className="space-y-0 relative z-10 pl-2">
                 <div className="absolute left-[19px] top-8 bottom-8 w-px bg-border/50 -z-10"></div>
                 
                 {/* Upstream */}
                 <div className="mb-6">
                   <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-muted-foreground mb-4 font-bold">
                     <ArrowUp className="w-3 h-3 text-primary" /> Antecedents
                   </div>
                   {upstream.length === 0 ? (
                     <div className="text-xs text-muted-foreground italic px-4 py-3 bg-black/30 rounded-sm border border-dashed border-border/50">
                       Root Axiom (No Dependencies)
                     </div>
                   ) : (
                     <div className="space-y-3">
                       {upstream.map(dep => (
                         <Link key={dep.id} href={`/axiom/${dep.id}`}>
                           <div className="ml-4 p-3 bg-black/40 rounded-sm border border-border hover:border-primary/50 cursor-pointer transition-all hover:translate-x-1 group">
                             <div className="text-[10px] font-mono text-primary/70 mb-1">{dep.id}</div>
                             <div className="text-sm font-serif font-medium text-muted-foreground group-hover:text-primary transition-colors">{dep.title}</div>
                           </div>
                         </Link>
                       ))}
                     </div>
                   )}
                 </div>

                 {/* Current Node (Visual) */}
                 <div className="relative my-8 ml-1">
                   <div className="absolute -left-[14px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-primary shadow-[0_0_10px_rgba(212,175,55,0.8)] z-20"></div>
                   <div className="p-4 bg-primary/10 border border-primary/30 text-primary-foreground rounded-sm shadow-lg backdrop-blur-md">
                     <div className="text-[10px] font-mono opacity-70 mb-1 tracking-widest">{axiom.id}</div>
                     <div className="text-sm font-display font-bold text-primary tracking-wide">Current State</div>
                   </div>
                 </div>

                 {/* Downstream */}
                 <div className="mt-6">
                   <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-muted-foreground mb-4 font-bold">
                     <ArrowDown className="w-3 h-3 text-primary" /> Consequents
                   </div>
                   {downstream.length === 0 ? (
                     <div className="text-xs text-muted-foreground italic px-4 py-3 bg-black/30 rounded-sm border border-dashed border-border/50">
                       Terminal Node (Leaf)
                     </div>
                   ) : (
                     <div className="space-y-3">
                       {downstream.map(dep => (
                         <Link key={dep.id} href={`/axiom/${dep.id}`}>
                           <div className="ml-4 p-3 bg-black/40 rounded-sm border border-border hover:border-primary/50 cursor-pointer transition-all hover:translate-x-1 group">
                             <div className="text-[10px] font-mono text-primary/70 mb-1">{dep.id}</div>
                             <div className="text-sm font-serif font-medium text-muted-foreground group-hover:text-primary transition-colors">{dep.title}</div>
                           </div>
                         </Link>
                       ))}
                     </div>
                   )}
                 </div>

               </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

