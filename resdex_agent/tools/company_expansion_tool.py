import pandas as pd
import os
from typing import Dict, Any, List, Optional
import logging
from .company_tools import CompanyNormalizationTool

logger = logging.getLogger(__name__)

class CompanyExpansionTool:
    """Tool for expanding companies using CSV data, predefined groups, and LLM fallback."""
    
    def __init__(self, name: str = "company_expansion_tool"):
        self.name = name
        self.company_normalizer = CompanyNormalizationTool()
        self.csv_path = "/data/analytics/rohit.agarwal/Resdex/resdex_agent/utils/similar_companies.csv" 
        self.company_df = None
        
        self._load_company_csv()
        
        # Predefined company groups
        self.company_groups = {
            "big4": {
                "description": "Big 4 consulting firms",
                "companies": ["Deloitte", "PwC", "EY", "KPMG"]
            },
            "big5": {
                "description": "Big 5 consulting firms", 
                "companies": ["Deloitte", "PwC", "EY", "KPMG", "Accenture"]
            },
            "mbb": {
                "description": "McKinsey, Bain & Company, Boston Consulting Group",
                "companies": ["McKinsey & Company", "Bain & Company", "Boston Consulting Group"]
            },
            "top10_india": {
                "description": "Top 10 companies in India",
                "companies": ["Reliance Industries", "Tata Consultancy Services", "HDFC Bank", 
                            "Infosys", "HDFC", "ICICI Bank", "Kotak Mahindra Bank", 
                            "Bharti Airtel", "ITC", "Larsen & Toubro"]
            },
            "top10_global": {
                "description": "Top 10 global companies",
                "companies": ["Apple", "Microsoft", "Saudi Aramco", "Alphabet", "Amazon", 
                            "Tesla", "Meta", "TSMC", "Berkshire Hathaway", "NVIDIA"]
            },
            "top_it": {
                "description": "Top IT companies",
                "companies": ["Microsoft", "Apple", "Alphabet", "Amazon", "Meta", "Tesla", 
                            "Oracle", "Salesforce", "Adobe", "ServiceNow", "TCS", "Infosys", 
                            "Wipro", "HCL Technologies", "Tech Mahindra"]
            },
            "top_indian": {
                "description": "Top Indian companies",
                "companies": ["Reliance Industries", "Tata Consultancy Services", "HDFC Bank", 
                            "Infosys", "Hindustan Unilever", "ICICI Bank", "State Bank of India", 
                            "Bharti Airtel", "ITC", "Axis Bank", "Kotak Mahindra Bank", 
                            "Larsen & Toubro", "Wipro", "HCL Technologies"]
            },
            "top_banks": {
                "description": "Top banking institutions",
                "companies": ["JPMorgan Chase", "Bank of America", "Wells Fargo", "Citigroup", 
                            "Goldman Sachs", "Morgan Stanley", "HDFC Bank", "ICICI Bank", 
                            "State Bank of India", "Axis Bank", "Kotak Mahindra Bank"]
            },
            "top_finance": {
                "description": "Top finance firms",
                "companies": ["BlackRock", "Vanguard", "Fidelity", "State Street", "JPMorgan Chase", 
                            "Goldman Sachs", "Morgan Stanley", "Credit Suisse", "UBS", 
                            "Deutsche Bank", "HDFC", "Bajaj Finance"]
            },
            "top_analysts": {
                "description": "Top analyst and research firms",
                "companies": ["McKinsey & Company", "Boston Consulting Group", "Bain & Company", 
                            "Deloitte", "PwC", "EY", "KPMG", "Accenture", "Gartner", 
                            "Forrester", "IDC", "Frost & Sullivan"]
            },
            "top_consulting": {
                "description": "Top consulting companies",
                "companies": ["McKinsey & Company", "Boston Consulting Group", "Bain & Company", 
                            "Deloitte", "PwC", "EY", "KPMG", "Accenture", "Oliver Wyman", 
                            "Roland Berger", "A.T. Kearney", "Strategy&"]
            },
            "top_core_engineering": {
                "description": "Top core engineering firms",
                "companies": ["General Electric", "Siemens", "ABB", "Schneider Electric", 
                            "Honeywell", "3M", "Caterpillar", "John Deere", "Boeing", 
                            "Airbus", "Larsen & Toubro", "Bharat Heavy Electricals", 
                            "Godrej", "Mahindra & Mahindra"]
            },
            "faang": {
                "description": "FAANG companies",
                "companies": ["Meta", "Apple", "Amazon", "Netflix", "Alphabet"]
            },
            "manga": {
                "description": "MANGA companies", 
                "companies": ["Meta", "Apple", "Netflix", "Alphabet", "Amazon"]
            },
            "top_automotive": {
                "description": "Top automotive companies",
                "companies": ["Toyota", "Volkswagen", "Mercedes-Benz", "BMW", "Ford", 
                            "General Motors", "Hyundai", "Nissan", "Honda", "Tesla",
                            "Tata Motors", "Mahindra & Mahindra", "Bajaj Auto", "Hero MotoCorp"]
            },
            "top_pharma": {
                "description": "Top pharmaceutical companies",
                "companies": ["Johnson & Johnson", "Pfizer", "Roche", "Novartis", "Merck", 
                            "AbbVie", "Bristol Myers Squibb", "GlaxoSmithKline", "Sanofi", 
                            "AstraZeneca", "Dr. Reddy's", "Cipla", "Sun Pharma", "Lupin"]
            },
            "top_fmcg": {
                "description": "Top FMCG companies",
                "companies": ["Procter & Gamble", "Unilever", "Nestlé", "Coca-Cola", "PepsiCo", 
                            "L'Oréal", "Colgate-Palmolive", "Hindustan Unilever", "ITC", 
                            "Godrej Consumer Products", "Dabur", "Marico"]
            },
            "unicorns": {
                "description": "Indian unicorn startups",
                "companies": ["Flipkart", "Paytm", "Ola", "Swiggy", "Zomato", "Byju's", 
                            "Dream11", "PolicyBazaar", "Razorpay", "PhonePe", "Lenskart", 
                            "Meesho", "Unacademy", "Vedantu"]
            },
            "edtech": {
                "description": "Education technology companies",
                "companies": ["Byju's", "Unacademy", "Vedantu", "Khan Academy", "Coursera", 
                            "Udemy", "Skillshare", "MasterClass", "Pluralsight", "LinkedIn Learning"]
            },
            "fintech": {
                "description": "Financial technology companies", 
                "companies": ["Paytm", "PhonePe", "Razorpay", "PolicyBazaar", "Zerodha", 
                            "Stripe", "Square", "PayPal", "Robinhood", "Coinbase", "Klarna"]
            },
            "foodtech": {
                "description": "Food delivery and technology companies",
                "companies": ["Zomato", "Swiggy", "Uber Eats", "DoorDash", "Grubhub", 
                            "Deliveroo", "Just Eat", "Foodpanda", "Dunzo", "BigBasket"]
            }
        }
    
    def _load_company_csv(self):
        """Load company similarity CSV data."""
        try:
            if os.path.exists(self.csv_path):
                self.company_df = pd.read_csv(self.csv_path)
                print(f"✅ Loaded company CSV with {len(self.company_df)} records")
                logger.info(f"Loaded company similarity CSV: {len(self.company_df)} records")
            else:
                print(f"⚠️ Company CSV not found at: {self.csv_path}")
                logger.warning(f"Company CSV not found at: {self.csv_path}")
                self.company_df = None
        except Exception as e:
            print(f"❌ Error loading company CSV: {e}")
            logger.error(f"Error loading company CSV: {e}")
            self.company_df = None
    
    async def __call__(self, expansion_type: str, **kwargs) -> Dict[str, Any]:
        """Main entry point for company expansion."""
        try:
            if expansion_type == "similar_companies":
                return await self._expand_similar_companies(**kwargs)
            elif expansion_type == "company_group":
                return await self._expand_company_group(**kwargs)
            elif expansion_type == "recruiter_similar":
                return await self._expand_recruiter_similar(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown expansion type: {expansion_type}"
                }
        except Exception as e:
            logger.error(f"Company expansion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _expand_similar_companies(self, company_name: str, **kwargs) -> Dict[str, Any]:
        """Expand similar companies using CSV data with LLM fallback."""
        try:
            print(f"🏢 Expanding similar companies for: {company_name}")
            
            # Get canonical ID for the company
            canonical_id = self.company_normalizer.get_company_id(company_name)
            if not canonical_id:
                print(f"⚠️ Could not get canonical ID for {company_name}, trying LLM fallback")
                return await self._llm_fallback_similar_companies(company_name)
            
            print(f"🔍 Canonical ID for {company_name}: {canonical_id}")
            
            # Search in CSV
            similar_companies = self._get_similar_from_csv(canonical_id)
            
            if similar_companies:
                return {
                    "success": True,
                    "expansion_type": "similar_companies",
                    "base_company": company_name,
                    "canonical_id": canonical_id,
                    "similar_companies": similar_companies,
                    "method": "csv_lookup",
                    "count": len(similar_companies)
                }
            else:
                print(f"⚠️ No similar companies found in CSV for {company_name}, trying LLM fallback")
                return await self._llm_fallback_similar_companies(company_name)
                    
        except Exception as e:
            logger.error(f"Similar company expansion failed: {e}")
            print(f"❌ CSV expansion failed, trying LLM fallback: {e}")
            return await self._llm_fallback_similar_companies(company_name)
    
    async def _llm_fallback_similar_companies(self, company_name: str) -> Dict[str, Any]:
        """LLM fallback for similar company expansion."""
        try:
            print(f"🤖 LLM fallback for similar companies to: {company_name}")
            
            # Import LLM tool
            from .llm_tools import LLMTool
            llm_tool = LLMTool("company_expansion_llm")
            
            prompt = f"""You are a business intelligence expert. Find 5-8 companies that are similar to "{company_name}" based on:
- Industry segment
- Business model  
- Company size/scale
- Geographic presence
- Target market

Company to analyze: {company_name}

Consider factors like:
- If it's a tech company, find similar tech companies
- If it's consulting, find similar consulting firms
- If it's automotive, find similar automotive companies
- If it's a startup, find similar-stage startups
- If it's an MNC, find similar MNCs
- If it's Indian, prioritize Indian companies but include global leaders too

Return ONLY valid JSON in this EXACT format:
{{
    "base_company": "{company_name}",
    "industry_segment": "brief industry description",
    "similar_companies": ["Company1", "Company2", "Company3", "Company4", "Company5"],
    "reasoning": "brief explanation of why these companies are similar"
}}

Focus on well-known companies that would be relevant for recruitment/talent search."""

            llm_result = await llm_tool._call_llm_direct(
                prompt=prompt,
                task="company_similarity_analysis"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result and llm_result["parsed_response"]:
                parsed = llm_result["parsed_response"]
                similar_companies = parsed.get("similar_companies", [])
                
                if similar_companies:
                    return {
                        "success": True,
                        "expansion_type": "similar_companies",
                        "base_company": company_name,
                        "similar_companies": similar_companies,
                        "industry_segment": parsed.get("industry_segment", "Unknown"),
                        "reasoning": parsed.get("reasoning", "LLM-based analysis"),
                        "method": "llm_fallback",
                        "count": len(similar_companies)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"LLM could not find similar companies for {company_name}"
                    }
            else:
                return {
                    "success": False,
                    "error": "LLM analysis failed to return valid results"
                }
                
        except Exception as e:
            logger.error(f"LLM fallback for company expansion failed: {e}")
            return {
                "success": False,
                "error": f"LLM fallback failed: {str(e)}"
            }
    
    async def _expand_company_group(self, group_name: str, **kwargs) -> Dict[str, Any]:
        """Expand predefined company groups with LLM fallback."""
        try:
            group_key = group_name.lower().replace(" ", "_")
            print(f"🏢 Expanding company group: {group_name} (key: {group_key})")
            
            if group_key in self.company_groups:
                group_data = self.company_groups[group_key]
                return {
                    "success": True,
                    "expansion_type": "company_group",
                    "group_name": group_name,
                    "description": group_data["description"],
                    "companies": group_data["companies"],
                    "method": "predefined_group",
                    "count": len(group_data["companies"])
                }
            else:
                # Try partial matching first
                matching_groups = [key for key in self.company_groups.keys() 
                                 if group_key in key or key in group_key]
                
                if matching_groups:
                    best_match = matching_groups[0]
                    group_data = self.company_groups[best_match]
                    return {
                        "success": True,
                        "expansion_type": "company_group",
                        "group_name": best_match.replace("_", " ").title(),
                        "description": group_data["description"],
                        "companies": group_data["companies"],
                        "method": "partial_match",
                        "count": len(group_data["companies"])
                    }
                else:
                    # LLM fallback for unknown groups
                    print(f"⚠️ Group '{group_name}' not found, trying LLM fallback")
                    return await self._llm_fallback_company_group(group_name)
                    
        except Exception as e:
            logger.error(f"Company group expansion failed: {e}")
            return await self._llm_fallback_company_group(group_name)
    
    async def _llm_fallback_company_group(self, group_name: str) -> Dict[str, Any]:
        """LLM fallback for company group expansion."""
        try:
            print(f"🤖 LLM fallback for company group: {group_name}")
            
            from .llm_tools import LLMTool
            llm_tool = LLMTool("company_group_llm")
            
            prompt = f"""You are a business intelligence expert. The user is asking for companies in the category: "{group_name}"

Interpret this request and provide 6-10 relevant companies. Consider categories like:
- Industry types (fintech, healthtech, edtech, etc.)
- Company stages (unicorns, startups, established, etc.) 
- Geographic focus (Indian companies, global companies, etc.)
- Business models (SaaS, consulting, manufacturing, etc.)
- Size categories (Fortune 500, mid-cap, large-cap, etc.)

Category requested: {group_name}

Return ONLY valid JSON in this EXACT format:
{{
    "group_name": "{group_name}",
    "interpreted_category": "your interpretation of what they're looking for",
    "companies": ["Company1", "Company2", "Company3", "Company4", "Company5", "Company6"],
    "reasoning": "brief explanation of the category and why these companies fit"
}}

Focus on well-known companies that would be relevant for recruitment/talent search."""

            llm_result = await llm_tool._call_llm_direct(
                prompt=prompt,
                task="company_group_analysis"
            )
            
            if llm_result["success"] and "parsed_response" in llm_result and llm_result["parsed_response"]:
                parsed = llm_result["parsed_response"]
                companies = parsed.get("companies", [])
                
                if companies:
                    return {
                        "success": True,
                        "expansion_type": "company_group",
                        "group_name": group_name,
                        "description": parsed.get("interpreted_category", "LLM-interpreted category"),
                        "companies": companies,
                        "reasoning": parsed.get("reasoning", "LLM-based analysis"),
                        "method": "llm_fallback",
                        "count": len(companies)
                    }
                else:
                    available_groups = list(self.company_groups.keys())
                    return {
                        "success": False,
                        "error": f"Could not interpret company group '{group_name}'",
                        "available_groups": available_groups
                    }
            else:
                available_groups = list(self.company_groups.keys())
                return {
                    "success": False,
                    "error": f"LLM could not process company group '{group_name}'",
                    "available_groups": available_groups
                }
                
        except Exception as e:
            logger.error(f"LLM fallback for company group failed: {e}")
            available_groups = list(self.company_groups.keys())
            return {
                "success": False,
                "error": f"LLM fallback failed: {str(e)}",
                "available_groups": available_groups
            }
    
    async def _expand_recruiter_similar(self, recruiter_company: str, **kwargs) -> Dict[str, Any]:
        """Expand similar companies for recruiter's company."""
        try:
            print(f"🏢 Expanding similar companies for recruiter company: {recruiter_company}")
            
            # Use the same logic as similar_companies
            result = await self._expand_similar_companies(recruiter_company)
            
            if result["success"]:
                result["expansion_type"] = "recruiter_similar"
                result["recruiter_company"] = recruiter_company
            
            return result
            
        except Exception as e:
            logger.error(f"Recruiter similar expansion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_similar_from_csv(self, canonical_id: str) -> List[str]:
        """Get similar companies from CSV data."""
        try:
            if self.company_df is None:
                print("⚠️ Company CSV not loaded")
                return []
            
            # Convert canonical_id to string for comparison
            canonical_id_str = str(canonical_id)
            
            # Find row with matching canonical_id
            matching_rows = self.company_df[self.company_df['canonical_id'].astype(str) == canonical_id_str]
            
            if matching_rows.empty:
                print(f"❌ No matching canonical_id found: {canonical_id_str}")
                return []
            
            # Get the first matching row
            row = matching_rows.iloc[0]
            
            # Extract similar companies
            similar_companies_str = row.get('clean_similar_companies', '')
            
            if pd.isna(similar_companies_str) or similar_companies_str == '':
                print(f"❌ No similar companies found for canonical_id: {canonical_id_str}")
                return []
            
            # Parse similar companies (assuming comma-separated)
            similar_companies = [company.strip() for company in similar_companies_str.split(',') 
                               if company.strip()]
            
            print(f"✅ Found {len(similar_companies)} similar companies for {canonical_id_str}")
            return similar_companies
            
        except Exception as e:
            print(f"❌ Error getting similar companies from CSV: {e}")
            logger.error(f"Error getting similar companies from CSV: {e}")
            return []
    
    def get_available_groups(self) -> Dict[str, str]:
        """Get all available company groups."""
        return {key.replace("_", " ").title(): data["description"] 
                for key, data in self.company_groups.items()}
    
    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded CSV."""
        if self.company_df is None:
            return {"loaded": False, "error": "CSV not loaded"}
        
        return {
            "loaded": True,
            "total_companies": len(self.company_df),
            "companies_with_similar": len(self.company_df[self.company_df['clean_similar_companies'].notna()]),
            "csv_path": self.csv_path
        }
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get comprehensive tool statistics."""
        csv_stats = self.get_csv_stats()
        
        return {
            "csv_status": csv_stats,
            "predefined_groups": len(self.company_groups),
            "available_groups": list(self.company_groups.keys()),
            "total_predefined_companies": sum(len(group["companies"]) for group in self.company_groups.values()),
            "fallback_methods": ["csv_lookup", "llm_fallback", "predefined_group", "partial_match"],
            "expansion_types": ["similar_companies", "company_group", "recruiter_similar"]
        }