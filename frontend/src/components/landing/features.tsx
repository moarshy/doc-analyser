'use client';

import { CheckCircle, Code2, Search, GitFork, AlertTriangle, TrendingUp } from 'lucide-react';

const features = [
  {
    name: 'Use Case Extraction',
    description: 'AI analyzes your documentation to identify practical use cases and examples that should work.',
    icon: Search,
    details: [
      'Identifies code examples in docs',
      'Extracts API usage patterns',
      'Finds tutorial scenarios',
      'Detects integration guides'
    ]
  },
  {
    name: 'Code Implementation',
    description: 'Our AI coding agent attempts to implement every documented use case based solely on your documentation.',
    icon: Code2,
    details: [
      'Implements examples from scratch',
      'Tests API integration',
      'Validates setup instructions',
      'Checks configuration steps'
    ]
  },
  {
    name: 'Gap Detection',
    description: 'Identify exactly where your documentation falls short - missing steps, unclear instructions, or broken examples.',
    icon: AlertTriangle,
    details: [
      'Missing prerequisites',
      'Incomplete code snippets',
      'Unclear configuration',
      'Broken API references'
    ]
  },
  {
    name: 'Quality Metrics',
    description: 'Get quantifiable insights into your documentation quality with actionable improvement suggestions.',
    icon: TrendingUp,
    details: [
      'Documentation completeness score',
      'Code example accuracy',
      'Setup success rate',
      'User journey mapping'
    ]
  }
];

export default function Features() {
  return (
    <section className="bg-white py-24 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
            Stop Guessing. Start Testing.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
            Our AI coding agent doesn't just read your documentation — it tries to use it. 
            Every example, every tutorial, every integration guide gets tested in real code.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <div className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-2">
            {features.map((feature) => (
              <div key={feature.name} className="flex flex-col">
                <div className="relative flex items-center gap-x-4">
                  <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-indigo-600">
                    <feature.icon className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  <h3 className="text-lg font-semibold leading-8 tracking-tight text-slate-900 dark:text-white">
                    {feature.name}
                  </h3>
                </div>
                
                <div className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-600 dark:text-slate-300">
                  <p className="flex-auto">{feature.description}</p>
                  
                  <ul role="list" className="mt-6 space-y-2">
                    {feature.details.map((detail) => (
                      <li key={detail} className="flex items-center">
                        <CheckCircle className="h-5 w-5 flex-none text-green-500" aria-hidden="true" />
                        <span className="ml-3 text-sm">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}