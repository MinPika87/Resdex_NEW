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
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resdex_agent.agent import ResDexRootAgent, Content
from resdex_agent.config import AgentConfig
from resdex_agent.utils.step_logger import step_logger

logging.basicConfig(
    level=logging.WARNING, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedActionCapture:
    """Enhanced action capture for new architecture with expansion support."""
    
    def __init__(self):
        self.actions = []
        self.session_state = {}
        self.query_start_time = None
        self.processing_time = 0.0
        self.agent_used = None
        self.memory_used = False
        self.expansion_used = False
        self.tools_used = []
        self.reset()
    
    def reset_for_new_query(self):
        self.actions = []
        self.query_start_time = None
        self.processing_time = 0.0
        self.agent_used = None
        self.memory_used = False
        self.expansion_used = False
        self.tools_used = []
    
    def start_timing(self):
        self.query_start_time = time.time()
    
    def end_timing(self):
        if self.query_start_time:
            self.processing_time = round(time.time() - self.query_start_time, 3)
        return self.processing_time
    
    def reset(self):
        self.actions = []
        self.query_start_time = None
        self.processing_time = 0.0
        self.agent_used = None
        self.memory_used = False
        self.expansion_used = False
        self.tools_used = []
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
    
    def capture_response_metadata(self, response_data: Dict[str, Any]):
        """Capture metadata about agent routing and tool usage."""
        # Detect which agent was used
        if "routed_to" in response_data:
            self.agent_used = response_data["routed_to"]
        elif "expansion_type" in response_data:
            self.agent_used = "expansion"
            self.expansion_used = True
        elif "search_results" in response_data:
            self.agent_used = "search_interaction"
        else:
            self.agent_used = "general_query"
        
        # Detect memory usage
        if "memory_context" in response_data or "memory_influenced" in response_data:
            self.memory_used = True
        
        # Detect expansion usage
        if response_data.get("expansion_type") or "matrix_stats" in response_data:
            self.expansion_used = True
        
        # Detect tool usage
        method = response_data.get("method", "")
        if "matrix" in method:
            self.tools_used.append("matrix_expansion")
        if "llm" in method:
            self.tools_used.append("llm_tool")
        if "search" in response_data:
            self.tools_used.append("search_tool")
        if "location_analysis" in response_data:
            self.tools_used.append("location_expansion_tool")
    
    def capture_modifications(self, modifications: List[Dict[str, Any]]):
        """Enhanced modification capture for new architecture."""
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
    
    def capture_expansion_actions(self, response_data: Dict[str, Any]):
        """Capture expansion-specific actions."""
        expansion_type = response_data.get("expansion_type")
        if expansion_type == "skill_expansion":
            expanded_skills = response_data.get("expanded_skills", [])
            if expanded_skills:
                self.actions.append(f"Skills expanded: {', '.join(expanded_skills[:3])}")
        
        elif expansion_type == "title_expansion":
            expanded_titles = response_data.get("expanded_titles", [])
            suggested_skills = response_data.get("suggested_skills", [])
            if expanded_titles:
                self.actions.append(f"Titles expanded: {', '.join(expanded_titles[:2])}")
            if suggested_skills:
                self.actions.append(f"Skills suggested: {', '.join(suggested_skills[:2])}")
        
        elif expansion_type == "location_expansion":
            expanded_locations = response_data.get("expanded_locations", [])
            if expanded_locations:
                self.actions.append(f"Locations expanded: {', '.join(expanded_locations[:3])}")
    
    def capture_search_trigger(self, triggered: bool):
        if triggered:
            self.actions.append("Search executed")
            self.session_state['search_applied'] = True
    
    def get_formatted_output(self) -> str:
        if not self.actions:
            return "No actions taken"
        
        unique_actions = []
        seen = set()
        for action in self.actions:
            if action not in seen:
                unique_actions.append(action)
                seen.add(action)
        
        return "; ".join(unique_actions)
    
    def get_analysis_info(self) -> Dict[str, Any]:
        """Get analysis information about the query processing."""
        return {
            "agent_used": self.agent_used,
            "memory_used": self.memory_used,
            "expansion_used": self.expansion_used,
            "tools_used": self.tools_used,
            "processing_time": self.processing_time
        }

class EnhancedGroundTruthManager:
    """Enhanced ground truth manager for new architecture with 4 query types."""
    
    def __init__(self):
        # Updated ground truth dictionary for the new queries

        self.ground_truth = {
            # TYPE 1: Single Tool, No Memory (10 queries)
            "add python and java": "Skill added: Python; Skill added: Java",
            "increase experience by 5 years": "Experience set: 0-15 years",  # Assuming current max is 10, adding 5
            "add bangalore location": "Location added: Bangalore",
            "set salary range 10-20 lpa": "Salary range set: 10-20 LPA",
            "add similar skills to java": "Skills expanded: Spring, Hibernate, Maven",
            "similar titles to software engineer": "Titles expanded: Developer, Programmer",
            "nearby locations to mumbai": "Locations expanded: Thane, Pune, Nashik",
            "similar skills": "No actions taken",  # Too vague, no specific skill mentioned
            "similar designations for my query": "No actions taken",  # Too vague, no specific designation mentioned
            "expand my query": "No actions taken",  # Too vague, no specific target for expansion
            
            # TYPE 2: Single Tool, With Memory (10 queries) - Keep existing
            "add the same skills we discussed": "No actions taken",  # Memory reference
            "use previous salary range": "No actions taken",  # Memory reference
            "add skills similar to what we used before": "No actions taken",  # Memory + expansion
            "include the cities from our last search": "No actions taken",  # Memory reference
            "make those skills mandatory like before": "No actions taken",  # Memory reference
            "repeat the same filter setup": "No actions taken",  # Memory reference
            "add experience range we had earlier": "No actions taken",  # Memory reference
            "use the locations from previous query": "No actions taken",  # Memory reference
            "apply filters like last time": "No actions taken",  # Memory reference
            "search with our usual criteria": "Search executed",  # Memory + search
            
            # TYPE 3: Multi Tool, No Memory (10 queries) - Updated
            "find similar skills to python and set experience 5+ years": "Skills expanded: Django, Flask, Pandas; Experience set: 5-10 years",
            "similar titles to data scientist from nearby to bangalore": "Titles expanded: ML Engineer, Data Analyst; Locations expanded: Mysore, Hubli, Coimbatore",
            "expand java skills and add nearby cities to mumbai": "Skills expanded: Spring, Hibernate, Maven; Locations expanded: Thane, Pune, Nashik",
            "find titles similar to software engineer and add relevant skills, from nearby noida": "Titles expanded: Developer, Programmer; Skills suggested: Java, Python; Locations expanded: Delhi, Gurgaon, Faridabad",
            "get skills for frontend developer and set salary 8-15 lpa": "Skills suggested: React, JavaScript; Salary range set: 8-15 LPA",
            "find similar titles to software engineer from nearby chennai and increase experience by 5 years": "Titles expanded: Developer, Programmer; Locations expanded: Coimbatore, Madurai, Trichy; Experience set: 0-15 years",
            "expand python skills and add 3+ years experience": "Skills expanded: Django, Flask, Pandas; Experience set: 3-10 years",
            "find nearby locations to goa and add devops skills": "Locations expanded: Mumbai, Pune, Bangalore; Skill added: DevOps",
            "get related skills to machine learning from nearby locations to bangalore": "Skills expanded: Python, TensorFlow, PyTorch; Locations expanded: Mysore, Hubli, Coimbatore",
            "find similar roles to product manager and set experience": "Titles expanded: Product Owner, Business Analyst; Experience set: 0-10 years",
            
            # TYPE 4: Multi Tool, With Memory (10 queries) - Keep existing
            "expand the skills we discussed and add similar cities": "Skills expanded: Django, Flask, Pandas; Locations expanded: Thane, Pune, Nashik",
            "find titles similar to our previous role and search": "Titles expanded: ML Engineer, Data Analyst; Search executed",
            "get related skills like before and add nearby locations": "Skills expanded: JavaScript, TypeScript, Redux; Locations expanded: Gurgaon, Noida, Faridabad",
            "expand our usual skills and increase experience range": "Skills expanded: Spring, Hibernate, Maven; Experience set: 5-10 years",
            "find similar titles to what we used and add skills": "Titles expanded: Developer, Programmer; Skills suggested: Java, Python",
            "get nearby cities like last time and search candidates": "Locations expanded: Thane, Pune, Nashik; Search executed",
            "expand skills from previous query and set salary": "Skills expanded: React, Vue.js, Angular; Salary range set: 10-20 LPA",
            "find related roles and add the locations we mentioned": "Titles expanded: Product Owner, Business Analyst; Location added: Mumbai",
            "get similar skills and search with our filters": "Skills expanded: Python, TensorFlow, PyTorch; Search executed",
            "expand previous titles and add experience like before": "Titles expanded: DevOps Engineer, Site Reliability Engineer; Experience set: 3-8 years"
        }
    
    def get_expected_output(self, query: str) -> str:
        query_clean = query.lower().strip()
        return self.ground_truth.get(query_clean, "No expected output defined")
    
    def get_query_type(self, query: str) -> str:
        """Determine query type based on content."""
        query_lower = query.lower()
        
        # Check for memory indicators
        memory_indicators = ["we discussed", "previous", "before", "last time", "our usual", "like before", "from previous"]
        has_memory = any(indicator in query_lower for indicator in memory_indicators)
        
        # Check for multi-tool indicators
        multi_tool_indicators = ["and", "expand", "similar", "find", "get"]
        tool_count = sum(1 for indicator in multi_tool_indicators if indicator in query_lower)
        has_multi_tool = tool_count >= 2 or "expand" in query_lower or "similar" in query_lower
        
        if has_memory and has_multi_tool:
            return "Type 4: Multi Tool + Memory"
        elif has_memory:
            return "Type 2: Single Tool + Memory"
        elif has_multi_tool:
            return "Type 3: Multi Tool + No Memory"
        else:
            return "Type 1: Single Tool + No Memory"

class EnhancedResDexTester:
    """Enhanced testing class for new ResDex Agent architecture."""
    
    def __init__(self):
        self.agent = None
        self.action_capture = EnhancedActionCapture()
        self.ground_truth = EnhancedGroundTruthManager()
        self.test_results = []
        self.type_results = {
            "Type 1: Single Tool + No Memory": [],
            "Type 2: Single Tool + Memory": [],
            "Type 3: Multi Tool + No Memory": [],
            "Type 4: Multi Tool + Memory": []
        }
        self.session_id = "enhanced_test_session"
    
    async def initialize_agent(self):
        try:
            print("🚀 Initializing Enhanced ResDex Agent...")
            config = AgentConfig.from_env()
            self.agent = ResDexRootAgent(config)
            print("✅ Enhanced ResDex Agent initialized successfully")
            print(f"📊 Available agents: {list(self.agent.sub_agents.keys())}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Enhanced ResDex Agent: {e}")
            traceback.print_exc()
            return False
    
    async def process_query(self, query: str) -> Tuple[str, Dict[str, Any], float, Dict[str, Any]]:
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
                return "No response received", {}, processing_time, {}
            
            response_data = response.data
            
            # Capture metadata
            self.action_capture.capture_response_metadata(response_data)
            
            # Capture modifications
            modifications = response_data.get("modifications", [])
            if modifications:
                self.action_capture.capture_modifications(modifications)
            
            # Capture expansion actions
            self.action_capture.capture_expansion_actions(response_data)
            
            # Capture search trigger
            trigger_search = response_data.get("trigger_search", False)
            if trigger_search:
                self.action_capture.capture_search_trigger(True)
            
            # Update session state
            if "session_state" in response_data:
                self.action_capture.session_state.update(response_data["session_state"])
            
            model_output = self.action_capture.get_formatted_output()
            analysis_info = self.action_capture.get_analysis_info()
            
            print(f"✅ Model output: {model_output}")
            print(f"🤖 Agent used: {analysis_info['agent_used']}")
            print(f"🧠 Memory used: {analysis_info['memory_used']}")
            print(f"🔧 Tools used: {analysis_info['tools_used']}")
            print(f"⏱️ Processing time: {processing_time}s")
            
            return model_output, response_data, processing_time, analysis_info
            
        except Exception as e:
            processing_time = self.action_capture.end_timing()
            error_msg = f"Error processing query: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return error_msg, {}, processing_time, {}
    
    def compare_outputs(self, expected: str, actual: str) -> Tuple[bool, List[str]]:
        expected_clean = expected.strip().lower()
        actual_clean = actual.strip().lower()
        
        if expected_clean == actual_clean:
            return True, []
        
        # Check if actual contains key components of expected
        expected_parts = [part.strip() for part in expected.split(';')]
        actual_parts = [part.strip() for part in actual.split(';')]
        
        matches = 0
        for exp_part in expected_parts:
            for act_part in actual_parts:
                if exp_part.lower() in act_part.lower() or act_part.lower() in exp_part.lower():
                    matches += 1
                    break
        
        match_ratio = matches / len(expected_parts) if expected_parts else 0
        is_match = match_ratio >= 0.7
        
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
    
    async def run_tests(self, query_file: str, output_file: str):
        if not await self.initialize_agent():
            return False
        
        print(f"\n📖 Reading queries from: {query_file}")
        
        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # FIXED: Filter out comment lines and empty lines
            queries = []
            for line in lines:
                cleaned_line = line.strip()
                # Skip comment lines (starting with #) and empty lines
                if cleaned_line and not cleaned_line.startswith('#'):
                    queries.append(cleaned_line)
                    
        except FileNotFoundError:
            print(f"❌ Query file not found: {query_file}")
            return False
        
        print(f"📊 Found {len(queries)} valid queries to test (skipped comment lines)")
        
        # Initialize session
        step_logger.start_session(self.session_id)
        print(f"🔄 Using enhanced session: {self.session_id}")
        
        # Process each query
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"🔍 Test {i}/{len(queries)}")
            
            query_type = self.ground_truth.get_query_type(query)
            expected_output = self.ground_truth.get_expected_output(query)
            model_output, response_data, processing_time, analysis_info = await self.process_query(query)
            
            is_match, diff = self.compare_outputs(expected_output, model_output)
            
            result = {
                'test_id': i,
                'query_type': query_type,
                'input_query': query,
                'expected_output': expected_output,
                'model_output': model_output,
                'processing_time': processing_time,
                'passed': is_match,
                'diff': diff,
                'agent_used': analysis_info.get('agent_used', 'unknown'),
                'memory_used': analysis_info.get('memory_used', False),
                'expansion_used': analysis_info.get('expansion_used', False),
                'tools_used': ', '.join(analysis_info.get('tools_used', []))
            }
            
            self.test_results.append(result)
            self.type_results[query_type].append(result)
            
            status = "✅ PASSED" if is_match else "❌ FAILED"
            print(f"{status}: {query} ({processing_time}s) [{query_type}]")
            if not is_match:
                print(f"   Expected: {expected_output}")
                print(f"   Actual:   {model_output}")
        
        await self.write_results_to_csv(output_file)
        await self.write_detailed_results()
        self.print_enhanced_summary()
        
        return True
    
    async def write_results_to_csv(self, output_file: str):
        try:
            print(f"\n📝 Writing results to: {output_file}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Query Type', 'Input Query', 'Expected Output', 'Model Output', 
                    'Processing Time (s)', 'Agent Used', 'Memory Used', 'Expansion Used', 
                    'Tools Used', 'Status'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow({
                        'Query Type': result['query_type'],
                        'Input Query': result['input_query'],
                        'Expected Output': result['expected_output'],
                        'Model Output': result['model_output'],
                        'Processing Time (s)': result['processing_time'],
                        'Agent Used': result['agent_used'],
                        'Memory Used': result['memory_used'],
                        'Expansion Used': result['expansion_used'],
                        'Tools Used': result['tools_used'],
                        'Status': 'PASSED' if result['passed'] else 'FAILED'
                    })
            
            print(f"✅ Results written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing results to CSV: {e}")
    
    async def write_detailed_results(self):
        """Write detailed results.txt file."""
        try:
            with open('results.txt', 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ENHANCED RESDEX AGENT TEST RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                # Overall summary
                total_tests = len(self.test_results)
                passed_tests = sum(1 for r in self.test_results if r['passed'])
                total_time = sum(r['processing_time'] for r in self.test_results)
                avg_time = total_time / total_tests if total_tests > 0 else 0
                
                f.write(f"OVERALL SUMMARY:\n")
                f.write(f"Total Queries: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {total_tests - passed_tests}\n")
                f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
                f.write(f"Total Time: {total_time:.3f}s\n")
                f.write(f"Average Time: {avg_time:.3f}s\n\n")
                
                # Results by type
                for query_type, results in self.type_results.items():
                    if not results:
                        continue
                        
                    type_passed = sum(1 for r in results if r['passed'])
                    type_total = len(results)
                    type_time = sum(r['processing_time'] for r in results)
                    type_avg_time = type_time / type_total if type_total > 0 else 0
                    
                    f.write(f"{query_type.upper()}:\n")
                    f.write(f"  Queries: {type_total}\n")
                    f.write(f"  Passed: {type_passed}\n")
                    f.write(f"  Success Rate: {(type_passed/type_total)*100:.1f}%\n")
                    f.write(f"  Total Time: {type_time:.3f}s\n")
                    f.write(f"  Average Time: {type_avg_time:.3f}s\n\n")
                
                # Agent usage statistics
                f.write("AGENT USAGE STATISTICS:\n")
                agent_counts = {}
                for result in self.test_results:
                    agent = result.get('agent_used', 'unknown')
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
                for agent, count in agent_counts.items():
                    f.write(f"  {agent}: {count} queries\n")
                f.write("\n")
                
                # Tool usage statistics
                f.write("TOOL USAGE STATISTICS:\n")
                memory_count = sum(1 for r in self.test_results if r.get('memory_used', False))
                expansion_count = sum(1 for r in self.test_results if r.get('expansion_used', False))
                
                f.write(f"  Memory Usage: {memory_count} queries\n")
                f.write(f"  Expansion Usage: {expansion_count} queries\n\n")
                
                # Failed test details
                failed_tests = [r for r in self.test_results if not r['passed']]
                if failed_tests:
                    f.write("FAILED TEST DETAILS:\n")
                    f.write("=" * 40 + "\n")
                    for result in failed_tests:
                        f.write(f"\nTest {result['test_id']}: {result['query_type']}\n")
                        f.write(f"Query: {result['input_query']}\n")
                        f.write(f"Expected: {result['expected_output']}\n")
                        f.write(f"Actual: {result['model_output']}\n")
                        f.write(f"Agent: {result['agent_used']}\n")
                        f.write(f"Time: {result['processing_time']}s\n")
                        f.write("-" * 40 + "\n")
            
            print("✅ Detailed results written to results.txt")
            
        except Exception as e:
            print(f"❌ Error writing detailed results: {e}")
    
    def print_enhanced_summary(self):
        """Print enhanced summary with type breakdown."""
        print(f"\n{'='*80}")
        print("📊 ENHANCED TEST SUMMARY")
        print(f"{'='*80}")
        
        # Overall stats
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        total_time = sum(r['processing_time'] for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Queries: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {total_tests - passed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   ⏱️ Total Time: {total_time:.3f}s")
        print(f"   ⏱️ Average Time: {avg_time:.3f}s")
        print()
        
        # Type breakdown
        print(f"📋 RESULTS BY TYPE:")
        for query_type, results in self.type_results.items():
            if not results:
                continue
                
            type_passed = sum(1 for r in results if r['passed'])
            type_total = len(results)
            type_time = sum(r['processing_time'] for r in results)
            type_avg_time = type_time / type_total if type_total > 0 else 0
            
            print(f"   {query_type}:")
            print(f"     Queries: {type_total}, Passed: {type_passed}, Rate: {(type_passed/type_total)*100:.1f}%")
            print(f"     Time: {type_time:.3f}s (avg: {type_avg_time:.3f}s)")
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
        
        # Tool usage stats
        print(f"🔧 TOOL USAGE:")
        memory_count = sum(1 for r in self.test_results if r.get('memory_used', False))
        expansion_count = sum(1 for r in self.test_results if r.get('expansion_used', False))
        
        print(f"   Memory: {memory_count}/{total_tests} queries")
        print(f"   Expansion: {expansion_count}/{total_tests} queries")
        print()

def create_enhanced_queries_file(filename: str = 'queries.txt'):
    """Create comprehensive queries file with 4 types of queries."""
    
    queries_by_type = {
        "# TYPE 1: Single Tool, No Memory (10 queries)": [
            "add python and java",
            "increase experience by 5 years", 
            "add bangalore location",
            "set salary range 10-20 lpa",
            "add similar skills to java",
            "similar titles to software engineer",
            "nearby locations to mumbai",
            "similar skills",
            "similar designations for my query",
            "expand my query"
        ],
        
        "# TYPE 3: Multi Tool, No Memory (10 queries)": [
            "find similar skills to python and set experience 5+ years",
            "similar titles to data scientist from nearby to bangalore",
            "expand java skills and add nearby cities to mumbai",
            "find titles similar to software engineer and add relevant skills, from nearby noida",
            "get skills for frontend developer and set salary 8-15 lpa",
            "find similar titles to software engineer from nearby Chennai and increase experience by 5 years",
            "expand python skills and add 3+ years experience",
            "find nearby locations to goa and add devops skills",
            "get related skills to machine learning from nearby locations to bangalore",
            "find similar roles to product manager and set experience"
        ]
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Enhanced ResDex Agent Test Queries\n")
            f.write("# Total: 40 queries across 4 types\n")
            f.write("# Each type tests different aspects of the agent architecture\n\n")
            
            for section_header, queries in queries_by_type.items():
                f.write(f"{section_header}\n")
                for query in queries:
                    f.write(f"{query}\n")
                f.write("\n")
        
        print(f"✅ Enhanced queries file created: {filename}")
        print(f"📊 Total queries: {sum(len(queries) for queries in queries_by_type.values())}")
        print(f"📋 Query types: {len(queries_by_type)}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating enhanced queries file: {e}")
        return False

async def main():
    """Enhanced main function with comprehensive testing options."""
    parser = argparse.ArgumentParser(
        description='Enhanced Test Suite for ResDex Agent Architecture',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py --create_sample              # Create sample queries.txt
  python test.py                              # Run all tests
  python test.py --query_file custom.txt      # Use custom query file
  python test.py --output_file results.csv    # Custom output file
        """
    )
    
    parser.add_argument('--query_file', default='queries.txt',
                       help='Path to file containing queries (default: queries.txt)')
    parser.add_argument('--output_file', default='output.csv',
                       help='Path to output CSV file (default: output.csv)')
    parser.add_argument('--create_sample', action='store_true',
                       help='Create enhanced sample queries.txt file with 4 query types')
    parser.add_argument('--clean_queries', action='store_true',
                       help='Clean invisible Unicode characters from queries file')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced ResDex Agent Test Suite")
    print("=" * 50)
    
    if args.create_sample:
        success = create_enhanced_queries_file(args.query_file)
        if success:
            print(f"\n🎯 Sample queries created successfully!")
            print(f"📝 File: {args.query_file}")
            print(f"🔍 You can now run: python test.py --query_file {args.query_file}")
            print(f"\n📋 Query Types Created:")
            print(f"   • Type 1: Single Tool + No Memory (10 queries)")
            print(f"   • Type 2: Single Tool + Memory (10 queries)")
            print(f"   • Type 3: Multi Tool + No Memory (10 queries)")
            print(f"   • Type 4: Multi Tool + Memory (10 queries)")
        return
    
    if not os.path.exists(args.query_file):
        print(f"❌ Query file not found: {args.query_file}")
        print(f"💡 Tip: Use --create_sample to create an enhanced queries.txt file")
        return
    
    if args.clean_queries:
        clean_queries_file(args.query_file)
        print("✅ Queries cleaned. Run again without --clean_queries flag.")
        return
    
    # Run enhanced tests
    print(f"🔍 Running enhanced tests...")
    print(f"📖 Query file: {args.query_file}")
    print(f"📊 Output file: {args.output_file}")
    print(f"📋 Detailed results: results.txt")
    
    tester = EnhancedResDexTester()
    success = await tester.run_tests(args.query_file, args.output_file)
    
    if success:
        print(f"\n🎉 Enhanced testing completed successfully!")
        print(f"📊 Summary results: {args.output_file}")
        print(f"📋 Detailed results: results.txt")
        print(f"🔍 Session: {tester.session_id}")
    else:
        print(f"\n💥 Enhanced testing failed!")
        sys.exit(1)

def clean_queries_file(input_file: str, output_file: str = None):
    """Clean queries.txt with UNICODE characters while preserving structure."""
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
        
        # Preserve comments and section headers
        if clean_line.startswith('#'):
            cleaned_lines.append(clean_line)
            print(f"  Line {i+1}: Comment preserved: '{clean_line}'")
        elif clean_line:  # Non-empty, non-comment lines
            cleaned_lines.append(clean_line)
            print(f"  Line {i+1}: '{line.strip()}' -> '{clean_line}'")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in cleaned_lines:
            f.write(f"{line}\n")
    
    print(f"✅ Cleaned file saved to: {output_file}")
    
    # Count actual queries (non-comment lines)
    query_count = sum(1 for line in cleaned_lines if line and not line.startswith('#'))
    print(f"📊 Total queries (excluding comments): {query_count}")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Enhanced testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error in enhanced testing: {e}")
        traceback.print_exc()
        sys.exit(1)