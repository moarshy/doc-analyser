'use client';

import { useAuth } from '@/hooks/use-auth';
import { useEffect } from 'react';

export default function DashboardHome() {
  const { user, apiClient, userSynced } = useAuth();

  useEffect(() => {
    if (userSynced && apiClient) {
      // Fetch user data or dashboard stats
      console.log('Dashboard loaded for user:', user?.email);
    }
  }, [userSynced, apiClient, user]);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Welcome back, {user?.name || 'Developer'}
        </h1>
        <p className="mt-2 text-slate-600 dark:text-slate-400">
          Ready to analyze your documentation? Let's get started.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Quick Stats */}
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
              <div className="h-6 w-6 bg-indigo-600 dark:bg-indigo-400 rounded"></div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Projects</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">0</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <div className="h-6 w-6 bg-green-600 dark:bg-green-400 rounded"></div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Completed Analyses</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">0</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <div className="h-6 w-6 bg-yellow-600 dark:bg-yellow-400 rounded"></div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Pending Jobs</p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">0</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-4">
            Getting Started
          </h3>
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </div>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                  Connect your repository
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Link your GitHub repository to start analyzing your documentation.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </div>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                  Configure analysis
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Select which documentation files to analyze and configure analysis options.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </div>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                  Review results
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Get detailed analysis reports with actionable insights for improvement.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}