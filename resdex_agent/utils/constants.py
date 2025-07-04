# Replace resdex_agent/utils/constants.py with this fixed version
# The key changes are in BASE_API_REQUEST and ACTIVE_PERIOD_MAPPING

"""
Constants and enums used throughout the ResDex Agent system.
"""

from enum import Enum
from typing import List, Dict, Any


class IntentType(Enum):
    """Types of user intents the agent can handle."""
    SEARCH_MODIFICATION = "search_modification"
    SKILL_EXPANSION = "skill_expansion"
    QUERY_REFINEMENT = "query_refinement"
    EXPLAINABILITY = "explainability"
    GENERAL_QUERY = "general_query"


class ModificationType(Enum):
    """Types of filter modifications."""
    SKILL_ADDED = "skill_added"
    SKILL_REMOVED = "skill_removed"
    SKILL_MADE_MANDATORY = "skill_made_mandatory"
    SKILL_MADE_OPTIONAL = "skill_made_optional"
    EXPERIENCE_MODIFIED = "experience_modified"
    SALARY_MODIFIED = "salary_modified"
    LOCATION_ADDED = "location_added"
    LOCATION_REMOVED = "location_removed"
    ACTIVE_PERIOD_MODIFIED = "active_period_modified"
    TARGET_COMPANY_ADDED = "target_company_added"
    TARGET_COMPANY_REMOVED = "target_company_removed"


TECH_SKILLS: List[str] = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "Ruby", "PHP", "Swift", 
    "Kotlin", "Go", "Rust", "Scala", "R", "MATLAB", "Perl", "Lua", "Dart", "Objective-C",
    "Assembly", "COBOL", "Fortran", "Pascal", "Ada", "Haskell", "Erlang", "Elixir", "Clojure",
    "F#", "VB.NET", "PowerShell", "Bash", "Shell Scripting", "Groovy", "Julia", "Crystal",
    "Nim", "Zig", "V", "Carbon", "Mojo", "OCaml", "Scheme", "Racket", "Prolog", "Solidity",
    # Frontend Technologies
    "React", "Angular", "Vue.js", "Svelte", "Next.js", "Nuxt.js", "Gatsby", "Ember.js",
    "Backbone.js", "jQuery", "Alpine.js", "Lit", "Stencil", "Preact", "Solid.js", "Qwik",
    "HTML", "HTML5", "CSS", "CSS3", "SCSS", "SASS", "Less", "Stylus", "PostCSS",
    "Bootstrap", "Tailwind CSS", "Material-UI", "Ant Design", "Chakra UI", "Semantic UI",
    "Foundation", "Bulma", "UIKit", "Pure CSS", "Materialize", "Skeleton",
    "Webpack", "Vite", "Parcel", "Rollup", "Browserify", "ESBuild", "Snowpack",
    "Babel", "ESLint", "Prettier", "JSHint", "TSLint", "Stylelint",
    # Backend Technologies
    "Node.js", "Express.js", "Koa.js", "Fastify", "NestJS", "Hapi.js", "Sails.js",
    "Django", "Flask", "FastAPI", "Tornado", "Pyramid", "CherryPy", "Bottle",
    "Spring Boot", "Spring Framework", "Spring MVC", "Spring Security", "Hibernate",
    "Struts", "JSF", "Play Framework", "Vert.x", "Micronaut", "Quarkus",
    "Ruby on Rails", "Sinatra", "Hanami", "Grape", "Roda", "Padrino",
    "Laravel", "Symfony", "CodeIgniter", "CakePHP", "Zend", "Phalcon", "Yii",
    "ASP.NET", "ASP.NET Core", ".NET Framework", ".NET 6", ".NET 7", "Entity Framework",
    "Gin", "Echo", "Fiber", "Beego", "Revel", "Buffalo",
    # Mobile Development
    "React Native", "Flutter", "Xamarin", "Ionic", "Cordova", "PhoneGap", "NativeScript",
    "Android Development", "iOS Development", "SwiftUI", "UIKit", "Android Studio",
    "Xcode", "Jetpack Compose", "Android SDK", "iOS SDK", "Core Data", "Realm",
    "Expo", "Metro", "Flipper", "Detox", "Appium", "Espresso", "XCTest",
    # Databases
    "MySQL", "PostgreSQL", "SQLite", "Oracle", "SQL Server", "MariaDB", "IBM DB2",
    "MongoDB", "CouchDB", "Amazon DynamoDB", "Cassandra", "HBase", "Neo4j", "ArangoDB",
    "Redis", "Memcached", "Elasticsearch", "Solr", "InfluxDB", "TimescaleDB",
    "Firebase Firestore", "Supabase", "PlanetScale", "Neon", "Cockroach DB", "FaunaDB",
    "GraphQL", "Apollo GraphQL", "Prisma", "TypeORM", "Sequelize", "Mongoose", "Knex.js",
    "SQL", "NoSQL", "ACID", "CAP Theorem", "Database Design", "Data Modeling",
    # Cloud & DevOps
    "AWS", "Azure", "Google Cloud Platform", "GCP", "DigitalOcean", "Linode", "Vultr",
    "Amazon EC2", "AWS Lambda", "AWS S3", "AWS RDS", "AWS CloudFormation", "AWS ECS",
    "Azure Functions", "Azure SQL", "Azure Storage", "Azure DevOps", "Azure Kubernetes",
    "Google Compute Engine", "Google Cloud Functions", "Google Cloud Storage", "BigQuery",
    "Docker", "Kubernetes", "Docker Compose", "Docker Swarm", "Podman", "containerd",
    "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI", "Azure Pipelines",
    "Terraform", "Ansible", "Chef", "Puppet", "CloudFormation", "Pulumi", "CDK",
    "Nginx", "Apache", "IIS", "HAProxy", "Traefik", "Envoy", "Kong", "Istio",
    "Monitoring", "Prometheus", "Grafana", "ELK Stack", "Splunk", "New Relic", "Datadog",
    # AI/ML & Data Science
    "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP", "Computer Vision",
    "Data Science", "Data Analysis", "Statistical Analysis", "Predictive Analytics",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM", "CatBoost",
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh",
    "Jupyter", "Google Colab", "Anaconda", "Spyder", "RStudio", "Tableau", "Power BI",
    "Apache Spark", "MLflow", "Kubeflow", "Apache Airflow", "Prefect", "Dagster",
    "OpenCV", "NLTK", "spaCy", "Transformers", "Hugging Face", "LangChain", "OpenAI API",
    "GPT", "BERT", "T5", "CLIP", "DALL-E", "Stable Diffusion", "ChatGPT", "LLM",
    "Reinforcement Learning", "Neural Networks", "CNN", "RNN", "LSTM", "GAN", "VAE",
    # Big Data & Analytics
    "Big Data", "Hadoop", "Apache Spark", "Hive", "HBase", "HDFS", "MapReduce",
    "Kafka", "Apache Storm", "Apache Flink", "Apache Beam", "Apache NiFi",
    "ETL", "Data Pipeline", "Data Warehousing", "Data Lake", "Delta Lake",
    "Snowflake", "Databricks", "Amazon Redshift", "Google BigQuery", "Azure Synapse",
    "Apache Iceberg", "Apache Hudi", "Dremio", "Presto", "Trino", "ClickHouse",
    # Testing & Quality Assurance
    "Unit Testing", "Integration Testing", "End-to-End Testing", "Performance Testing",
    "Security Testing", "API Testing", "Mobile Testing", "Cross-browser Testing",
    "Jest", "Mocha", "Chai", "Jasmine", "Karma", "Protractor", "Cypress", "Playwright",
    "Selenium", "WebDriver", "TestNG", "JUnit", "Mockito", "WireMock", "Postman",
    "JMeter", "LoadRunner", "K6", "Artillery", "Gatling", "OWASP ZAP", "Burp Suite",
    "TestRail", "Zephyr", "Allure", "TestComplete", "Ranorex", "UFT", "Appium",
    # Version Control & Collaboration
    "Git", "GitHub", "GitLab", "Bitbucket", "Azure DevOps", "SVN", "Mercurial",
    "Git Flow", "GitHub Flow", "Feature Branching", "Pull Requests", "Code Review",
    "CI/CD", "Continuous Integration", "Continuous Deployment", "DevOps",
    # Project Management & Methodologies
    "Agile", "Scrum", "Kanban", "Lean", "Waterfall", "SAFe", "DevOps", "XP",
    "Jira", "Confluence", "Trello", "Asana", "Monday.com", "ClickUp", "Notion",
    "Slack", "Microsoft Teams", "Discord", "Zoom", "Google Workspace", "Office 365",
    # Security & Networking
    "Cybersecurity", "Information Security", "Network Security", "Web Security",
    "OAuth", "JWT", "SSL/TLS", "PKI", "Encryption", "Hashing", "Digital Signatures",
    "Penetration Testing", "Vulnerability Assessment", "SIEM", "SOC", "Incident Response",
    "Firewall", "VPN", "IDS/IPS", "WAF", "DDoS Protection", "Zero Trust", "SASE",
    "TCP/IP", "HTTP/HTTPS", "DNS", "DHCP", "BGP", "OSPF", "VLAN", "MPLS",
    "Network Administration", "System Administration", "Linux Administration",
    # Emerging Technologies
    "Blockchain", "Web3", "Smart Contracts", "DeFi", "NFT", "Cryptocurrency",
    "Ethereum", "Bitcoin", "Polygon", "Solana", "Chainlink", "IPFS", "MetaMask",
    "Internet of Things", "IoT", "Edge Computing", "5G", "AR/VR", "Metaverse",
    "Quantum Computing", "Quantum Algorithms", "Quantum Cryptography",
    "Robotics", "ROS", "Automation", "Process Automation", "RPA", "UiPath",
    # Design & UX/UI
    "UI/UX Design", "User Experience", "User Interface", "Product Design", "Interaction Design",
    "Figma", "Sketch", "Adobe XD", "InVision", "Zeplin", "Marvel", "Principle",
    "Adobe Creative Suite", "Photoshop", "Illustrator", "After Effects", "Premiere Pro",
    "Wireframing", "Prototyping", "User Research", "Usability Testing", "A/B Testing",
    "Design Systems", "Atomic Design", "Material Design", "Human Interface Guidelines",
    # E-commerce & CMS
    "Shopify", "WooCommerce", "Magento", "BigCommerce", "Salesforce Commerce",
    "WordPress", "Drupal", "Joomla", "Contentful", "Strapi", "Sanity", "Ghost",
    "Headless CMS", "JAMstack", "Static Site Generators", "Gatsby", "Next.js", "Nuxt.js",    
    # Enterprise Technologies
    "Salesforce", "SAP", "Oracle ERP", "Microsoft Dynamics", "ServiceNow", "Workday",
    "SharePoint", "Power Platform", "PowerApps", "Power Automate", "Power BI",
    "Tableau", "QlikView", "MicroStrategy", "Looker", "Domo", "Sisense",
    # Game Development
    "Unity", "Unreal Engine", "Godot", "GameMaker Studio", "Construct 3", "Defold",
    "C# for Unity", "C++ for Unreal", "GDScript", "Lua Scripting", "HLSL", "GLSL",
    "2D Game Development", "3D Game Development", "Mobile Game Development",
    "AR/VR Game Development", "Game Physics", "Game AI", "Multiplayer Networking",
    # Other Important Skills
    "API Development", "REST API", "GraphQL", "gRPC", "WebSockets", "Socket.io",
    "Microservices", "Serverless", "Event-Driven Architecture", "Domain-Driven Design",
    "Clean Code", "SOLID Principles", "Design Patterns", "Software Architecture",
    "Performance Optimization", "Scalability", "Load Balancing", "Caching",
    "Technical Writing", "Documentation", "Code Documentation", "API Documentation",
    "Open Source", "Community Management", "Technical Leadership", "Mentoring",
    # Industry-Specific Skills
    "FinTech", "HealthTech", "EdTech", "E-commerce", "Gaming", "Media & Entertainment",
    "Automotive", "Aerospace", "Manufacturing", "Supply Chain", "Logistics",
    "Real Estate Tech", "Legal Tech", "InsurTech", "AgriTech", "CleanTech",
    # Soft Skills (Technical Context)
    "Problem Solving", "Critical Thinking", "Analytical Skills", "Communication",
    "Team Leadership", "Technical Leadership", "Cross-functional Collaboration",
    "Requirement Analysis", "Technical Specification", "System Design", "Architecture Design"
]

CITIES: List[str] = [
    # Tier 1 Cities (Major Metro Cities)
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad",
    # Tier 2 Cities (Major State Capitals & Important Cities)
    "Jaipur", "Surat", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
    "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara", "Ghaziabad", "Ludhiana",
    "Agra", "Nashik", "Faridabad", "Meerut", "Rajkot", "Kalyan-Dombivali", "Vasai-Virar",
    "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai", "Allahabad",
    "Ranchi", "Howrah", "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur",
    "Madurai", "Raipur", "Kota", "Guwahati", "Chandigarh", "Solapur", "Hubli-Dharwad",
    "Tiruchirappalli", "Bareilly", "Mysore", "Tiruppur", "Gurgaon", "Aligarh", "Jalandhar",
    "Bhubaneswar", "Salem", "Mira-Bhayandar", "Warangal", "Guntur", "Bhiwandi", "Saharanpur",
    "Gorakhpur", "Bikaner", "Amravati", "Noida", "Jamshedpur", "Bhilai", "Cuttack",
    "Firozabad", "Kochi", "Nellore", "Bhavnagar", "Dehradun", "Durgapur", "Asansol",
    # Additional cities...
    "New Delhi", "Gurgaon", "Noida", "Greater Noida", "Faridabad", "Electronic City", 
    "Whitefield", "Hinjewadi", "Magarpatta", "Baner", "Viman Nagar", "Koramangala", 
    "Indiranagar", "HSR Layout", "BTM Layout", "Marathahalli", "Sarjapur", "Bellandur"
]

# API Headers and configurations (from your working version)
API_HEADERS: Dict[str, Dict[str, str]] = {
    "search": {
        'AppId': '1',
        'SystemId': '2',
        'Content-Type': 'application/json',
        'X-Application-Select': 'naukri-resdexsearch-services-v0',
        'X-TRANSACTION-ID': '1234'
    },
    "user_details": {
        'X-TRANSACTION-ID': 'search123',
        'AppId': '123',
        'SystemId': 'search_data',
        'Content-Type': 'application/json'
    },
    "location": {
        'AppId': '1',
        'SystemId': '2',
        'Content-Type': 'application/json'
    }
}

# API Cookies (from your working version)
API_COOKIES: Dict[str, Dict[str, str]] = {
    "search": {'_t_ds': '4650858271171281-1641533823-1641533823-1641533823'},
    "user_details": {'_t_ds': '134455811095415731-1632467630-1632467630-1632467630'}
}

# CRITICAL FIX: Base API request template (using working version format)
null=None
true=True
false=False
BASE_API_REQUEST: Dict[str, Any] = {
    "sid": None,
    "ctc_Type": "rs",
    "company_id": 238592,  # Keep your existing company_id
    "comnotGroupId": "4634501",  # Keep your existing value
    "recruiter_id": 3922808,  # Keep your existing recruiter_id
    "preference_key": "3256ce65-2c16-48a6-b233-4b09ca76e34e",  # Keep your existing
    "user_ids": None,
    "search_flag": "adv",
    "unique_id": None,
    "ez_keyword_any": [],
    "anyKeywords": [],
    "ez_keyword_all": [],
    "allKeywords": [],
    "ez_keyword_exclude": [],
    "excludeKeywords": [],
    "inc_keyword": "",
    "incKeywords": "",
    "key_type": "ezkw",
    "swr_key": None,
    "swr_exclude_key": None,
    "swr_type": "bool",
    "srch_key_in": "ER",
    "it_params": {
        "operator": "OR",
        "fullSearchFlag": 0,
        "skills": None,
        "enableTaxonomy": True
    },
    "min_exp": "-1",
    "max_exp": "-1",
    "min_ctc": "0",
    "max_ctc": "100",
    "ctc_type": "rs",
    "CTC_Type": "rs",
    "dollarRate": 60,
    "dollar_rate": 60,
    "zero_ctc_search": False,
    "city": [],
    "currentStateId": [],
    "OCity": "",
    "pref_loc": [],
    "preferredStateId": [],
    "loc_city_only": 0,
    "location_op": "or",
    "farea_roles": [],
    "indtype": [],
    "excludeIndtype": [],
    "emp_key": "",
    "emp_type": "ezkw",
    "srch_emp_in": "C",
    "exemp_key": "",
    "exemp_type": "ezkw",
    "srch_exemp_in": "C",
    "desig_key_entity": None,
    "desig_key": None,
    "desig_type": "ezkw",
    "srch_des_in": "C",
    "noticePeriodArr": [0],
    "notice_period": [0],
    "ugcourse": [],
    "ug_year_range": [-1, -1],
    "uginst_key": "",
    "uginst_id_key_map": {},
    "uginst_type": "all",
    "ug_edu_type": [0],
    "pgcourse": [],
    "pg_year_range": [-1, -1],
    "pginst_key": "",
    "pginst_id_key_map": {},
    "pginst_type": "all",
    "pg_edu_type": [0],
    "ppgcourse": [],
    "ppg_year_range": [-1, -1],
    "ppginst_key": "",
    "ppginst_id_key_map": {},
    "ppginst_type": "all",
    "ppg_edu_type": [0],
    "ug_pg_type": "and",
    "pg_ppg_type": "and",
    "caste_id": [],
    "gender": "n",
    "dis_type": False,
    "candidate_age_range": [-1, -1],
    "wstatus_usa": [-1],
    "work_auth_others": [-1],
    "all_new": "ALL",
    "search_on_verified_numbers": False,
    "verified_email": False,
    "uploaded_cv": False,
    "search_on_job_type": "",
    "search_on_jobs_status_type": "",
    "premium": False,
    "featured_search": False,
    "PAGE_LIMIT": 40,
    "sort_by": "RELEVANCE",
    "isMakeSenseSrch": 1,
    "days_old": 3650,
    "hiring_for": None,
    "hiring_for_search_type": "bool",
    "fetch_clusters": {},
    "cluster_industry": None,
    "cluster_exclude_industry": None,
    "cluster_role": None,
    "kwMap": "n",
    "kw_map": "n",
    "ezSearch": "n",
    "SEARCH_OFFSET": 0,
    "SEARCH_COUNT": 80,
    "freeSearch": False,
    "subQuery": "",
    "uid": "madhesiyaaaaa::318611090120763389791::2711329165430845::15953068524754885928",
    "al_engine_ip": "rpcservices1.resdex.com",
    "al_engine_port": 9123,
    "makesense_url": "http://test.semantic.resdex.com/v1/restructureresdexquery",
    "makesense_timeout": 1000,
    "makesense_response_timeout": 1000,
    "appname": "resdex",
    "ctcclus_sel": ["0000", "5200"],
    "roles": "",
    "magicFlag": "0",
    "magic_flag": "0",
    "farea": [0],
    "any_keyword_srch_type": "bool",
    "x_xii_type": None,
    "immediatelyAvailable": False,
    "cluster_notice_period": None,
    "cluster_location": None,
    "date_range": None,
    "emp_key_globalid": {},
    "exemp_key_globalid": {},
    "verifiedSkillIds": None,
    "candidatesWithVerifiedSkills": None,
    "company_type": None,
    "expActive": True,
    "rerankEnabled": True,
    "excludeTestProfiles": False,
    "contests": None,
    "profileTags": None,
    "segmentEnabled": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "anyKeywordTags": "",
    "allKeywordTags": ""
}
"""
BASE_API_REQUEST: Dict[str, Any] = {
    "transactionId": "madhesiyaaaaa::318611090120763389791::2711329165430845::15953068524754885928",
    "city": [],
    "fields": None,
    "premium": False,
    "hlQuery": None,
    "anyKeywords": [],
    "allKeywords": [],
    "excludeKeywords": [],
    "subQuery": "",
    "gender": "n",
    "immediatelyAvailable": False,
    "exactSearchBoostOnAny": None,
    "exactSearchBoostOnAll": None,
    "exactSearchBoostOnInc": None,
    "operator1": None,
    "operator2": None,
    "performanceTimeMap": None,
    "fareaRoles": [],
    "ocity": "",
    "xthOrXIIType": False,
    "appname": "resdex",
    "freeSearch": False,
    "x_xii_type": False,
    "pref_loc": [],
    "loc_city_only": 0,
    "inc_keyword": "",
    "key_type": "ezkw",
    "sort_by": "RELEVANCE",
    "OCity": "",
    "unique_id": None,
    "notice_period": [0],
    "candidate_age_range": ["-1", "-1"],
    "wstatus_usa": [-1],
    "work_auth_others": [-1],
    "verified_email": False,
    "uploaded_cv": False,
    "search_on_verified_numbers": False,
    "featured_search": False,
    "days_old": "3650",
    "all_new": "ALL",
    "indtype": [],
    "excludeIndtype": [],
    "highlight_arr": None,
    "min_exp": "-1",
    "max_exp": "-1",
    "magic_flag": "0",
    "MMMSearch": False,
    "search_flag": "adv",
    "user_ids": None,
    "min_ctc": "0",      # FIXED: Changed from "53.99" to "0"
    "max_ctc": "100",    # FIXED: Changed from "53.99" to "100"
    "min_ctc_usd": None,
    "max_ctc_usd": None,
    "ctc_type": "rs",
    "dollar_rate": "60",
    "zero_ctc_search": False,
    "ctcclus_sel": ["0000", "5200"],
    "location_op": "and",
    "SEARCH_OFFSET": 0,
    "SEARCH_COUNT": 80,
    "recruiter_id": 3922808,
    "company_id": 238592,
    "emp_type":"ezkw",
    "emp_key": "Accenture",
    "emp_key_globalid": {"10476": "Accenture"},
    "PAGE_LIMIT": "40",
    "preference_key": "be246d94-4302-46d1-afd8-557b9e551cf7",#3256ce65-2c16-48a6-b233-4b09ca76e34e
    "verifiedSkillIds": None,
    "candidatesWithVerifiedSkills": False,
    "comnotGroupId": "4634501"
}"""

# CRITICAL FIX: Active period mapping (using working version that works with staging)
ACTIVE_PERIOD_MAPPING: Dict[str, str] = {
    "1 day": "3650",      # FIXED: All set to "3650" to match working version
    "15 days": "3650", 
    "1 month": "3650",
    "2 months": "3650",
    "3 months": "3650",
    "6 months": "3650",
    "1 year": "3650"
}
UI_CONFIG = {
    "pagination_size": 5,
    "max_candidates_fetch": 20,
    "batch_size_api": 100,
    "batch_size_db": 1000,
    "max_skills_display": 15,
    "max_may_know_skills": 10
}