import type React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import type { JobDescription } from '@/js/api/models';
import { FileUpload } from '@/js/components/FileUpload';
import { MainLayout } from '@/js/components/main-layout';
import { Button } from '@/js/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';
import { Label } from '@/js/components/ui/label';

export default function UploadResumes() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  const fetchJobDescriptions = async () => {
    try {
      const response = await fetch('/api/recruitment/job-descriptions/');
      const data = (await response.json()) as { results: JobDescription[] };
      setJobDescriptions(data.results || []);
      if (data.results && data.results.length > 0) {
        setSelectedJobId(data.results[0].id.toString());
      }
    } catch (error) {
      console.error('Failed to fetch job descriptions:', error);
    }
  };

  useEffect(() => {
    fetchJobDescriptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (files.length === 0) {
      setMessage('Please select at least one resume file.');
      return;
    }

    if (!selectedJobId) {
      setMessage('Please select a job description.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('resumes', file);
      });
      formData.append('job_description_id', selectedJobId);

      const response = await fetch('/api/recruitment/candidates/upload-resumes/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0] || '',
        },
      });

      if (response.ok) {
        const data = (await response.json()) as { candidates: unknown[] };
        setMessage(
          `Successfully uploaded ${data.candidates.length} resume(s). Processing started.`
        );
        setTimeout(() => navigate('/'), 2000);
      } else {
        const error = (await response.json()) as { error?: string };
        setMessage(`Error: ${error.error || 'Failed to upload resumes'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setMessage('An error occurred while uploading resumes.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Upload Resumes' }]}
    >
      <div className="max-w-3xl mx-auto">
        <Card>
        <CardHeader>
          <CardTitle>Upload Candidate Resumes</CardTitle>
          <CardDescription>Upload up to 10 resumes for AI-powered evaluation</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="job_description">Job Position</Label>
              <select
                id="job_description"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                required
              >
                <option value="">Select a position...</option>
                {jobDescriptions.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label>Resume Files</Label>
              <FileUpload onFilesSelected={setFiles} maxFiles={10} />
            </div>

            {message && (
              <div
                className={`p-4 rounded-md ${
                  message.startsWith('Error')
                    ? 'bg-destructive/10 text-destructive'
                    : 'bg-green-50 text-green-800'
                }`}
              >
                {message}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={() => navigate('/')}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading || files.length === 0}>
                {loading
                  ? 'Uploading...'
                  : `Upload ${files.length} Resume${files.length !== 1 ? 's' : ''}`}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      </div>
    </MainLayout>
  );
}
