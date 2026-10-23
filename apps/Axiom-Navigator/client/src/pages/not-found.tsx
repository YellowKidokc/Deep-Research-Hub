import { Layout } from "@/components/layout";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, Home } from "lucide-react";
import { Link } from "wouter";

export default function NotFound() {
  return (
    <Layout>
      <div className="min-h-[60vh] w-full flex items-center justify-center">
        <Card className="w-full max-w-md border-destructive/20 bg-destructive/5">
          <CardContent className="pt-6">
            <div className="flex mb-4 gap-3 items-center">
              <AlertCircle className="h-6 w-6 text-destructive" />
              <h1 className="text-xl font-serif font-bold text-destructive">404: Axiom Not Found</h1>
            </div>

            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              The requested resource lies beyond the known horizon. It may have been deprecated, moved, or never defined.
            </p>

            <div className="mt-6">
              <Link href="/">
                <div className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline cursor-pointer">
                  <Home className="w-4 h-4" />
                  Return to System Root
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
