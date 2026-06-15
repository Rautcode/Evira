
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { HelpCircle } from 'lucide-react';

export default function HelpPage() {
  return (
    <div className="container mx-auto py-8">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center text-2xl font-bold">
            <HelpCircle className="mr-3 h-7 w-7 text-primary" />
            Help & Documentation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Find answers to common questions, tutorials, and detailed documentation for SCADA Assistant
            features in this section.
          </p>
          <div className="mt-6 p-8 border-2 border-dashed border-border rounded-lg text-center">
            <HelpCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-foreground">Help Center Coming Soon</h3>
            <p className="text-sm text-muted-foreground">
              Comprehensive documentation and support resources will be available here.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
