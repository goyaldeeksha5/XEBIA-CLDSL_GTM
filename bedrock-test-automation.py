#!/usr/bin/env python3
"""
Bedrock Agent Testing Automation Framework
Tests all 4 layers: Think, Sense, Action, Safety

REQUIRED SETUP:
1. Create Bedrock Agent in AWS Console > Bedrock > Agents
2. Get Agent ID and Alias ID from console
3. Run tests with actual IDs

USAGE:
  python3 bedrock-test-automation.py --agent-id <ID> [--alias <ALIAS>] [--region ap-south-1]

ENVIRONMENT VARIABLES:
  BEDROCK_AGENT_ID: Bedrock Agent ID (from console)
  BEDROCK_AGENT_ALIAS: Agent Alias ID (default: PROD)
  AWS_REGION: AWS region (default: ap-south-1)

EXAMPLE:
  export BEDROCK_AGENT_ID=A6N7J8C9K2X1
  python3 bedrock-test-automation.py --alias PROD
"""

import json
import time
import boto3
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class BedrockAgentTester:
    def __init__(self, agent_id: str, agent_alias_id: str, region: str = "ap-south-1"):
        # Validate agent_id format
        if not agent_id or agent_id.startswith("YOUR_") or agent_id == "PLACEHOLDER":
            raise ValueError(
                "❌ INVALID AGENT ID\n\n"
                "Setup required:\n"
                "1. Go to AWS Console > Bedrock > Agents\n"
                "2. Create 'GTM-Dynamic-Pricing-Agent'\n"
                "3. Get Agent ID from settings page\n"
                "4. Run: python3 bedrock-test-automation.py --agent-id <YOUR_ACTUAL_ID>\n"
            )
        
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id or "PROD"
        self.region = region
        
        try:
            self.bedrock_client = boto3.client("bedrock-agent-runtime", region_name=region)
            self.lambda_client = boto3.client("lambda", region_name=region)
            self.dynamodb_client = boto3.client("dynamodb", region_name=region)
            print(f"✅ AWS clients initialized")
            print(f"   Agent ID: {agent_id}")
            print(f"   Alias: {agent_alias_id}")
            print(f"   Region: {region}\n")
        except Exception as e:
            raise ValueError(f"❌ Failed to initialize AWS clients: {e}\nCheck AWS credentials and region")
        
        self.test_results = {
            "think": [],
            "action": [],
            "safety": [],
            "e2e": []
        }
        
    def load_test_data(self, filepath: str) -> Dict:
        """Load test scenarios from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    # ===== LAYER 1: THINK LAYER =====
    def test_think_layer(self, test_data: Dict) -> None:
        """Test agent orchestration and reasoning"""
        print("\n" + "="*50)
        print("LAYER 1: THINK LAYER - Agent Evaluation")
        print("="*50)
        
        think_tests = [t for t in test_data["test_scenarios"] if t["layer"] == "Think"]
        
        for test in think_tests:
            print(f"\n▶ Test: {test['name']}")
            print(f"  Input: {test['query']}")
            
            try:
                start_time = time.time()
                
                response = self.bedrock_client.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=f"think-{test['id']}",
                    inputText=test['query']
                )
                
                latency = (time.time() - start_time) * 1000
                
                # Parse response
                completion_text = ""
                for event in response["completion"]:
                    if "text" in event:
                        completion_text += event["text"]
                
                # Check tool selection
                tool_selected = self._extract_tool_from_trace(response.get("trace", {}))
                
                # Verify success criteria
                passed = True
                details = []
                
                if tool_selected == test["expected_tool"]:
                    details.append(f"✅ Correct tool selected: {tool_selected}")
                else:
                    details.append(f"❌ Wrong tool. Expected: {test['expected_tool']}, Got: {tool_selected}")
                    passed = False
                
                if "CorrectPremium" in completion_text or str(test["expected_output"]["proposed_premium"]) in completion_text:
                    details.append(f"✅ Correct premium calculation")
                else:
                    details.append(f"⚠️  Premium verification inconclusive")
                
                self.test_results["think"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": passed,
                    "latency_ms": round(latency, 2),
                    "details": details
                })
                
                print(f"  {'✅ PASSED' if passed else '❌ FAILED'} ({latency:.0f}ms)")
                for detail in details:
                    print(f"    {detail}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                self.test_results["think"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": False,
                    "error": str(e)
                })
    
    # ===== LAYER 3: ACTION LAYER =====
    def test_action_layer(self, test_data: Dict) -> None:
        """Test Lambda integration and schema validation"""
        print("\n" + "="*50)
        print("LAYER 3: ACTION LAYER - Lambda Integration")
        print("="*50)
        
        action_tests = [t for t in test_data["test_scenarios"] if t["layer"] == "Action"]
        
        for test in action_tests:
            print(f"\n▶ Test: {test['name']}")
            
            if test["id"] == "action-001":
                # Schema validation test
                print(f"  Input: {test['lambda_input']}")
                
                try:
                    start_time = time.time()
                    
                    response = self.lambda_client.invoke(
                        FunctionName="GTM_insurance_dynamicpricing_ratingengine_Gateway",
                        InvocationType="RequestResponse",
                        Payload=json.dumps({"detail": test["lambda_input"]})
                    )
                    
                    latency = (time.time() - start_time) * 1000
                    
                    response_stream = json.loads(response["Payload"].read())
                    
                    # Validate schema
                    passed = True
                    details = []
                    
                    for key, expected_type in test["expected_parameter_types"].items():
                        if key in test["lambda_input"]:
                            actual_type = type(test["lambda_input"][key]).__name__
                            if (expected_type == "number" and isinstance(test["lambda_input"][key], (int, float))) or \
                               (expected_type == actual_type):
                                details.append(f"✅ {key}: {expected_type} - OK")
                            else:
                                details.append(f"❌ {key}: expected {expected_type}, got {actual_type}")
                                passed = False
                    
                    self.test_results["action"].append({
                        "test_id": test["id"],
                        "test_name": test["name"],
                        "passed": passed,
                        "latency_ms": round(latency, 2),
                        "details": details
                    })
                    
                    print(f"  {'✅ PASSED' if passed else '❌ FAILED'} ({latency:.0f}ms)")
                    for detail in details:
                        print(f"    {detail}")
                    
                except Exception as e:
                    print(f"  ❌ ERROR: {str(e)}")
                    self.test_results["action"].append({
                        "test_id": test["id"],
                        "test_name": test["name"],
                        "passed": False,
                        "error": str(e)
                    })
    
    # ===== LAYER 4: SAFETY LAYER =====
    def test_safety_layer(self, test_data: Dict) -> None:
        """Test guardrails and adversarial inputs"""
        print("\n" + "="*50)
        print("LAYER 4: SAFETY LAYER - Guardrails")
        print("="*50)
        
        safety_tests = [t for t in test_data["test_scenarios"] if t["layer"] == "Safety"]
        
        for test in safety_tests:
            print(f"\n▶ Test: {test['name']}")
            print(f"  Query: {test['query']}")
            
            try:
                start_time = time.time()
                
                response = self.bedrock_client.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=f"safety-{test['id']}-{int(time.time())}",
                    inputText=test['query']
                )
                
                latency = (time.time() - start_time) * 1000
                
                # Check guardrail action
                guardrail_action = self._extract_guardrail_action(response.get("trace", {}))
                
                # Get response text
                completion_text = ""
                for event in response["completion"]:
                    if "text" in event:
                        completion_text += event["text"]
                
                passed = (guardrail_action == test["expected_guardrail_action"])
                
                details = [
                    f"Guardrail Action: {guardrail_action}",
                    f"Expected: {test['expected_guardrail_action']}",
                    f"Response: {completion_text[:100]}..."
                ]
                
                self.test_results["safety"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": passed,
                    "latency_ms": round(latency, 2),
                    "guardrail_action": guardrail_action,
                    "details": details
                })
                
                print(f"  {'✅ PASSED' if passed else '⚠️  CHECK'} ({latency:.0f}ms)")
                print(f"    Guardrail: {guardrail_action}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                self.test_results["safety"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": False,
                    "error": str(e)
                })
    
    # ===== END-TO-END TESTS =====
    def test_e2e(self, test_data: Dict) -> None:
        """Test complete workflow"""
        print("\n" + "="*50)
        print("LAYER 5: END-TO-END Integration")
        print("="*50)
        
        e2e_tests = [t for t in test_data["test_scenarios"] if t["layer"] == "End-to-End"]
        
        for test in e2e_tests:
            print(f"\n▶ Test: {test['name']}")
            print(f"  Query: {test['user_query']}")
            
            try:
                start_time = time.time()
                
                response = self.bedrock_client.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=f"e2e-{test['id']}-{int(time.time())}",
                    inputText=test['user_query']
                )
                
                latency = (time.time() - start_time) * 1000
                
                # Extract results
                completion_text = ""
                for event in response["completion"]:
                    if "text" in event:
                        completion_text += event["text"]
                
                # Verify DynamoDB entry
                proposals = self.dynamodb_client.scan(
                    TableName="GTM_insurance_dynamicpricing_ratingengine_Proposals",
                    Limit=1
                )
                
                passed = latency < 2000 and len(proposals["Items"]) > 0
                
                details = [
                    f"Latency: {latency:.0f}ms {'✅' if latency < 2000 else '❌'}",
                    f"DynamoDB Entry: {'✅ Found' if len(proposals['Items']) > 0 else '❌ Not found'}",
                    f"Response Preview: {completion_text[:80]}..."
                ]
                
                self.test_results["e2e"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": passed,
                    "latency_ms": round(latency, 2),
                    "details": details
                })
                
                print(f"  {'✅ PASSED' if passed else '❌ FAILED'} ({latency:.0f}ms)")
                for detail in details:
                    print(f"    {detail}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                self.test_results["e2e"].append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "passed": False,
                    "error": str(e)
                })
    
    # ===== UTILITY METHODS =====
    def _extract_tool_from_trace(self, trace: Dict) -> str:
        """Extract tool name from agent trace"""
        try:
            if "orchestrationTrace" in trace:
                for event in trace["orchestrationTrace"]:
                    if "invocationInput" in event and "toolUseDetails" in event["invocationInput"]:
                        return event["invocationInput"]["toolUseDetails"].get("toolName", "UNKNOWN")
        except:
            pass
        return "UNKNOWN"
    
    def _extract_guardrail_action(self, trace: Dict) -> str:
        """Extract guardrail action from trace"""
        try:
            if "guardrailTrace" in trace:
                for event in trace["guardrailTrace"]:
                    return event.get("action", "UNKNOWN")
        except:
            pass
        return "NO_TRACE"
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = "\n" + "="*60 + "\n"
        report += "BEDROCK AGENT TEST REPORT\n"
        report += "="*60 + "\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        total_tests = sum(len(v) for v in self.test_results.values())
        passed_tests = sum(1 for v in self.test_results.values() for t in v if t.get("passed", False))
        
        report += f"SUMMARY: {passed_tests}/{total_tests} tests passed ({100*passed_tests//total_tests}%)\n\n"
        
        for layer, results in self.test_results.items():
            if not results:
                continue
            
            layer_passed = sum(1 for t in results if t.get("passed", False))
            report += f"{layer.upper()}: {layer_passed}/{len(results)} passed\n"
            
            for test in results:
                status = "✅" if test.get("passed", False) else "❌"
                report += f"  {status} {test['test_name']}"
                if "latency_ms" in test:
                    report += f" ({test['latency_ms']}ms)"
                report += "\n"
                
                for detail in test.get("details", []):
                    report += f"     {detail}\n"
            
            report += "\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description="Bedrock Agent Testing Framework",
        epilog="Environment Variables: BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS, AWS_REGION"
    )
    parser.add_argument(
        "--agent-id", 
        help="Bedrock Agent ID (from AWS Console > Bedrock > Agents)",
        default=os.getenv("BEDROCK_AGENT_ID")
    )
    parser.add_argument(
        "--alias", 
        dest="agent_alias_id",
        help="Bedrock Agent Alias (default: PROD)",
        default=os.getenv("BEDROCK_AGENT_ALIAS", "PROD")
    )
    parser.add_argument(
        "--region", 
        help="AWS Region (default: ap-south-1)",
        default=os.getenv("AWS_REGION", "ap-south-1")
    )
    parser.add_argument(
        "--test-data", 
        help="Test data JSON file",
        default="bedrock-test-data.json"
    )
    parser.add_argument(
        "--layer", 
        help="Run specific layer tests",
        choices=["think", "action", "safety", "e2e", "all"],
        default="all"
    )
    
    args = parser.parse_args()
    
    # Validate Agent ID
    if not args.agent_id:
        print("❌ ERROR: Agent ID required\n")
        print("Provide Agent ID via:")
        print("  1. Command line: --agent-id <ID>")
        print("  2. Environment: export BEDROCK_AGENT_ID=<ID>")
        print("\nTo get Agent ID:")
        print("  1. Go to AWS Console > Bedrock > Agents")
        print("  2. Create new agent (name: GTM-Dynamic-Pricing-Agent)")
        print("  3. Copy Agent ID from agent settings\n")
        sys.exit(1)
    
    # Initialize tester
    try:
        tester = BedrockAgentTester(args.agent_id, args.agent_alias_id, args.region)
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    
    # Load test data
    try:
        test_data = tester.load_test_data(args.test_data)
    except FileNotFoundError:
        print(f"❌ ERROR: Test data file not found: {args.test_data}")
        print(f"   Create it by running: python3 bedrock-test-automation.py --generate-data")
        sys.exit(1)
    
    # Run tests
    if args.layer in ["think", "all"]:
        tester.test_think_layer(test_data)
    
    if args.layer in ["action", "all"]:
        tester.test_action_layer(test_data)
    
    if args.layer in ["safety", "all"]:
        tester.test_safety_layer(test_data)
    
    if args.layer in ["e2e", "all"]:
        tester.test_e2e(test_data)
    
    # Print report
    report = tester.generate_report()
    print(report)
    
    # Save report
    with open(f"bedrock-test-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main()
