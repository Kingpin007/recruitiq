// Auto-generated API client
import axios from 'axios';

const API_BASE_URL = '/api';

export const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// API endpoints
export const api = {
  recruitment: {
    jobDescriptionsList: async () => {
      const response = await client.get('/recruitment/job-descriptions/');
      return response.data;
    },
    candidatesList: async () => {
      const response = await client.get('/recruitment/candidates/');
      return response.data;
    },
    candidatesRetrieve: async ({ id }: { id: number }) => {
      const response = await client.get(`/recruitment/candidates/${id}/`);
      return response.data;
    },
    candidatesUploadResumeCreate: async ({ formData }: { formData: FormData }) => {
      const response = await client.post('/recruitment/candidates/upload_resume/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  },
};

export default client;
