import { Github, Linkedin, Mail, Phone } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { EvaluationCard } from '@/js/components/EvaluationCard';
import { MainLayout } from '@/js/components/main-layout';
import { ProcessingStatus } from '@/js/components/ProcessingStatus';
import { Badge } from '@/js/components/ui/badge';
import { Button } from '@/js/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/js/components/ui/card';

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState<any>(null);
  const [processingLogs, setProcessingLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCandidateDetails = async () => {
    try {
      const response = await fetch(`/api/recruitment/candidates/${id}/`);
      const data = await response.json();
      setCandidate(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch candidate:', error);
      setLoading(false);
    }
  };

  const fetchProcessingLogs = async () => {
    try {
      const response = await fetch(`/api/recruitment/processing-logs/?candidate=${id}`);
      const data = await response.json();
      setProcessingLogs(data.results || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  useEffect(() => {
    fetchCandidateDetails();
    fetchProcessingLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) {
    return (
      <MainLayout breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Candidate Details' }]}>
        <div className="text-center">Loading...</div>
      </MainLayout>
    );
  }

  if (!candidate) {
    return (
      <MainLayout breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Candidate Details' }]}>
        <div className="text-center">Candidate not found</div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      breadcrumbs={[
        { label: 'Dashboard', href: '/' },
        { label: 'Candidates', href: '/' },
        { label: candidate.name },
      ]}
    >
      <div className="space-y-6">
        {/* Candidate Info */}
        <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl">{candidate.name}</CardTitle>
              <p className="text-muted-foreground mt-2">
                Position: {candidate.job_description_title}
              </p>
            </div>
            <Badge variant={candidate.status === 'completed' ? 'outline' : 'default'}>
              {candidate.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center space-x-2 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span>{candidate.email}</span>
          </div>
          {candidate.phone && (
            <div className="flex items-center space-x-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <span>{candidate.phone}</span>
            </div>
          )}
          {candidate.linkedin_url && (
            <div className="flex items-center space-x-2 text-sm">
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
            <div className="flex items-center space-x-2 text-sm">
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
        </CardContent>
      </Card>

      {/* Processing Status */}
      {candidate.status !== 'completed' && (
        <ProcessingStatus
          status={candidate.status}
          logs={processingLogs}
          errorMessage={candidate.error_message}
        />
      )}

      {/* Evaluation */}
      {candidate.evaluation && (
        <EvaluationCard evaluation={candidate.evaluation} candidateName={candidate.name} />
      )}

      {/* Resume */}
      {candidate.resume && (
        <Card>
          <CardHeader>
            <CardTitle>Resume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">
                <span className="font-medium">File:</span> {candidate.resume.original_filename}
              </p>
              <p className="text-sm">
                <span className="font-medium">Type:</span>{' '}
                {candidate.resume.file_type.toUpperCase()}
              </p>
              {candidate.resume.file && (
                <Button variant="outline" size="sm" asChild>
                  <a href={candidate.resume.file} target="_blank" rel="noopener noreferrer">
                    Download Resume
                  </a>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      </div>
    </MainLayout>
  );
}
