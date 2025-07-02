#!/usr/bin/env python3
"""
Quick test script to hit the relaxation API with the working payload
"""

import requests
import json

def test_working_payload():
    """Test with the exact payload your senior provided"""
    
    # Your working request object
    working_request = {
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
    
    # API details
    api_url = "http://10.10.112.202:8125/get_relaxed_query_optimized"
    headers = {
        'Content-Type': 'application/json',
        'X-TRANSACTION-ID': '3113ea131'
    }
    
    # Payload
    payload = {
        'request_object': working_request,
        'totalcount': 50  # Test with 50 current candidates
    }
    
    print("🚀 TESTING WORKING PAYLOAD")
    print("=" * 50)
    print(f"📡 API URL: {api_url}")
    print(f"📊 Current count: 50")
    print(f"🔧 Skills (any): {len(working_request['ez_keyword_any'])}")
    print(f"🔧 Skills (all): {len(working_request['ez_keyword_all'])}")
    print(f"📈 Experience: {working_request['min_exp']}-{working_request['max_exp']}")
    print(f"💰 Salary: {working_request['min_ctc']}-{working_request['max_ctc']}")
    
    try:
        print(f"\n📡 Sending request...")
        response = requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload, default=str),
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"\n✅ SUCCESS! API Response:")
            print("=" * 30)
            
            # Check for approx_new_count
            approx_count = response_data.get('approx_new_count')
            print(f"🎯 approx_new_count: {approx_count} (type: {type(approx_count)})")
            
            # Check for relaxed_query
            if 'relaxed_query' in response_data:
                relaxed = response_data['relaxed_query']
                print(f"🔄 relaxed_query found: YES")
                
                # Compare key differences
                original_any_skills = len(working_request['ez_keyword_any'])
                relaxed_any_skills = len(relaxed.get('ez_keyword_any', []))
                print(f"   Skills (any): {original_any_skills} → {relaxed_any_skills}")
                
                original_all_skills = len(working_request['ez_keyword_all'])  
                relaxed_all_skills = len(relaxed.get('ez_keyword_all', []))
                print(f"   Skills (all): {original_all_skills} → {relaxed_all_skills}")
                
                original_exp = f"{working_request['min_exp']}-{working_request['max_exp']}"
                relaxed_exp = f"{relaxed.get('min_exp', '?')}-{relaxed.get('max_exp', '?')}"
                print(f"   Experience: {original_exp} → {relaxed_exp}")
                
            else:
                print(f"❌ relaxed_query: NOT FOUND")
            
            print(f"\n📋 Full Response Keys: {list(response_data.keys())}")
            
            # Print first few lines of full response for debugging
            print(f"\n🔍 Full Response Preview:")
            response_str = json.dumps(response_data, indent=2, default=str)
            lines = response_str.split('\n')
            for line in lines[:20]:  # First 20 lines
                print(f"   {line}")
            if len(lines) > 20:
                print(f"   ... ({len(lines)-20} more lines)")
                
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


def test_with_your_tool():
    """Test using your QueryRelaxationTool with equivalent session state"""
    
    print(f"\n🧪 TESTING WITH YOUR TOOL")
    print("=" * 50)
    
    # Convert the working payload to session state format
    session_state = {
        "keywords": ["Java 8", "Spring Boot", "Microservices", "Collections", "Memory management", "RESTful microservices", "kafka"],
        "min_exp": 6,
        "max_exp": 50,  # -1 becomes 50
        "min_salary": 1,
        "max_salary": 18,
        "current_cities": ["Bangalore"],  # city: ['9501']
        "preferred_cities": ["Mumbai", "Delhi", "Pune", "Hyderabad"],  # pref_loc: ['6', '17', '139', '220']
        "total_results": 50
    }
    
    print(f"📊 Session State:")
    for key, value in session_state.items():
        print(f"   {key}: {value}")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.abspath('.'))
        
        from resdex_agent.tools.query_relaxation_tool import QueryRelaxationTool
        
        tool = QueryRelaxationTool("test_tool")
        
        # Test conversion
        api_request = tool._convert_session_to_api_request(session_state)
        
        print(f"\n🔧 Your Tool Generated:")
        print(f"   Skills (any): {len(api_request.get('ez_keyword_any', []))}")
        print(f"   Skills (all): {len(api_request.get('ez_keyword_all', []))}")  
        print(f"   Experience: {api_request.get('min_exp')}-{api_request.get('max_exp')}")
        print(f"   Salary: {api_request.get('min_ctc')}-{api_request.get('max_ctc')}")
        
        print(f"\n✅ Tool conversion successful!")
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test 1: Direct API call with working payload
    test_working_payload()
    
    # Test 2: Your tool conversion
    test_with_your_tool()