import { createBrowserRouter } from 'react-router';
import CandidateDetail from '@/js/pages/CandidateDetail';
import Dashboard from '@/js/pages/Dashboard';
import LoginPage from '@/js/pages/LoginPage';
import SignupPage from '@/js/pages/SignupPage';
import UploadResumes from '@/js/pages/UploadResumes';

const router = createBrowserRouter([
  { index: true, Component: Dashboard },
  { path: 'upload', Component: UploadResumes },
  { path: 'candidates/:id', Component: CandidateDetail },
  { path: 'login', Component: LoginPage },
  { path: 'signup', Component: SignupPage },
]);

export default router;
