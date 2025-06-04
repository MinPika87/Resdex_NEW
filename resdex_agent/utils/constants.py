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


# Tech Skills
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
    "Requirement Analysis", "Technical Specification", "System Design", "Ar chitecture Design"
]

# Cities
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
    # State Capitals & Important Administrative Centers
    "Shimla", "Gangtok", "Aizawl", "Shillong", "Kohima", "Imphal", "Agartala", "Dispur",
    "Panaji", "Silvassa", "Daman", "Kavaratti", "Port Blair", "Puducherry",
    # Major Business & IT Hubs
    "Noida", "Greater Noida", "Gurgaon", "Faridabad", "Electronic City", "Whitefield",
    "Hinjewadi", "Magarpatta", "Baner", "Viman Nagar", "Koramangala", "Indiranagar",
    "HSR Layout", "BTM Layout", "Marathahalli", "Sarjapur", "Bellandur", "Kondapur",
    "Gachibowli", "Kukatpally", "Jubilee Hills", "Banjara Hills", "Ameerpet", "Secunderabad",
    "Dilsukhnagar", "Manikonda", "Financial District", "Nizampet", "Miyapur",
    # Tier 3 Cities & District Headquarters
    "Siliguri", "Rourkela", "Nanded", "Kolhapur", "Ajmer", "Akola", "Gulbarga", "Jamnagar",
    "Ujjain", "Loni", "Sikar", "Jhansi", "Ulhasnagar", "Jammu", "Sangli-Miraj & Kupwad",
    "Mangalore", "Erode", "Belgaum", "Ambattur", "Tirunelveli", "Malegaon", "Gaya",
    "Jalgaon", "Udaipur", "Maheshtala", "Davanagere", "Kozhikode", "Kurnool", "Rajpur Sonarpur",
    "Rajahmundry", "Bokaro", "South Dumdum", "Bellary", "Patiala", "Gopalpur", "Agartala",
    "Bhagalpur", "Muzaffarnagar", "Bhatpara", "Panihati", "Latur", "Dhule", "Rohtak",
    "Korba", "Bhilwara", "Berhampur", "Muzaffarpur", "Ahmednagar", "Mathura", "Kollam",
    "Avadi", "Kadapa", "Kamarhati", "Sambalpur", "Bilaspur", "Shahjahanpur", "Satara",
    "Bijapur", "Rampur", "Shivamogga", "Chandrapur", "Junagadh", "Thrissur", "Alwar",
    "Bardhaman", "Kulti", "Kakinada", "Nizamabad", "Parbhani", "Tumkur", "Khammam",
    "Ozhukarai", "Bihar Sharif", "Panipat", "Darbhanga", "Bally", "Aizawl", "Dewas",
    "Ichalkaranji", "Karnal", "Bathinda", "Jalna", "Eluru", "Kirari Suleman Nagar",
    "Barabanki", "Purnia", "Satna", "Mau", "Sonipat", "Farrukhabad", "Sagar", "Rourkela",
    "Durg", "Imphal", "Ratlam", "Hapur", "Arrah", "Anantapur", "Karimnagar", "Etawah",
    "Ambernath", "North Dumdum", "Bharatpur", "Begusarai", "New Delhi", "Gandhidham",
    "Baranagar", "Tiruvottiyur", "Puducherry", "Sikar", "Thoothukudi", "Rewa", "Mirzapur",
    "Raichur", "Pali", "Ramagundam", "Silchar", "Orai", "Tenali", "Jorhat", "Karaikudi",
    "Rishikesh", "Anand", "Batala", "Hospet", "Raiganj", "Sirsa", "Danapur", "Serampore",
    # Emerging IT & Business Cities
    "Thiruvananthapuram", "Kottayam", "Thrissur", "Palakkad", "Kozhikode", "Kannur",
    "Kollam", "Alappuzha", "Malappuram", "Kasaragod", "Pathanamthitta", "Idukki",
    "Ernakulam", "Wayanad", "Tirupati", "Chittoor", "Nellore", "Prakasam", "Krishna",
    "West Godavari", "East Godavari", "Visakhapatnam", "Vizianagaram", "Srikakulam",
    "Medak", "Rangareddy", "Mahbubnagar", "Nalgonda", "Warangal", "Karimnagar",
    "Adilabad", "Nizamabad", "Khammam", "Nanded", "Hingoli", "Parbhani", "Jalna",
    "Beed", "Latur", "Osmanabad", "Solapur", "Satara", "Sangli", "Kolhapur", "Sindhudurg",
    "Ratnagiri", "Raigad", "Pune", "Ahmednagar", "Nashik", "Dhule", "Nandurbar",
    "Jalgaon", "Buldhana", "Akola", "Washim", "Amravati", "Wardha", "Nagpur", "Bhandara",
    "Gondia", "Chandrapur", "Gadchiroli", "Yavatmal",
    # Satellite Towns & Suburbs
    "Yelahanka", "Hebbal", "Rajajinagar", "Jayanagar", "Malleshwaram", "Basavanagudi",
    "Shivajinagar", "Commercial Street", "Brigade Road", "MG Road Bangalore",
    "Cunningham Road", "Richmond Road", "Residency Road", "Infantry Road",
    "Vasant Kunj", "Dwarka", "Rohini", "Janakpuri", "Lajpat Nagar", "Karol Bagh",
    "Connaught Place", "Khan Market", "Saket", "Nehru Place", "Laxmi Nagar",
    "Andheri", "Bandra", "Juhu", "Powai", "Goregaon", "Malad", "Borivali", "Kandivali",
    "Dahisar", "Mira Road", "Bhayander", "Virar", "Nalasopara", "Vasai",
    "Madhapur", "Miyapur", "Bachupally", "Kompally", "Alwal", "Trimulgherry",
    "Sainikpuri", "Moosapet", "Balanagar", "Quthbullapur", "Medchal", "Shamirpet"
]
# API Headers and configurations (from your constants.py)
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

# API Cookies (from your constants.py)
API_COOKIES: Dict[str, Dict[str, str]] = {
    "search": {'_t_ds': '4650858271171281-1641533823-1641533823-1641533823'},
    "user_details": {'_t_ds': '134455811095415731-1632467630-1632467630-1632467630'}
}

# Base API request template (from your constants.py)
BASE_API_REQUEST: Dict[str, Any] = {
    "transactionId": "resdex-agent::search-request",
    "city": [],
    "premium": False,
    "anyKeywords": [],
    "allKeywords": [],
    "excludeKeywords": [],
    "gender": "n",
    "appname": "resdex",
    "sort_by": "RELEVANCE",
    "min_exp": "-1",
    "max_exp": "-1",
    "min_ctc": "0",
    "max_ctc": "100",
    "days_old": "365",
    "SEARCH_OFFSET": 0,
    "SEARCH_COUNT": 50,
    "PAGE_LIMIT": "40",
    "recruiter_id": 3922808,
    "company_id": 238592
}

# Active period mapping
ACTIVE_PERIOD_MAPPING: Dict[str, str] = {
    "1 day": "1",
    "15 days": "15",
    "1 month": "30",
    "2 months": "60",
    "3 months": "90",
    "6 months": "180",
    "1 year": "365"
}