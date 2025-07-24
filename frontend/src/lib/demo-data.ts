export const DEMO_PROJECT = {
  id: 'demo-guardrails-project',
  name: 'Guardrails AI Demo',
  description: 'Interactive demo showcasing Guardrails AI documentation analysis with 16 use cases',
  repository_url: 'https://github.com/guardrails-ai/guardrails',
  created_at: '2024-07-24T05:34:29Z',
  updated_at: '2024-07-24T06:09:36Z',
  settings: {
    demo: true,
    use_cases_count: 16,
    completed_cases: 16
  }
};

export const DEMO_JOB = {
  id: '64d672a7-4130-4566-8805-2fa9c6e6c956',
  project_id: 'demo-guardrails-project',
  status: 'completed',
  repository: 'https://github.com/guardrails-ai/guardrails',
  created_at: '2024-07-24T05:34:29Z',
  updated_at: '2024-07-24T06:09:36Z',
  use_cases: [
    {
      id: 'use_case_0',
      name: 'Basic Input Validation',
      description: 'Validate basic text input using built-in validators like regex matching, length constraints, and format validation',
      status: 'completed',
      code_file: '/demo/use_case_0.py',
      results_file: '/demo/use_case_results_0.json',
      execution_time_seconds: 2109.23,
      difficulty_level: 'Beginner'
    },
    {
      id: 'use_case_1',
      name: 'Structured Data Generation',
      description: 'Generate structured data (JSON, Pydantic models) from LLM responses with schema validation',
      status: 'completed',
      code_file: '/demo/use_case_1.py',
      results_file: '/demo/use_case_results_1.json',
      execution_time_seconds: 742.91,
      difficulty_level: 'Beginner'
    },
    {
      id: 'use_case_2',
      name: 'Entity Extraction from Documents',
      description: 'Extract structured entities (fees, interest rates, etc.) from PDF documents like contracts or agreements',
      status: 'completed',
      code_file: '/demo/use_case_2.py',
      results_file: '/demo/use_case_results_2.json',
      execution_time_seconds: 672.27,
      difficulty_level: 'Intermediate'
    }
  ]
};

export const DEMO_USE_CASES = [
  {
    id: 'use_case_0',
    name: 'Basic Input Validation',
    description: 'Validate basic text input using built-in validators like regex matching, length constraints, and format validation',
    success_criteria: [
      'Successfully install validators from Guardrails Hub',
      'Create a Guard object with single or multiple validators',
      'Validate text input against defined criteria',
      'Handle validation failures appropriately'
    ],
    difficulty_level: 'Beginner',
    status: 'completed',
    code_file: '/demo/use_case_0.py',
    results_file: '/demo/use_case_results_0.json'
  },
  {
    id: 'use_case_1',
    name: 'Structured Data Generation',
    description: 'Generate structured data (JSON, Pydantic models) from LLM responses with schema validation',
    success_criteria: [
      'Define Pydantic model or RAIL spec for desired output structure',
      'Create Guard.for_pydantic() or Guard.for_rail_string()',
      'Generate valid JSON that conforms to schema',
      'Validate data types and constraints automatically'
    ],
    difficulty_level: 'Beginner',
    status: 'completed',
    code_file: '/demo/use_case_1.py',
    results_file: '/demo/use_case_results_1.json'
  },
  {
    id: 'use_case_2',
    name: 'Entity Extraction from Documents',
    description: 'Extract structured entities (fees, interest rates, etc.) from PDF documents like contracts or agreements',
    success_criteria: [
      'Load PDF document as text',
      'Define Pydantic model for entities to extract',
      'Use Guard to extract and validate entities',
      'Ensure extracted data matches expected format'
    ],
    difficulty_level: 'Intermediate',
    status: 'completed',
    code_file: '/demo/use_case_2.py',
    results_file: '/demo/use_case_results_2.json'
  }
];