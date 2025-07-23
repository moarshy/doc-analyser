'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { LogOut } from 'lucide-react';

interface LogoutButtonProps {
  className?: string;
}

export default function LogoutButton({ className = '' }: LogoutButtonProps) {
  const { logout, isLoading } = useAuth0();

  const handleLogout = () => {
    logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  return (
    <button
      onClick={handleLogout}
      disabled={isLoading}
      className={`inline-flex items-center justify-center rounded-md bg-slate-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:opacity-50 ${className}`}
    >
      <LogOut className="mr-2 h-4 w-4" />
      {isLoading ? 'Loading...' : 'Sign Out'}
    </button>
  );
}