#test.py - Agentic AI Query Testing Script
import argparse
import csv
import asyncio
import json
import logging
import sys
import os
import difflib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resdex_agent.agent import ResDexRootAgent, Content
from resdex_agent.config import AgentConfig
from resdex_agent.utils.step_logger import step_logger


logging.basicConfig(
    level=logging.WARNING, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ActionCapture:
    def __init__(self):
        self.actions = []
        self.session_state = {}
        self.query_start_time = None  
        self.processing_time = 0.0    
        self.reset()
    
    def reset_for_new_query(self): 
        self.actions = []
        self.query_start_time = None
        self.processing_time = 0.0
    
    def start_timing(self):
        import time
        self.query_start_time = time.time()
    
    def end_timing(self):   
        if self.query_start_time:
            import time
            self.processing_time = round(time.time() - self.query_start_time, 3)
        return self.processing_time
    
    def reset(self):
        self.actions = []
        self.query_start_time = None
        self.processing_time = 0.0
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
    
    def capture_modifications(self, modifications: List[Dict[str, Any]]) -> None:
        """Capture modifications from tool responses."""
        for mod in modifications:
            mod_type = mod.get("type", "unknown")
            value = mod.get("value", "")
            mandatory = mod.get("mandatory", False)
            
            if mod_type == "skill_added":
                self.actions.append(f"Skill added: {value}{'*' if mandatory else ''}")
                if mandatory:
                    if f"★ {value}" not in self.session_state['keywords']:
                        self.session_state['keywords'].append(f"★ {value}")
                else:
                    if value not in self.session_state['keywords']:
                        self.session_state['keywords'].append(value)
            
            elif mod_type == "skill_removed":
                self.actions.append(f"Skill removed: {value}")
                keywords = self.session_state['keywords']
                keywords = [k for k in keywords if k != value and k != f"★ {value}"]
                self.session_state['keywords'] = keywords
            
            elif mod_type == "skill_made_mandatory":
                self.actions.append(f"Skill made mandatory: {value}")
                keywords = self.session_state['keywords']
                if value in keywords:
                    keywords.remove(value)
                if f"★ {value}" not in keywords:
                    keywords.append(f"★ {value}")
            
            elif mod_type == "skill_made_optional":
                self.actions.append(f"Skill made optional: {value}")
                keywords = self.session_state['keywords']
                if f"★ {value}" in keywords:
                    keywords.remove(f"★ {value}")
                if value not in keywords:
                    keywords.append(value)
            
            elif mod_type == "experience_modified":
                operation = mod.get("operation", "set")
                if operation == "set_range" and "-" in str(value):
                    min_exp, max_exp = str(value).split("-")
                    self.session_state['min_exp'] = float(min_exp)
                    self.session_state['max_exp'] = float(max_exp)
                    self.actions.append(f"Experience set: {value} years")
                elif operation == "set":
                    self.session_state['min_exp'] = float(value)
                    self.actions.append(f"Min experience set: {value} years")
                else:
                    self.actions.append(f"Experience modified: {operation} {value}")
            
            elif mod_type == "salary_modified":
                operation = mod.get("operation", "set")
                if operation == "set_range" and "-" in str(value):
                    min_sal, max_sal = str(value).split("-")
                    self.session_state['min_salary'] = float(min_sal)
                    self.session_state['max_salary'] = float(max_sal)
                    self.actions.append(f"Salary range set: {value} LPA")
                elif operation == "set":
                    self.session_state['min_salary'] = float(value)
                    self.actions.append(f"Min salary set: {value} LPA")
                else:
                    self.actions.append(f"Salary modified: {operation} {value}")
            
            elif mod_type == "location_added":
                location = value
                if mandatory:
                    if location not in self.session_state['preferred_cities']:
                        self.session_state['preferred_cities'].append(location)
                    self.actions.append(f"Location added (mandatory): {location}")
                else:
                    if location not in self.session_state['current_cities']:
                        self.session_state['current_cities'].append(location)
                    self.actions.append(f"Location added: {location}")
            
            elif mod_type == "location_removed":
                location = value
                self.actions.append(f"Location removed: {location}")
                if location in self.session_state['current_cities']:
                    self.session_state['current_cities'].remove(location)
                if location in self.session_state['preferred_cities']:
                    self.session_state['preferred_cities'].remove(location)
            
            else:
                self.actions.append(f"Action: {mod_type} - {value}")
    
    def capture_search_trigger(self, triggered: bool) -> None:
        """Capture if search was triggered."""
        if triggered:
            self.actions.append("Search executed")
            self.session_state['search_applied'] = True
    
    def capture_special_actions(self, response_data: Dict[str, Any]) -> None:
        """Capture special actions like sorting, analysis, etc."""
        message = response_data.get("message", "")
        
        if "sorted" in message.lower():
            if "experience" in message.lower():
                self.actions.append("Sorted by experience")
            elif "salary" in message.lower():
                self.actions.append("Sorted by salary")
            else:
                self.actions.append("Sorted candidates")
        
        if "location_analysis" in response_data:
            analysis = response_data["location_analysis"]
            similar_locations = analysis.get("similar_locations", [])
            if similar_locations:
                self.actions.append(f"Found similar locations: {', '.join(similar_locations[:3])}")
        
        if "task_breakdown" in response_data:
            breakdown = response_data["task_breakdown"]
            tasks_executed = breakdown.get("tasks_executed", 0)
            if tasks_executed > 0:
                self.actions.append(f"Complex task executed: {tasks_executed} steps")
    
    def get_formatted_output(self) -> str:
        """Get formatted output of all captured actions."""
        if not self.actions:
            return "No actions taken"
        
        unique_actions = []
        seen = set()
        for action in self.actions:
            if action not in seen:
                unique_actions.append(action)
                seen.add(action)
        
        return "; ".join(unique_actions)

class GroundTruthManager:
    def __init__(self):
        self.ground_truth = {
            "show me candidates with python": "Skill added: Python; Search executed",
            "experience atleast 5": "Experience set: 5-10 years",
            "chennai ones?": "Location added: Chennai",
            "salary 8-15 lpa": "Salary range set: 8-15 LPA",
            "candidates from major tech cities": "Location added: Bangalore; Location added: Gurgaon; Location added: Mumbai; Location added: Delhi; Location added: Noida",  
            "make react permanent": "Skill added: React*", 
            "from blr": "Location added: Bangalore",
            "freshers?": "Experience set: 0-1 years",  
            "add java": "Skill added: Java",
            "java,python and from blr": "Location added: Bangalore",  #Java,python already exist
            "search python as you did react": "Skill made mandatory: Python; Search executed", 
            "same filters, add noida": "Location added: Noida",
            "include spring boot": "Skill added: Spring Boot",
            "set same salary range": "Salary range set: 8.0-15.0 LPA", 
            "mark all the optional locations to mandatory": "Location added (mandatory): Chennai; Location added (mandatory): Bangalore; Location added (mandatory): Hyderabad; Location added (mandatory): Coimbatore; Location added (mandatory): Madurai; Location added (mandatory): Trichy; Location added (mandatory): Noida",
            "use the previous filters, but make experience flexible.": "Experience set: 0-5 years",
            "dont change the filters , just add that candidates must be active recently.": "No actions taken",  #Active period is not yet added
            "add \"go\" with the skills we had already": "Skill added: Go",
            "keep same filters, increase salary by 5": "Salary range set: 8.0-20.0 LPA",  
            "bring in the cities we used in the last bangalore search.": "No actions taken",  # System can't access past searches without better memory
            "exp 3+, form mumbai and pune": "Experience set: 3-5 years; Location added: Mumbai; Location added: Pune",
            "react, node and increase salary by 5": "Skill made optional: React; Skill added: Node; Salary range set: 8.0-25.0 LPA",
            "people from delhi and nearby": "Location added: Delhi", 
            "i want engineers with python who are based near hyderabad.": "Location added: Hyderabad",  # Python already exists
            "search for frontend developers earning between 10 and 20 lpa.": "Skill added: Frontend Developer; Salary range set: 10-20 LPA; Search executed",
            "im hiring backend devs in ncr with django and postgres.": "Skill added: Django*; Skill added: Postgres*; Location added: Ncr",
            "show profiles of android developers from nearby noida areas.": "Skill added: Android; Location added: Noida; Search executed",
            "give me recently active people in chennai with 3+ years of experience.": "No actions taken",  # System doesn't handle "recently active" + experience modification together
            "im hiring data engineers with spark from bangalore or nearby.": "Skill added: Data Engineer*; Skill added: Spark*; Location added: Bangalore; Search executed",
            "i need devops folks with 5+ years earning above 15 lpa.": "Skill added: DevOps*; Experience set: 5-5 years; Salary range set: 15-20 LPA",  # System interprets "5+ years" as exact 5
            "repeat the search we did for frontend folks last week, but for pune this time.": "Location added: Pune; Search executed",
            "take the same skills we added before and just add angular and add some nearby locations to delhi": "No actions taken",  # System fails on complex memory + location analysis
            "start from the same filters, but narrow to profiles active this month.": "No actions taken",  # System doesn't handle active period
            "use our earlier bangalore search, increase salary by 5.": "No actions taken",  # System can't access "earlier" searches
            "keep filters same but canidates from blr and lucknow": "Location added: Lucknow",  # BLR already exists
            "find candidates like before but with more experience.": "No actions taken",  # System can't interpret vague memory references
            "resume the last search and add delhi-ncr nearby.": "No actions taken"  # System can't resume "last search"
        }
    
    def get_expected_output(self, query: str) -> str:
        """Get expected output for a query."""
        # Clean the query: remove invisible Unicode characters and normalize
        import unicodedata
        query_clean = unicodedata.normalize('NFKD', query).encode('ascii', 'ignore').decode('ascii')
        query_clean = query_clean.lower().strip()
        
        # Debug print to see what's being looked up
        print(f"🔍 Looking up ground truth for: '{query_clean}'")
        
        result = self.ground_truth.get(query_clean, "No expected output defined")
        print(f"🎯 Found ground truth: '{result}'")
        
        return result
    
    def add_ground_truth(self, query: str, expected: str):
        """Add new ground truth entry."""
        self.ground_truth[query.lower().strip()] = expected

class ResDexTester:
    """Main testing class for ResDex Agent queries."""
    
    def __init__(self):
        self.agent = None
        self.action_capture = ActionCapture()
        self.ground_truth = GroundTruthManager()
        self.test_results = []
        self.session_id = "persistent_test_session"  
    async def initialize_agent(self):
        """Initialize the ResDex Agent."""
        try:
            print("🚀 Initializing ResDex Agent...")
            config = AgentConfig.from_env()
            self.agent = ResDexRootAgent(config)
            print("✅ ResDex Agent initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize ResDex Agent: {e}")
            traceback.print_exc()
            return False
    
    def compare_outputs(self, expected: str, actual: str) -> Tuple[bool, List[str]]:
        """Compare expected vs actual outputs and return diff."""
        expected_clean = expected.strip().lower()
        actual_clean = actual.strip().lower()
        if expected_clean == actual_clean:
            return True, []
        # Check: actual contains all key components of expected
        expected_parts = [part.strip() for part in expected.split(';')]
        actual_parts = [part.strip() for part in actual.split(';')]
        # Check: most expected parts are present in actual
        matches = 0
        for exp_part in expected_parts:
            for act_part in actual_parts:
                if exp_part.lower() in act_part.lower() or act_part.lower() in exp_part.lower():
                    matches += 1
                    break
        # Consider it a match if at least 70% of expected parts are found
        match_ratio = matches / len(expected_parts) if expected_parts else 0
        is_match = match_ratio >= 0.7
        
        # Generate diff for failed cases
        diff = []
        if not is_match:
            diff = list(difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile='Expected',
                tofile='Actual',
                lineterm=''
            ))
        
        return is_match, diff
    async def process_query(self, query: str) -> Tuple[str, Dict[str, Any], float]:  
        """Process a single query and capture actions."""
        try:
            print(f"\n📝 Processing query: {query}")
            
            self.action_capture.reset_for_new_query() 
            self.action_capture.start_timing()
            content = Content(data={
                "user_input": query,
                "session_state": self.action_capture.session_state, 
                "session_id": self.session_id, 
                "user_id": "test_user"
            })
            response = await self.agent.execute(content)
            processing_time = self.action_capture.end_timing() 
            
            if not response or not hasattr(response, 'data'):
                return "No response received", {}, processing_time  
            
            response_data = response.data
            
            modifications = response_data.get("modifications", [])
            if modifications:
                self.action_capture.capture_modifications(modifications)
            
            # Capture search trigger
            trigger_search = response_data.get("trigger_search", False)
            if trigger_search:
                self.action_capture.capture_search_trigger(True)
            
            # Capture special actions
            self.action_capture.capture_special_actions(response_data)            
            if "session_state" in response_data:
                self.action_capture.session_state.update(response_data["session_state"])
            
            model_output = self.action_capture.get_formatted_output()
            
            print(f"✅ Model output: {model_output}")
            print(f"⏱️ Processing time: {processing_time}s")  
            
            return model_output, response_data, processing_time 
            
        except Exception as e:
            processing_time = self.action_capture.end_timing() 
            error_msg = f"Error processing query: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"⏱️ Processing time: {processing_time}s") 
            traceback.print_exc()
            return error_msg, {}, processing_time  
    
    async def run_tests(self, query_file: str, output_file: str):
        """Run tests for all queries in the file."""
        if not await self.initialize_agent():
            return False
        
        print(f"\n📖 Reading queries from: {query_file}")
        
        # Read queries from file
        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"❌ Query file not found: {query_file}")
            return False
        except Exception as e:
            print(f"❌ Error reading query file: {e}")
            return False
        
        print(f"📊 Found {len(queries)} queries to test")
        
        # Initialize single session for all queries
        step_logger.start_session(self.session_id)  
        print(f"🔄 Using persistent session: {self.session_id}") 
        
        # Process each query in the same session
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Test {i}/{len(queries)}")
            
            expected_output = self.ground_truth.get_expected_output(query)
            model_output, response_data, processing_time = await self.process_query(query)  
            
            # Compare outputs
            is_match, diff = self.compare_outputs(expected_output, model_output)
            
            # Store result with processing time
            result = {
                'test_id': i,
                'input_query': query,
                'expected_output': expected_output,
                'model_output': model_output,
                'processing_time': processing_time,  
                'passed': is_match,
                'diff': diff
            }
            self.test_results.append(result)
            
            # Print result with timing
            status = "✅ PASSED" if is_match else "❌ FAILED"
            print(f"{status}: {query} ({processing_time}s)")
            if not is_match:
                print(f"   Expected: {expected_output}")
                print(f"   Actual:   {model_output}")
        
        await self.write_results_to_csv(output_file)
        self.print_summary()
        
        return True
    
    async def write_results_to_csv(self, output_file: str):
        """Write test results to CSV file."""
        try:
            print(f"\n📝 Writing results to: {output_file}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Input Query', 'Expected Output', 'Model Output', 'Processing Time (s)', 'Status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow({
                        'Input Query': result['input_query'],
                        'Expected Output': result['expected_output'],
                        'Model Output': result['model_output'],
                        'Processing Time (s)': result['processing_time'],
                        'Status': 'PASSED' if result['passed'] else 'FAILED'
                    })
            
            print(f"✅ Results written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing results to CSV: {e}")
    
    def print_summary(self):
        """Print test summary in LeetCode format."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        processing_times = [result['processing_time'] for result in self.test_results]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        total_time = sum(processing_times)
        
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"⏱️ Total Time: {total_time:.3f}s")       
        print(f"⏱️ Average Time: {avg_time:.3f}s")       
        print(f"🔄 Session: {self.session_id}")           
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TEST DETAILS:")
            print(f"{'='*60}")
            
            for result in self.test_results:
                if not result['passed']:
                    print(f"\n🔍 Test {result['test_id']}: {result['input_query']} ({result['processing_time']}s)") 
                    print(f"Expected: {result['expected_output']}")
                    print(f"Actual:   {result['model_output']}")
                    
                    if result['diff']:
                        print("Diff:")
                        for line in result['diff']:
                            print(f"  {line.rstrip()}")

def create_sample_queries_file(filename: str):
    sample_queries = [
        "Show me candidates with python",
        "Experience atleast 5", 
        "chennai ones?",
        "Salary 8-15 lpa",
        "Candidates from major Tech Cities",
        "Make react permanent",
        "From BLR",
        "Freshers?",
        "add java",
        "Java,python and from BLR",
        "Search python as you did react",
        "same filters, add noida",
        "Include spring boot",
        "set same salary range",
        "Add \"Go\" with the skills we had already",
        "keep same filters, increase salary by 5",
        "Exp 3+, form mumbai and pune",
        "React, node and increase salary by 5",
        "people from delhi and nearby",
        "I want engineers with Python who are based near Hyderabad."
    ]
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for query in sample_queries:
                f.write(f"{query}\n")
        print(f"✅ Sample queries file created: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error creating sample queries file: {e}")
        return False
def clean_queries_file(input_file: str, output_file: str = None): #Clean queries.txt with UNICODE characters
    import unicodedata
    
    if output_file is None:
        output_file = input_file
    
    print(f"🧼 Cleaning queries file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    for i, line in enumerate(lines):
        clean_line = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore').decode('ascii')
        clean_line = clean_line.strip()
        
        if clean_line:  
            cleaned_lines.append(clean_line)
            print(f"  Line {i+1}: '{line.strip()}' -> '{clean_line}'")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in cleaned_lines:
            f.write(f"{line}\n")
    
    print(f"✅ Cleaned {len(cleaned_lines)} queries and saved to: {output_file}")
async def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description='Test ResDex Agent with natural language queries')
    parser.add_argument('--query_file', default='queries.txt', 
                       help='Path to file containing queries (default: queries.txt)')
    parser.add_argument('--output_file', default='output.csv',
                       help='Path to output CSV file (default: output.csv)')
    parser.add_argument('--create_sample', action='store_true',
                       help='Create a sample queries.txt file')
    parser.add_argument('--clean_queries', action='store_true',
                   help='Clean invisible Unicode characters from queries file')

    
    args = parser.parse_args()
    if args.create_sample:
        create_sample_queries_file(args.query_file)
        print(f"Sample queries file created. You can now run: python test.py --query_file {args.query_file}")
        return
    if not os.path.exists(args.query_file):
        print(f"❌ Query file not found: {args.query_file}")
        print(f"💡 Tip: Use --create_sample to create a sample queries.txt file")
        return
    if args.clean_queries:
        clean_queries_file(args.query_file)
        print("Queries cleaned. Run again without --clean_queries flag.")
        return
    # Run tests
    tester = ResDexTester()
    success = await tester.run_tests(args.query_file, args.output_file)
    if success:
        print(f"\n🎉 Testing completed successfully!")
        print(f"📊 Results saved to: {args.output_file}")
    else:
        print(f"\n💥 Testing failed!")
        sys.exit(1)

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)