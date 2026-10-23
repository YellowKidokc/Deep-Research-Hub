import { Link } from "wouter";
import { LOGOS_PAPERS } from "@/lib/logos-data";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, FileText, Calendar, User } from "lucide-react";

export default function LogosPapers() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8 pl-80">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center gap-3 text-primary/80">
            <FileText className="w-5 h-5" />
            <span className="text-xs font-mono uppercase tracking-[0.2em]">The Launching Arm</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold tracking-tight text-white">
            Logos Papers
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl font-serif leading-relaxed">
            The foundational documents establishing the theoretical, physical, and theological basis of the Theophysics framework.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {LOGOS_PAPERS.map((paper, index) => (
            <Link key={paper.id} href={`/logos-papers/${paper.id}`}>
              <Card className="h-full bg-card/50 backdrop-blur-sm border-white/10 hover:border-primary/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.1)] group cursor-pointer flex flex-col">
                <CardHeader className="space-y-4">
                  <div className="flex justify-between items-start">
                    <Badge variant="outline" className="font-mono text-[10px] tracking-widest border-primary/30 text-primary/80">
                      PAPER {paper.number.toString().padStart(2, '0')}
                    </Badge>
                    <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors opacity-0 group-hover:opacity-100 transform group-hover:translate-x-1 duration-300" />
                  </div>
                  <div className="space-y-2">
                    <CardTitle className="font-display text-xl leading-tight group-hover:text-primary transition-colors">
                      {paper.title}
                    </CardTitle>
                    {paper.subtitle && (
                      <CardDescription className="font-serif text-sm line-clamp-2">
                        {paper.subtitle}
                      </CardDescription>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6 flex-1 flex flex-col justify-between">
                  <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">
                    {paper.summary}
                  </p>
                  
                  <div className="space-y-4 pt-4 border-t border-white/5">
                    <div className="flex items-center gap-4 text-xs text-muted-foreground/60 font-mono">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3" />
                        <span>{paper.date}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <User className="w-3 h-3" />
                        <span>{paper.author}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2">
                      {paper.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/5 text-primary/60 border border-primary/10">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
