import { Eye, RefreshCw } from 'lucide-react';
import { Badge } from '@/js/components/ui/badge';
import { Button } from '@/js/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/js/components/ui/table';

interface Candidate {
  id: number;
  name: string;
  email: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'processed' | 'rejected';
  job_description_title: string;
  created: string;
  evaluation?: {
    overall_score: number;
    recommendation: 'interview' | 'decline';
  };
}

interface CandidateTableProps {
  candidates: Candidate[];
  onViewDetails: (candidateId: number) => void;
  onReprocess?: (candidateId: number) => void;
}

export function CandidateTable({ candidates, onViewDetails, onReprocess }: CandidateTableProps) {
  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'secondary',
      processing: 'default',
      completed: 'outline',
      failed: 'destructive',
    };

    return (
      <Badge variant={variants[status] || 'outline'} className="capitalize">
        {status}
      </Badge>
    );
  };

  const getRecommendationBadge = (recommendation: string) => {
    return (
      <Badge
        variant={recommendation === 'interview' ? 'default' : 'destructive'}
        className="capitalize"
      >
        {recommendation}
      </Badge>
    );
  };

  const getScoreBadge = (score: number) => {
    let variant: 'default' | 'secondary' | 'destructive' = 'secondary';
    if (score >= 7) variant = 'default';
    else if (score < 5) variant = 'destructive';

    return <Badge variant={variant}>{score}/10</Badge>;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Position</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Recommendation</TableHead>
            <TableHead>Submitted</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {candidates.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-muted-foreground">
                No candidates found
              </TableCell>
            </TableRow>
          ) : (
            candidates.map((candidate) => (
              <TableRow key={candidate.id}>
                <TableCell className="font-medium">{candidate.name}</TableCell>
                <TableCell>{candidate.email}</TableCell>
                <TableCell>{candidate.job_description_title}</TableCell>
                <TableCell>{getStatusBadge(candidate.status)}</TableCell>
                <TableCell>
                  {candidate.evaluation ? getScoreBadge(candidate.evaluation.overall_score) : '-'}
                </TableCell>
                <TableCell>
                  {candidate.evaluation
                    ? getRecommendationBadge(candidate.evaluation.recommendation)
                    : '-'}
                </TableCell>
                <TableCell>{new Date(candidate.created).toLocaleDateString()}</TableCell>
                <TableCell className="text-right space-x-2">
                  <Button variant="ghost" size="icon" onClick={() => onViewDetails(candidate.id)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  {onReprocess && candidate.status === 'failed' && (
                    <Button variant="ghost" size="icon" onClick={() => onReprocess(candidate.id)}>
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
