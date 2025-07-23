'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { LogIn } from 'lucide-react';

interface LoginButtonProps {
  className?: string;
  returnTo?: string;
  children?: React.ReactNode;
}

export default function LoginButton({ className = '', returnTo, children }: LoginButtonProps) {
  const { loginWithRedirect, isLoading } = useAuth0();

  const handleLogin = () => {
    loginWithRedirect({
      appState: { returnTo: returnTo || '/dashboard' },
    });
  };

  return (
    <button
      onClick={handleLogin}
      disabled={isLoading}
      className={`inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${className}`}
    >
      <LogIn className="mr-2 h-4 w-4" />
      {children || (isLoading ? 'Loading...' : 'Sign In')}
    </button>
  );
}