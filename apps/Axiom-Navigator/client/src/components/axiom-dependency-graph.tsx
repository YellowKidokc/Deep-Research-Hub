import React, { useState } from 'react';
import { AXIOMS, type Axiom, type Phase, getAxiom } from '@/lib/data';
import { Card } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { ArrowDown, AlertTriangle } from 'lucide-react';

const TIER_COLORS = [
  "border-white/40 bg-white/10", // Tier 0 (Foundations)
  "border-primary/40 bg-primary/10", // Tier 1
  "border-blue-500/40 bg-blue-500/10", // Tier 2
  "border-purple-500/40 bg-purple-500/10", // Tier 3
  "border-emerald-500/40 bg-emerald-500/10", // Tier 4
  "border-amber-500/40 bg-amber-500/10", // Tier 5
  "border-red-500/40 bg-red-500/10", // Tier 6
];

const DependencyNode = ({ 
  axiom, 
  onSelect, 
  selectedId, 
  isUpstream, 
  isDownstream 
}: { 
  axiom: Axiom, 
  onSelect: (id: string) => void,
  selectedId: string | null,
  isUpstream: boolean,
  isDownstream: boolean
}) => {
  const isSelected = selectedId === axiom.id;
  const isDimmed = selectedId && !isSelected && !isUpstream && !isDownstream;

  return (
    <div 
      className={cn(
        "relative p-3 rounded-md border cursor-pointer transition-all duration-300 w-full max-w-[200px] flex flex-col items-center text-center gap-1 hover:scale-105 z-10",
        isSelected ? "border-primary bg-primary/20 shadow-[0_0_15px_rgba(234,179,8,0.3)] scale-110" : TIER_COLORS[Math.min(axiom.tier, 6)],
        isUpstream && !isSelected ? "border-blue-400 bg-blue-400/20 shadow-[0_0_10px_rgba(96,165,250,0.2)]" : "",
        isDownstream && !isSelected ? "border-red-400 bg-red-400/20 shadow-[0_0_10px_rgba(248,113,113,0.2)]" : "",
        isDimmed ? "opacity-20 blur-[1px]" : "opacity-100"
      )}
      onClick={() => onSelect(axiom.id)}
    >
      <div className="text-[10px] font-mono opacity-70 uppercase tracking-widest">{axiom.id}</div>
      <div className="font-display font-bold text-sm leading-tight text-foreground">{axiom.title}</div>
      {axiom.falsification && (
        <Tooltip>
          <TooltipTrigger>
             <AlertTriangle className="w-3 h-3 text-destructive animate-pulse mt-1" />
          </TooltipTrigger>
          <TooltipContent className="max-w-[250px] bg-destructive text-destructive-foreground border-destructive">
            <p className="text-xs font-bold mb-1">FALSIFICATION CONDITION:</p>
            {axiom.falsification}
          </TooltipContent>
        </Tooltip>
      )}
      
      {/* Connector Line Stub */}
      <div className="absolute -bottom-4 left-1/2 w-px h-4 bg-border/50 group-last:hidden" />
    </div>
  );
};

export const AxiomDependencyGraph = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Group axioms by tier for visualization layers
  // Simple layout: Tier 0 at top, increasing tiers downwards
  const tiers = Array.from(new Set(AXIOMS.map(a => a.tier))).sort((a, b) => a - b);
  
  const getUpstream = (id: string, visited = new Set<string>()): Set<string> => {
    if (visited.has(id)) return visited;
    visited.add(id);
    const axiom = getAxiom(id);
    if (!axiom) return visited;
    axiom.depends_on.forEach(depId => getUpstream(depId, visited));
    return visited;
  };

  const getDownstream = (id: string, visited = new Set<string>()): Set<string> => {
    if (visited.has(id)) return visited;
    visited.add(id);
    const dependents = AXIOMS.filter(a => a.depends_on.includes(id));
    dependents.forEach(dep => getDownstream(dep.id, visited));
    return visited;
  };

  const upstreamSet = selectedId ? getUpstream(selectedId) : new Set<string>();
  const downstreamSet = selectedId ? getDownstream(selectedId) : new Set<string>();

  return (
    <div className="w-full overflow-x-auto pb-12">
      <div className="min-w-[800px] flex flex-col gap-16 relative p-8">
        
        {/* Background Grid Lines (Abstract) */}
        <div className="absolute inset-0 pointer-events-none opacity-10" 
             style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)', backgroundSize: '40px 40px' }}>
        </div>

        {tiers.map((tier) => (
          <div key={tier} className="relative flex justify-center gap-8">
            {/* Tier Label */}
            <div className="absolute -left-4 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] font-mono text-muted-foreground uppercase tracking-widest opacity-50 whitespace-nowrap">
              Tier {tier}
            </div>

            {AXIOMS.filter(a => a.tier === tier).map(axiom => (
              <DependencyNode 
                key={axiom.id} 
                axiom={axiom} 
                onSelect={setSelectedId}
                selectedId={selectedId}
                isUpstream={upstreamSet.has(axiom.id) && axiom.id !== selectedId}
                isDownstream={downstreamSet.has(axiom.id) && axiom.id !== selectedId}
              />
            ))}
          </div>
        ))}
        
        {/* Connections SVG Layer - Simplified */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
            </marker>
          </defs>
          {/* This would require calculating precise coordinates which is hard in pure React without a library. 
              For now, the hierarchical layout implies the flow. 
              The node highlighting serves the functional purpose.
          */}
        </svg>

      </div>
      
      <div className="flex justify-center gap-6 mt-8 text-xs text-muted-foreground font-mono">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500/20 border border-blue-500 rounded-sm"></div>
          <span>Foundation (Upstream)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-primary/20 border border-primary rounded-sm"></div>
          <span>Selected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500/20 border border-red-500 rounded-sm"></div>
          <span>Dependency (Downstream)</span>
        </div>
      </div>
    </div>
  );
};

export default AxiomDependencyGraph;
