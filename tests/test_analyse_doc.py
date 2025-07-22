#!/usr/bin/env python3
"""
Test script to call the analysis endpoint and poll for results.

Usage:
    python test_analyse_doc.py
"""

import asyncio
import time
import sys
from typing import Dict, Any
import httpx


class AnalysisClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def submit_analysis(self, repository_url: str, include_folders: list[str], branch: str = "main") -> str:
        """Submit a repository for analysis."""
        payload = {
            "url": repository_url,
            "branch": branch,
            "include_folders": include_folders
        }
        
        response = await self.client.post("/api/analyze", json=payload)
        response.raise_for_status()
        
        result = response.json()
        job_id = result.get("job_id")
        if not job_id:
            raise ValueError("No job_id returned from API")
        
        print(f"✅ Analysis submitted successfully!")
        print(f"   Job ID: {job_id}")
        print(f"   Repository: {repository_url}")
        print(f"   Include folders: {include_folders}")
        print()
        
        return job_id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of an analysis job."""
        response = await self.client.get(f"/api/status/{job_id}")
        response.raise_for_status()
        return response.json()

    async def poll_for_completion(self, job_id: str, timeout: int = 60*60*3, poll_interval: int = 60) -> Dict[str, Any]:
        """Poll for job completion."""
        print(f"⏳ Polling for job completion... (timeout: {timeout}s, poll interval: {poll_interval}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = await self.get_job_status(job_id)
                current_status = status.get("status", "unknown")
                
                if current_status == "completed":
                    print(f"✅ Analysis completed!")
                    return status
                elif current_status == "failed":
                    print(f"❌ Analysis failed!")
                    return status
                elif current_status == "processing":
                    print(f"🔄 Processing... (elapsed: {int(time.time() - start_time)}s)")
                else:
                    print(f"⏳ Status: {current_status} (elapsed: {int(time.time() - start_time)}s)")
                
                await asyncio.sleep(poll_interval)
                
            except httpx.HTTPError as e:
                print(f"⚠️  Error polling status: {e}")
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    async def list_all_jobs(self) -> list[Dict[str, Any]]:
        """List all analysis jobs."""
        response = await self.client.get("/api/jobs")
        response.raise_for_status()
        return response.json()


async def test_analysis():
    """Test the complete analysis workflow."""
    
    # Test configuration
    repository_url = "https://github.com/guardrails-ai/guardrails"
    include_folders = ["docs"]
    
    try:
        async with AnalysisClient() as client:
            print("🚀 Starting document analysis test...")
            print(f"   Target: {repository_url}")
            print(f"   Folders: {include_folders}")
            print()
            
            # Submit analysis
            job_id = await client.submit_analysis(repository_url, include_folders)
            
            # Poll for completion
            result = await client.poll_for_completion(job_id)
            
            # Display results
            print("\n" + "="*50)
            print("📊 ANALYSIS RESULTS")
            print("="*50)
            
            print(f"Status: {result.get('status')}")
            print(f"Repository: {result.get('repository')}")
            print(f"Include folders: {result.get('use_cases')}")
            
            if "use_cases" in result and result["use_cases"]:
                print(f"\n📋 Found {len(result['use_cases'])} use cases:")
                for i, use_case in enumerate(result["use_cases"], 1):
                    print(f"   {i}. {use_case.get('title', 'Untitled')}")
                    print(f"      Type: {use_case.get('type', 'unknown')}")
                    print(f"      Description: {use_case.get('description', 'No description')[:100]}...")
                    print()
            else:
                print("\n📋 No use cases found")
            
            if "error" in result and result["error"]:
                print(f"\n❌ Error: {result['error']}")
            
            # List current jobs
            print("\n📋 Current jobs:")
            jobs = await client.list_all_jobs()
            for job in jobs:
                print(f"   - {job.get('id')} ({job.get('status')})")
            
            return result
            
    except httpx.ConnectError:
        print("❌ Cannot connect to the API server. Make sure it's running on http://localhost:8000")
        print("   Try starting it with: make gateway")
        return None
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


async def main():
    """Main test function."""
    result = await test_analysis()
    if result:
        print("\n✅ Test completed successfully!")
        return 0
    else:
        print("\n❌ Test failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)