import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Button } from '@/js/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/js/components/ui/card';
import { Input } from '@/js/components/ui/input';
import { Label } from '@/js/components/ui/label';
import { cn } from '@/js/lib/utils';

export function SignupForm({ className, ...props }: React.ComponentPropsWithoutRef<'div'>) {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password1, setPassword1] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState('');
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setErrors({});
    setLoading(true);

    // Client-side validation
    if (password1 !== password2) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Get CSRF token from cookies
      const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
      
      const response = await fetch('/accounts/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken || '',
        },
        body: new URLSearchParams({
          email,
          password1,
          password2,
        }),
        credentials: 'include',
      });

      if (response.ok || response.redirected) {
        // Signup successful, redirect to dashboard
        window.location.href = '/';
      } else {
        const text = await response.text();
        // Try to parse as JSON, otherwise use text
        try {
          const data = JSON.parse(text) as { email?: string[]; password1?: string[]; password2?: string[]; non_field_errors?: string[] };
          setErrors(data);
          if (data.non_field_errors) {
            setError(data.non_field_errors[0]);
          } else if (data.email) {
            setError(data.email[0]);
          } else if (data.password1) {
            setError(data.password1[0]);
          } else {
            setError('Signup failed. Please check your information.');
          }
        } catch {
          setError('Signup failed. Please try again.');
        }
      }
    } catch (err: unknown) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn('flex flex-col gap-6', className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Sign Up</CardTitle>
          <CardDescription>Create your account to get started</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              {error && (
                <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">
                  {error}
                </div>
              )}
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                {errors.email && <p className="text-sm text-destructive">{errors.email[0]}</p>}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password1">Password</Label>
                <Input
                  id="password1"
                  type="password"
                  value={password1}
                  onChange={(e) => setPassword1(e.target.value)}
                  required
                />
                {errors.password1 && <p className="text-sm text-destructive">{errors.password1[0]}</p>}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password2">Confirm Password</Label>
                <Input
                  id="password2"
                  type="password"
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                  required
                />
                {errors.password2 && <p className="text-sm text-destructive">{errors.password2[0]}</p>}
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Sign Up'}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => (window.location.href = '/accounts/google/login/')}
              >
                Sign up with Google
              </Button>
            </div>
            <div className="mt-4 text-center text-sm">
              Already have an account?{' '}
              <a href="/login" className="underline underline-offset-4">
                Log in
              </a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
