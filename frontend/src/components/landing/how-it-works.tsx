'use client';

import { Github, Bot, FileCheck } from 'lucide-react';

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-slate-50 py-24 dark:bg-slate-800/50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
            Simple 3-Step Process
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
            We test your documentation like a real developer would — by trying to use it.
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-12 sm:max-w-none sm:grid-cols-3">
          
          {/* Step 1 */}
          <div className="relative">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-600 text-white">
              <span className="text-xl font-bold">1</span>
            </div>
            <div className="mt-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/50">
                <Github className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h3 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">
                Connect Repository
              </h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                Paste your GitHub URL and select docs folders
              </p>
            </div>
          </div>

          {/* Connector */}
          <div className="hidden sm:block absolute left-1/3 top-8 h-0.5 w-1/3 bg-slate-300 dark:bg-slate-600"></div>

          {/* Step 2 */}
          <div className="relative">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-purple-600 text-white">
              <span className="text-xl font-bold">2</span>
            </div>
            <div className="mt-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/50">
                <Bot className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">
                AI Tests Your Docs
              </h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                Coding agent implements every example from your docs
              </p>
            </div>
          </div>

          {/* Connector */}
          <div className="hidden sm:block absolute right-1/3 top-8 h-0.5 w-1/3 bg-slate-300 dark:bg-slate-600"></div>

          {/* Step 3 */}
          <div className="relative">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-600 text-white">
              <span className="text-xl font-bold">3</span>
            </div>
            <div className="mt-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/50">
                <FileCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">
                Get Results
              </h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                See exactly which examples work and what needs fixing
              </p>
            </div>
          </div>

        </div>

        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-8 rounded-lg bg-white p-6 shadow-lg dark:bg-slate-800">
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600">5min</div>
              <div className="text-sm text-slate-600">Setup Time</div>
            </div>
            <div className="h-8 w-px bg-slate-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">100%</div>
              <div className="text-sm text-slate-600">Automated</div>
            </div>
            <div className="h-8 w-px bg-slate-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">Realtime</div>
              <div className="text-sm text-slate-600">Results</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}