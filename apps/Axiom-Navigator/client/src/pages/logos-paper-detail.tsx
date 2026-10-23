import { useRoute, Link } from "wouter";
import { LOGOS_PAPERS } from "@/lib/logos-data";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft, Calendar, User, Tag, Share2, Download } from "lucide-react";
import ReactMarkdown from "react-markdown";
import NotFound from "@/pages/not-found";

export default function LogosPaperDetail() {
  const [match, params] = useRoute("/logos-papers/:id");
  const paperId = params?.id;
  
  const paper = LOGOS_PAPERS.find(p => p.id === paperId);

  if (!paper) {
    return <NotFound />;
  }

  return (
    <div className="min-h-screen bg-background text-foreground pl-64">
      <div className="h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-white/10 bg-background/50 backdrop-blur-md p-6 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto w-full space-y-6">
            <Link href="/logos-papers">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-primary -ml-4 gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back to Papers
              </Button>
            </Link>
            
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="font-mono text-xs tracking-widest border-primary/40 text-primary bg-primary/5">
                  PAPER {paper.number.toString().padStart(2, '0')}
                </Badge>
                <span className="text-muted-foreground/50 text-xs font-mono uppercase tracking-wider">
                  Theophysics Framework
                </span>
              </div>
              
              <h1 className="text-3xl md:text-4xl font-display font-bold tracking-tight text-white leading-tight">
                {paper.title}
              </h1>
              
              {paper.subtitle && (
                <p className="text-xl text-muted-foreground font-serif italic">
                  {paper.subtitle}
                </p>
              )}

              <div className="flex items-center gap-6 text-sm text-muted-foreground font-mono pt-2">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span>{paper.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>{paper.date}</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="max-w-4xl mx-auto w-full p-8 pb-32">
            <div className="prose prose-invert prose-lg max-w-none 
              prose-headings:font-display prose-headings:font-bold prose-headings:tracking-tight
              prose-h1:text-3xl prose-h1:text-primary/90 prose-h1:mb-8
              prose-h2:text-2xl prose-h2:text-white/90 prose-h2:mt-12 prose-h2:mb-6 prose-h2:border-b prose-h2:border-white/10 prose-h2:pb-2
              prose-h3:text-xl prose-h3:text-white/80 prose-h3:mt-8
              prose-p:text-muted-foreground prose-p:leading-relaxed prose-p:font-serif
              prose-strong:text-white prose-strong:font-semibold
              prose-blockquote:border-l-primary/50 prose-blockquote:bg-white/5 prose-blockquote:py-2 prose-blockquote:px-6 prose-blockquote:rounded-r-sm prose-blockquote:italic
              prose-ul:list-disc prose-ul:pl-6 prose-li:marker:text-primary/50
              prose-code:bg-black/50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-primary/80 prose-code:font-mono prose-code:text-sm
              prose-a:text-primary hover:prose-a:text-primary/80 prose-a:no-underline hover:prose-a:underline
            ">
              <ReactMarkdown>
                {paper.content}
              </ReactMarkdown>
            </div>

            {/* Footer Meta */}
            <div className="mt-16 pt-8 border-t border-white/10 space-y-6">
              <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Topics & Tags</h3>
              <div className="flex flex-wrap gap-2">
                {paper.tags.map(tag => (
                  <div key={tag} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-muted-foreground hover:border-primary/30 hover:text-primary transition-colors cursor-default">
                    <Tag className="w-3 h-3" />
                    <span>{tag}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
