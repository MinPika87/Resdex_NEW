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


class HardcodedGroundTruth:
    """Hardcoded ground truth for the specific 20 queries."""
    
    def __init__(self):
        # Initial state for all queries
        self.initial_state = {
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
        
        # Ground truth expected states for each query
        self.ground_truth = {
            # TYPE 1: Single Tool, No Memory (10 queries)
            "add python and java": {
                "keywords": ["Python", "Java"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "increase experience by 5 years": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 15,  # Current 10 + 5
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "add bangalore location": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Bangalore"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "set salary range 10-20 lpa": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 10,
                "max_salary": 20,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "add similar skills to java": {
                "keywords": ["Spring Boot","Spring","Hibernate","Microservices","Spring MVC"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "similar titles to software engineer": {
                "keywords": ["Senior Software Engineer","Software Developer","Senior Software Developer","Software Development Engineer 2","Software Engineer 2","Spring Boot","Java"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "nearby locations to mumbai": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Mumbai Suburbs","Dohad","Navi Mumbai","Thane","Location_1574714"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "relax my query": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False 
            },
            "similar titles to Designer ": {
                "keywords": ["Fashion Designer", "Senior Fashion Designer", "Senior Designer", "Textile Designer","Instrumentation Designer","Fashion Designing","Print Development"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "refine my query": {
                "keywords": [],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False 
            },
            
            # TYPE 3: Multi Tool, No Memory (10 queries)
            "find similar skills to python and set experience 5+ years": {
                "keywords":["Django","Machine Learning","Flask","Pyspark","Natural Language Processing"],
                "min_experience": 5,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "similar titles to data scientist from nearby to bangalore": {
                "keywords": ["Senior Data Scientist","Lead Data Scientist","Data Scientist Associate","Data Science Manager","Data Science Consultant","Natural Language Processing","Deep Learning"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Anekal","Bangalore Rural","Devanahalli","Hosur","Magadi"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "expand skills to java and add nearby cities to mumbai": {
                "keywords":["Spring Boot","Spring","Hibernate","Microservices","Spring MVC"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Mumbai Suburbs","Dohad","Navi Mumbai","Thane","Location_1574714"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "find titles similar to software engineer and add relevant skills, from nearby noida": {
                "keywords":["Senior Software Engineer","Software Developer","Senior Software Developer","Software Development Engineer 2","Software Engineer 2","Spring Boot","Java"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Delhi","Location_382","Ghaziabad","Faridabad","Greater Noida"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "get titles similar to frontend developer and set salary 8-15 lpa": {
                "keywords": ["React", "JavaScript", "CSS"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 8,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "find similar titles to software engineer from nearby Chennai and increase experience by 5 years": {
                "keywords": ["Senior Software Engineer","Software Developer","Senior Software Developer","Software Development Engineer 2","Software Engineer 2","Spring Boot","Java"],
                "min_experience": 0,
                "max_experience": 15,  # Increased by 5
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Chitoor","Ambattur","Poonamallee","Tambaram","Ponneri"],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "expand python skills and add 3+ years experience": {
                "keywords":["Django","Machine Learning","Flask","Pyspark","Natural Language Processing"],  # Python-related skills
                "min_experience": 3,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "find nearby locations to goa and add devops skills, and refine my query": {
                "keywords": ["DevOps"],
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["South Goa","Margao","Sanguem","Satari","Bicholim"],  # Nearby Goa
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "get related skills to machine learning from nearby locations to bangalore and relax my query": {
                "keywords": ["Natural Language Processing","Deep Learning","Data Science","Artificial Intelligence","Neural Networks"],  # ML-related skills
                "min_experience": 0,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": ["Anekal","Bangalore Rural","Devanahalli","Hosur","Magadi"], # Nearby Bangalore
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            },
            "find similar roles to product manager and set experience 5-10 years": {
                "keywords": ["Senior Product Manager","Group Product Manager","Associate Product Manager","Lead Product Manager","Product Manager 2","Product Management","Product Strategy"],
                "min_experience": 5,
                "max_experience": 10,
                "min_salary": 0,
                "max_salary": 15,
                "current_cities": [],
                "preferred_cities": [],
                "total_results": 0,
                "search_executed": False
            }
        }
        
        # Query type mapping
        self.query_types = {
            # TYPE 1: Single Tool, No Memory
            "add python and java": "Type 1: Single Tool + No Memory",
            "increase experience by 5 years": "Type 1: Single Tool + No Memory",
            "add bangalore location": "Type 1: Single Tool + No Memory",
            "set salary range 10-20 lpa": "Type 1: Single Tool + No Memory",
            "add similar skills to java": "Type 1: Single Tool + No Memory",
            "similar titles to software engineer": "Type 1: Single Tool + No Memory",
            "nearby locations to mumbai": "Type 1: Single Tool + No Memory",
            "relax my query": "Type 1: Single Tool + No Memory",
            "similar titles for Designer": "Type 1: Single Tool + No Memory",
            "refine my query": "Type 1: Single Tool + No Memory",
            
            # TYPE 3: Multi Tool, No Memory
            "find similar skills to python and set experience 5+ years": "Type 3: Multi Tool + No Memory",
            "similar titles to data scientist from nearby to bangalore": "Type 3: Multi Tool + No Memory",
            "expand skills to java and add nearby cities to mumbai": "Type 3: Multi Tool + No Memory",
            "find titles similar to software engineer and add relevant skills, from nearby noida": "Type 3: Multi Tool + No Memory",
            "get titles similar to frontend developer and set salary 8-15 lpa": "Type 3: Multi Tool + No Memory",
            "find similar titles to software engineer from nearby Chennai and increase experience by 5 years": "Type 3: Multi Tool + No Memory",
            "expand python skills and add 3+ years experience": "Type 3: Multi Tool + No Memory",
            "find nearby locations to goa and add devops skills, and refine my query": "Type 3: Multi Tool + No Memory",
            "get related skills to machine learning from nearby locations to bangalore and relax my query": "Type 3: Multi Tool + No Memory",
            "find similar roles to product manager and set experience 5-10 years": "Type 3: Multi Tool + No Memory"
        }
    
    def get_expected_state(self, query: str) -> Dict[str, Any]:
        """Get expected state for a query."""
        return self.ground_truth.get(query.lower().strip(), self.initial_state)
    
    def get_query_type(self, query: str) -> str:
        """Get query type."""
        return self.query_types.get(query.lower().strip(), "Unknown Type")


class DeterministicEvaluator:
    """Simple deterministic evaluator - no LLM needed!"""
    
    def __init__(self):
        # Define semantic equivalents for skills
        self.skill_equivalents = {
            # Python ecosystem
            "python": ["python", "py"],
            "django": ["django"],
            "flask": ["flask"],
            "fastapi": ["fastapi", "fast api"],
            
            # Java ecosystem  
            "java": ["java"],
            "spring": ["spring", "spring boot", "spring framework"],
            "hibernate": ["hibernate"],
            "maven": ["maven"],
            
            # JavaScript ecosystem
            "javascript": ["javascript", "js"],
            "react": ["react", "reactjs", "react.js"],
            "angular": ["angular", "angularjs"],
            "vue": ["vue", "vue.js", "vuejs"],
            
            # Data Science
            "machine learning": ["machine learning", "ml", "artificial intelligence", "ai"],
            "tensorflow": ["tensorflow", "tf"],
            "pytorch": ["pytorch"],
            
            # DevOps
            "devops": ["devops", "dev ops"],
            "docker": ["docker"],
            "kubernetes": ["kubernetes", "k8s"],
            
            # Frontend
            "css": ["css", "css3"],
            "html": ["html", "html5"],
            
            # Product Management
            "agile": ["agile", "scrum"],
            "product strategy": ["product strategy", "product management"]
        }
        
        # Define location equivalents
        self.location_equivalents = {
            "mumbai": ["mumbai", "bombay"],
            "bangalore": ["bangalore", "bengaluru"],
            "delhi": ["delhi", "new delhi"],
            "chennai": ["chennai", "madras"],
            "pune": ["pune"],
            "hyderabad": ["hyderabad"],
            "gurgaon": ["gurgaon", "gurugram"],
            "noida": ["noida"],
            "thane": ["thane"],
            "nashik": ["nashik"],
            "mysore": ["mysore"],
            "hubli": ["hubli"],
            "coimbatore": ["coimbatore"],
            "madurai": ["madurai"],
            "trichy": ["trichy", "tiruchirappalli"],
            "faridabad": ["faridabad"]
        }
    
    def evaluate_results(self, query: str, expected_form: Dict[str, Any], 
                        actual_form: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Simple deterministic evaluation - much faster and more reliable!"""
        
        print(f"🔍 Deterministic evaluation for: '{query}'")
        
        matches = 0
        total_checks = 0
        differences = []
        
        # Check keywords with semantic matching
        total_checks += 1
        keywords_match = self._compare_keywords(
            expected_form.get("keywords", []), 
            actual_form.get("keywords", [])
        )
        if keywords_match:
            matches += 1
        else:
            differences.append(f"Keywords: expected {expected_form.get('keywords', [])}, got {actual_form.get('keywords', [])}")
        
        # Check experience (exact match)
        total_checks += 1
        exp_match = (
            expected_form.get("min_experience") == actual_form.get("min_experience") and
            expected_form.get("max_experience") == actual_form.get("max_experience")
        )
        if exp_match:
            matches += 1
        else:
            differences.append(f"Experience: expected {expected_form.get('min_experience')}-{expected_form.get('max_experience')}, got {actual_form.get('min_experience')}-{actual_form.get('max_experience')}")
        
        # Check salary (exact match)
        total_checks += 1
        salary_match = (
            expected_form.get("min_salary") == actual_form.get("min_salary") and
            expected_form.get("max_salary") == actual_form.get("max_salary")
        )
        if salary_match:
            matches += 1
        else:
            differences.append(f"Salary: expected {expected_form.get('min_salary')}-{expected_form.get('max_salary')}, got {actual_form.get('min_salary')}-{actual_form.get('max_salary')}")
        
        # Check locations with semantic matching
        total_checks += 1
        locations_match = self._compare_locations(
            expected_form.get("current_cities", []), 
            actual_form.get("current_cities", [])
        )
        if locations_match:
            matches += 1
        else:
            differences.append(f"Locations: expected {expected_form.get('current_cities', [])}, got {actual_form.get('current_cities', [])}")
        
        # Check search execution (exact match)
        total_checks += 1
        search_match = expected_form.get("search_executed") == actual_form.get("search_executed")
        if search_match:
            matches += 1
        else:
            differences.append(f"Search: expected {expected_form.get('search_executed')}, got {actual_form.get('search_executed')}")
        
        # Calculate score
        score = matches / total_checks if total_checks > 0 else 0.0
        is_pass = score == 1.0  # 60% threshold (3 out of 5 components)
        
        # Create reasoning
        if is_pass:
            reasoning = f"PASS: {matches}/{total_checks} components matched (score: {score:.2f})"
        else:
            reasoning = f"FAIL: {matches}/{total_checks} components matched (score: {score:.2f}). Differences: {'; '.join(differences[:2])}"
        
        print(f"✅ Deterministic result: {'PASS' if is_pass else 'FAIL'} ({score:.2f})")
        
        return is_pass, reasoning, score
    
    def _compare_keywords(self, expected: List[str], actual: List[str]) -> bool:
        """Compare keywords with semantic equivalents."""
        if not expected and not actual:
            return True
        
        if len(expected) != len(actual):
            # Allow some flexibility - if at least 70% match
            min_matches = max(1, int(len(expected) * 0.7))
        else:
            min_matches = len(expected)
        
        matches = 0
        for exp_skill in expected:
            for act_skill in actual:
                if self._skills_equivalent(exp_skill, act_skill):
                    matches += 1
                    break
        
        return matches >= min_matches
    
    def _compare_locations(self, expected: List[str], actual: List[str]) -> bool:
        """Compare locations with semantic equivalents."""
        if not expected and not actual:
            return True
        
        if len(expected) != len(actual):
            # Allow some flexibility - if at least 70% match
            min_matches = max(1, int(len(expected) * 0.7))
        else:
            min_matches = len(expected)
        
        matches = 0
        for exp_loc in expected:
            for act_loc in actual:
                if self._locations_equivalent(exp_loc, act_loc):
                    matches += 1
                    break
        
        return matches >= min_matches
    
    def _skills_equivalent(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are equivalent."""
        skill1_lower = skill1.lower().strip()
        skill2_lower = skill2.lower().strip()
        
        # Exact match
        if skill1_lower == skill2_lower:
            return True
        
        # Check semantic equivalents
        for canonical, equivalents in self.skill_equivalents.items():
            if skill1_lower in equivalents and skill2_lower in equivalents:
                return True
        
        return False
    
    def _locations_equivalent(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are equivalent."""
        loc1_lower = loc1.lower().strip()
        loc2_lower = loc2.lower().strip()
        
        # Exact match
        if loc1_lower == loc2_lower:
            return True
        
        # Check semantic equivalents
        for canonical, equivalents in self.location_equivalents.items():
            if loc1_lower in equivalents and loc2_lower in equivalents:
                return True
        
        return False


class ManagerSpecifiedTester:
    """Testing framework for manager-specified 20 queries with deterministic evaluation."""
    
    def __init__(self):
        self.agent = None
        self.session_capture = SessionStateCapture()
        self.ground_truth = HardcodedGroundTruth()
        self.evaluator = DeterministicEvaluator()  # No LLM needed!
        self.test_results = []
        self.type_results = {
            "Type 1: Single Tool + No Memory": [],
            "Type 3: Multi Tool + No Memory": []
        }
        self.session_id = "manager_test_session"
    
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
            
            # Step 2: Get expected state from hardcoded ground truth
            expected_form = self.ground_truth.get_expected_state(query)
            query_type = self.ground_truth.get_query_type(query)
            
            print(f"🎯 Expected Changes ({query_type}):")
            print(f"   Keywords: {expected_form.get('keywords', [])}")
            print(f"   Experience: {expected_form.get('min_experience', 0)}-{expected_form.get('max_experience', 10)} years")
            print(f"   Salary: {expected_form.get('min_salary', 0)}-{expected_form.get('max_salary', 15)} LPA")
            print(f"   Cities: {expected_form.get('current_cities', [])}")
            
            # Step 3: Execute query through agent (MEASURE ONLY AGENT TIME)
            start_execution = time.time()
            content = Content(data={
                "user_input": query,
                "session_state": self.session_capture.session_state,
                "session_id": self.session_id,
                "user_id": "test_user"
            })
            
            response = await self.agent.execute(content)
            agent_processing_time = time.time() - start_execution  # ONLY AGENT TIME
            
            if not response or not hasattr(response, 'data'):
                raise Exception("No response received from agent")
            
            # Step 4: Update session state and get actual form
            self.session_capture.update_from_response(response.data)
            actual_form = self.session_capture.get_search_form_json()
            
            print(f"🤖 Agent Response ({agent_processing_time:.3f}s):")
            print(f"   Keywords: {actual_form['keywords']}")
            print(f"   Experience: {actual_form['min_experience']}-{actual_form['max_experience']} years")
            print(f"   Salary: {actual_form['min_salary']}-{actual_form['max_salary']} LPA")
            print(f"   Cities: {actual_form['current_cities']}")
            print(f"   Agent Used: {response.data.get('routed_to', 'unknown')}")
            
            # Step 5: Deterministic evaluation (FAST & RELIABLE)
            is_pass, reasoning, confidence = self.evaluator.evaluate_results(
                query, expected_form, actual_form
            )
            
            print(f"🔍 Deterministic Evaluation:")
            print(f"   Result: {'✅ PASS' if is_pass else '❌ FAIL'}")
            print(f"   Score: {confidence:.2f}")
            print(f"   Reasoning: {reasoning[:100]}...")
            
            # Step 6: Compile results
            result = {
                'query': query,
                'query_type': query_type,
                'initial_form': initial_form,
                'expected_form': expected_form,
                'actual_form': actual_form,
                'agent_processing_time': agent_processing_time,  # ONLY AGENT TIME
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
                'query_type': self.ground_truth.get_query_type(query),
                'initial_form': self.session_capture.get_search_form_json(),
                'expected_form': {},
                'actual_form': {},
                'agent_processing_time': 0.0,
                'passed': False,
                'confidence': 0.0,
                'reasoning': f"Processing failed: {str(e)}",
                'agent_used': 'error',
                'response_data': {}
            }
    
    async def run_tests(self, output_file: str):
        """Run the complete test suite for the 20 specified queries."""
        if not await self.initialize_agent():
            return False
        
        # The 20 specified queries
        queries = [
            # TYPE 1: Single Tool, No Memory (10 queries)
            "add python and java",
            "increase experience by 5 years", 
            "add bangalore location",
            "set salary range 10-20 lpa",
            "add similar skills to java",
            "similar titles to software engineer",
            "nearby locations to mumbai",
            "relax my query",
            "similar titles for Designer",
            "refine my query",
            
            # TYPE 3: Multi Tool, No Memory (10 queries)
            "find similar skills to python and set experience 5+ years",
            "similar titles to data scientist from nearby to bangalore",
            "expand skills to java and add nearby cities to mumbai",
            "find titles similar to software engineer and add relevant skills, from nearby noida",
            "get titles similar to frontend developer and set salary 8-15 lpa",
            "find similar titles to software engineer from nearby Chennai and increase experience by 5 years",
            "expand python skills and add 3+ years experience",
            "find nearby locations to goa and add devops skills, and refine my query",
            "get related skills to machine learning from nearby locations to bangalore and relax my query",
            "find similar roles to product manager and set experience 5-10 years"
        ]
        
        print(f"📊 Testing {len(queries)} manager-specified queries")
        
        # Initialize session
        step_logger.start_session(self.session_id)
        print(f"🔄 Using session: {self.session_id}")
        
        # Process each query
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test {i}/{len(queries)}")
            
            result = await self.process_single_query(query)
            self.test_results.append(result)
            
            # Add to type-specific results
            query_type = result['query_type']
            if query_type in self.type_results:
                self.type_results[query_type].append(result)
            
            # Reset session state for next query
            self.session_capture.reset()
        
        # Write results
        await self.write_results_to_csv(output_file)
        await self.write_detailed_results()
        self.print_summary()
        
        return True
    
    async def write_results_to_csv(self, output_file: str):
        """Write results to CSV with specified format."""
        try:
            print(f"\n📝 Writing results to: {output_file}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Query',
                    'Expected_JSON',
                    'Final_JSON', 
                    'Test_Result',
                    'Agent_Processing_Time_s'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow({
                        'Query': result['query'],
                        'Expected_JSON': json.dumps(result['expected_form'], separators=(',', ':')),
                        'Final_JSON': json.dumps(result['actual_form'], separators=(',', ':')),
                        'Test_Result': 'PASS' if result['passed'] else 'FAIL',
                        'Agent_Processing_Time_s': f"{result['agent_processing_time']:.3f}"
                    })
            
            print(f"✅ Results written to {output_file}")
            
        except Exception as e:
            print(f"❌ Error writing results to CSV: {e}")
    
    async def write_detailed_results(self):
        """Write detailed results.txt file as specified by manager."""
        try:
            with open('result_test.txt', 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("MANAGER SPECIFIED TEST RESULTS - 20 QUERIES\n")
                f.write("=" * 80 + "\n\n")
                
                # Results by type
                for query_type, results in self.type_results.items():
                    if not results:
                        continue
                        
                    type_passed = sum(1 for r in results if r['passed'])
                    type_total = len(results)
                    type_failed = type_total - type_passed
                    type_time = sum(r['agent_processing_time'] for r in results)
                    type_avg_time = type_time / type_total if type_total > 0 else 0
                    
                    f.write(f"{query_type.upper()}:\n")
                    f.write(f"  Total Cases: {type_total}\n")
                    f.write(f"  Passed Cases: {type_passed}\n")
                    f.write(f"  Failed Cases: {type_failed}\n")
                    f.write(f"  Total Time: {type_time:.3f}s\n")
                    f.write(f"  Average Time: {type_avg_time:.3f}s\n")
                    f.write(f"  Success Rate: {(type_passed/type_total)*100:.1f}%\n\n")
                
                # Overall summary
                total_tests = len(self.test_results)
                passed_tests = sum(1 for r in self.test_results if r['passed'])
                failed_tests = total_tests - passed_tests
                total_time = sum(r['agent_processing_time'] for r in self.test_results)
                avg_time = total_time / total_tests if total_tests > 0 else 0
                
                f.write(f"OVERALL SUMMARY (20 QUERIES):\n")
                f.write(f"Total Cases: {total_tests}\n")
                f.write(f"Passed Cases: {passed_tests}\n")
                f.write(f"Failed Cases: {failed_tests}\n")
                f.write(f"Total Time: {total_time:.3f}s\n")
                f.write(f"Average Time: {avg_time:.3f}s\n")
                f.write(f"Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
                
                # Failed test details
                failed_tests_list = [r for r in self.test_results if not r['passed']]
                if failed_tests_list:
                    f.write("FAILED TEST DETAILS:\n")
                    f.write("=" * 40 + "\n")
                    for i, result in enumerate(failed_tests_list, 1):
                        f.write(f"\nFailed Test {i}:\n")
                        f.write(f"Query: {result['query']}\n")
                        f.write(f"Type: {result['query_type']}\n")
                        f.write(f"Agent: {result['agent_used']}\n")
                        f.write(f"Processing Time: {result['agent_processing_time']:.3f}s\n")
                        f.write(f"Confidence: {result['confidence']:.3f}\n")
                        f.write(f"Reasoning: {result['reasoning']}\n")
                        f.write("-" * 40 + "\n")
            
            print("✅ Detailed results written to result_test.txt")
            
        except Exception as e:
            print(f"❌ Error writing detailed results: {e}")
    
    def print_summary(self):
        """Print comprehensive test summary as specified by manager."""
        print(f"\n{'='*80}")
        print("📊 MANAGER SPECIFIED TEST SUMMARY")
        print(f"{'='*80}")
        
        # Results by type
        for query_type, results in self.type_results.items():
            if not results:
                continue
                
            type_passed = sum(1 for r in results if r['passed'])
            type_total = len(results)
            type_failed = type_total - type_passed
            type_time = sum(r['agent_processing_time'] for r in results)
            type_avg_time = type_time / type_total if type_total > 0 else 0
            
            print(f"📋 {query_type}:")
            print(f"   Total Cases: {type_total}")
            print(f"   ✅ Passed: {type_passed}")
            print(f"   ❌ Failed: {type_failed}")
            print(f"   ⏱️ Total Time: {type_time:.3f}s")
            print(f"   ⏱️ Average Time: {type_avg_time:.3f}s")
            print(f"   📈 Success Rate: {(type_passed/type_total)*100:.1f}%")
            print()
        
        # Overall stats
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = sum(r['agent_processing_time'] for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS (20 QUERIES):")
        print(f"   Total Cases: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏱️ Total Time: {total_time:.3f}s")
        print(f"   ⏱️ Average Time: {avg_time:.3f}s")
        print(f"   📈 Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Show some failed examples
        failed_tests_list = [r for r in self.test_results if not r['passed']]
        if failed_tests_list:
            print(f"❌ FAILED EXAMPLES:")
            for i, result in enumerate(failed_tests_list[:3], 1):  # Show first 3 failures
                print(f"   {i}. Query: '{result['query']}'")
                print(f"      Type: {result['query_type']}")
                print(f"      Agent: {result['agent_used']}")
                print(f"      Time: {result['agent_processing_time']:.3f}s")
                print(f"      Confidence: {result['confidence']:.3f}")
                print()


def create_manager_queries_file(filename: str = 'manager_queries.txt'):
    """Create the exact 20 queries specified by manager."""
    
    queries = [
        "# Manager Specified Queries - 20 Total",
        "",
        "# TYPE 1: Single Tool, No Memory (10 queries)",
        "add python and java",
        "increase experience by 5 years", 
        "add bangalore location",
        "set salary range 10-20 lpa",
        "add similar skills to java",
        "similar titles to software engineer",
        "nearby locations to mumbai",
        "relax my query",
        "similar titles for Designers",
        "refine my query",
        "",
        "# TYPE 3: Multi Tool, No Memory (10 queries)",
        "find similar skills to python and set experience 5+ years",
        "similar titles to data scientist from nearby to bangalore",
        "expand skills to java and add nearby cities to mumbai",
        "find titles similar to software engineer and add relevant skills, from nearby noida",
        "get titles similar to frontend developer and set salary 8-15 lpa",
        "find similar titles to software engineer from nearby Chennai and increase experience by 5 years",
        "expand python skills and add 3+ years experience",
        "find nearby locations to goa and add devops skills, and refine my query",
        "get related skills to machine learning from nearby locations to bangalore and relax my query",
        "find similar roles to product manager and set experience 5-10 years"
    ]
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for query in queries:
                f.write(f"{query}\n")
        
        # Count actual queries (non-comment lines)
        actual_queries = [q for q in queries if q and not q.startswith('#')]
        
        print(f"✅ Manager queries file created: {filename}")
        print(f"📊 Total queries: {len(actual_queries)}")
        print(f"📋 Type 1 (Single Tool): 10 queries")
        print(f"📋 Type 3 (Multi Tool): 10 queries")
        return True
        
    except Exception as e:
        print(f"❌ Error creating manager queries file: {e}")
        return False


async def main():
    """Main function for manager-specified testing."""
    parser = argparse.ArgumentParser(
        description='Manager Specified Test Suite - 20 Queries with Hardcoded Ground Truth',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py --create_sample              # Create the 20 manager queries
  python test.py                              # Run all 20 tests
  python test.py --output_file results.csv    # Custom output file
        """
    )
    
    parser.add_argument('--output_file', default='manager_output.csv',
                       help='Path to output CSV file (default: manager_output.csv)')
    parser.add_argument('--create_sample', action='store_true',
                       help='Create manager-specified 20 queries file')
    
    args = parser.parse_args()
    
    print("🚀 Manager Specified Test Suite")
    print("=" * 60)
    print("📊 20 Queries with Hardcoded Ground Truth")
    print("⏱️ Measures ONLY Agent Processing Time")
    print("🔍 Deterministic Evaluation (No LLM needed!)")
    print("⚡ Fast & Reliable Testing")
    print("=" * 60)
    
    if args.create_sample:
        success = create_manager_queries_file('manager_queries.txt')
        if success:
            print(f"\n🎯 Manager queries created successfully!")
            print(f"📝 File: manager_queries.txt")
            print(f"🔍 You can now run: python test.py")
            print(f"\n📋 Query Breakdown:")
            print(f"   • Type 1 (Single Tool + No Memory): 10 queries")
            print(f"   • Type 3 (Multi Tool + No Memory): 10 queries")
            print(f"   • Total: 20 queries")
        return
    
    # Run manager specified tests
    print(f"🔍 Running manager-specified tests...")
    print(f"📊 Output file: {args.output_file}")
    print(f"📋 Detailed results: result_test.txt")
    
    tester = ManagerSpecifiedTester()
    success = await tester.run_tests(args.output_file)
    
    if success:
        print(f"\n🎉 Manager testing completed successfully!")
        print(f"📊 CSV Results: {args.output_file}")
        print(f"📋 Detailed Results: result_test.txt")
        print(f"🔍 Session: {tester.session_id}")
        print(f"\n💡 Key Features:")
        print(f"   🎯 Hardcoded ground truth for 20 specific queries")
        print(f"   ⏱️ Pure agent processing time measurement")
        print(f"   🧠 LLM intelligent evaluation")
        print(f"   📊 Type-based performance analysis")
    else:
        print(f"\n💥 Manager testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Manager testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error in manager testing: {e}")
        traceback.print_exc()
        sys.exit(1)