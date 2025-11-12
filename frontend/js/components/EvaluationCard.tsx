import { CheckCircle2, Star, XCircle } from 'lucide-react';
import { Badge } from '@/js/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';
import { Progress } from '@/js/components/ui/progress';

interface Evaluation {
  overall_score: number;
  recommendation: 'interview' | 'decline';
  detailed_analysis: {
    summary?: string;
    key_highlights?: string[];
    concerns?: string[];
    skill_matches?: Record<string, { score: number; matched: boolean; evidence: string }>;
    technical_depth?: { score: number; notes: string };
    experience_assessment?: {
      years_of_experience: number;
      meets_requirement: boolean;
      notes: string;
    };
  };
}

interface EvaluationCardProps {
  evaluation: Evaluation;
  candidateName: string;
}

export function EvaluationCard({ evaluation, candidateName }: EvaluationCardProps) {
  const { overall_score, recommendation, detailed_analysis } = evaluation;

  const getScoreColor = (score: number) => {
    if (score >= 7) return 'text-green-600';
    if (score >= 5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      {/* Overall Score and Recommendation */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Assessment</CardTitle>
          <CardDescription>AI-generated evaluation for {candidateName}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Overall Score</p>
              <p className={`text-4xl font-bold ${getScoreColor(overall_score)}`}>
                {overall_score}/10
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-muted-foreground mb-2">Recommendation</p>
              <Badge
                variant={recommendation === 'interview' ? 'default' : 'destructive'}
                className="text-lg px-4 py-1"
              >
                {recommendation === 'interview' ? (
                  <>
                    <CheckCircle2 className="mr-2 h-5 w-5" />
                    Interview
                  </>
                ) : (
                  <>
                    <XCircle className="mr-2 h-5 w-5" />
                    Decline
                  </>
                )}
              </Badge>
            </div>
          </div>

          {detailed_analysis.summary && (
            <div>
              <h4 className="font-medium mb-2">Summary</h4>
              <p className="text-sm text-muted-foreground">{detailed_analysis.summary}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Key Highlights */}
      {detailed_analysis.key_highlights && detailed_analysis.key_highlights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Key Strengths</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {detailed_analysis.key_highlights.map((highlight, index) => (
                <li key={index} className="flex items-start">
                  <CheckCircle2 className="h-5 w-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{highlight}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Concerns */}
      {detailed_analysis.concerns && detailed_analysis.concerns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Areas of Concern</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {detailed_analysis.concerns.map((concern, index) => (
                <li key={index} className="flex items-start">
                  <XCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{concern}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Skills Assessment */}
      {detailed_analysis.skill_matches && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Skills Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(detailed_analysis.skill_matches)
                .slice(0, 10)
                .map(([skill, data]) => (
                  <div key={skill}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium flex items-center">
                        {data.matched ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600 mr-2" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600 mr-2" />
                        )}
                        {skill}
                      </span>
                      <span className="text-sm text-muted-foreground">{data.score}/10</span>
                    </div>
                    <Progress value={data.score * 10} className="h-2" />
                    {data.evidence && (
                      <p className="text-xs text-muted-foreground mt-1">{data.evidence}</p>
                    )}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Technical Depth & Experience */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {detailed_analysis.technical_depth && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Technical Depth</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2 mb-2">
                <Star
                  className={`h-5 w-5 ${getScoreColor(detailed_analysis.technical_depth.score)}`}
                />
                <span className="text-2xl font-bold">
                  {detailed_analysis.technical_depth.score}/10
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {detailed_analysis.technical_depth.notes}
              </p>
            </CardContent>
          </Card>
        )}

        {detailed_analysis.experience_assessment && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Experience</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm">
                  <span className="font-medium">Years:</span>{' '}
                  {detailed_analysis.experience_assessment.years_of_experience}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Meets Requirement:</span>{' '}
                  {detailed_analysis.experience_assessment.meets_requirement ? (
                    <Badge variant="outline">Yes</Badge>
                  ) : (
                    <Badge variant="destructive">No</Badge>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {detailed_analysis.experience_assessment.notes}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
