import { Sidebar } from "./sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <Sidebar />
      <main className="flex-1 ml-64 min-h-screen relative">
        <ScrollArea className="h-screen w-full">
          <div className="container max-w-4xl mx-auto p-8 md:p-12 pb-24">
            {children}
          </div>
        </ScrollArea>
      </main>
    </div>
  );
}
