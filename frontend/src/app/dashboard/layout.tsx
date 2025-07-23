'use client';

import ProtectedRoute from '@/components/auth/protected-route';
import { Sidebar } from '@/components/dashboard/sidebar';
import { Header } from '@/components/dashboard/header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto">
            <div className="container mx-auto px-4 py-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}