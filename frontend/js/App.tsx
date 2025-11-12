import * as Sentry from '@sentry/react';
import { parse as cookieParse } from 'cookie';
import { RouterProvider } from 'react-router/dom';

import { client } from '@/js/api/client.gen';
import { ThemeProvider } from '@/js/components/theme-provider';
import { AuthProvider } from '@/js/contexts/AuthContext';
import router from '@/js/routes';

client.interceptors.request.use((request) => {
  const { csrftoken } = cookieParse(document.cookie);
  if (request.headers && csrftoken) {
    request.headers['X-CSRFTOKEN'] = csrftoken;
  }
  return request;
});

const App = () => (
  <Sentry.ErrorBoundary fallback={<p>An error has occurred</p>}>
    <AuthProvider>
      <ThemeProvider defaultTheme="system" storageKey="recruitiq-ui-theme">
        <RouterProvider router={router} />
      </ThemeProvider>
    </AuthProvider>
  </Sentry.ErrorBoundary>
);

export default App;
