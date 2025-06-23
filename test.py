# test_resdex_v2.py - Updated Testing Framework for ResDex Agent
import argparse
import csv
import asyncio
import json
import logging
import sys
import os
import copy
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

class QueryType:
    SINGLE_TOOL_NO_MEMORY = "single_tool_no_memory"
    SINGLE_TOOL_WITH_MEMORY = "single_tool_with_memory" 
    MULTI_TOOL_NO_MEMORY = "multi_tool_no_memory"
    MULTI_TOOL_WITH_MEMORY = "multi_tool_with_memory"

class StateComparator:
    """Compare initial vs final session states to detect changes."""
    
    @staticmethod
    def get_state_changes(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the changes between initial and final states."""
        changes = {}
        
        # Check skills/keywords changes
        initial_keywords = set(initial_state.get('keywords', []))
        final_keywords = set(final_state.get('keywords', []))
        
        if initial_keywords != final_keywords:
            changes['keywords'] = {
                'added': list(final_keywords - initial_keywords),
                'removed': list(initial_keywords - final_keywords),
                'final': list(final_keywords)
            }
        
        # Check experience changes
        initial_exp = (initial_state.get('min_exp', 0), initial_state.get('max_exp', 10))
        final_exp = (final_state.get('min_exp', 0), final_state.get('max_exp', 10))
        
        if initial_exp != final_exp:
            changes['experience'] = {
                'initial': f"{initial_exp[0]}-{initial_exp[1]}",
                'final': f"{final_exp[0]}-{final_exp[1]}"
            }
        
        # Check salary changes
        initial_sal = (initial_state.get('min_salary', 0), initial_state.get('max_salary', 15))
        final_sal = (final_state.get('min_salary', 0), final_state.get('max_salary', 15))
        
        if initial_sal != final_sal:
            changes['salary'] = {
                'initial': f"{initial_sal[0]}-{initial_sal[1]}",
                'final': f"{final_sal[0]}-{final_sal[1]}"
            }
        
        # Check location changes
        initial_current = set(initial_state.get('current_cities', []))
        final_current = set(final_state.get('current_cities', []))
        initial_preferred = set(initial_state.get('preferred_cities', []))
        final_preferred = set(final_state.get('preferred_cities', []))
        
        if initial_current != final_current or initial_preferred != final_preferred:
            changes['locations'] = {
                'current_added': list(final_current - initial_current),
                'current_removed': list(initial_current - final_current),
                'preferred_added': list(final_preferred - initial_preferred),
                'preferred_removed': list(initial_preferred - final_preferred),
                'final_current': list(final_current),
                'final_preferred': list(final_preferred)
            }
        
        # Check search execution
        initial_search = initial_state.get('search_applied', False)
        final_search = final_state.get('search_applied', False)
        search_triggered = final_state.get('candidates', []) != initial_state.get('candidates', [])
        
        if final_search != initial_search or search_triggered:
            changes['search_executed'] = True
        
        return changes
    
    @staticmethod
    def states_match(expected_changes: Dict[str, Any], actual_changes: Dict[str, Any]) -> bool:
        """Check if actual changes match expected changes exactly."""
        return json.dumps(expected_changes, sort_keys=True) == json.dumps(actual_changes, sort_keys=True)

class GroundTruthManager:
    """Manage ground truth data loaded from external files."""
    
    def __init__(self, queries_file: str = "queries.txt", groundtruth_file: str = "groundtruth.txt"):
        self.queries_file = queries_file
        self.groundtruth_file = groundtruth_file
        self.queries_by_type = {}
        self.ground_truth = {}
        self.load_queries_and_groundtruth()
    
    def load_queries_and_groundtruth(self):
        """Load queries and ground truth from external files."""
        try:
            # Load queries
            with open(self.queries_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Parse queries by type based on numbering
            self.queries_by_type = {
                QueryType.SINGLE_TOOL_NO_MEMORY: [],      # 1-10
                QueryType.SINGLE_TOOL_WITH_MEMORY: [],    # 11-20
                QueryType.MULTI_TOOL_NO_MEMORY: [],       # 21-30
                QueryType.MULTI_TOOL_WITH_MEMORY: []      # 31-40
            }
            
            for line in lines:
                if '. ' in line:
                    try:
                        num_str, query = line.split('. ', 1)
                        num = int(num_str)
                        
                        if 1 <= num <= 10:
                            self.queries_by_type[QueryType.SINGLE_TOOL_NO_MEMORY].append((num, query))
                        elif 11 <= num <= 20:
                            self.queries_by_type[QueryType.SINGLE_TOOL_WITH_MEMORY].append((num, query))
                        elif 21 <= num <= 30:
                            self.queries_by_type[QueryType.MULTI_TOOL_NO_MEMORY].append((num, query))
                        elif 31 <= num <= 40:
                            self.queries_by_type[QueryType.MULTI_TOOL_WITH_MEMORY].append((num, query))
                    except ValueError:
                        continue
            
            # Load ground truth
            with open(self.groundtruth_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse ground truth entries
            import re
            import json
            
            pattern = r'(\d+):\s*(\{.*?\})\s*(?=\n\d+:|$)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for match in matches:
                query_num = int(match[0])
                try:
                    # Clean and parse JSON
                    json_str = match[1].strip()
                    # Handle Python boolean/null values
                    json_str = json_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
                    expected_changes = eval(json_str)  # Using eval for Python dict format
                    self.ground_truth[query_num] = expected_changes
                except Exception as e:
                    print(f"Warning: Failed to parse ground truth for query {query_num}: {e}")
            
            print(f"✅ Loaded {len(lines)} queries and {len(self.ground_truth)} ground truth entries")
            
        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
            print("Please ensure queries.txt and groundtruth.txt exist in the current directory")
        except Exception as e:
            print(f"❌ Error loading files: {e}")
    
    def get_test_queries(self) -> Dict[str, List[Tuple[int, str, Dict[str, Any]]]]:
        """Get all test queries organized by type with ground truth."""
        test_queries = {}
        
        for query_type, queries in self.queries_by_type.items():
            test_queries[query_type] = []
            for query_num, query_text in queries:
                expected_changes = self.ground_truth.get(query_num, {})
                test_queries[query_type].append((query_num, query_text, expected_changes))
        
        return test_queries
    
    def get_expected_changes(self, query_num: int) -> Optional[Dict[str, Any]]:
        """Get expected changes for a specific query number."""
        return self.ground_truth.get(query_num)

class ResDexTesterV2:
    """Updated testing framework for ResDex Agent."""
    
    def __init__(self):
        self.agent = None
        self.ground_truth = GroundTruthManager()
        self.test_results = []
        self.summary_stats = {
            QueryType.SINGLE_TOOL_NO_MEMORY: {"passed": 0, "total": 0, "times": []},
            QueryType.SINGLE_TOOL_WITH_MEMORY: {"passed": 0, "total": 0, "times": []},
            QueryType.MULTI_TOOL_NO_MEMORY: {"passed": 0, "total": 0, "times": []},
            QueryType.MULTI_TOOL_WITH_MEMORY: {"passed": 0, "total": 0, "times": []}
        }
        self.session_id = "test_session_v2"
        self.persistent_state = self._get_initial_state()
    
    def _get_initial_state(self) -> Dict[str, Any]:
        """Get clean initial state."""
        return {
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
    
    async def process_query(self, query: str, query_type: str, reset_state: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any], float, bool]:
        """Process a query and return state changes."""
        try:
            print(f"\n📝 Processing query: {query}")
            print(f"🔖 Query type: {query_type}")
            
            # Reset state for no-memory tests, preserve for memory tests
            if reset_state or "no_memory" in query_type:
                initial_state = copy.deepcopy(self._get_initial_state())
                print("🔄 Using fresh state (no memory)")
            else:
                initial_state = copy.deepcopy(self.persistent_state)
                print("🧠 Using persistent state (with memory)")
            
            print(f"📊 Initial state: {json.dumps(initial_state, indent=2)}")
            
            # Start timing
            import time
            start_time = time.time()
            
            # Execute query
            content = Content(data={
                "user_input": query,
                "session_state": initial_state,
                "session_id": self.session_id,
                "user_id": "test_user"
            })
            
            response = await self.agent.execute(content)
            processing_time = round(time.time() - start_time, 3)
            
            if not response or not hasattr(response, 'data'):
                return initial_state, initial_state, processing_time, False
            
            # Get final state
            final_state = response.data.get("session_state", initial_state)
            success = response.data.get("success", False)
            
            # Update persistent state for memory tests
            if "with_memory" in query_type:
                self.persistent_state = copy.deepcopy(final_state)
            
            print(f"📊 Final state: {json.dumps(final_state, indent=2)}")
            print(f"✅ Success: {success}")
            print(f"⏱️ Processing time: {processing_time}s")
            
            return initial_state, final_state, processing_time, success
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            traceback.print_exc()
            return initial_state, initial_state, 0.0, False
    
    async def run_comprehensive_tests(self, output_csv: str, output_txt: str):
        """Run all tests organized by query types."""
        if not await self.initialize_agent():
            return False
        
        print(f"\n📖 Starting comprehensive ResDex testing...")
        
        # Initialize session
        step_logger.start_session(self.session_id)
        
        # Get all test queries
        test_queries = self.ground_truth.get_test_queries()
        
        total_tests = sum(len(queries) for queries in test_queries.values())
        print(f"📊 Total tests to run: {total_tests}")
        
        test_number = 0
        
        # Run tests for each query type
        for query_type, queries in test_queries.items():
            print(f"\n{'='*60}")
            print(f"🧪 Testing {query_type.upper()}")
            print(f"{'='*60}")
            
            # Reset state at the beginning of each category for clean slate
            self.persistent_state = copy.deepcopy(self._get_initial_state())
            
            for query_num, query_text, expected_changes in queries:
                test_number += 1
                print(f"\n🔍 Test {test_number}/{total_tests} - Query #{query_num}")
                
                # Determine if we should reset state
                reset_state = "no_memory" in query_type
                
                initial_state, final_state, processing_time, success = await self.process_query(
                    query_text, query_type, reset_state
                )
                
                # Calculate actual changes
                actual_changes = StateComparator.get_state_changes(initial_state, final_state)
                
                # Compare with expected changes
                is_match = StateComparator.states_match(expected_changes, actual_changes)
                
                # Store result
                result = {
                    'test_id': test_number,
                    'query_num': query_num,
                    'query_type': query_type,
                    'query': query_text,
                    'initial_state': initial_state,
                    'final_state': final_state,
                    'expected_changes': expected_changes,
                    'actual_changes': actual_changes,
                    'processing_time': processing_time,
                    'passed': is_match and success,
                    'agent_success': success
                }
                self.test_results.append(result)
                
                # Update summary stats
                self.summary_stats[query_type]["total"] += 1
                self.summary_stats[query_type]["times"].append(processing_time)
                if is_match and success:
                    self.summary_stats[query_type]["passed"] += 1
                
                # Print result
                status = "✅ PASSED" if (is_match and success) else "❌ FAILED"
                print(f"{status}: Query #{query_num} - {query_text} ({processing_time}s)")
                
                if not is_match or not success:
                    print(f"   Expected changes: {expected_changes}")
                    print(f"   Actual changes:   {actual_changes}")
                    print(f"   Agent success:    {success}")
                
                if not is_match or not success:
                    print(f"   Expected changes: {expected_changes}")
                    print(f"   Actual changes:   {actual_changes}")
                    print(f"   Agent success:    {success}")
        
        # Write results
        await self.write_results_to_csv(output_csv)
        await self.write_summary_to_txt(output_txt)
        self.print_summary()
        
        return True
    
    async def write_results_to_csv(self, output_file: str):
        """Write detailed test results to CSV."""
        try:
            print(f"\n📝 Writing detailed results to: {output_file}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Test ID', 'Query Number', 'Query Type', 'Query', 'Expected Changes JSON', 
                    'Actual Changes JSON', 'Processing Time (s)', 'Status', 'Agent Success'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow({
                        'Test ID': result['test_id'],
                        'Query Number': result['query_num'],
                        'Query Type': result['query_type'],
                        'Query': result['query'],
                        'Expected Changes JSON': json.dumps(result['expected_changes']),
                        'Actual Changes JSON': json.dumps(result['actual_changes']),
                        'Processing Time (s)': result['processing_time'],
                        'Status': 'PASSED' if result['passed'] else 'FAILED',
                        'Agent Success': 'YES' if result['agent_success'] else 'NO'
                    })
            
            print(f"✅ Detailed results written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing CSV results: {e}")
    
    async def write_summary_to_txt(self, output_file: str):
        """Write summary results to TXT file."""
        try:
            print(f"\n📝 Writing summary to: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("RESDEX AGENT TESTING SUMMARY\n")
                f.write("="*50 + "\n\n")
                
                f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session ID: {self.session_id}\n\n")
                
                total_passed = 0
                total_tests = 0
                all_times = []
                
                # Write results by query type
                for query_type, stats in self.summary_stats.items():
                    if stats["total"] > 0:
                        success_rate = (stats["passed"] / stats["total"]) * 100
                        avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
                        total_time = sum(stats["times"])
                        
                        f.write(f"{query_type.upper().replace('_', ' ')}\n")
                        f.write("-" * 40 + "\n")
                        f.write(f"Passed: {stats['passed']}/{stats['total']}\n")
                        f.write(f"Success Rate: {success_rate:.1f}%\n")
                        f.write(f"Average Time: {avg_time:.3f}s\n")
                        f.write(f"Total Time: {total_time:.3f}s\n\n")
                        
                        total_passed += stats["passed"]
                        total_tests += stats["total"]
                        all_times.extend(stats["times"])
                
                # Write overall summary
                overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
                overall_avg_time = sum(all_times) / len(all_times) if all_times else 0
                overall_total_time = sum(all_times)
                
                f.write("OVERALL SUMMARY\n")
                f.write("="*30 + "\n")
                f.write(f"Total Passed: {total_passed}/{total_tests}\n")
                f.write(f"Overall Success Rate: {overall_success:.1f}%\n")
                f.write(f"Overall Average Time: {overall_avg_time:.3f}s\n")
                f.write(f"Overall Total Time: {overall_total_time:.3f}s\n\n")
                
                # Write failed test details
                failed_tests = [r for r in self.test_results if not r['passed']]
                if failed_tests:
                    f.write("FAILED TESTS DETAILS\n")
                    f.write("="*30 + "\n")
                    for result in failed_tests:
                        f.write(f"\nTest {result['test_id']} - Query #{result['query_num']}: {result['query']}\n")
                        f.write(f"Type: {result['query_type']}\n")
                        f.write(f"Expected: {json.dumps(result['expected_changes'], indent=2)}\n")
                        f.write(f"Actual: {json.dumps(result['actual_changes'], indent=2)}\n")
                        f.write(f"Processing Time: {result['processing_time']}s\n")
                        f.write(f"Agent Success: {result['agent_success']}\n")
                        f.write("-" * 40 + "\n")
            
            print(f"✅ Summary written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing summary: {e}")
    
    def print_summary(self):
        """Print summary to console."""
        print(f"\n{'='*60}")
        print("📊 RESDEX TESTING SUMMARY")
        print(f"{'='*60}")
        
        total_passed = 0
        total_tests = 0
        all_times = []
        
        for query_type, stats in self.summary_stats.items():
            if stats["total"] > 0:
                success_rate = (stats["passed"] / stats["total"]) * 100
                avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
                
                print(f"\n{query_type.upper().replace('_', ' ')}:")
                print(f"  ✅ Passed: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
                print(f"  ⏱️ Avg Time: {avg_time:.3f}s")
                
                total_passed += stats["passed"]
                total_tests += stats["total"]
                all_times.extend(stats["times"])
        
        overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_avg_time = sum(all_times) / len(all_times) if all_times else 0
        
        print(f"\n{'='*40}")
        print(f"🎯 OVERALL: {total_passed}/{total_tests} ({overall_success:.1f}%)")
        print(f"⏱️ AVERAGE TIME: {overall_avg_time:.3f}s")
        print(f"🔄 SESSION: {self.session_id}")

async def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description='Test ResDex Agent with comprehensive JSON state testing')
    parser.add_argument('--output_csv', default='resdex_test_results.csv',
                       help='Path to output CSV file (default: resdex_test_results.csv)')
    parser.add_argument('--output_txt', default='resdex_test_summary.txt',
                       help='Path to output TXT summary file (default: resdx_test_summary.txt)')
    
    args = parser.parse_args()
    
    # Run comprehensive tests
    tester = ResDexTesterV2()
    success = await tester.run_comprehensive_tests(args.output_csv, args.output_txt)
    
    if success:
        print(f"\n🎉 Testing completed successfully!")
        print(f"📊 Detailed results: {args.output_csv}")
        print(f"📝 Summary: {args.output_txt}")
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