'use client';

import { Zap, FileCheck } from 'lucide-react';
import { GitHubLogoIcon } from '@radix-ui/react-icons';
import Link from 'next/link';
import { LoginButton } from '@/components/auth';

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-800">
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0))]"></div>
      <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
            Naptha Doc Analyser
            <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent block mt-2"> Turn Your Documentation Into Working Code</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
            Connect your GitHub documentation repository and let our AI coding agent test every example, 
            identify gaps, and validate that your docs actually work in practice.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <LoginButton className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" />
            <Link href="#how-it-works" className="text-sm font-semibold leading-6 text-slate-900 dark:text-white">
              Learn more <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
        
        <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-8 sm:max-w-none sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg bg-white p-6 shadow-lg dark:bg-slate-800">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/50">
              <GitHubLogoIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">Repository Analysis</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Clone and analyze your documentation repositories to extract practical use cases.
            </p>
          </div>
          
          <div className="rounded-lg bg-white p-6 shadow-lg dark:bg-slate-800">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/50">
              <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">AI Code Testing</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Our coding agent implements every documented use case to verify they actually work.
            </p>
          </div>
          
          <div className="rounded-lg bg-white p-6 shadow-lg dark:bg-slate-800">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/50">
              <FileCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">Gap Identification</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Identify missing steps, unclear instructions, and broken examples in your documentation.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}