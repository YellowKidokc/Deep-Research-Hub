import React from 'react';
import { AXIOMS, type Axiom } from '@/lib/data';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ShieldCheck, CheckCircle } from 'lucide-react';

const FalsificationMatrix = () => {
  // Only show axioms that have explicit falsification conditions
  const falsifiableAxioms = AXIOMS.filter(a => a.falsification);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4">
        {falsifiableAxioms.map((axiom) => (
          <div 
            key={axiom.id} 
            className="group relative grid grid-cols-1 md:grid-cols-[1fr_2fr_1fr] gap-4 p-4 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 transition-colors"
          >
            {/* Column 1: The Claim */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[10px] text-primary border-primary/30">
                  {axiom.id}
                </Badge>
                <span className="font-display font-bold text-sm">{axiom.title}</span>
              </div>
              <p className="text-xs text-muted-foreground font-serif italic border-l-2 border-white/10 pl-2">
                "{axiom.content}"
              </p>
            </div>

            {/* Column 2: The Kill Switch (Falsification) */}
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-destructive/80 text-[10px] font-bold uppercase tracking-widest">
                <AlertTriangle className="w-3 h-3" />
                Falsification Condition
              </div>
              <p className="text-sm font-medium text-foreground/90 leading-relaxed">
                {axiom.falsification}
              </p>
            </div>

            {/* Column 3: Status */}
            <div className="flex items-center justify-end md:justify-center">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500">
                <ShieldCheck className="w-4 h-4" />
                <span className="text-xs font-bold tracking-wide">ROBUST</span>
              </div>
            </div>

            {/* Hover Effect Line */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary scale-y-0 group-hover:scale-y-100 transition-transform origin-top" />
          </div>
        ))}
      </div>
      
      <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg flex gap-4 items-start">
        <CheckCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-bold text-primary mb-1">Why This Matters</h4>
          <p className="text-xs text-muted-foreground">
            A theory that cannot be killed is not science; it is mythology. 
            Theophysics explicitly defines the conditions under which it fails. 
            If any of these conditions are met, the entire dependency chain collapses. 
            To date, none have been observed.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FalsificationMatrix;
