#!/usr/bin/env python3
"""
Build script for packaging Lambda functions for GTM Commercial Underwriter Co-Pilot
"""

import os
import zipfile
import json
from pathlib import Path

LAMBDA_FUNCTIONS = {
    'orchestration_agent': 'orchestration_agent.py',
    'extraction_agent': 'extraction_agent.py',
    'validation_agent': 'validation_agent.py',
    'summary_agent': 'summary_agent.py'
}

FUNCTIONS_DIR = Path(__file__).parent
BUILD_DIR = FUNCTIONS_DIR / 'build'


def create_lambda_zip(function_name: str, handler_file: str) -> str:
    """Create a deployment package for Lambda function"""
    
    # Create build directory if it doesn't exist
    BUILD_DIR.mkdir(exist_ok=True)
    
    zip_file = BUILD_DIR / f"{function_name}.zip"
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the handler file
        handler_path = FUNCTIONS_DIR / handler_file
        zf.write(handler_path, arcname='index.py')
        
        print(f"Created {zip_file} ({handler_file})")
    
    return str(zip_file)


def create_requirements_file() -> str:
    """Create requirements.txt for dependencies"""
    
    requirements = """boto3>=1.26.0
botocore>=1.29.0
"""
    
    req_file = BUILD_DIR / 'requirements.txt'
    with open(req_file, 'w') as f:
        f.write(requirements)
    
    print(f"Created {req_file}")
    return str(req_file)


def build_all():
    """Build all Lambda function packages"""
    
    print("Building Lambda function packages...")
    print(f"Output directory: {BUILD_DIR}")
    print()
    
    for func_name, handler_file in LAMBDA_FUNCTIONS.items():
        zip_path = create_lambda_zip(func_name, handler_file)
        print(f"✓ {func_name}")
    
    create_requirements_file()
    print()
    print("Build complete!")
    print()
    print("To deploy, update the Lambda function references in lambda.tf")
    print(f"Lambda packages are located in: {BUILD_DIR}")


if __name__ == '__main__':
    build_all()
