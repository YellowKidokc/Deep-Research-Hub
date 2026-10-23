# Website Components Integration Guide

This folder contains the React components for the "Theophysics: Trans-Domain Unity" website.

## 1. Components Overview

### `FruitsScorer.jsx`
*   **Purpose:** Allows users to paste text (theories, policies, emails) and get a "Coherence Score" based on the 12 Fruits of the Spirit.
*   **Logic:** Uses Regex pattern matching to detect Structural Invariants (e.g., "Love" = Positive Sum patterns).
*   **Usage:** Embed this on the "Metrics" or "Tools" page.

### `MasterEquationSimulator.jsx`
*   **Purpose:** Interactive graph allowing users to manipulate $S$ (Entropy), $G$ (Grace), and $R$ (Reception) to see the trajectory of a system (Collapse vs. Restoration).
*   **Logic:** Runs a real-time Euler integration of the differential equation: $d\chi/dt = -S\chi + G \cdot R$.
*   **Usage:** Embed this on the "Home" page or "The Master Equation" explanatory page.

## 2. Dependencies
These components use `lucide-react` for icons and `shadcn/ui` components for styling (standard in modern React/Next.js stacks).

If you are using a raw React setup, you may need to install:
```bash
npm install lucide-react clsx tailwind-merge
```

## 3. Quick Start (Next.js / React)

1.  Copy these `.jsx` files into your `components/` directory.
2.  Import them into your page:

```jsx
import FruitsScorer from '@/components/FruitsScorer';
import MasterEquationSimulator from '@/components/MasterEquationSimulator';

export default function Home() {
  return (
    <main>
      <h1>The Physics of Coherence</h1>
      
      <section>
        <h2>Simulate the Master Equation</h2>
        <MasterEquationSimulator />
      </section>

      <section>
        <h2>Test Your Theory</h2>
        <FruitsScorer />
      </section>
    </main>
  )
}
```
