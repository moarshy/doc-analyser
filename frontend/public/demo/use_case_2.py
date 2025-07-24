#!/usr/bin/env python3
"""
Entity Extraction from Documents Use Case
Based on the Guardrails AI documentation for extracting entities from PDF documents

This script demonstrates how to extract structured entities (fees, interest rates, etc.)
from PDF documents like contracts or agreements using Guardrails AI.

Success Criteria:
- Load PDF document as text
- Define Pydantic model for entities to extract
- Use Guard to extract and validate entities
- Ensure extracted data matches expected format
"""

import os
import json
import time
from typing import List
from pydantic import BaseModel, Field
import guardrails as gd

# Import validators from test assets or create simplified versions
# Note: In production, these would be imported from guardrails.hub
# For this example, we'll create simplified versions or use basic validation

# Import rich for pretty printing
from rich import print


def load_pdf_document(pdf_path: str) -> str:
    """
    Load PDF document as text using guardrails' built-in utilities.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Text content of the PDF
    """
    try:
        content = gd.docs_utils.read_pdf(pdf_path)
        print(f"✅ Successfully loaded PDF: {pdf_path}")
        print(f"📄 Document length: {len(content)} characters")
        print(f"📝 Preview: {content[:200]}...")
        return content
    except Exception as e:
        print(f"❌ Error loading PDF: {e}")
        raise


class Fee(BaseModel):
    """Model for fee information extracted from documents."""
    name: str = Field(description="Name of the fee")
    explanation: str = Field(description="Explanation of what the fee is for")
    value: float = Field(description="The fee amount in USD or as a percentage")


class AccountFee(BaseModel):
    """Model for interest rate information."""
    account_type: str = Field(description="Type of account (e.g., purchase, balance transfer, cash advance)")
    rate: float = Field(description="The annual percentage rate (APR)")


class CreditCardAgreement(BaseModel):
    """Main model for credit card agreement data."""
    fees: List[Fee] = Field(
        description="What fees and charges are associated with my account?"
    )
    interest_rates: List[AccountFee] = Field(
        description="What are the interest rates offered by the bank on different kinds of accounts and products?"
    )


def create_guard() -> gd.Guard:
    """
    Create a Guard object for validating extracted entities.
    
    Returns:
        Guard object configured for entity extraction
    """
    try:
        guard = gd.Guard.for_pydantic(output_class=CreditCardAgreement)
        print("✅ Successfully created Guard object")
        return guard
    except Exception as e:
        print(f"❌ Error creating Guard: {e}")
        raise


def extract_entities(document_text: str, guard: gd.Guard) -> dict:
    """
    Extract entities from document text using Guardrails.
    
    Args:
        document_text: Text content of the document
        guard: Guard object for validation
        
    Returns:
        Validated and structured entity data
    """
    prompt = """
    Given the following document, answer the following questions. If the answer doesn't exist in the document, enter 'None'.

    ${document}

    ${gr.complete_xml_suffix_v2}
    """
    
    try:
        print("🔄 Starting entity extraction...")
        raw_llm_response, validated_response, *rest = guard(
            messages=[{"role": "user", "content": prompt}],
            prompt_params={"document": document_text[:6000]},  # Limit to first 6000 chars
            model="gpt-4o-mini",
            max_tokens=2048,
            temperature=0
        )
        
        print("✅ Entity extraction completed")
        return validated_response
        
    except Exception as e:
        print(f"❌ Error during entity extraction: {e}")
        raise


def validate_extracted_data(data: dict) -> bool:
    """
    Validate that the extracted data matches expected format.
    
    Args:
        data: Extracted entity data
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        # Check if required fields exist
        if not isinstance(data, dict):
            print("❌ Data is not a dictionary")
            return False
            
        if 'fees' not in data or 'interest_rates' not in data:
            print("❌ Missing required keys: fees or interest_rates")
            return False
            
        # Validate fees structure
        fees = data.get('fees', [])
        if not isinstance(fees, list):
            print("❌ Fees is not a list")
            return False
            
        for fee in fees:
            if not isinstance(fee, dict):
                print("❌ Fee item is not a dictionary")
                return False
            if 'name' not in fee or 'explanation' not in fee or 'value' not in fee:
                print("❌ Fee item missing required fields")
                return False
                
        # Validate interest rates structure
        rates = data.get('interest_rates', [])
        if not isinstance(rates, list):
            print("❌ Interest rates is not a list")
            return False
            
        for rate in rates:
            if not isinstance(rate, dict):
                print("❌ Interest rate item is not a dictionary")
                return False
            if 'account_type' not in rate or 'rate' not in rate:
                print("❌ Interest rate item missing required fields")
                return False
                
        print("✅ Extracted data validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating data: {e}")
        return False


def main():
    """Main execution function for entity extraction use case."""
    start_time = time.time()
    
    print("🚀 Starting Entity Extraction from Documents Use Case")
    print("=" * 60)
    
    try:
        # Step 1: Load PDF document as text
        pdf_path = "/workspace/repo/docs/examples/data/chase_card_agreement.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return None
            
        document_text = load_pdf_document(pdf_path)
        
        # Step 2: Create Pydantic models and Guard
        guard = create_guard()
        
        # Step 3: Extract and validate entities using Guard
        extracted_data = extract_entities(document_text, guard)
        
        # Step 4: Validate extracted data format
        is_valid = validate_extracted_data(extracted_data)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Prepare results
        results = {
            "execution_status": "success" if is_valid else "partial",
            "execution_time": f"{execution_time:.2f} seconds",
            "extracted_entities": extracted_data,
            "validation_passed": is_valid,
            "document_processed": pdf_path,
            "entity_counts": {
                "total_fees": len(extracted_data.get('fees', [])),
                "total_interest_rates": len(extracted_data.get('interest_rates', []))
            }
        }
        
        print("\n" + "=" * 60)
        print("📊 EXTRACTION RESULTS")
        print("=" * 60)
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print(f"✅ Validation passed: {is_valid}")
        print(f"💰 Fees extracted: {len(extracted_data.get('fees', []))}")
        print(f"📈 Interest rates extracted: {len(extracted_data.get('interest_rates', []))}")
        
        if extracted_data.get('fees'):
            print("\n💸 FEES FOUND:")
            for fee in extracted_data['fees']:
                print(f"   • {fee['name']}: ${fee['value']} - {fee['explanation']}")
                
        if extracted_data.get('interest_rates'):
            print("\n📊 INTEREST RATES:")
            for rate in extracted_data['interest_rates']:
                print(f"   • {rate['account_type']}: {rate['rate']}% APR")
        
        return results
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n❌ Use case failed with error: {e}")
        
        return {
            "execution_status": "failure",
            "execution_time": f"{execution_time:.2f} seconds",
            "error": str(e),
            "extracted_entities": None,
            "validation_passed": False,
            "document_processed": None,
            "entity_counts": {"total_fees": 0, "total_interest_rates": 0}
        }


if __name__ == "__main__":
    results = main()
    
    # Save results to JSON file
    if results:
        with open('/workspace/data/use_case_results_2.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: /workspace/data/use_case_results_2.json")