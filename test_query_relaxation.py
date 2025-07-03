#!/usr/bin/env python3
"""
Enhanced Query Relaxation Testing Script
Tests both direct API hits and tool integration with change comparison
"""

import asyncio
import requests
import json
import sys
import os
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class EnhancedQueryRelaxationTester:
    """Enhanced test suite for query relaxation with change comparison."""
    
    def __init__(self):
        # API Configuration
        self.api_url = "http://10.10.112.202:8125/get_relaxed_query_optimized"
        self.headers = {
            'Content-Type': 'application/json',
            'X-TRANSACTION-ID': '3113ea131'
        }
        
        # Test scenarios with different candidate counts
        self.test_scenarios = [
            {
                "name": "Low Results Scenario",
                "current_count": 8,
                "session_state": {
                    "keywords": ["Python", "Django", "REST API", "AWS", "Docker"],
                    "min_exp": 5,
                    "max_exp": 8,
                    "min_salary": 12,
                    "max_salary": 18,
                    "current_cities": ["Bangalore"],
                    "preferred_cities": [],
                    "total_results": 8
                }
            },
            {
                "name": "Moderate Results Scenario", 
                "current_count": 25,
                "session_state": {
                    "keywords": ["Java", "Spring Boot", "Microservices"],
                    "min_exp": 3,
                    "max_exp": 10,
                    "min_salary": 5,
                    "max_salary": 15,
                    "current_cities": ["Mumbai"],
                    "preferred_cities": ["Pune"],
                    "total_results": 25
                }
            },
            {
                "name": "High Results Scenario",
                "current_count": 75,
                "session_state": {
                    "keywords": ["JavaScript", "React"],
                    "min_exp": 2,
                    "max_exp": 15,
                    "min_salary": 3,
                    "max_salary": 20,
                    "current_cities": ["Delhi"],
                    "preferred_cities": ["Gurgaon", "Noida"],
                    "total_results": 75
                }
            },
            {
                "name": "Working Payload Scenario",
                "current_count": 50,
                "session_state": {
                    "keywords": ["Java 8", "Spring Boot", "Microservices", "Collections", "Memory management", "RESTful microservices", "kafka"],
                    "min_exp": 6,
                    "max_exp": 50,
                    "min_salary": 1,
                    "max_salary": 18,
                    "current_cities": ["Bangalore"],
                    "preferred_cities": ["Mumbai", "Delhi", "Pune", "Hyderabad"],
                    "total_results": 50
                }
            }
        ]
    
    def create_working_api_request(self):
        """Create the exact working API request."""
        return {
            'sid': None,
            'ctc_Type': 'rs',
            'company_id': 3812074,
            'comnotGroupId': 4634055,
            'recruiter_id': 124271564,
            'preference_key': 'e7d47e8e-4728-4a9f-9bfe-d9e8e9586a2b',
            'user_ids': None,
            'search_flag': 'adv',
            'unique_id': None,
            'ez_keyword_any': [
                {'key': '133', 'value': 'Java 8', 'type': 'skill', 'globalName': 'java'},
                {'key': '56155', 'value': ' Spring Boot', 'type': 'skill', 'globalName': 'spring boot'},
                {'key': '56016', 'value': ' Microservices', 'type': 'skill', 'globalName': 'microservices'},
                {'key': '407', 'value': ' Collections', 'type': 'skill', 'globalName': 'collections'},
                {'key': '37176', 'value': ' Memory management', 'type': 'skill', 'globalName': 'memory management'},
                {'key': '-1', 'value': 'RESTful microservices', 'type': None, 'globalName': None},
                {'key': '56229', 'value': 'kafka', 'type': 'skill', 'globalName': 'kafka'}
            ],
            'anyKeywords': [
                {'key': '133', 'value': 'Java 8', 'type': 'skill', 'globalName': 'java'},
                {'key': '56155', 'value': ' Spring Boot', 'type': 'skill', 'globalName': 'spring boot'},
                {'key': '56016', 'value': ' Microservices', 'type': 'skill', 'globalName': 'microservices'},
                {'key': '407', 'value': ' Collections', 'type': 'skill', 'globalName': 'collections'},
                {'key': '37176', 'value': ' Memory management', 'type': 'skill', 'globalName': 'memory management'},
                {'key': '-1', 'value': 'RESTful microservices', 'type': None, 'globalName': None},
                {'key': '56229', 'value': 'kafka', 'type': 'skill', 'globalName': 'kafka'}
            ],
            'ez_keyword_all': [
                {'key': '6031', 'value': 'Multithreading', 'type': 'skill', 'globalName': 'multithreading'},
                {'key': '2700', 'value': 'Java Developer', 'type': 'designation', 'globalName': None},
                {'key': '9125', 'value': 'AWS', 'type': 'skill', 'globalName': None},
                {'key': '4232', 'value': 'JUnit', 'type': 'skill', 'globalName': None},
                {'key': '56026', 'value': 'Mockito', 'type': 'skill', 'globalName': None}
            ],
            'allKeywords': [
                {'key': '6031', 'value': 'Multithreading', 'type': 'skill', 'globalName': 'multithreading'},
                {'key': '2700', 'value': 'Java Developer', 'type': 'designation', 'globalName': None},
                {'key': '9125', 'value': 'AWS', 'type': 'skill', 'globalName': None},
                {'key': '4232', 'value': 'JUnit', 'type': 'skill', 'globalName': None},
                {'key': '56026', 'value': 'Mockito', 'type': 'skill', 'globalName': None}
            ],
            'ez_keyword_exclude': [],
            'excludeKeywords': [],
            'inc_keyword': '',
            'incKeywords': '',
            'key_type': 'ezkw',
            'swr_key': None,
            'swr_exclude_key': None,
            'swr_type': 'bool',
            'srch_key_in': 'ER',
            'it_params': {
                'operator': 'OR',
                'fullSearchFlag': 0,
                'skills': None,
                'enableTaxonomy': True
            },
            'min_exp': '6',
            'max_exp': '-1',
            'min_ctc': '1.00',
            'max_ctc': '18.00',
            'ctc_type': 'rs',
            'CTC_Type': 'rs',
            'dollarRate': 60,
            'dollar_rate': 60,
            'zero_ctc_search': False,
            'city': ['9501'],
            'currentStateId': [],
            'OCity': '',
            'pref_loc': ['6', '17', '139', '220'],
            'preferredStateId': [],
            'loc_city_only': 0,
            'location_op': 'and',
            'farea_roles': [],
            'indtype': [],
            'excludeIndtype': [],
            'emp_key': '',
            'emp_type': 'ezkw',
            'srch_emp_in': 'C',
            'exemp_key': '',
            'exemp_type': 'ezkw',
            'srch_exemp_in': 'C',
            'desig_key_entity': None,
            'desig_key': None,
            'desig_type': 'ezkw',
            'srch_des_in': 'C',
            'noticePeriodArr': [1],
            'notice_period': [1],
            'ugcourse': [],
            'ug_year_range': [-1, -1],
            'uginst_key': '',
            'uginst_id_key_map': {},
            'uginst_type': 'all',
            'ug_edu_type': [0],
            'pgcourse': [],
            'pg_year_range': [-1, -1],
            'pginst_key': '',
            'pginst_id_key_map': {},
            'pginst_type': 'all',
            'pg_edu_type': [0],
            'ppgcourse': [],
            'ppg_year_range': [-1, -1],
            'ppginst_key': '',
            'ppginst_id_key_map': {},
            'ppginst_type': 'all',
            'ppg_edu_type': [0],
            'ug_pg_type': 'and',
            'pg_ppg_type': 'and',
            'caste_id': [],
            'gender': 'n',
            'dis_type': False,
            'candidate_age_range': [-1, -1],
            'wstatus_usa': [-1],
            'work_auth_others': [-1],
            'all_new': 'ALL',
            'search_on_verified_numbers': False,
            'verified_email': False,
            'uploaded_cv': False,
            'search_on_job_type': '',
            'search_on_jobs_status_type': '',
            'premium': False,
            'featured_search': False,
            'PAGE_LIMIT': 40,
            'sort_by': 'RELEVANCE',
            'isMakeSenseSrch': 1,
            'days_old': '3650',
            'hiring_for': None,
            'hiring_for_search_type': 'bool',
            'fetch_clusters': {},
            'cluster_industry': None,
            'cluster_exclude_industry': None,
            'cluster_role': None,
            'kwMap': 'n',
            'kw_map': 'n',
            'ezSearch': 'n',
            'SEARCH_OFFSET': 0,
            'SEARCH_COUNT': 80,
            'freeSearch': False,
            'subQuery': '',
            'uid': 'adv2979127398455226146023051300~~84e12a::48707923710953277141::269663223661042',
            'al_engine_ip': 'rpcservices1.resdex.com',
            'al_engine_port': 9123,
            'makesense_url': 'http://test.semantic.resdex.com/v1/restructureresdexquery',
            'makesense_timeout': 1000,
            'makesense_response_timeout': 1000,
            'appname': 'resdex',
            'ctcclus_sel': ['0000', '5200'],
            'roles': '',
            'magicFlag': '0',
            'magic_flag': '0',
            'farea': [0],
            'any_keyword_srch_type': 'bool',
            'x_xii_type': None,
            'immediatelyAvailable': False,
            'cluster_notice_period': None,
            'cluster_location': None,
            'date_range': None,
            'emp_key_globalid': {},
            'exemp_key_globalid': {},
            'verifiedSkillIds': None,
            'candidatesWithVerifiedSkills': None,
            'company_type': None,
            'expActive': True,
            'rerankEnabled': False,
            'excludeTestProfiles': True,
            'contests': None,
            'profileTags': None,
            'segmentEnabled': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'anyKeywordTags': 'Java 8, Spring Boot, Microservices, Collections, Memory management,RESTful microservices,kafka',
            'allKeywordTags': 'Multithreading,Java Developer,AWS,JUnit,Mockito',
            'daysold': '3650'
        }
    
    def test_direct_api_with_change_analysis(self, current_count: int):
        """Test direct API call and analyze changes."""
        print(f"\n🧪 TEST 1: Direct API Call with Change Analysis")
        print("=" * 60)
        
        working_request = self.create_working_api_request()
        
        payload = {
            'request_object': working_request,
            'totalcount': current_count
        }
        
        print(f"📊 Testing with current_count: {current_count}")
        print(f"📡 API URL: {self.api_url}")
        
        try:
            print(f"\n📡 Sending request...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload, default=str),
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                print(f"\n✅ SUCCESS! Analyzing API Response:")
                print("=" * 40)
                
                # Check approx_new_count
                approx_count = response_data.get('approx_new_count')
                print(f"🎯 approx_new_count: {approx_count} (type: {type(approx_count)})")
                
                # Analyze changes
                if 'relaxed_query' in response_data and response_data['relaxed_query']:
                    relaxed = response_data['relaxed_query']
                    print(f"\n🔄 CHANGE ANALYSIS:")
                    
                    # Skills analysis
                    original_any_skills = working_request['ez_keyword_any']
                    relaxed_any_skills = relaxed.get('ez_keyword_any', [])
                    print(f"   Skills (any): {len(original_any_skills)} → {len(relaxed_any_skills)}")
                    
                    if len(relaxed_any_skills) != len(original_any_skills):
                        if len(relaxed_any_skills) > len(original_any_skills):
                            added_skills = relaxed_any_skills[len(original_any_skills):]
                            print(f"   ➕ Added skills: {[skill['value'] for skill in added_skills]}")
                        else:
                            print(f"   ➖ Removed {len(original_any_skills) - len(relaxed_any_skills)} skills")
                    
                    # Mandatory skills analysis
                    original_all_skills = working_request['ez_keyword_all']
                    relaxed_all_skills = relaxed.get('ez_keyword_all', [])
                    print(f"   Skills (mandatory): {len(original_all_skills)} → {len(relaxed_all_skills)}")
                    
                    if len(relaxed_all_skills) != len(original_all_skills):
                        print(f"   ⚖️ Mandatory skill change: {len(original_all_skills) - len(relaxed_all_skills)} skills made optional")
                    
                    # Experience analysis
                    original_exp = f"{working_request['min_exp']}-{working_request['max_exp']}"
                    relaxed_exp = f"{relaxed.get('min_exp', '?')}-{relaxed.get('max_exp', '?')}"
                    print(f"   Experience: {original_exp} → {relaxed_exp}")
                    
                    # Salary analysis
                    original_salary = f"{working_request['min_ctc']}-{working_request['max_ctc']}"
                    relaxed_salary = f"{relaxed.get('min_ctc', '?')}-{relaxed.get('max_ctc', '?')}"
                    print(f"   Salary: {original_salary} → {relaxed_salary}")
                    
                    print(f"\n💡 RELAXATION IMPACT:")
                    print(f"   Current candidates: {current_count}")
                    if approx_count:
                        print(f"   Estimated after relaxation: {approx_count}")
                        print(f"   Potential increase: +{approx_count - current_count}")
                        print(f"   Improvement: {int(((approx_count - current_count) / current_count) * 100)}%")
                    
                    return {
                        "success": True,
                        "current_count": current_count,
                        "estimated_count": approx_count,
                        "changes_detected": True,
                        "api_response": response_data
                    }
                else:
                    print(f"❌ relaxed_query: NOT FOUND or NULL")
                    return {
                        "success": True,
                        "current_count": current_count,
                        "estimated_count": approx_count,
                        "changes_detected": False,
                        "api_response": response_data
                    }
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_tool_integration(self, scenario: Dict[str, Any]):
        """Test the QueryRelaxationTool integration."""
        print(f"\n🧪 TEST 2: Tool Integration - {scenario['name']}")
        print("=" * 60)
        
        try:
            from resdex_agent.tools.query_relaxation_tool import QueryRelaxationTool
            
            tool = QueryRelaxationTool("test_tool")
            session_state = scenario["session_state"]
            
            print(f"📊 Session State Summary:")
            print(f"   Keywords: {session_state['keywords']}")
            print(f"   Experience: {session_state['min_exp']}-{session_state['max_exp']} years")
            print(f"   Salary: {session_state['min_salary']}-{session_state['max_salary']} lakhs")
            print(f"   Current results: {session_state['total_results']}")
            
            print(f"\n🔧 Calling QueryRelaxationTool...")
            
            result = await tool(
                session_state=session_state,
                user_input="relax search for more candidates",
                memory_context=[]
            )
            
            print(f"\n📊 TOOL RESULT:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Current count: {result.get('current_count', 0)}")
            print(f"   Estimated increase: {result.get('estimated_new_count', 0)}")
            
            suggestions = result.get('suggestions', [])
            print(f"   Suggestions: {len(suggestions)}")
            
            print(f"\n💡 GENERATED SUGGESTIONS:")
            for i, suggestion in enumerate(suggestions, 1):
                api_suggested = suggestion.get('api_suggested', False)
                confidence = suggestion.get('confidence', 0)
                
                print(f"   {i}. {suggestion.get('title', 'Unknown')}")
                print(f"      Description: {suggestion.get('description', 'No description')}")
                print(f"      Impact: {suggestion.get('impact', 'Unknown impact')}")
                print(f"      Source: {'🤖 API' if api_suggested else '🧠 Rule-based'}")
                print(f"      Confidence: {confidence:.0%}")
                
                # Show changes if available
                changes = suggestion.get('changes', {})
                if changes:
                    print(f"      Changes: {changes}")
                print()
            
            print(f"\n📝 USER MESSAGE:")
            message = result.get('message', '')
            print(f"   {message}")
            
            return {
                "success": result.get('success', False),
                "suggestions_count": len(suggestions),
                "api_suggestions": len([s for s in suggestions if s.get('api_suggested', False)]),
                "fallback_suggestions": len([s for s in suggestions if not s.get('api_suggested', False)]),
                "estimated_increase": result.get('estimated_new_count', 0)
            }
            
        except Exception as e:
            print(f"❌ Tool integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def compare_results(self, direct_result: Dict[str, Any], tool_result: Dict[str, Any], scenario_name: str):
        """Compare direct API vs tool results."""
        print(f"\n🔍 COMPARISON: Direct API vs Tool - {scenario_name}")
        print("=" * 60)
        
        print(f"📊 DIRECT API:")
        print(f"   Success: {direct_result.get('success', False)}")
        print(f"   Changes detected: {direct_result.get('changes_detected', False)}")
        print(f"   Estimated count: {direct_result.get('estimated_count', 'N/A')}")
        
        print(f"\n🔧 TOOL INTEGRATION:")
        print(f"   Success: {tool_result.get('success', False)}")
        print(f"   Total suggestions: {tool_result.get('suggestions_count', 0)}")
        print(f"   API-based suggestions: {tool_result.get('api_suggestions', 0)}")
        print(f"   Fallback suggestions: {tool_result.get('fallback_suggestions', 0)}")
        print(f"   Estimated increase: {tool_result.get('estimated_increase', 'N/A')}")
        
        # Analysis
        if direct_result.get('success') and tool_result.get('success'):
            if direct_result.get('changes_detected') and tool_result.get('api_suggestions', 0) > 0:
                print(f"\n✅ PERFECT ALIGNMENT: Both API and tool working correctly")
            elif direct_result.get('changes_detected') and tool_result.get('api_suggestions', 0) == 0:
                print(f"\n⚠️ PARTIAL ISSUE: API has changes but tool using fallback")
            elif not direct_result.get('changes_detected') and tool_result.get('fallback_suggestions', 0) > 0:
                print(f"\n✅ GOOD FALLBACK: API no changes, tool provides rule-based suggestions")
            else:
                print(f"\n❌ ISSUE: Unexpected result combination")
        else:
            print(f"\n❌ FAILURE: One or both tests failed")
    
    async def run_comprehensive_test(self):
        """Run comprehensive test suite."""
        print("🚀 ENHANCED QUERY RELAXATION TEST SUITE")
        print("=" * 80)
        
        results_summary = []
        
        # Test each scenario
        for scenario in self.test_scenarios:
            print(f"\n🎯 TESTING SCENARIO: {scenario['name']}")
            print("=" * 50)
            
            current_count = scenario['current_count']
            
            # Test 1: Direct API
            direct_result = self.test_direct_api_with_change_analysis(current_count)
            
            # Test 2: Tool integration
            tool_result = await self.test_tool_integration(scenario)
            
            # Test 3: Compare results
            self.compare_results(direct_result, tool_result, scenario['name'])
            
            # Store results
            results_summary.append({
                "scenario": scenario['name'],
                "current_count": current_count,
                "direct_success": direct_result.get('success', False),
                "tool_success": tool_result.get('success', False),
                "api_suggestions": tool_result.get('api_suggestions', 0),
                "estimated_increase": direct_result.get('estimated_count', 0)
            })
        
        # Final summary
        self.print_final_summary(results_summary)
    
    def print_final_summary(self, results: List[Dict[str, Any]]):
        """Print final test summary."""
        print("\n" + "=" * 80)
        print("🏁 FINAL TEST SUMMARY")
        print("=" * 80)
        
        successful_scenarios = len([r for r in results if r['direct_success'] and r['tool_success']])
        total_scenarios = len(results)
        
        print(f"📊 Overall Results:")
        print(f"   Total scenarios tested: {total_scenarios}")
        print(f"   Successful scenarios: {successful_scenarios}")
        print(f"   Success rate: {(successful_scenarios/total_scenarios)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        print("-" * 50)
        
        for result in results:
            status = "✅ PASS" if result['direct_success'] and result['tool_success'] else "❌ FAIL"
            api_suggestions = result['api_suggestions']
            estimated = result['estimated_increase']
            
            print(f"{status} | {result['scenario']}")
            print(f"     Count: {result['current_count']} → Est: {estimated}")
            print(f"     API suggestions: {api_suggestions}")
            print()
        
        print("=" * 80)
        
        if successful_scenarios == total_scenarios:
            print("🎉 ALL TESTS PASSED! Query relaxation is working perfectly!")
        else:
            print(f"⚠️ {total_scenarios - successful_scenarios} scenarios failed. Review the issues above.")


async def main():
    """Main test execution."""
    tester = EnhancedQueryRelaxationTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())