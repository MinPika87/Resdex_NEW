import argparse
import csv
import asyncio
import json
import logging
import sys
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resdex_agent.agent import ResDexRootAgent, Content
from resdex_agent.config import AgentConfig
from resdex_agent.utils.step_logger import step_logger
from resdex_agent.tools.llm_tools import LLMTool

logging.basicConfig(
    level=logging.WARNING, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionStateCapture:
    """Captures and manages session state for testing."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset to initial session state."""
        self.session_state = {
            'keywords': [],
            'min_exp': 0,
            'max_exp': 10,
            'min_salary': 0,
            'max_salary': 15,
            'current_cities': [],
            'preferred_cities': [],
            'recruiter_company': 'TestCompany',
            'candidates': [],
            'total_results': 0,
            'search_applied': False,
            'page': 0,
            'max_candidates': 100
        }
    
    def get_search_form_json(self) -> Dict[str, Any]:
        """Get current search form as JSON."""
        return {
            "keywords": self.session_state.get('keywords', []),
            "min_experience": self.session_state.get('min_exp', 0),
            "max_experience": self.session_state.get('max_exp', 10),
            "min_salary": self.session_state.get('min_salary', 0),
            "max_salary": self.session_state.get('max_salary', 15),
            "current_cities": self.session_state.get('current_cities', []),
            "preferred_cities": self.session_state.get('preferred_cities', []),
            "total_results": self.session_state.get('total_results', 0),
            "search_executed": self.session_state.get('search_applied', False)
        }
    
    def update_from_response(self, response_data: Dict[str, Any]):
        """Update session state from agent response."""
        if "session_state" in response_data:
            self.session_state.update(response_data["session_state"])
        
        # Update search execution status
        if response_data.get("trigger_search", False):
            self.session_state['search_applied'] = True
        
        # Update results if search was executed
        if "search_results" in response_data:
            search_results = response_data["search_results"]
            self.session_state['total_results'] = search_results.get('total_count', 0)
            self.session_state['candidates'] = search_results.get('candidates', [])


class LLMQueryPredictor:
    """Uses LLM to predict expected search form changes."""
    
    def __init__(self):
        self.llm_tool = LLMTool("test_llm_tool")
    
    async def predict_search_form_changes(self, query: str, initial_form: Dict[str, Any]) -> Dict[str, Any]:
        """Predict how the search form should change after processing the query."""
        
        prompt = f"""You are an expert at understanding search form modifications for a recruitment system.

CURRENT SEARCH FORM STATE:
{json.dumps(initial_form, indent=2)}

USER QUERY: "{query}"

TASK: Predict what the search form should look like AFTER processing this user query.

SEARCH FORM MODIFICATION RULES:
1. **Keywords/Skills**: 
   - Adding skills: append to keywords array
   - Mandatory skills: prefix with "★ " (e.g., "★ Python")
   - Optional skills: no prefix (e.g., "Java")
   - Removing skills: remove from keywords array
   - Similar/related skills: add expanded skills to array

2. **Experience**: 
   - Range format: min_experience and max_experience (in years)
   - "5+ years" means min_experience=5, keep current max
   - "5-10 years" means min_experience=5, max_experience=10
   - "increase by X" means add X to current max_experience

3. **Salary**: 
   - Range format: min_salary and max_salary (in lakhs LPA)
   - "10-20 LPA" means min_salary=10, max_salary=20
   - "increase by X" means add X to current max_salary

4. **Locations**:
   - current_cities: optional locations
   - preferred_cities: mandatory locations
   - "nearby X" or "similar to X": add expanded locations

5. **Search Execution**:
   - search_executed: true if query contains "search", "find candidates", "execute", etc.
   - total_results: estimate based on filter complexity (more filters = fewer results)

6. **Expansion Logic**:
   - "similar skills to Python" → add related skills like ["Django", "Flask", "FastAPI"]
   - "similar titles to Data Scientist" → add skills like ["Python", "Machine Learning", "SQL"]
   - "nearby Mumbai" → add locations like ["Pune", "Thane", "Nashik"]

EXAMPLES:

Query: "add python and java"
→ Add "Python" and "Java" to keywords

Query: "add python as mandatory"
→ Add "★ Python" to keywords

Query: "set experience 5-10 years"
→ min_experience: 5, max_experience: 10

Query: "similar skills to python"
→ Add related skills: ["Django", "Flask", "FastAPI", "NumPy", "Pandas"]

Query: "nearby locations to mumbai"
→ Add to current_cities: ["Pune", "Thane", "Nashik", "Aurangabad"]

Query: "find candidates with java"
→ Add "Java" to keywords AND set search_executed: true

Query: "expand python skills and search"
→ Add Python-related skills AND set search_executed: true

RESULT ESTIMATION:
- More keywords/filters → fewer results (estimate 100-500)
- Fewer keywords/filters → more results (estimate 1000-5000)
- Very specific queries → very few results (estimate 10-100)
- Very broad queries → many results (estimate 5000-10000)

Return ONLY valid JSON in this EXACT format:
{{
    "keywords": ["array", "of", "skills"],
    "min_experience": 0,
    "max_experience": 10,
    "min_salary": 0,
    "max_salary": 15,
    "current_cities": ["array", "of", "optional", "cities"],
    "preferred_cities": ["array", "of", "mandatory", "cities"],
    "total_results": estimated_number,
    "search_executed": true_or_false,
    "reasoning": "brief explanation of changes made"
}}"""

        try:
            print(f"🔮 LLM predicting search form changes for: '{query}'")
            
            llm_result = await self.llm_tool._call_llm_direct(
                prompt=prompt,
                task="search_form_prediction"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result:
                predicted_form = llm_result["parsed_response"]
                print(f"✅ LLM prediction successful")
                print(f"🔍 Predicted reasoning: {predicted_form.get('reasoning', 'No reasoning provided')}")
                return predicted_form
            
            elif llm_result["success"] and "response_text" in llm_result:
                # Try to parse JSON from response text
                import re
                response_text = llm_result["response_text"]
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    try:
                        predicted_form = json.loads(json_match.group())
                        print(f"✅ LLM prediction successful (manual parsing)")
                        return predicted_form
                    except json.JSONDecodeError:
                        pass
            
            print(f"❌ LLM prediction failed: {llm_result.get('error', 'Unknown error')}")
            return self._fallback_prediction(query, initial_form)
            
        except Exception as e:
            print(f"❌ LLM prediction error: {e}")
            return self._fallback_prediction(query, initial_form)
    
    def _fallback_prediction(self, query: str, initial_form: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction when LLM fails."""
        print(f"🔄 Using fallback prediction for: '{query}'")
        
        # Simple rule-based fallback
        predicted = initial_form.copy()
        predicted["reasoning"] = "Fallback prediction - LLM unavailable"
        
        query_lower = query.lower()
        
        # Simple skill detection
        if "python" in query_lower:
            if "Python" not in predicted["keywords"]:
                predicted["keywords"].append("Python")
        
        if "java" in query_lower:
            if "Java" not in predicted["keywords"]:
                predicted["keywords"].append("Java")
        
        # Simple experience detection
        if "experience" in query_lower and "5" in query_lower:
            predicted["min_experience"] = 5
        
        # Simple search detection
        if any(word in query_lower for word in ["search", "find", "execute"]):
            predicted["search_executed"] = True
            predicted["total_results"] = 500  # Default estimate
        
        return predicted


class LLMResultEvaluator:
    """Uses LLM to evaluate if actual results match predicted results."""
    
    def __init__(self):
        self.llm_tool = LLMTool("eval_llm_tool")
    
    async def evaluate_results(self, query: str, predicted_form: Dict[str, Any], 
                             actual_form: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Evaluate if actual results match predicted results using LLM."""
        
        prompt = f"""You are an expert evaluator for a recruitment search system. Your job is to determine if the actual search form changes match the predicted changes for a given user query.

USER QUERY: "{query}"

PREDICTED SEARCH FORM:
{json.dumps(predicted_form, indent=2)}

ACTUAL SEARCH FORM:
{json.dumps(actual_form, indent=2)}

EVALUATION CRITERIA:

1. **EXACT MATCHES** (High Weight):
   - Keywords/skills added correctly
   - Experience ranges set correctly
   - Salary ranges set correctly
   - Location additions are correct
   - Search execution status matches

2. **SEMANTIC MATCHES** (Medium Weight):
   - Similar skills added (e.g., predicted "Django" but got "Flask" for Python)
   - Nearby locations added (e.g., predicted "Pune" but got "Thane" for Mumbai)
   - Equivalent titles/roles added

3. **ACCEPTABLE VARIATIONS** (Low Weight):
   - Minor differences in skill names (e.g., "JavaScript" vs "JS")
   - Small differences in number ranges (±1-2 years experience)
   - Different but equivalent locations

4. **CRITICAL FAILURES** (Immediate FAIL):
   - Completely wrong operation (added skills when should remove)
   - Totally wrong values (experience 20 when should be 5)
   - Missing mandatory changes (didn't add required skills)
   - Wrong search execution (executed when shouldn't or vice versa)

5. **SPECIAL CASES**:
   - If query was vague/ambiguous, be more lenient
   - If expansion was involved, accept reasonable variations
   - If search was complex, allow some differences

SCORING GUIDELINES:
- **PASS (90-100%)**: Excellent match, minor or no differences
- **PASS (70-89%)**: Good match with acceptable variations
- **PASS (50-69%)**: Reasonable match with some differences but core intent preserved
- **FAIL (0-49%)**: Poor match, significant differences or wrong operations

Return ONLY valid JSON in this EXACT format:
{{
    "pass": true_or_false,
    "confidence_score": 0.0_to_1.0,
    "detailed_analysis": {{
        "keywords_match": "exact|good|partial|poor",
        "experience_match": "exact|good|partial|poor", 
        "salary_match": "exact|good|partial|poor",
        "location_match": "exact|good|partial|poor",
        "search_execution_match": "exact|different|not_applicable"
    }},
    "reasoning": "detailed explanation of why this passed or failed",
    "key_differences": ["list", "of", "main", "differences"],
    "score_percentage": 0_to_100
}}"""

        try:
            print(f"🧠 LLM evaluating results for: '{query}'")
            
            llm_result = await self.llm_tool._call_llm_direct(
                prompt=prompt,
                task="result_evaluation"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result:
                evaluation = llm_result["parsed_response"]
                
                is_pass = evaluation.get("pass", False)
                confidence = evaluation.get("confidence_score", 0.0)
                reasoning = evaluation.get("reasoning", "No reasoning provided")
                
                print(f"✅ LLM evaluation: {'PASS' if is_pass else 'FAIL'} (confidence: {confidence:.2f})")
                print(f"🔍 Reasoning: {reasoning}")
                
                return is_pass, reasoning, confidence
            
            elif llm_result["success"] and "response_text" in llm_result:
                # Try to parse JSON from response text
                import re
                response_text = llm_result["response_text"]
                
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    try:
                        evaluation = json.loads(json_match.group())
                        is_pass = evaluation.get("pass", False)
                        confidence = evaluation.get("confidence_score", 0.0)
                        reasoning = evaluation.get("reasoning", "Parsed from text")
                        
                        print(f"✅ LLM evaluation (manual parsing): {'PASS' if is_pass else 'FAIL'}")
                        return is_pass, reasoning, confidence
                    except json.JSONDecodeError:
                        pass
            
            print(f"❌ LLM evaluation failed: {llm_result.get('error', 'Unknown error')}")
            return self._fallback_evaluation(predicted_form, actual_form)
            
        except Exception as e:
            print(f"❌ LLM evaluation error: {e}")
            return self._fallback_evaluation(predicted_form, actual_form)
    
    def _fallback_evaluation(self, predicted_form: Dict[str, Any], 
                           actual_form: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Fallback evaluation when LLM fails."""
        print(f"🔄 Using fallback evaluation")
        
        # Simple comparison fallback
        matches = 0
        total_checks = 0
        
        # Check keywords
        total_checks += 1
        if predicted_form.get("keywords") == actual_form.get("keywords"):
            matches += 1
        
        # Check experience
        total_checks += 1
        if (predicted_form.get("min_experience") == actual_form.get("min_experience") and
            predicted_form.get("max_experience") == actual_form.get("max_experience")):
            matches += 1
        
        # Check search execution
        total_checks += 1
        if predicted_form.get("search_executed") == actual_form.get("search_executed"):
            matches += 1
        
        score = matches / total_checks if total_checks > 0 else 0.0
        is_pass = score >= 0.7
        
        reasoning = f"Fallback evaluation: {matches}/{total_checks} components matched (score: {score:.2f})"
        
        return is_pass, reasoning, score


class RobustResDexTester:
    """Robust testing framework using LLM for intelligent evaluation."""
    
    def __init__(self):
        self.agent = None
        self.session_capture = SessionStateCapture()
        self.predictor = LLMQueryPredictor()
        self.evaluator = LLMResultEvaluator()
        self.test_results = []
        self.session_id = "robust_test_session"
    
    async def initialize_agent(self):
        """Initialize the ResDex agent."""
        try:
            print("🚀 Initializing ResDex Agent...")
            config = AgentConfig.from_env()
            self.agent = ResDexRootAgent(config)
            print("✅ ResDex Agent initialized successfully")
            print(f"📊 Available agents: {list(self.agent.sub_agents.keys())}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize ResDex Agent: {e}")
            traceback.print_exc()
            return False
    
    async def process_single_query(self, query: str) -> Dict[str, Any]:
        """Process a single query and return comprehensive results."""
        print(f"\n{'='*80}")
        print(f"🔍 Processing Query: {query}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Get initial search form state
            initial_form = self.session_capture.get_search_form_json()
            print(f"📋 Initial Search Form:")
            print(f"   Keywords: {initial_form['keywords']}")
            print(f"   Experience: {initial_form['min_experience']}-{initial_form['max_experience']} years")
            print(f"   Salary: {initial_form['min_salary']}-{initial_form['max_salary']} LPA")
            print(f"   Cities: {initial_form['current_cities']} | Preferred: {initial_form['preferred_cities']}")
            
            # Step 2: LLM predicts expected changes
            start_prediction = time.time()
            predicted_form = await self.predictor.predict_search_form_changes(query, initial_form)
            prediction_time = time.time() - start_prediction
            
            print(f"🔮 LLM Predicted Changes ({prediction_time:.2f}s):")
            print(f"   Keywords: {predicted_form.get('keywords', [])}")
            print(f"   Experience: {predicted_form.get('min_experience', 0)}-{predicted_form.get('max_experience', 10)} years")
            print(f"   Salary: {predicted_form.get('min_salary', 0)}-{predicted_form.get('max_salary', 15)} LPA")
            print(f"   Search Executed: {predicted_form.get('search_executed', False)}")
            
            # Step 3: Execute query through agent
            start_execution = time.time()
            content = Content(data={
                "user_input": query,
                "session_state": self.session_capture.session_state,
                "session_id": self.session_id,
                "user_id": "test_user"
            })
            
            response = await self.agent.execute(content)
            execution_time = time.time() - start_execution
            
            if not response or not hasattr(response, 'data'):
                raise Exception("No response received from agent")
            
            # Step 4: Update session state and get actual form
            self.session_capture.update_from_response(response.data)
            actual_form = self.session_capture.get_search_form_json()
            
            print(f"🤖 Agent Response ({execution_time:.2f}s):")
            print(f"   Keywords: {actual_form['keywords']}")
            print(f"   Experience: {actual_form['min_experience']}-{actual_form['max_experience']} years")
            print(f"   Salary: {actual_form['min_salary']}-{actual_form['max_salary']} LPA")
            print(f"   Search Executed: {actual_form['search_executed']}")
            print(f"   Agent Used: {response.data.get('routed_to', 'unknown')}")
            
            # Step 5: LLM evaluates the match
            start_evaluation = time.time()
            is_pass, reasoning, confidence = await self.evaluator.evaluate_results(
                query, predicted_form, actual_form
            )
            evaluation_time = time.time() - start_evaluation
            
            print(f"🧠 LLM Evaluation ({evaluation_time:.2f}s):")
            print(f"   Result: {'✅ PASS' if is_pass else '❌ FAIL'}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Reasoning: {reasoning}")
            
            # Step 6: Compile results
            result = {
                'query': query,
                'initial_form': initial_form,
                'predicted_form': predicted_form,
                'actual_form': actual_form,
                'prediction_time': prediction_time,
                'execution_time': execution_time,
                'evaluation_time': evaluation_time,
                'total_time': prediction_time + execution_time + evaluation_time,
                'passed': is_pass,
                'confidence': confidence,
                'reasoning': reasoning,
                'agent_used': response.data.get('routed_to', 'unknown'),
                'response_data': response.data
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            traceback.print_exc()
            
            return {
                'query': query,
                'initial_form': self.session_capture.get_search_form_json(),
                'predicted_form': {},
                'actual_form': {},
                'prediction_time': 0.0,
                'execution_time': 0.0,
                'evaluation_time': 0.0,
                'total_time': 0.0,
                'passed': False,
                'confidence': 0.0,
                'reasoning': f"Processing failed: {str(e)}",
                'agent_used': 'error',
                'response_data': {}
            }
    
    async def run_tests(self, query_file: str, output_file: str):
        """Run the complete test suite."""
        if not await self.initialize_agent():
            return False
        
        print(f"\n📖 Reading queries from: {query_file}")
        
        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out comment lines and empty lines
            queries = []
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line and not cleaned_line.startswith('#'):
                    queries.append(cleaned_line)
                    
        except FileNotFoundError:
            print(f"❌ Query file not found: {query_file}")
            return False
        
        print(f"📊 Found {len(queries)} valid queries to test")
        
        # Initialize session
        step_logger.start_session(self.session_id)
        print(f"🔄 Using session: {self.session_id}")
        
        # Process each query
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test {i}/{len(queries)}")
            
            result = await self.process_single_query(query)
            self.test_results.append(result)
            
            # Reset session state for next query (optional)
            # self.session_capture.reset()
        
        # Write results
        await self.write_results_to_csv(output_file)
        await self.write_detailed_results()
        self.print_summary()
        
        return True
    
    async def write_results_to_csv(self, output_file: str):
        """Write results to CSV with comprehensive information."""
        try:
            print(f"\n📝 Writing results to: {output_file}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Query',
                    'Predicted_JSON',
                    'Actual_JSON', 
                    'LLM_Binary_Response',
                    'Confidence_Score',
                    'LLM_Reasoning',
                    'Agent_Used',
                    'Prediction_Time_s',
                    'Execution_Time_s',
                    'Evaluation_Time_s',
                    'Total_Time_s',
                    'Status'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow({
                        'Query': result['query'],
                        'Predicted_JSON': json.dumps(result['predicted_form'], separators=(',', ':')),
                        'Actual_JSON': json.dumps(result['actual_form'], separators=(',', ':')),
                        'LLM_Binary_Response': 'PASS' if result['passed'] else 'FAIL',
                        'Confidence_Score': f"{result['confidence']:.3f}",
                        'LLM_Reasoning': result['reasoning'],
                        'Agent_Used': result['agent_used'],
                        'Prediction_Time_s': f"{result['prediction_time']:.3f}",
                        'Execution_Time_s': f"{result['execution_time']:.3f}",
                        'Evaluation_Time_s': f"{result['evaluation_time']:.3f}",
                        'Total_Time_s': f"{result['total_time']:.3f}",
                        'Status': 'PASSED' if result['passed'] else 'FAILED'
                    })
            
            print(f"✅ Results written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing results to CSV: {e}")
    
    async def write_detailed_results(self):
        """Write detailed results file."""
        try:
            with open('detailed_results.txt', 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ROBUST RESDEX AGENT TEST RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                # Overall summary
                total_tests = len(self.test_results)
                passed_tests = sum(1 for r in self.test_results if r['passed'])
                total_time = sum(r['total_time'] for r in self.test_results)
                avg_time = total_time / total_tests if total_tests > 0 else 0
                avg_confidence = sum(r['confidence'] for r in self.test_results) / total_tests if total_tests > 0 else 0
                
                f.write(f"OVERALL SUMMARY:\n")
                f.write(f"Total Queries: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {total_tests - passed_tests}\n")
                f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
                f.write(f"Average Confidence: {avg_confidence:.3f}\n")
                f.write(f"Total Time: {total_time:.3f}s\n")
                f.write(f"Average Time per Query: {avg_time:.3f}s\n\n")
                
                # Time breakdown
                total_prediction_time = sum(r['prediction_time'] for r in self.test_results)
                total_execution_time = sum(r['execution_time'] for r in self.test_results)
                total_evaluation_time = sum(r['evaluation_time'] for r in self.test_results)
                
                f.write(f"TIME BREAKDOWN:\n")
                f.write(f"Prediction Time: {total_prediction_time:.3f}s ({total_prediction_time/total_time*100:.1f}%)\n")
                f.write(f"Execution Time: {total_execution_time:.3f}s ({total_execution_time/total_time*100:.1f}%)\n")
                f.write(f"Evaluation Time: {total_evaluation_time:.3f}s ({total_evaluation_time/total_time*100:.1f}%)\n\n")
                
                # Agent usage statistics
                f.write("AGENT USAGE STATISTICS:\n")
                agent_counts = {}
                for result in self.test_results:
                    agent = result.get('agent_used', 'unknown')
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
                for agent, count in agent_counts.items():
                    f.write(f"  {agent}: {count} queries\n")
                f.write("\n")
                
                # Failed test details
                failed_tests = [r for r in self.test_results if not r['passed']]
                if failed_tests:
                    f.write("FAILED TEST DETAILS:\n")
                    f.write("=" * 40 + "\n")
                    for i, result in enumerate(failed_tests, 1):
                        f.write(f"\nFailed Test {i}:\n")
                        f.write(f"Query: {result['query']}\n")
                        f.write(f"Agent: {result['agent_used']}\n")
                        f.write(f"Confidence: {result['confidence']:.3f}\n")
                        f.write(f"Reasoning: {result['reasoning']}\n")
                        f.write(f"Predicted: {json.dumps(result['predicted_form'], indent=2)}\n")
                        f.write(f"Actual: {json.dumps(result['actual_form'], indent=2)}\n")
                        f.write("-" * 40 + "\n")
            
            print("✅ Detailed results written to detailed_results.txt")
            
        except Exception as e:
            print(f"❌ Error writing detailed results: {e}")
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print(f"\n{'='*80}")
        print("📊 ROBUST TEST SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        total_time = sum(r['total_time'] for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        avg_confidence = sum(r['confidence'] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Queries: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {total_tests - passed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   🎯 Average Confidence: {avg_confidence:.3f}")
        print(f"   ⏱️ Total Time: {total_time:.3f}s")
        print(f"   ⏱️ Average Time per Query: {avg_time:.3f}s")
        print()
        
        # Time breakdown
        total_prediction_time = sum(r['prediction_time'] for r in self.test_results)
        total_execution_time = sum(r['execution_time'] for r in self.test_results)
        total_evaluation_time = sum(r['evaluation_time'] for r in self.test_results)
        
        print(f"⏱️ TIME BREAKDOWN:")
        print(f"   🔮 Prediction: {total_prediction_time:.3f}s ({total_prediction_time/total_time*100:.1f}%)")
        print(f"   🤖 Execution: {total_execution_time:.3f}s ({total_execution_time/total_time*100:.1f}%)")
        print(f"   🧠 Evaluation: {total_evaluation_time:.3f}s ({total_evaluation_time/total_time*100:.1f}%)")
        print()
        
        # Agent usage stats
        print(f"🤖 AGENT USAGE:")
        agent_counts = {}
        for result in self.test_results:
            agent = result.get('agent_used', 'unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        for agent, count in agent_counts.items():
            print(f"   {agent}: {count} queries")
        print()
        
        # Confidence distribution
        high_conf = sum(1 for r in self.test_results if r['confidence'] >= 0.8)
        med_conf = sum(1 for r in self.test_results if 0.5 <= r['confidence'] < 0.8)
        low_conf = sum(1 for r in self.test_results if r['confidence'] < 0.5)
        
        print(f"🎯 CONFIDENCE DISTRIBUTION:")
        print(f"   High (≥0.8): {high_conf} queries")
        print(f"   Medium (0.5-0.8): {med_conf} queries")
        print(f"   Low (<0.5): {low_conf} queries")
        print()
        
        # Show some examples
        failed_tests = [r for r in self.test_results if not r['passed']]
        if failed_tests:
            print(f"❌ FAILED EXAMPLES:")
            for i, result in enumerate(failed_tests[:3], 1):  # Show first 3 failures
                print(f"   {i}. Query: '{result['query']}'")
                print(f"      Agent: {result['agent_used']}")
                print(f"      Confidence: {result['confidence']:.3f}")
                print(f"      Reason: {result['reasoning'][:100]}...")
                
                # Show key differences in JSON
                predicted = result.get('predicted_form', {})
                actual = result.get('actual_form', {})
                
                # Show keywords comparison if different
                pred_keywords = predicted.get('keywords', [])
                actual_keywords = actual.get('keywords', [])
                if pred_keywords != actual_keywords:
                    print(f"      Keywords - Predicted: {pred_keywords}")
                    print(f"      Keywords - Actual: {actual_keywords}")
                
                # Show experience comparison if different
                pred_exp = f"{predicted.get('min_experience', 0)}-{predicted.get('max_experience', 10)}"
                actual_exp = f"{actual.get('min_experience', 0)}-{actual.get('max_experience', 10)}"
                if pred_exp != actual_exp:
                    print(f"      Experience - Predicted: {pred_exp} years")
                    print(f"      Experience - Actual: {actual_exp} years")
                
                # Show search execution if different
                pred_search = predicted.get('search_executed', False)
                actual_search = actual.get('search_executed', False)
                if pred_search != actual_search:
                    print(f"      Search - Predicted: {pred_search}")
                    print(f"      Search - Actual: {actual_search}")
                
                print()
        
        # Show some successful examples
        passed_tests = [r for r in self.test_results if r['passed'] and r['confidence'] >= 0.9]
        if passed_tests:
            print(f"✅ HIGH-CONFIDENCE SUCCESSES:")
            for i, result in enumerate(passed_tests[:2], 1):  # Show first 2 high-confidence passes
                print(f"   {i}. Query: '{result['query']}'")
                print(f"      Agent: {result['agent_used']}")
                print(f"      Confidence: {result['confidence']:.3f}")
                print(f"      Time: {result['total_time']:.2f}s")
                print()


def create_robust_queries_file(filename: str = 'robust_queries.txt'):
    """Create a comprehensive queries file for robust testing."""
    
    queries = [
        "# Simple Skill Operations",
        "add python skill",
        "add java and javascript",
        "remove python skill",
        "add python as mandatory",
        "make java optional",
        
        "# Experience Operations", 
        "set experience 5+ years",
        "set experience range 3-8 years",
        "increase experience by 2 years",
        "set minimum experience to 7 years",
        
        "# Salary Operations",
        "set salary 10-20 lpa",
        "increase salary range by 5 lakhs",
        "set minimum salary 15 lakhs",
        "salary range 8-25 lpa",
        
        "# Location Operations",
        "add bangalore location",
        "add mumbai as preferred location",
        "remove delhi location",
        "add pune and hyderabad",
        
        "# Expansion Operations",
        "find similar skills to python",
        "get skills related to data science",
        "similar titles to software engineer",
        "nearby locations to mumbai",
        "expand python skills",
        
        "# Search Operations",
        "search with current filters",
        "find candidates with java",
        "execute search now",
        "show me results",
        
        "# Complex Multi-step Operations",
        "add python skill and search",
        "find similar skills to java and set experience 5+ years",
        "add nearby cities to bangalore and search candidates",
        "get data science skills and set salary 15-30 lpa",
        "similar titles to product manager and add relevant skills",
        
        "# Edge Cases",
        "similar skills",
        "expand my query",
        "add more filters",
        "improve search results",
        "find better candidates",
        
        "# Ambiguous Queries", 
        "make it better",
        "add relevant skills",
        "update experience",
        "modify location",
        "enhance the search",
        
        "# Complex Contextual Queries",
        "find frontend developers with react experience in bangalore",
        "search for senior java developers with 8+ years in mumbai or pune",
        "get machine learning engineers with python skills and 10-20 lpa salary",
        "find devops engineers with aws experience near delhi",
        "search for product managers with 5+ years experience in tech companies"
    ]
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Robust ResDex Agent Test Queries\n")
            f.write("# Comprehensive test cases for LLM-based evaluation\n")
            f.write("# Total queries: covers all major operations and edge cases\n\n")
            
            for query in queries:
                f.write(f"{query}\n")
        
        # Count actual queries (non-comment lines)
        actual_queries = [q for q in queries if not q.startswith('#')]
        
        print(f"✅ Robust queries file created: {filename}")
        print(f"📊 Total queries: {len(actual_queries)}")
        print(f"📋 Categories: Skills, Experience, Salary, Location, Expansion, Search, Complex, Edge Cases")
        return True
        
    except Exception as e:
        print(f"❌ Error creating robust queries file: {e}")
        return False


async def test_llm_components():
    """Test LLM components independently."""
    print("🧪 Testing LLM Components...")
    
    # Test predictor
    print("\n🔮 Testing LLM Predictor...")
    predictor = LLMQueryPredictor()
    
    initial_form = {
        "keywords": [],
        "min_experience": 0,
        "max_experience": 10,
        "min_salary": 0,
        "max_salary": 15,
        "current_cities": [],
        "preferred_cities": [],
        "total_results": 0,
        "search_executed": False
    }
    
    test_query = "add python and java skills"
    predicted = await predictor.predict_search_form_changes(test_query, initial_form)
    
    print(f"   Query: {test_query}")
    print(f"   Predicted: {json.dumps(predicted, indent=2)}")
    
    # Test evaluator
    print("\n🧠 Testing LLM Evaluator...")
    evaluator = LLMResultEvaluator()
    
    actual_form = {
        "keywords": ["Python", "Java"],
        "min_experience": 0,
        "max_experience": 10,
        "min_salary": 0,
        "max_salary": 15,
        "current_cities": [],
        "preferred_cities": [],
        "total_results": 0,
        "search_executed": False
    }
    
    is_pass, reasoning, confidence = await evaluator.evaluate_results(
        test_query, predicted, actual_form
    )
    
    print(f"   Result: {'PASS' if is_pass else 'FAIL'}")
    print(f"   Confidence: {confidence:.3f}")
    print(f"   Reasoning: {reasoning}")
    
    return True


async def main():
    """Enhanced main function with robust testing options."""
    parser = argparse.ArgumentParser(
        description='Robust LLM-Based Test Suite for ResDex Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py --create_sample              # Create robust sample queries
  python test.py --test_llm                   # Test LLM components only
  python test.py                              # Run full robust test suite
  python test.py --query_file custom.txt      # Use custom query file
  python test.py --output_file results.csv    # Custom output file
        """
    )
    
    parser.add_argument('--query_file', default='robust_queries.txt',
                       help='Path to file containing queries (default: robust_queries.txt)')
    parser.add_argument('--output_file', default='robust_output.csv',
                       help='Path to output CSV file (default: robust_output.csv)')
    parser.add_argument('--create_sample', action='store_true',
                       help='Create robust sample queries file')
    parser.add_argument('--test_llm', action='store_true',
                       help='Test LLM components only (predictor and evaluator)')
    parser.add_argument('--reset_session', action='store_true',
                       help='Reset session state between queries (default: maintain state)')
    
    args = parser.parse_args()
    
    print("🚀 Robust ResDex Agent Test Suite")
    print("=" * 60)
    print("🧠 Uses LLM (Qwen) for intelligent prediction and evaluation")
    print("📊 Compares predicted vs actual search form JSON")
    print("🎯 Provides confidence scores and detailed reasoning")
    print("=" * 60)
    
    if args.create_sample:
        success = create_robust_queries_file(args.query_file)
        if success:
            print(f"\n🎯 Robust queries created successfully!")
            print(f"📝 File: {args.query_file}")
            print(f"🔍 You can now run: python test.py --query_file {args.query_file}")
            print(f"\n📋 Features:")
            print(f"   • Comprehensive query coverage")
            print(f"   • Edge cases and ambiguous queries") 
            print(f"   • Complex multi-step operations")
            print(f"   • LLM-based intelligent evaluation")
        return
    
    if args.test_llm:
        success = await test_llm_components()
        if success:
            print("\n✅ LLM components test completed!")
        else:
            print("\n❌ LLM components test failed!")
        return
    
    if not os.path.exists(args.query_file):
        print(f"❌ Query file not found: {args.query_file}")
        print(f"💡 Tip: Use --create_sample to create a robust queries file")
        return
    
    # Run robust tests
    print(f"🔍 Running robust LLM-based tests...")
    print(f"📖 Query file: {args.query_file}")
    print(f"📊 Output file: {args.output_file}")
    print(f"📋 Detailed results: detailed_results.txt")
    print(f"🔄 Reset session: {args.reset_session}")
    
    tester = RobustResDexTester()
    
    # Configure session reset behavior
    if args.reset_session:
        print("🔄 Will reset session state between queries")
    else:
        print("🔗 Will maintain session state across queries")
    
    success = await tester.run_tests(args.query_file, args.output_file)
    
    if success:
        print(f"\n🎉 Robust testing completed successfully!")
        print(f"📊 Summary results: {args.output_file}")
        print(f"📋 Detailed results: detailed_results.txt")
        print(f"🔍 Session: {tester.session_id}")
        print(f"\n💡 Key Features Used:")
        print(f"   🔮 LLM prediction of expected changes")
        print(f"   🤖 Agent execution and response capture")
        print(f"   🧠 LLM evaluation with confidence scoring")
        print(f"   📊 Comprehensive JSON comparison")
    else:
        print(f"\n💥 Robust testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Robust testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error in robust testing: {e}")
        traceback.print_exc()
        sys.exit(1)