import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// ==========================================
// LEXICONS (Structural Invariants)
// ==========================================

const PATTERNS: Record<string, { positive: RegExp[], negative: RegExp[] }> = {
  grace: {
    positive: [/\brepair\b/i, /\brecover\b/i, /\brestore\b/i, /\bheal\b/i, /\breconcil\b/i, /\bforgiv\b/i, /\bredempt\b/i, /\bgrace\b/i, /\bmercy\b/i, /\bcompassion\b/i, /\bresilient\b/i, /\badapt\b/i, /\babsorb\b/i, /\bbuffer\b/i, /\bdampen\b/i, /\berror[- ]?correct\b/i, /\bself[- ]?repair\b/i, /\bfault[- ]?toleran\b/i, /\brobust\b/i, /\bantifragil\b/i, /\brebuild\b/i, /\brenew\b/i],
    negative: [/\bblame\b/i, /\bscapegoat\b/i, /\bdeni\b/i, /\bcatastroph\b/i, /\birrevers\b/i, /\bpermanent.*damage\b/i, /\bno.*recov\b/i, /\bcannot.*repair\b/i, /\bbrittle\b/i, /\bfragile\b/i, /\btotal.*collapse\b/i, /\bterminal\b/i]
  },
  hope: {
    positive: [/\bhope\b/i, /\bfuture\b/i, /\bpossib\b/i, /\bpotential\b/i, /\bcan.*recover\b/i, /\bnot.*end\b/i, /\bsurviv\b/i, /\bpersis\b/i, /\bendur\b/i, /\bcontin\b/i, /\brestart\b/i, /\bbegin.*again\b/i, /\bnew.*opportun\b/i, /\bpath.*forward\b/i, /\brecovery.*state\b/i, /\bfallback\b/i, /\bcheckpoint\b/i, /\bsafe.*state\b/i],
    negative: [/\bhopeless\b/i, /\bno.*future\b/i, /\bdoom\b/i, /\binevitab.*fail\b/i, /\bno.*escape\b/i, /\btrap\b/i, /\bpermanent\b/i, /\birrevers\b/i, /\bsingle.*point.*failure\b/i, /\bno.*recovery\b/i, /\bend.*state\b/i, /\bnihil\b/i, /\bmeaningless\b/i, /\bfutil\b/i]
  },
  patience: {
    positive: [/\bpatien\b/i, /\bgradual\b/i, /\biterat\b/i, /\bconverg\b/i, /\bfeedback\b/i, /\bover.*time\b/i, /\blong[- ]?term\b/i, /\bprogress\b/i, /\bevolv\b/i, /\blearn\b/i, /\brefin\b/i, /\bimprov\b/i, /\bsteady\b/i, /\bstabil\b/i, /\basymptot\b/i, /\bapproach\b/i, /\btend.*toward\b/i, /\bincrement\b/i],
    negative: [/\bimmediat\b/i, /\binstant\b/i, /\bforce\b/i, /\bdemand\b/i, /\brequir.*now\b/i, /\boverfit\b/i, /\bpurge\b/i, /\binstabil\b/i, /\boscillat\b/i, /\bunstable\b/i, /\bvolatil\b/i, /\bjerk\b/i, /\bdiscontin\b/i, /\bshock\b/i]
  },
  faithfulness: {
    positive: [/\bfaithful\b/i, /\bloyal\b/i, /\bconsisten\b/i, /\bpreserv\b/i, /\bmaintain\b/i, /\bidentity\b/i, /\bintegrity\b/i, /\bfidelit\b/i, /\bstable.*struct\b/i, /\bcore.*value\b/i, /\bfundament\b/i, /\bessenti\b/i, /\binvariant\b/i, /\bconserv\b/i, /\bretain\b/i, /\buphold\b/i],
    negative: [/\bbetra\b/i, /\bsacrific.*truth\b/i, /\bexpedien\b/i, /\bconvenien\b/i, /\buseful.*lie\b/i, /\bperform.*over.*truth\b/i, /\bpragmat.*over\b/i, /\babandon\b/i, /\bcompromis\b/i, /\bcorrupt\b/i, /\bdistort\b/i]
  },
  self_control: {
    positive: [/\bboundar\b/i, /\blimit\b/i, /\bscope\b/i, /\bdefin.*domain\b/i, /\bconstraint\b/i, /\bself[- ]?control\b/i, /\bdisciplin\b/i, /\bmoderat\b/i, /\brestrain\b/i, /\bonly.*within\b/i, /\bdoes.*not.*claim\b/i, /\blimited.*to\b/i, /\bfalsifiabl\b/i, /\btestabl\b/i, /\bspecific\b/i],
    negative: [/\bexplain.*everything\b/i, /\buniversal.*claim\b/i, /\bno.*limit\b/i, /\btotaliz\b/i, /\bunfalsifiabl\b/i, /\birrefut\b/i, /\boverreach\b/i, /\bexpand.*indefinit\b/i, /\ball[- ]?encompass\b/i, /\bomni\b/i]
  },
  love: {
    positive: [/\blove\b/i, /\bcooperat\b/i, /\bcoexist\b/i, /\bmutual\b/i, /\bshare\b/i, /\bpositive[- ]?sum\b/i, /\bwin[- ]?win\b/i, /\bsynerg\b/i, /\bharmony\b/i, /\bcomplement\b/i, /\bsupport\b/i, /\benable\b/i, /\ballow.*other\b/i, /\btogether\b/i, /\bcommunit\b/i, /\brelation\b/i],
    negative: [/\bzero[- ]?sum\b/i, /\bdestroy.*alternat\b/i, /\belimin.*compet\b/i, /\bonly.*one.*true\b/i, /\bexclus.*claim\b/i, /\bannihilat\b/i, /\bdomin\b/i, /\bconquer\b/i, /\bsubjugat\b/i, /\bextinct\b/i]
  },
  peace: {
    positive: [/\bpeace\b/i, /\bconsisten\b/i, /\bcoher\b/i, /\bharmoni\b/i, /\bunifi\b/i, /\binternal.*align\b/i, /\bno.*contradic\b/i, /\blogical\b/i, /\bcompat\b/i, /\bagree\b/i, /\binteg\b/i, /\bwhole\b/i, /\bseamless\b/i],
    negative: [/\bcontradic\b/i, /\binconsisten\b/i, /\bparadox\b/i, /\btension\b/i, /\bconflict.*internal\b/i, /\bself[- ]?refut\b/i, /\bincompat\b/i, /\bpatchwork\b/i, /\bad[- ]?hoc\b/i, /\bincoher\b/i]
  },
  truth: {
    positive: [/\btruth\b/i, /\baccura\b/i, /\bprecis\b/i, /\bcorrect\b/i, /\bvalid\b/i, /\bverif\b/i, /\bconfirm\b/i, /\bobserv\b/i, /\bevidence\b/i, /\bdata\b/i, /\bexperiment\b/i, /\bempiri\b/i, /\bmeasur\b/i, /\bpredict.*match\b/i, /\breplicat\b/i, /\breproducib\b/i],
    negative: [/\bdistort\b/i, /\bmisrepresent\b/i, /\blie\b/i, /\bfalsif\b/i, /\bignor.*data\b/i, /\bsuppress\b/i, /\bredefin.*failure\b/i, /\bexcuse\b/i, /\brationali\b/i, /\bnarrat.*override\b/i, /\bspin\b/i, /\bpropagand\b/i]
  },
  humility: {
    positive: [/\bhumil\b/i, /\bupdat\b/i, /\brevis\b/i, /\bcorrect.*self\b/i, /\blearn.*from\b/i, /\bopen.*criticism\b/i, /\backn.*wrong\b/i, /\baccept.*error\b/i, /\bbayesian\b/i, /\bprior\b/i, /\bposterior\b/i, /\bnew.*evidence\b/i, /\brefin\b/i, /\badapt\b/i, /\bmodif\b/i],
    negative: [/\bdogma\b/i, /\binfallible\b/i, /\bnever.*wrong\b/i, /\bimmun.*critiqu\b/i, /\breject.*evidence\b/i, /\bhostile.*counter\b/i, /\bcannot.*be.*question\b/i, /\barrog\b/i, /\bpride\b/i, /\bstubborn\b/i]
  },
  goodness: {
    positive: [/\bgood\b/i, /\bgenerat\b/i, /\bcreat\b/i, /\bproduc\b/i, /\bsurplus\b/i, /\bbuild\b/i, /\bcontribut\b/i, /\benrich\b/i, /\bvalue.*add\b/i, /\bnew.*insight\b/i, /\bnew.*structur\b/i, /\bemerg\b/i, /\binvent\b/i, /\bpositive.*extern\b/i, /\bspillover\b/i],
    negative: [/\bextract\b/i, /\bparasit\b/i, /\bexploit\b/i, /\bdeplet\b/i, /\bdrain\b/i, /\brent[- ]?seek\b/i, /\bzero.*contribut\b/i, /\btake.*without\b/i, /\bdestructiv\b/i, /\bnegativ.*extern\b/i]
  },
  unity: {
    positive: [/\bunity\b/i, /\bunit\b/i, /\bintegrat\b/i, /\bdivers\b/i, /\bsynthe\b/i, /\bbridg\b/i, /\bconnect.*domain\b/i, /\bunifi.*without.*flatten\b/i, /\bplural\b/i, /\bmulti[- ]?disciplin\b/i, /\binter[- ]?disciplin\b/i, /\bholistic\b/i, /\bcomprehensiv\b/i],
    negative: [/\bhomogen\b/i, /\bflatten\b/i, /\bmonocult\b/i, /\bgroupthink\b/i, /\benforce.*same\b/i, /\belimin.*differ\b/i, /\buniform\b/i, /\breduct.*to.*one\b/i, /\bsilo\b/i, /\bfragment\b/i]
  },
  joy: {
    positive: [/\bjoy\b/i, /\breson\b/i, /\bamplif\b/i, /\bpositive.*feedback\b/i, /\breinforc\b/i, /\bvirtuous.*cycle\b/i, /\bener\b/i, /\benthusi\b/i, /\bengag\b/i, /\bflourish\b/i, /\bthrive\b/i, /\bbloom\b/i, /\bfulfill\b/i, /\bsatisf\b/i],
    negative: [/\bburnout\b/i, /\bcynic\b/i, /\bdamp\b/i, /\bnegative.*feedback\b/i, /\bvicious.*cycle\b/i, /\bdrain.*ener\b/i, /\bexhaust\b/i, /\bdespair\b/i, /\bdepress\b/i, /\bapathy\b/i]
  }
};

interface ScoreData {
  score: number;
  pos: number;
  neg: number;
}

const FruitsScorer = () => {
  const [inputText, setInputText] = useState('');
  const [scores, setScores] = useState<Record<string, ScoreData>>({});
  const [totalScore, setTotalScore] = useState(0);
  const [grade, setGrade] = useState('');

  const analyzeText = (text: string) => {
    if (!text.trim()) {
      setScores({});
      setTotalScore(0);
      setGrade('');
      return;
    }

    let tempScores: Record<string, ScoreData> = {};
    let tempTotal = 0;

    Object.keys(PATTERNS).forEach(key => {
      const positiveHits = PATTERNS[key].positive.reduce((acc, regex) => 
        acc + (text.match(regex) || []).length, 0);
      
      const negativeHits = PATTERNS[key].negative.reduce((acc, regex) => 
        acc + (text.match(regex) || []).length, 0);

      const totalHits = positiveHits + negativeHits;
      
      let score = 0;
      if (totalHits > 0) {
        score = (positiveHits - negativeHits) / totalHits;
      }
      
      tempScores[key] = {
        score: score, // -1 to 1
        pos: positiveHits,
        neg: negativeHits
      };
      
      tempTotal += score;
    });

    // Normalize Total (-12 to 12) -> (0 to 100)
    const normalized = ((tempTotal + 12) / 24) * 100;
    
    setScores(tempScores);
    setTotalScore(normalized);
    setGrade(calculateGrade(normalized));
  };

  const calculateGrade = (score: number) => {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  };

  // Real-time analysis with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      analyzeText(inputText);
    }, 500);
    return () => clearTimeout(timer);
  }, [inputText]);

  const getScoreColor = (score: number) => {
    if (score > 0.5) return "bg-green-500";
    if (score > 0.1) return "bg-green-300";
    if (score > -0.1) return "bg-gray-300";
    if (score > -0.5) return "bg-red-300";
    return "bg-red-500";
  };

  return (
    <div className="w-full space-y-6">
      <Card className="border border-border/50 bg-black/40 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex justify-between items-center font-display tracking-wide text-primary">
            <span>Fruits of the Spirit Scorer</span>
            {grade && <span className="text-2xl font-bold font-mono text-primary gold-glow">Grade: {grade} <span className="text-sm opacity-70">({Math.round(totalScore)}%)</span></span>}
          </CardTitle>
          <p className="text-sm text-muted-foreground font-serif italic">
            Evaluates text for structural coherence invariants. Paste your theory, policy, or manifesto below to test its viability.
          </p>
        </CardHeader>
        <CardContent>
          <textarea
            className="w-full h-48 p-4 border border-border/50 bg-secondary/10 rounded-sm font-mono text-sm focus:outline-none focus:border-primary/50 transition-colors"
            placeholder="Paste text here to analyze for coherence..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
        </CardContent>
      </Card>

      {Object.keys(scores).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {Object.entries(scores).map(([key, data]) => (
            <Card key={key} className="p-4 border border-border/30 bg-black/20">
              <div className="flex justify-between mb-2 capitalize font-bold text-xs tracking-widest">
                <span className="text-muted-foreground">{key}</span>
                <span className={data.score > 0 ? "text-emerald-500" : data.score < 0 ? "text-destructive" : "text-muted-foreground"}>
                  {data.score.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-secondary/30 h-1.5 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${getScoreColor(data.score)}`} 
                  style={{ width: `${((data.score + 1) / 2) * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-muted-foreground mt-2 font-mono opacity-60">
                <span>Entropy</span>
                <span>+{data.pos} / -{data.neg}</span>
                <span>Coherence</span>
              </div>
            </Card>
          ))}
        </div>
      )}
      
      {grade && (
        <Alert className={`border ${totalScore >= 60 ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-destructive/30 bg-destructive/5'}`}>
          <AlertTitle className="font-display tracking-widest text-sm uppercase mb-2">Interpretation</AlertTitle>
          <AlertDescription className="font-serif italic text-muted-foreground">
            {totalScore >= 80 ? "High Coherence: This text exhibits structural stability and generative properties. It aligns with the Logos." :
             totalScore >= 60 ? "Moderate Coherence: Contains mixed signals. Likely requires more error-tolerance (Grace) or feedback loops (Joy)." :
             "Entropy Dominated: This text relies on coercive, extractive, or fragile structures. High risk of systemic collapse."}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default FruitsScorer;
