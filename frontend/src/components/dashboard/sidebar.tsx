'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Folder,
  FileText,
  Menu,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: Home },
  { name: 'Projects', href: '/dashboard/projects', icon: Folder },
  { name: 'Analyses', href: '/dashboard/analyses', icon: FileText },
];

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-600 bg-opacity-75 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-slate-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200 dark:border-slate-700">
          <Link href="/dashboard" className="flex items-center">
            <img 
              src="/logo.svg" 
              alt="Naptha Logo" 
              className="h-8 w-8"
            />
            <span className="ml-2 text-lg font-semibold text-slate-900 dark:text-white">
              Naptha
            </span>
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden p-2 rounded-md text-slate-400 hover:text-slate-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-5 px-2">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = item.href === '/dashboard' 
                ? pathname === '/dashboard' 
                : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-200'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                  )}
                >
                  <item.icon
                    className={cn(
                      'mr-3 h-5 w-5',
                      isActive
                        ? 'text-indigo-600 dark:text-indigo-400'
                        : 'text-slate-400 group-hover:text-slate-500'
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="p-2 rounded-md bg-white dark:bg-slate-800 shadow-md text-slate-400 hover:text-slate-500"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>
    </>
  );
}