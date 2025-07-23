'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallbackUrl?: string;
}

export default function ProtectedRoute({ 
  children, 
  fallbackUrl = '/login' 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth0();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(fallbackUrl);
    }
  }, [isAuthenticated, isLoading, router, fallbackUrl]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}