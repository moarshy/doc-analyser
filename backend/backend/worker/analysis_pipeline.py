import json
import os
from pathlib import Path
from typing import Dict, Any, List

from .use_case import extract_use_cases
from .execute_use_case import execute_use_cases


class AnalysisPipeline:
    """Main analysis pipeline for processing repository documentation."""
    
    def __init__(self, job_id: str, repo_path: str, include_folders: List[str]):
        self.job_id = job_id
        self.repo_path = Path(repo_path)
        self.include_folders = include_folders
        self.results_path = Path(os.getenv("RESULTS_PATH", "/tmp/results"))
        
    def run(self) -> Dict[str, Any]:
        """Run the complete analysis pipeline."""
        try:
            print(f"Starting analysis for job {self.job_id}")
            
            # Step 1: Extract use cases from documentation
            print("Extracting use cases...")
            use_cases = self._extract_use_cases()
            
            if not use_cases:
                print("No use cases found in documentation")
                return {
                    "status": "completed",
                    "use_cases": [],
                    "analysis_results": {},
                    "message": "No use cases found in documentation"
                }
            
            # Step 2: Execute use cases
            print(f"Executing {len(use_cases)} use cases...")
            results = self._execute_use_cases(use_cases)
            
            # Step 3: Generate final report
            report = self._generate_report(use_cases, results)
            
            # Step 4: Save results
            self._save_results(report)
            
            return report
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "use_cases": [],
                "analysis_results": {}
            }
    
    def _extract_use_cases(self) -> List[Dict[str, Any]]:
        """Extract use cases from documentation."""
        docs_path = self.repo_path
        
        # Find documentation files
        doc_files = []
        for folder in self.include_folders:
            folder_path = self.repo_path / folder
            if folder_path.exists():
                for ext in ["*.md", "*.rst", "*.txt"]:
                    doc_files.extend(folder_path.rglob(ext))
        
        if not doc_files:
            print("No documentation files found")
            return []
        
        # Run use case extraction
        extraction_result = extract_use_cases(
            repo_path=str(self.repo_path),
            doc_files=[str(f) for f in doc_files]
        )
        
        return extraction_result.get("use_cases", [])
    
    def _execute_use_cases(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute all use cases."""
        results = {}
        
        for i, use_case in enumerate(use_cases):
            print(f"Executing use case {i+1}/{len(use_cases)}: {use_case.get('name', 'Unknown')}")
            
            try:
                result = execute_use_cases(
                    use_case=use_case,
                    repo_path=str(self.repo_path),
                    include_folders=self.include_folders
                )
                results[use_case.get("name", f"use_case_{i}")] = result
                
            except Exception as e:
                print(f"Failed to execute use case {use_case.get('name', 'Unknown')}: {e}")
                results[use_case.get("name", f"use_case_{i}")] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return results
    
    def _generate_report(self, use_cases: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        
        successful_executions = sum(1 for r in results.values() if r.get("status") == "success")
        failed_executions = len(results) - successful_executions
        
        report = {
            "job_id": self.job_id,
            "status": "completed",
            "summary": {
                "total_use_cases": len(use_cases),
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": successful_executions / len(use_cases) if use_cases else 0
            },
            "use_cases": use_cases,
            "analysis_results": results,
            "documentation_quality": self._assess_documentation_quality(use_cases, results),
            "recommendations": self._generate_recommendations(use_cases, results)
        }
        
        return report
    
    def _assess_documentation_quality(self, use_cases: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the documentation."""
        
        score = 0
        max_score = 0
        
        for use_case in use_cases:
            max_score += 10
            
            # Check if use case has clear description
            if use_case.get("description"):
                score += 2
            
            # Check if use case has success criteria
            if use_case.get("success_criteria"):
                score += 2
            
            # Check if use case has been successfully executed
            use_case_name = use_case.get("name")
            if use_case_name in results and results[use_case_name].get("status") == "success":
                score += 3
            
            # Check if documentation source is provided
            if use_case.get("documentation_source"):
                score += 1
            
            # Check if difficulty level is specified
            if use_case.get("difficulty_level"):
                score += 2
        
        quality_score = (score / max_score) * 100 if max_score > 0 else 0
        
        return {
            "quality_score": quality_score,
            "grade": "A" if quality_score >= 90 else 
                     "B" if quality_score >= 80 else 
                     "C" if quality_score >= 70 else 
                     "D" if quality_score >= 60 else "F",
            "issues": self._identify_issues(use_cases, results)
        }
    
    def _identify_issues(self, use_cases: List[Dict], results: Dict[str, Any]) -> List[str]:
        """Identify issues in documentation and execution."""
        issues = []
        
        for use_case in use_cases:
            use_case_name = use_case.get("name")
            
            if not use_case.get("description"):
                issues.append(f"Use case '{use_case_name}' lacks clear description")
            
            if not use_case.get("success_criteria"):
                issues.append(f"Use case '{use_case_name}' lacks success criteria")
            
            if use_case_name in results and results[use_case_name].get("status") == "failed":
                issues.append(f"Use case '{use_case_name}' failed execution")
        
        return issues
    
    def _generate_recommendations(self, use_cases: List[Dict], results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving documentation."""
        recommendations = []
        
        failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
        
        if failed_count > 0:
            recommendations.append(
                f"{failed_count} use case(s) failed execution. Review the implementation "
                f"and ensure the documentation provides accurate code examples."
            )
        
        for use_case in use_cases:
            if not use_case.get("description"):
                recommendations.append(
                    f"Add clear description to use case '{use_case.get('name')}'"
                )
            
            if not use_case.get("success_criteria"):
                recommendations.append(
                    f"Define clear success criteria for use case '{use_case.get('name')}'"
                )
        
        return recommendations
    
    def _save_results(self, report: Dict[str, Any]):
        """Save analysis results to file."""
        results_file = self.results_path / "results.json"
        
        with open(results_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Results saved to {results_file}")


if __name__ == "__main__":
    # For testing
    job_id = os.getenv("JOB_ID", "test")
    repo_path = os.getenv("REPO_PATH", "/workspace/repo")
    include_folders = json.loads(os.getenv("INCLUDE_FOLDERS", '["docs"]'))
    
    pipeline = AnalysisPipeline(job_id, repo_path, include_folders)
    results = pipeline.run()
    print(json.dumps(results, indent=2))