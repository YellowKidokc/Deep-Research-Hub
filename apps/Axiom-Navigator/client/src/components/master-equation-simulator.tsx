import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const MasterEquationSimulator = () => {
  // ==============================
  // 1. STATE: The Variables
  // ==============================
  // S = Entropy (Sin/Disorder) - The Decay Constant
  const [S, setS] = useState(0.05);
  
  // G = Grace (External Input) - The Energy Source
  const [G, setG] = useState(0);
  
  // R = Reception (Faith/Openness) - The Coupling Coefficient
  const [R, setR] = useState(1.0);

  // Initial Chi (Coherence)
  const [initialChi, setInitialChi] = useState(1.0);

  // Simulation Time
  const timeSteps = 100;
  
  // Canvas Ref
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // ==============================
  // 2. THE ENGINE: Euler Integration
  // ==============================
  // dX/dt = -S*X + G*R
  const generateData = () => {
    let data = [];
    let currentChi = initialChi;
    const dt = 1; // Time step

    for (let t = 0; t < timeSteps; t++) {
      data.push({ t, chi: currentChi });
      
      // The Master Equation
      const dChi = (-S * currentChi) + (G * R);
      
      currentChi += dChi * dt;
      
      // Clamp to prevent infinite explosion for visual sanity
      if (currentChi > 5) currentChi = 5;
      if (currentChi < 0) currentChi = 0;
    }
    return data;
  };

  const data = generateData();

  // ==============================
  // 3. VISUALIZATION: Canvas
  // ==============================
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40; // Increased padding for labels

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Draw Axes
    ctx.beginPath();
    ctx.strokeStyle = '#444'; // Darker axes for dark mode
    ctx.lineWidth = 1;
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding); // Y axis
    ctx.lineTo(width - padding, height - padding); // X axis
    ctx.stroke();

    // Plot Data
    ctx.beginPath();
    ctx.strokeStyle = '#eab308'; // Primary Gold
    ctx.lineWidth = 3;

    const maxChi = 2.0; // Y-axis scale max
    const xScale = (width - 2 * padding) / timeSteps;
    const yScale = (height - 2 * padding) / maxChi;

    data.forEach((point, index) => {
      const x = padding + point.t * xScale;
      const y = (height - padding) - (point.chi * yScale);
      
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw Threshold Line (Critical Failure)
    const criticalY = (height - padding) - (0.2 * yScale); // Assuming 0.2 is collapse
    ctx.beginPath();
    ctx.strokeStyle = '#ef4444'; // Red-500
    ctx.setLineDash([5, 5]);
    ctx.lineWidth = 2;
    ctx.moveTo(padding, criticalY);
    ctx.lineTo(width - padding, criticalY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#ef4444';
    ctx.font = '12px Inter';
    ctx.fillText("Critical Collapse Threshold (X < 0.2)", width - 220, criticalY - 10);

  }, [data]);

  return (
    <div className="w-full space-y-6 font-serif">
      <Card className="border border-border/50 bg-black/40 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="font-display text-primary tracking-wide text-xl">The Master Equation Simulator</CardTitle>
          <p className="font-mono text-xs bg-primary/10 text-primary p-2 rounded border border-primary/20 inline-block w-fit">
            dχ/dt = -S·χ + G·R
          </p>
          <p className="text-sm text-muted-foreground font-serif italic">
            Visualize how Entropy (S) and Grace (G) compete to determine the fate of a system.
          </p>
        </CardHeader>
        <CardContent className="space-y-8">
          
          {/* CONTROLS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-6 bg-secondary/20 rounded-sm border border-border/50">
            
            {/* ENTROPY CONTROL */}
            <div className="space-y-4">
              <label className="font-bold text-destructive flex justify-between text-xs uppercase tracking-wider">
                <span>Entropy (S)</span>
                <span className="font-mono">{S.toFixed(2)}</span>
              </label>
              <Slider 
                value={[S]} 
                min={0} max={0.2} step={0.01} 
                onValueChange={(val) => setS(val[0])} 
                className="cursor-pointer"
              />
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest opacity-70">Rate of natural decay (Sin/Disorder)</p>
            </div>

            {/* GRACE CONTROL */}
            <div className="space-y-4">
              <label className="font-bold text-emerald-500 flex justify-between text-xs uppercase tracking-wider">
                <span>Grace (G)</span>
                <span className="font-mono">{G.toFixed(2)}</span>
              </label>
              <Slider 
                value={[G]} 
                min={0} max={0.2} step={0.01} 
                onValueChange={(val) => setG(val[0])} 
                className="cursor-pointer"
              />
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest opacity-70">External energy input (Revelation/Work)</p>
            </div>

            {/* RECEPTION CONTROL */}
            <div className="space-y-4">
              <label className="font-bold text-blue-500 flex justify-between text-xs uppercase tracking-wider">
                <span>Reception (R)</span>
                <span className="font-mono">{R.toFixed(2)}</span>
              </label>
              <Slider 
                value={[R]} 
                min={0} max={2.0} step={0.1} 
                onValueChange={(val) => setR(val[0])} 
                className="cursor-pointer"
              />
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest opacity-70">Capacity to receive input (Faith/Openness)</p>
            </div>
          </div>

          {/* VISUALIZATION */}
          <div className="border border-border/50 rounded-sm p-4 bg-black/60 shadow-inner">
            <canvas 
              ref={canvasRef} 
              width={800} 
              height={400} 
              className="w-full h-auto"
            />
          </div>

          {/* ANALYSIS */}
          <Alert variant={data[timeSteps-1].chi < 0.2 ? "destructive" : "default"} className={`border ${data[timeSteps-1].chi < 0.2 ? 'border-destructive/50 bg-destructive/10' : 'border-emerald-500/50 bg-emerald-500/10'}`}>
            <AlertTitle className="font-display tracking-wide uppercase text-sm mb-2">
              System Status: <span className="font-mono ml-2 text-lg">{data[timeSteps-1].chi.toFixed(3)}</span>
            </AlertTitle>
            <AlertDescription className="font-serif italic text-base">
              {data[timeSteps-1].chi < 0.2 
                ? "SYSTEM COLLAPSE. Entropy (S) has overwhelmed the system. External input (G) is required immediately to reverse decoherence."
                : "SYSTEM STABLE. Coherence is being maintained or growing. The Logos Field is operative."}
            </AlertDescription>
          </Alert>

        </CardContent>
      </Card>
    </div>
  );
};

export default MasterEquationSimulator;
