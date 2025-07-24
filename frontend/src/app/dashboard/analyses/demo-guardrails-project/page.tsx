'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, FileCode, Activity, FileText, Container, ChevronRight, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface UseCase {
  name: string;
  description: string;
  success_criteria: string[];
  difficulty_level: string;
  documentation_source: string[];
  status: string;
  execution_time_seconds?: number;
  container_logs?: string;
  data?: any;
  start_time?: number;
  end_time?: number;
}

interface UseCaseResult {
  execution_status?: string;
  execution_results?: string;
  documentation_sources_used?: string[];
  documentation_usefulness?: string[];
  documentation_weaknesses?: string[];
  documentation_improvements?: string[];
  code_file_path?: string;
  execution_time?: string;
  success_criteria_met?: string[];
  challenges_encountered?: string[];
  use_case_name?: string;
  use_case_index?: number;
  error?: string;
  success?: boolean;
  timestamp?: string;
}

interface DemoData {
  status: string;
  total_use_cases: number;
  completed: number;
  failed: number;
  pending: number;
  job_params: {
    repository_url: string;
    branch: string;
    include_folders: string[];
    job_id: string;
    user_id: string;
    project_id: string;
  };
  use_cases: { [key: string]: UseCase };
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'pending':
    case 'processing':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    default:
      return <Activity className="h-4 w-4 text-gray-500" />;
  }
};

const getDifficultyColor = (level: string) => {
  switch (level?.toLowerCase()) {
    case 'beginner':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    case 'intermediate':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    case 'advanced':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  }
};

export default function DemoAnalysisPage() {
  const router = useRouter();
  const [demoData, setDemoData] = useState<DemoData | null>(null);
  const [selectedUseCaseIndex, setSelectedUseCaseIndex] = useState(0);
  const [useCaseFiles, setUseCaseFiles] = useState<{[key: number]: {code: string, results: UseCaseResult | null}}>({});
  const [activeTab, setActiveTab] = useState('details');

  useEffect(() => {
    const loadDemoData = async () => {
      try {
        const response = await fetch('/demo/job.json');
        const data: DemoData = await response.json();
        setDemoData(data);
        
        // Load use case files
        const files: {[key: number]: {code: string, results: any}} = {};
        
        for (let i = 0; i < data.total_use_cases; i++) {
          try {
            const resultsResponse = await fetch(`/demo/use_case_results_${i}.json`);
            const results = await resultsResponse.json();
            
            try {
              const codeResponse = await fetch(`/demo/use_case_${i}.py`);
              const codeContent = await codeResponse.text();
              files[i] = { code: codeContent, results };
            } catch (error) {
              files[i] = { code: '# Code file not available', results };
            }
          } catch (error) {
            console.warn(`Failed to load use case ${i}:`, error);
          }
        }
        
        setUseCaseFiles(files);
      } catch (error) {
        console.error('Failed to load demo data:', error);
      }
    };
    
    loadDemoData();
  }, []);

  const handleBack = () => {
    router.push('/dashboard/analyses');
  };

  if (!demoData) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <h3 className="text-lg font-medium mb-2">Loading Demo Data...</h3>
        </div>
      </div>
    );
  }

  const useCases = Object.entries(demoData.use_cases).map(([index, useCase]) => ({
    ...useCase,
    index: parseInt(index)
  }));

  const selectedUseCase = useCases[selectedUseCaseIndex];
  const selectedFiles = useCaseFiles[selectedUseCaseIndex];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg shadow-sm border dark:border-slate-700 p-4 mb-6 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-xl font-bold">Guardrails AI Demo Analysis</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Complete evaluation of 16 use cases from the Guardrails AI repository
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {getStatusIcon(demoData.status)}
              <Badge variant={demoData.status === 'completed' ? 'default' : 'secondary'}>
                {demoData.status}
              </Badge>
            </div>
            
            {/* Progress Stats */}
            <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
              <div className="flex items-center gap-1">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span>{demoData.completed} completed</span>
              </div>
              <span className="text-slate-400">•</span>
              <span>{demoData.total_use_cases} total use cases</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar */}
        <div className="col-span-4">
          <Card className="dark:bg-slate-800 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg">Use Cases ({demoData.total_use_cases})</CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-2 max-h-[800px] overflow-y-auto">
                {useCases.map((useCase) => (
                  <button
                    key={useCase.index}
                    onClick={() => setSelectedUseCaseIndex(useCase.index)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedUseCaseIndex === useCase.index
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700'
                        : 'bg-white dark:bg-slate-700 border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon(useCase.status)}
                          <span className="text-sm font-medium truncate">
                            {useCase.name}
                          </span>
                        </div>
                        
                        <div className="mb-2">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge 
                              variant={
                                useCase.status === 'completed' ? 'default' : 
                                useCase.status === 'failed' ? 'destructive' : 
                                useCase.status === 'running' ? 'outline' :
                                'secondary'
                              }
                              className={`text-xs font-medium ${
                                useCase.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                                useCase.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                                useCase.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400 border-blue-300' :
                                'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                              }`}
                            >
                              {useCase.status === 'running' && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                              {useCase.status}
                            </Badge>
                            {useCase.execution_time_seconds && (
                              <Badge variant="outline" className="text-xs bg-slate-50 dark:bg-slate-800">
                                {useCase.execution_time_seconds.toFixed(1)}s
                              </Badge>
                            )}
                            {/* File availability indicators */}
                            {useCase.status === 'completed' && useCaseFiles[useCase.index] && (
                              <div className="flex gap-1">
                                {useCaseFiles[useCase.index]?.code && (
                                  <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 border-blue-200">
                                    <FileCode className="h-3 w-3 mr-1" />
                                    Code
                                  </Badge>
                                )}
                                {useCaseFiles[useCase.index]?.results && (
                                  <Badge variant="outline" className="text-xs bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400 border-purple-200">
                                    <Activity className="h-3 w-3 mr-1" />
                                    Results
                                  </Badge>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                          {useCase.data?.description || useCase.description}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          {(useCase.data?.difficulty_level || useCase.difficulty_level) && (
                            <Badge className={`text-xs ${getDifficultyColor(useCase.data?.difficulty_level || useCase.difficulty_level)}`}>
                              {useCase.data?.difficulty_level || useCase.difficulty_level}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-400 ml-2 flex-shrink-0" />
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-8">
          {selectedUseCase ? (
            <Card className="dark:bg-slate-800 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-xl">
                  {selectedUseCase.name}
                </CardTitle>
                <p className="text-slate-600 dark:text-slate-400">
                  {selectedUseCase.description}
                </p>
                
                <Badge className={`text-sm mt-2 ${getDifficultyColor(selectedUseCase.difficulty_level)}`}>
                  {selectedUseCase.difficulty_level}
                </Badge>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-3 mb-6">
                    <TabsTrigger value="details" className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Details
                    </TabsTrigger>
                    <TabsTrigger value="code" className="flex items-center gap-2">
                      <FileCode className="h-4 w-4" />
                      Code
                    </TabsTrigger>
                    <TabsTrigger value="results" className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Results
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="details">
                    <div className="space-y-6">
                      {/* Success Criteria */}
                      {(selectedUseCase.data?.success_criteria || selectedUseCase.success_criteria) && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Success Criteria</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="list-disc list-inside space-y-2">
                              {(selectedUseCase.data?.success_criteria || selectedUseCase.success_criteria).map((criteria: string, idx: number) => (
                                <li key={idx} className="text-sm">{criteria}</li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      )}

                      {/* Documentation Sources */}
                      {(selectedUseCase.data?.documentation_source || selectedUseCase.documentation_source) && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Documentation Sources</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="space-y-2">
                              {(selectedUseCase.data?.documentation_source || selectedUseCase.documentation_source).map((source: string, idx: number) => (
                                <li key={idx} className="flex items-center gap-2 text-sm">
                                  <FileText className="h-4 w-4 text-slate-400" />
                                  <code className="bg-slate-100 dark:bg-slate-600 px-2 py-1 rounded text-xs">
                                    {source.replace('/workspace/repo/', '')}
                                  </code>
                                </li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      )}

                      {/* Execution Info */}
                      {selectedUseCase.execution_time_seconds && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Execution Information</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Execution Time</p>
                                <p className="text-lg font-semibold">{selectedUseCase.execution_time_seconds.toFixed(2)}s</p>
                              </div>
                              <div>
                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Status</p>
                                <div className="flex items-center gap-2">
                                  <CheckCircle className="h-4 w-4 text-green-500" />
                                  <span className="font-medium">Completed</span>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="code">
                    <div className="space-y-6">
                      {/* Generated Code */}
                      {selectedFiles?.code && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <FileCode className="h-5 w-5" />
                              Generated Code
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm">
                              <code>{selectedFiles.code}</code>
                            </pre>
                          </CardContent>
                        </Card>
                      )}

                      {/* Container Logs */}
                      {selectedUseCase.container_logs && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <Container className="h-5 w-5" />
                              Container Logs
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs max-h-96 overflow-y-auto">
                              <code>{selectedUseCase.container_logs}</code>
                            </pre>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="results">
                    <div className="space-y-6">
                      {selectedFiles?.results && (
                        <>
                          {/* Error Case */}
                          {selectedFiles.results.error && (
                            <Card className="dark:bg-red-900/20 border-red-200 dark:border-red-700">
                              <CardHeader>
                                <CardTitle className="text-lg text-red-800 dark:text-red-200">Execution Failed</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="flex items-center gap-2 mb-3">
                                  <AlertCircle className="h-5 w-5 text-red-500" />
                                  <Badge variant="destructive">Failed</Badge>
                                </div>
                                <pre className="bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 p-3 rounded text-sm whitespace-pre-wrap font-mono">
                                  {typeof selectedFiles.results.error === 'object' 
                                    ? JSON.stringify(selectedFiles.results.error, null, 2)
                                    : selectedFiles.results.error}
                                </pre>
                                {selectedFiles.results.timestamp && (
                                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                                    Failed at: {new Date(selectedFiles.results.timestamp).toLocaleString()}
                                  </p>
                                )}
                              </CardContent>
                            </Card>
                          )}

                          {/* Success Case */}
                          {!selectedFiles.results.error && (
                            <>
                              {/* Execution Status */}
                              <Card className="dark:bg-slate-700 dark:border-slate-600">
                                <CardHeader>
                                  <CardTitle className="text-lg">Execution Status</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <Badge className={selectedFiles.results.execution_status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}>
                                    {selectedFiles.results.execution_status || 'Success'}
                                  </Badge>
                                  {selectedFiles.results.execution_time && (
                                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                                      Completed in: {selectedFiles.results.execution_time}
                                    </p>
                                  )}
                                </CardContent>
                              </Card>
                            </>
                          )}

                          {/* Execution Results */}
                          {selectedFiles.results.execution_results && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Execution Results</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="bg-slate-50 dark:bg-slate-600 p-4 rounded border text-sm whitespace-pre-wrap">
                                  {typeof selectedFiles.results.execution_results === 'object' 
                                    ? JSON.stringify(selectedFiles.results.execution_results, null, 2)
                                    : selectedFiles.results.execution_results}
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* Success Criteria */}
                          {selectedFiles.results.success_criteria_met?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Success Criteria Met</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="list-disc list-inside space-y-2">
                                  {selectedFiles.results.success_criteria_met.map((criteria: string, idx: number) => (
                                    <li key={idx} className="text-sm">{criteria}</li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}

                          {/* Documentation Sources */}
                          {selectedFiles.results.documentation_sources_used?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Documentation Sources Used</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="space-y-2">
                                  {selectedFiles.results.documentation_sources_used.map((source: string, idx: number) => (
                                    <li key={idx} className="flex items-center gap-2 text-sm">
                                      <FileText className="h-4 w-4 text-slate-400" />
                                      <code className="bg-slate-100 dark:bg-slate-600 px-2 py-1 rounded text-xs">
                                        {source.replace('/workspace/repo/', '')}
                                      </code>
                                    </li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}

                          {/* Documentation Usefulness */}
                          {selectedFiles.results.documentation_usefulness?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Documentation Usefulness</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="list-disc list-inside space-y-2">
                                  {selectedFiles.results.documentation_usefulness.map((item: string, idx: number) => (
                                    <li key={idx} className="text-sm">{item}</li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}

                          {/* Documentation Weaknesses */}
                          {selectedFiles.results.documentation_weaknesses?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Documentation Weaknesses</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="list-disc list-inside space-y-2">
                                  {selectedFiles.results.documentation_weaknesses.map((item: string, idx: number) => (
                                    <li key={idx} className="text-sm">{item}</li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}

                          {/* Documentation Improvements */}
                          {selectedFiles.results.documentation_improvements?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Suggested Improvements</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="list-disc list-inside space-y-2">
                                  {selectedFiles.results.documentation_improvements.map((item: string, idx: number) => (
                                    <li key={idx} className="text-sm">{item}</li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}

                          {/* Challenges Encountered */}
                          {selectedFiles.results.challenges_encountered?.length > 0 && (
                            <Card className="dark:bg-slate-700 dark:border-slate-600">
                              <CardHeader>
                                <CardTitle className="text-lg">Challenges & Solutions</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <ul className="list-disc list-inside space-y-2">
                                  {selectedFiles.results.challenges_encountered.map((item: string, idx: number) => (
                                    <li key={idx} className="text-sm">{item}</li>
                                  ))}
                                </ul>
                              </CardContent>
                            </Card>
                          )}
                        </>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card className="dark:bg-slate-800 dark:border-slate-700">
              <CardContent className="flex items-center justify-center py-12 text-slate-500 dark:text-slate-400">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No use cases found</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}