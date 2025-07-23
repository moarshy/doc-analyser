'use client';

import { useAuth0 } from '@auth0/auth0-react';
import { User } from 'lucide-react';
import Image from 'next/image';

export default function Profile() {
  const { user, isAuthenticated, isLoading } = useAuth0();

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="h-8 w-8 animate-pulse rounded-full bg-slate-300 dark:bg-slate-600"></div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex items-center space-x-3">
      {user.picture && (
        <Image
          src={user.picture}
          alt={user.name || 'Profile'}
          width={32}
          height={32}
          className="rounded-full"
        />
      )}
      {!user.picture && (
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900">
          <User className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
        </div>
      )}
      <div className="hidden sm:block">
        <p className="text-sm font-medium text-slate-900 dark:text-white">
          {user.name || user.email}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {user.email}
        </p>
      </div>
    </div>
  );
}