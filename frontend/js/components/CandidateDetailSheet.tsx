import { Github, Linkedin, Mail, Phone, Trash2 } from 'lucide-react';
import * as React from 'react';

import { api, client } from '@/js/api/client.gen';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/js/components/ui/sheet';
import { Badge } from '@/js/components/ui/badge';
import { Button } from '@/js/components/ui/button';
import { ScrollArea } from '@/js/components/ui/scroll-area';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/js/components/ui/alert-dialog';

interface CandidateDetailSheetProps {
  candidateId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCandidateUpdated: () => void;
}

export function CandidateDetailSheet({
  candidateId,
  open,
  onOpenChange,
  onCandidateUpdated,
}: CandidateDetailSheetProps) {
  const [candidate, setCandidate] = React.useState<any | null>(null);
  const [logs, setLogs] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [actionLoading, setActionLoading] = React.useState(false);

  const fetchData = React.useCallback(async () => {
    if (!candidateId) return;
    setLoading(true);
    try {
      const [candidateRes, logsRes] = await Promise.all([
        api.recruitment.candidatesRetrieve({ id: candidateId }),
        client.get('/recruitment/processing-logs/', {
          params: { candidate: candidateId },
        }),
      ]);
      setCandidate(candidateRes);
      setLogs(logsRes.data.results || []);
    } catch (error) {
      console.error('Failed to fetch candidate sheet data:', error);
    } finally {
      setLoading(false);
    }
  }, [candidateId]);

  React.useEffect(() => {
    if (open && candidateId) {
      fetchData();
    }
  }, [open, candidateId, fetchData]);

  const handleStatusChange = async (status: 'processed' | 'rejected') => {
    if (!candidateId) return;
    setActionLoading(true);
    try {
      await client.post(`/recruitment/candidates/${candidateId}/set-status/`, {
        status,
      });
      await fetchData();
      onCandidateUpdated();
    } catch (error) {
      console.error('Failed to update candidate status:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!candidateId) return;
    setActionLoading(true);
    try {
      await client.delete(`/recruitment/candidates/${candidateId}/`);
      onCandidateUpdated();
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to delete candidate:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const renderStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'secondary',
      processing: 'default',
      completed: 'outline',
      failed: 'destructive',
      processed: 'default',
      rejected: 'destructive',
    };
    return (
      <Badge variant={variants[status] || 'outline'} className="capitalize">
        {status}
      </Badge>
    );
  };

  const renderAuditTrail = () => {
    if (!logs.length) {
      return <p className="text-sm text-muted-foreground">No processing events recorded yet.</p>;
    }

    return (
      <div className="space-y-3">
        {logs.map((log) => (
          <div key={log.id} className="flex flex-col gap-1 rounded-md border p-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {log.stage.replace('_', ' ')}
              </span>
              <Badge variant="outline" className="text-xs capitalize">
                {log.status}
              </Badge>
            </div>
            {log.message && <p className="text-sm">{log.message}</p>}
            {log.error_message && (
              <p className="text-xs text-destructive">Error: {log.error_message}</p>
            )}
            <span className="text-xs text-muted-foreground">
              {new Date(log.created).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const renderWorkExperience = () => {
    const detailed = candidate?.evaluation?.detailed_analysis;
    if (!detailed) {
      return <p className="text-sm text-muted-foreground">No work experience data available.</p>;
    }

    const work = detailed.work_experience || detailed.experience || detailed;

    if (Array.isArray(work)) {
      return (
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {work.map((item: any, index: number) => (
            <li key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
          ))}
        </ul>
      );
    }

    if (typeof work === 'string') {
      return <p className="text-sm whitespace-pre-line">{work}</p>;
    }

    return (
      <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 text-xs">
        {JSON.stringify(work, null, 2)}
      </pre>
    );
  };

  const renderResumeAnalysis = () => {
    const detailed = candidate?.evaluation?.detailed_analysis;
    if (!detailed) {
      return <p className="text-sm text-muted-foreground">No analysis data available yet.</p>;
    }

    return (
      <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 text-xs">
        {JSON.stringify(detailed, null, 2)}
      </pre>
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0">
        <SheetHeader>
          <div className="px-6 pt-6 pb-2 border-b">
            <SheetTitle>Candidate Details</SheetTitle>
          </div>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-72px)] px-6 pb-6 pt-4">
          {loading || !candidate ? (
            <div className="mt-6 text-center text-muted-foreground">Loading candidate...</div>
          ) : (
            <div className="flex flex-col gap-4">
            {/* Basic Info */}
            <Card>
              <CardHeader className="flex flex-row items-start justify-between gap-2">
                <div>
                  <CardTitle className="text-2xl">{candidate.name}</CardTitle>
                  <CardDescription>{candidate.job_description_title}</CardDescription>
                </div>
                <div className="flex flex-col items-end gap-2">
                  {renderStatusBadge(candidate.status)}
                  {candidate.evaluation && (
                    <span className="text-xs text-muted-foreground">
                      Score: {candidate.evaluation.overall_score}/10 (
                      {candidate.evaluation.recommendation})
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{candidate.email}</span>
                </div>
                {candidate.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{candidate.phone}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Links */}
            <Card>
              <CardHeader>
                <CardTitle>Profiles</CardTitle>
                <CardDescription>External links for this candidate</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {candidate.linkedin_url && (
                  <div className="flex items-center gap-2">
                    <Linkedin className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={candidate.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      LinkedIn Profile
                    </a>
                  </div>
                )}
                {candidate.github_profile && (
                  <div className="flex items-center gap-2">
                    <Github className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={candidate.github_profile.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      @{candidate.github_profile.username}
                    </a>
                  </div>
                )}
                {!candidate.linkedin_url && !candidate.github_profile && (
                  <p className="text-sm text-muted-foreground">No external profiles available.</p>
                )}
              </CardContent>
            </Card>

            {/* Work Experience */}
            <Card>
              <CardHeader>
                <CardTitle>Work Experience</CardTitle>
                <CardDescription>Highlights from the candidate&apos;s background</CardDescription>
              </CardHeader>
              <CardContent>{renderWorkExperience()}</CardContent>
            </Card>

            {/* Resume Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Resume Analysis</CardTitle>
                <CardDescription>LLM-generated insights and details</CardDescription>
              </CardHeader>
              <CardContent>{renderResumeAnalysis()}</CardContent>
            </Card>

            {/* Resume */}
            {candidate.resume && (
              <Card>
                <CardHeader>
                  <CardTitle>Resume</CardTitle>
                  <CardDescription>
                    View or download the original resume submitted by the candidate.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p>
                    <span className="font-medium">File:</span> {candidate.resume.original_filename}
                  </p>
                  <p>
                    <span className="font-medium">Type:</span>{' '}
                    {candidate.resume.file_type?.toUpperCase()}
                  </p>
                  {candidate.resume.file && (
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href={candidate.resume.file}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        View / Download PDF
                      </a>
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Audit Trail */}
            <Card>
              <CardHeader>
                <CardTitle>Audit Trail</CardTitle>
                <CardDescription>
                  Chronological processing events and manual actions for this candidate.
                </CardDescription>
              </CardHeader>
              <CardContent>{renderAuditTrail()}</CardContent>
            </Card>

              {/* Actions */}
              <div className="sticky bottom-0 mt-2 flex flex-wrap items-center justify-between gap-3 bg-background/80 py-3 backdrop-blur-sm">
                <div className="flex gap-2">
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        size="sm"
                        variant={candidate.status === 'processed' ? 'default' : 'outline'}
                        disabled={actionLoading}
                      >
                        Mark as Processed
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Mark candidate as processed?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This will update the candidate&apos;s status to &quot;processed&quot;. You can
                          always change it again later.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleStatusChange('processed')}
                          disabled={actionLoading}
                        >
                          Confirm
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>

                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        size="sm"
                        variant={candidate.status === 'rejected' ? 'destructive' : 'outline'}
                        disabled={actionLoading}
                      >
                        Mark as Rejected
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Reject candidate?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This will update the candidate&apos;s status to &quot;rejected&quot;. You can
                          always change it again later.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleStatusChange('rejected')}
                          disabled={actionLoading}
                        >
                          Confirm
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      size="sm"
                      variant="destructive"
                      className="flex items-center gap-1"
                      disabled={actionLoading}
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete Candidate
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete candidate?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will permanently delete the candidate and all associated data. This action
                        cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDelete}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        disabled={actionLoading}
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}


