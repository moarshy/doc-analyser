'use client';

import { ArrowRight, Star } from 'lucide-react';
import { GitHubLogoIcon } from '@radix-ui/react-icons';
import { LoginButton } from '@/components/auth';

export default function CTA() {
  return (
    <section className="bg-white dark:bg-slate-900">
      <div className="mx-auto max-w-7xl py-24 px-4 sm:px-6 lg:px-8">
        <div className="relative isolate overflow-hidden bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-24 text-center shadow-2xl rounded-3xl sm:px-16">
          <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Start Testing Your Documentation Today
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-indigo-200">
            Join developers using Naptha Doc Analyser to improve their documentation quality through real implementation testing.
          </p>
          
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <LoginButton 
              className="rounded-md bg-dark px-3.5 py-2.5 text-sm font-semibold text-indigo-600 shadow-sm hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Sign Up
              <ArrowRight className="ml-2 inline-block h-4 w-4" />
            </LoginButton>
            
            <a href="#how-it-works" className="text-sm font-semibold leading-6 text-white">
              Learn More <span aria-hidden="true">→</span>
            </a>
          </div>

          {/* Social Proof */}
          <div className="mt-12 flex items-center justify-center gap-x-8">
            <div className="flex items-center gap-x-1">
              <GitHubLogoIcon className="h-5 w-5 text-white" />
              <span className="text-sm text-indigo-200">GitHub Integration</span>
            </div>
            <div className="flex items-center gap-x-1">
              <Star className="h-5 w-5 text-white" />
              <span className="text-sm text-indigo-200">Real Code Testing</span>
            </div>
          </div>

          {/* Decorative Elements */}
          <svg
            viewBox="0 0 1024 1024"
            className="absolute left-1/2 top-1/2 -z-10 h-[64rem] w-[64rem] -translate-x-1/2"
            aria-hidden="true"
          >
            <circle cx={512} cy={512} r={512} fill="url(#827591b1-ce8c-4110-b064-7cb85a0b1217)" fillOpacity="0.7" />
            <defs>
              <radialGradient
                id="827591b1-ce8c-4110-b064-7cb85a0b1217"
                cx={0}
                cy={0}
                r={1}
                gradientUnits="userSpaceOnUse"
                gradientTransform="translate(512 512) rotate(90) scale(512)"
              >
                <stop stopColor="#7775D6" />
                <stop offset={1} stopColor="#E935C1" stopOpacity={0} />
              </radialGradient>
            </defs>
          </svg>
        </div>

      </div>
    </section>
  );
}