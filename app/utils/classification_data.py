# app/utils/classification_data.py

# Classification data for job descriptions
JOB_CATEGORIES_KEYWORDS = {
    'Data Science': [
        'data scientist', 'machine learning', 'deep learning', 'artificial intelligence', 'ai', 'ml',
        'neural network', 'predictive modeling', 'data mining', 'natural language processing', 'nlp',
        'statistical analysis', 'data analysis', 'python', 'r programming', 'big data', 'data visualization',
        'TensorFlow', 'PyTorch', 'scikit-learn', 'data wrangling', 'A/B testing', 'experiment design',
        'data storytelling', 'data cleaning', 'feature engineering', 'model deployment', 'cloud computing',
        'aws', 'azure', 'google cloud', 'database management', 'sql', 'nosql'
    ],
    'Software Development': [
        'software engineer', 'developer', 'programmer', 'software developer', 'coding',
        'programming', 'application development', 'software design', 'full stack', 'frontend',
        'backend', 'web development', 'mobile development', 'java', 'c++', 'c#', 'javascript', 'php',
        'ruby', 'golang', 'scala', 'perl', 'software architecture', 'api development', 'RESTful APIs', 
        'microservices', 'Git', 'Agile development', 'Scrum', 'Kanban', 'testing', 'debugging',
        'problem-solving', 'communication', 'collaboration', 'cloud computing', 'aws', 'azure', 'google cloud'
    ],
    'Project Management': [
        'project manager', 'scrum master', 'agile', 'project coordination', 'project planning',
        'project execution', 'pmp', 'prince2', 'project delivery', 'stakeholder management',
        'risk management', 'project scheduling', 'budget management', 'program management', 
        'project leadership', 'Agile methodologies', 'waterfall', 'communication', 'leadership',
        'problem-solving', 'time management', 'organization', 'Jira', 'Asana', 'Trello'
    ],
    'DevOps': [
        'devops', 'continuous integration', 'continuous deployment', 'ci/cd', 'infrastructure as code',
        'automation', 'jenkins', 'docker', 'kubernetes', 'ansible', 'terraform', 'cloud infrastructure',
        'monitoring', 'aws', 'azure', 'google cloud', 'cloud services', 'linux', ' scripting',
        'python', 'bash', 'git', 'version control', 'security', 'networking', 'problem-solving'
    ],
    'Quality Assurance': [
        'qa engineer', 'quality assurance', 'software tester', 'testing', 'test automation',
        'selenium', 'defect tracking', 'quality control', 'test cases', 'bug tracking',
        'manual testing', 'performance testing', 'regression testing', 'API testing', 'mobile testing',
        'web testing', 'test planning', 'test strategy', 'communication', 'collaboration', 'detail-oriented'
    ],
    'Cybersecurity': [
        'cybersecurity', 'information security', 'network security', 'security analyst',
        'penetration testing', 'ethical hacking', 'security protocols', 'firewall', 'encryption',
        'incident response', 'vulnerability assessment', 'security compliance', 'security architecture',
        'threat modeling', 'security auditing', 'ISO 27001', 'NIST Cybersecurity Framework', 'SIEM',
        'SOC', 'malware analysis', 'forensics', 'risk management', 'cloud security'
    ],
    'Database Administration': [
        'database administrator', 'dba', 'database management', 'sql', 'nosql', 'database design',
        'data warehousing', 'oracle', 'mysql', 'postgresql', 'mongodb', 'database performance tuning',
        'backup and recovery', 'data modeling', 'ETL', 'data integration', 'cloud databases',
        'AWS RDS', 'Azure SQL', 'Google Cloud SQL', 'database security', 'performance monitoring',
        'troubleshooting', 'query optimization'
    ],
    'Network Engineering': [
        'network engineer', 'networking', 'lan', 'wan', 'network protocols', 'routing', 'switching',
        'network infrastructure', 'cisco', 'network architecture', 'vpn', 'firewalls', 'network security',
        'wireless networks', 'network troubleshooting', 'TCP/IP', 'DNS', 'DHCP', 'VLAN', 'cloud networking',
        'network automation', 'security protocols', 'firewalls', 'intrusion detection systems'
    ],
    'Business Analysis': [
        'business analyst', 'requirements gathering', 'process improvement', 'stakeholder management',
        'business process modeling', 'user stories', 'gap analysis', 'business requirements',
        'functional specifications', 'system analysis', 'data analysis', 'use cases', 'agile',
        'scrum', 'communication', 'problem-solving', 'analytical thinking', 'documentation', 'UML',
        'BPMN', 'Jira', 'Confluence'
    ],
    'UX/UI Design': [
        'ux designer', 'ui designer', 'user experience', 'user interface', 'wireframing',
        'prototyping', 'usability testing', 'visual design', 'interaction design', 'adobe xd', 'figma',
        'sketch', 'adobe photoshop', 'adobe illustrator', 'responsive design', 'user research',
        'user-centered design', 'information architecture', 'accessibility', 'wireframes', 'mockups',
        'prototyping tools', 'user flows', 'design systems', 'HTML', 'CSS', 'JavaScript'
    ],
    'Technical Support': [
        'technical support', 'help desk', 'support engineer', 'troubleshooting', 'customer support',
        'ticketing systems', 'it support', 'service desk', 'hardware support', 'software support',
        'remote support', 'technical assistance', 'communication', 'problem-solving', 'patience',
        'active listening', 'windows', 'macOS', 'linux', 'networking', ' troubleshooting tools'
    ],
    'Product Management': [
        'product manager', 'product strategy', 'roadmap', 'product lifecycle', 'market analysis',
        'product development', 'user feedback', 'product vision', 'competitive analysis',
        'go-to-market strategy', 'product marketing', 'feature prioritization', 'agile', 'scrum',
        'communication', 'leadership', 'data analysis', 'user research', 'A/B testing', 'roadmapping tools',
        'Jira', 'Aha!', 'ProductPlan'
    ],
    'Data Engineering': [
        'data engineer', 'data pipeline', 'etl', 'extract transform load', 'big data', 'hadoop',
        'spark', 'data modeling', 'data integration', 'data lakes', 'data warehouses',
        'apache kafka', 'cloud data platforms', 'aws', 'azure', 'google cloud', 'python', 'sql',
        'data warehousing', 'database design', 'data governance', 'data quality', 'big data technologies',
        'Hadoop', 'Spark', 'Hive', 'Pig', 'NoSQL databases'
    ],
    'Cloud Computing': [
        'cloud engineer', 'aws', 'azure', 'google cloud', 'cloud infrastructure', 'cloud services',
        'saas', 'paas', 'iaas', 'cloud deployment', 'cloud security', 'cloud architecture',
        'serverless computing', 'cloud migration', 'DevOps', 'automation', 'terraform', 'kubernetes',
        'docker', 'python', 'linux', 'windows server', 'cloud certifications', 'AWS Certified',
        'Azure Certified', 'Google Cloud Certified'
    ],
    'Artificial Intelligence': [
        'artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural networks',
        'computer vision', 'nlp', 'natural language processing', 'intelligent systems',
        'speech recognition', 'robotics', 'automation', 'python', 'r programming', 'tensorflow',
        'pytorch', 'data science', 'algorithms', 'mathematics', 'statistics', 'deep learning frameworks',
        'computer vision libraries', 'natural language processing libraries'
    ],
    'Mobile Development': [
        'mobile developer', 'ios developer', 'android developer', 'react native', 'swift',
        'kotlin', 'flutter', 'mobile apps', 'app store', 'mobile ux/ui', 'cross-platform development',
        'objective-c', 'mobile sdk', 'java', 'c++', 'javascript', 'api development', 'agile', 'scrum',
        'git', 'version control', 'ui design', 'ux design', 'mobile design patterns', 'testing', 'debugging'
    ],
    'IT Management': [
        'it manager', 'it director', 'information technology management', 'it strategy', 'team leadership',
        'it operations', 'budget management', 'vendor management', 'it governance', 'it policy',
        'compliance', 'resource allocation'
    ],
    'System Administration': [
        'system administrator', 'sysadmin', 'linux', 'windows server', 'system maintenance',
        'virtualization', 'vmware', 'system monitoring', 'backup and recovery', 'active directory',
        'shell scripting', 'system security', 'configuration management'
    ],
    'Embedded Systems': [
        'embedded engineer', 'firmware', 'microcontrollers', 'real-time operating systems', 'rtos',
        'hardware-software integration', 'c programming', 'embedded c', 'arduino', 'raspberry pi',
        'fpga', 'verilog', 'vhdl'
    ],
    'Sales Engineering': [
        'sales engineer', 'technical sales', 'pre-sales', 'post-sales', 'customer engagement',
        'solution selling', 'product demonstrations', 'technical presentations', 'client relationships'
    ],
    'Marketing': [
        'digital marketing', 'seo', 'content marketing', 'social media', 'marketing campaigns',
        'brand management', 'market research', 'email marketing', 'ppc', 'google analytics',
        'marketing strategy', 'advertising'
    ],
    'Human Resources': [
        'hr manager', 'recruitment', 'talent acquisition', 'employee relations', 'performance management',
        'training and development', 'hr policies', 'compensation and benefits', 'onboarding',
        'hr compliance'
    ],
    # Add more categories and keywords as needed
}

# Use the same categories for candidate profiles
CANDIDATE_CATEGORIES_KEYWORDS = JOB_CATEGORIES_KEYWORDS