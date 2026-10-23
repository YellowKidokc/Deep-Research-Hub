import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';

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
  const canvasRef = useRef(null);

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
    const width = canvas.width;
    const height = canvas.height;
    const padding = 20;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Draw Axes
    ctx.beginPath();
    ctx.strokeStyle = '#ccc';
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding); // Y axis
    ctx.lineTo(width - padding, height - padding); // X axis
    ctx.stroke();

    // Plot Data
    ctx.beginPath();
    ctx.strokeStyle = '#0066cc'; // Theophysics Blue
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
    ctx.strokeStyle = 'red';
    ctx.setLineDash([5, 5]);
    ctx.moveTo(padding, criticalY);
    ctx.lineTo(width - padding, criticalY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'red';
    ctx.fillText("Critical Collapse Threshold (X < 0.2)", width - 200, criticalY - 5);

  }, [data]);

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>The Master Equation Simulator</CardTitle>
          <p className="font-mono text-sm bg-gray-100 p-2 rounded">
            dχ/dt = -S·χ + G·R
          </p>
          <p className="text-sm text-gray-500">
            Visualize how Entropy (S) and Grace (G) compete to determine the fate of a system.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* CONTROLS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-4 bg-slate-50 rounded-lg">
            
            {/* ENTROPY CONTROL */}
            <div className="space-y-2">
              <label className="font-bold text-red-600 flex justify-between">
                <span>Entropy (S)</span>
                <span>{S.toFixed(2)}</span>
              </label>
              <Slider 
                value={[S]} 
                min={0} max={0.2} step={0.01} 
                onValueChange={(val) => setS(val[0])} 
              />
              <p className="text-xs text-gray-500">The rate of natural decay (Sin/Disorder).</p>
            </div>

            {/* GRACE CONTROL */}
            <div className="space-y-2">
              <label className="font-bold text-green-600 flex justify-between">
                <span>Grace (G)</span>
                <span>{G.toFixed(2)}</span>
              </label>
              <Slider 
                value={[G]} 
                min={0} max={0.2} step={0.01} 
                onValueChange={(val) => setG(val[0])} 
              />
              <p className="text-xs text-gray-500">External energy input (Revelation/Work).</p>
            </div>

            {/* RECEPTION CONTROL */}
            <div className="space-y-2">
              <label className="font-bold text-blue-600 flex justify-between">
                <span>Reception (R)</span>
                <span>{R.toFixed(2)}</span>
              </label>
              <Slider 
                value={[R]} 
                min={0} max={2.0} step={0.1} 
                onValueChange={(val) => setR(val[0])} 
              />
              <p className="text-xs text-gray-500">Capacity to receive input (Faith/Openness).</p>
            </div>
          </div>

          {/* VISUALIZATION */}
          <div className="border rounded-lg p-4 bg-white shadow-inner">
            <canvas 
              ref={canvasRef} 
              width={800} 
              height={400} 
              className="w-full h-auto"
            />
          </div>

          {/* ANALYSIS */}
          <Alert variant={data[timeSteps-1].chi < 0.2 ? "destructive" : "default"}>
            <AlertTitle>System Status: {data[timeSteps-1].chi.toFixed(3)}</AlertTitle>
            <AlertDescription>
              {data[timeSteps-1].chi < 0.2 
                ? "SYSTEM COLLAPSE. Entropy (S) has overwhelmed the system. External input (G) is required immediately."
                : "SYSTEM STABLE. Coherence is being maintained or growing."}
            </AlertDescription>
          </Alert>

        </CardContent>
      </Card>
    </div>
  );
};

export default MasterEquationSimulator;
