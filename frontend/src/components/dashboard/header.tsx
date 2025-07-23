'use client';

import { Profile, LogoutButton } from '@/components/auth';

export function Header() {
  return (
    <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            Dashboard
          </h2>
        </div>
        <div className="flex items-center space-x-4">
          <Profile />
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}