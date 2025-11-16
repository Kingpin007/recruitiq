import { CheckCircle, Upload, Users, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { CandidateTable } from '@/js/components/CandidateTable';
import { CandidateDetailSheet } from '@/js/components/CandidateDetailSheet';
import { MainLayout } from '@/js/components/main-layout';
import { Button } from '@/js/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';

export default function Dashboard() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  const fetchCandidates = async () => {
    try {
      // Replace with actual API call
      const response = await fetch('/api/recruitment/candidates/');
      const data = await response.json();
      setCandidates(data.results || []);

      // Calculate stats
      const newStats = {
        total: data.results.length,
        pending: data.results.filter((c: any) => c.status === 'pending').length,
        processing: data.results.filter((c: any) => c.status === 'processing').length,
        completed: data.results.filter((c: any) => c.status === 'completed' || c.status === 'processed').length,
        failed: data.results.filter((c: any) => c.status === 'failed' || c.status === 'rejected').length,
      };
      setStats(newStats);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch candidates:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleViewDetails = (candidateId: number) => {
    setSelectedCandidateId(candidateId);
    setSheetOpen(true);
  };

  const handleReprocess = async (candidateId: number) => {
    try {
      await fetch(`/api/recruitment/candidates/${candidateId}/reprocess/`, {
        method: 'POST',
      });
      fetchCandidates();
    } catch (error) {
      console.error('Failed to reprocess candidate:', error);
    }
  };

  return (
    <MainLayout breadcrumbs={[{ label: 'Dashboard' }]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Recruitment Dashboard</h1>
            <p className="text-muted-foreground">Manage and track candidate evaluations</p>
          </div>
          <Button onClick={() => navigate('/upload')}>
            <Upload className="mr-2 h-4 w-4" />
            Upload Resumes
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Candidates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.total}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
              <span className="text-2xl font-bold">{stats.processing}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Accepted</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-2xl font-bold">{stats.completed}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <XCircle className="h-4 w-4 text-red-600" />
              <span className="text-2xl font-bold">{stats.failed}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Candidates Table */}
      <Card>
        <CardHeader>
          <CardTitle>Candidates</CardTitle>
          <CardDescription>View and manage all candidate submissions</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : (
            <CandidateTable
              candidates={candidates}
              onViewDetails={handleViewDetails}
              onReprocess={handleReprocess}
            />
          )}
        </CardContent>
      </Card>
      <CandidateDetailSheet
        candidateId={selectedCandidateId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        onCandidateUpdated={fetchCandidates}
      />
      </div>
    </MainLayout>
  );
}
