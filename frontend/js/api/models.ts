// API models/types
export interface JobDescription {
  id: number;
  title: string;
  description: string;
  requirements?: string;
  is_active: boolean;
  created: string;
  modified: string;
}

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  celery_task_id?: string;
  error_message?: string;
  audit_log: Array<{ step: string; timestamp: string }>;
  job_description: JobDescription;
  submitted_by: number;
  created: string;
  modified: string;
  resume?: Resume;
  evaluation?: Evaluation;
}

export interface Resume {
  id: number;
  file: string;
  original_filename: string;
  file_type: string;
  extracted_text?: string;
  candidate: number;
  created: string;
  modified: string;
}

export interface Evaluation {
  id: number;
  overall_score: number;
  resume_score: number;
  github_score?: number;
  linkedin_score?: number;
  ai_summary: string;
  recommendation: 'interview' | 'decline';
  github_analysis?: any;
  linkedin_analysis?: any;
  generated_report?: string;
  candidate: number;
  created: string;
  modified: string;
}

export interface StakeholderFeedback {
  id: number;
  comments: string;
  decision: 'interview' | 'decline' | 'pending';
  evaluation: number;
  stakeholder: number;
  created: string;
  modified: string;
}
