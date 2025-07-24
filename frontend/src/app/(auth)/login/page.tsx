'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogIn, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleLogin = () => {
    loginWithRedirect({
      appState: {
        returnTo: '/dashboard'
      }
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Redirecting...</h1>
          <p className="text-gray-600">You're already logged in. Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Link href="/" className="inline-flex items-center text-blue-600 hover:text-blue-500 mb-8">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Link>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back
          </h2>
          <p className="text-gray-600">
            Sign in to your account to continue
          </p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Sign In</CardTitle>
            <CardDescription>
              Access your document analysis dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleLogin}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg shadow-sm border border-blue-600 hover:border-blue-700 transition-all duration-200"
              size="lg"
            >
              <LogIn className="mr-2 h-5 w-5" />
              Continue with Auth0
            </Button>

            <div className="text-center text-sm text-gray-500">
              Don't have an account?{' '}
              <Link href="/signup" className="text-blue-600 hover:text-blue-500 font-medium">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="text-center text-xs text-gray-500">
          By signing in, you agree to our Terms of Service and Privacy Policy
        </div>
      </div>
    </div>
  );
}