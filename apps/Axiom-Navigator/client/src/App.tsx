import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import Home from "@/pages/home";
import PhaseView from "@/pages/phase-view";
import AxiomView from "@/pages/axiom-view";
import LensView from "@/pages/lens-view";
import Metrics from "@/pages/metrics";
import Manifestos from "@/pages/manifestos";
import AxiomMap from "@/pages/axiom-map";
import AxiomsDashboard from "@/pages/axioms-dashboard";
import Generations from "@/pages/generations";
import Synthesis from "@/pages/synthesis";
import Research from "@/pages/research";
import LogosPapers from "@/pages/logos-papers";
import LogosPaperDetail from "@/pages/logos-paper-detail";
import HorizonAcademia from "@/pages/horizon-academia";
import Tier1View from "@/pages/tier-1";
import Tier1Walkthrough from "@/pages/tier-1-walkthrough";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/phase/:phaseId" component={PhaseView} />
      <Route path="/axiom/:axiomId" component={AxiomView} />
      <Route path="/lens/:lensId" component={LensView} />
      <Route path="/metrics" component={Metrics} />
      <Route path="/manifestos" component={Manifestos} />
      <Route path="/map" component={AxiomMap} />
      <Route path="/axioms" component={AxiomsDashboard} />
      <Route path="/generations" component={Generations} />
      <Route path="/generations/:narrativeId" component={Generations} />
      <Route path="/synthesis" component={Synthesis} />
      <Route path="/research" component={Research} />
      <Route path="/logos-papers" component={LogosPapers} />
      <Route path="/logos-papers/:id" component={LogosPaperDetail} />
      <Route path="/horizon" component={HorizonAcademia} />
      <Route path="/tier-1" component={Tier1View} />
      <Route path="/tier-1/walkthrough/:axiomId" component={Tier1Walkthrough} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
