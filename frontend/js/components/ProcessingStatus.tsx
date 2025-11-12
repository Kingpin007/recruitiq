import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';
import { Badge } from '@/js/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';
import { Progress } from '@/js/components/ui/progress';

interface ProcessingLog {
  stage: string;
  status: 'started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  message?: string;
  error_message?: string;
  created: string;
}

interface ProcessingStatusProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  logs?: ProcessingLog[];
  errorMessage?: string;
}

export function ProcessingStatus({ status, logs = [], errorMessage }: ProcessingStatusProps) {
  const getStatusIcon = (logStatus: string) => {
    switch (logStatus) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'in_progress':
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'skipped':
        return <span className="h-5 w-5 text-gray-400">—</span>;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'secondary',
      processing: 'default',
      completed: 'outline',
      failed: 'destructive',
    };

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const calculateProgress = () => {
    if (status === 'completed') return 100;
    if (status === 'failed') return 0;
    if (status === 'pending') return 0;

    if (logs.length === 0) return 10;

    const completedStages = logs.filter((log) => log.status === 'completed').length;
    const totalStages = logs.length;

    return totalStages > 0 ? (completedStages / totalStages) * 100 : 10;
  };

  const formatStageName = (stage: string) => {
    return stage
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Processing Status</CardTitle>
          {getStatusBadge(status)}
        </div>
        <CardDescription>Real-time candidate evaluation pipeline</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Progress</span>
            <span className="text-sm text-muted-foreground">
              {Math.round(calculateProgress())}%
            </span>
          </div>
          <Progress value={calculateProgress()} className="h-2" />
        </div>

        {errorMessage && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
            <div className="flex items-start">
              <XCircle className="h-5 w-5 text-destructive mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-destructive">Error</p>
                <p className="text-sm text-muted-foreground mt-1">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {logs.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Pipeline Stages</h4>
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-3 p-2 rounded-md hover:bg-muted/50"
                >
                  {getStatusIcon(log.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{formatStageName(log.stage)}</p>
                    {log.message && <p className="text-xs text-muted-foreground">{log.message}</p>}
                    {log.error_message && (
                      <p className="text-xs text-destructive mt-1">{log.error_message}</p>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(log.created).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {status === 'pending' && logs.length === 0 && (
          <div className="text-center py-4">
            <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Waiting to start processing...</p>
          </div>
        )}

        {status === 'processing' && logs.length === 0 && (
          <div className="text-center py-4">
            <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Processing candidate...</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
