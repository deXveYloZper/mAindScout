# app/prompts/job_prompts.py

TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT = r"""
You are an expert technical recruiter specializing in the tech industry. Your task is to extract key information from the job description text and output it in a structured JSON format according to the schema provided.

**Schema:**

\{
  "title": "str (required)",
  "company_name": "str or null",
  "company_description": "str or null",
  "company_industry_focus": ["str", "str", ...] or null,
  "company_collaborations": ["str", "str", ...] or null,
  "location": "str or null",
  "employment_type": "str or null (e.g., 'Full-time', 'Part-time', 'Contract', 'Remote', 'Contractor')",
  "description": "str (required)",
  "responsibilities": ["str", "str", ...],
  "must_have_skills": ["str", "str", ...],
  "good_to_have_skills": ["str", "str", ...],
  "technologies_and_protocols": ["str", "str", ...],
  "experience_level": "str (e.g., 'Entry-level', 'Mid-level', 'Senior-level')",
  "experience_years": "str or null (e.g., '5+ years', 'At least 3 years')",
  "qualifications": ["str", "str", ...],
  "education_level": "str or null",
  "salary_and_benefits": "str or null",
  "additional_requirements": "str or null",
  "application_instructions": "str or null",
  "posting_date": "YYYY-MM-DD or null",
  "closing_date": "YYYY-MM-DD or null",
  "industry": "str or null (should be 'Technology' for tech jobs)"
\}

**Instructions:**

1. **Thorough Analysis**: Carefully read the job description text and extract relevant information based on the schema.

2. **Specific Details**:
   - **Company Information**: Extract details about the company's description, industry focus, and collaborations.
   - **Skills and Qualifications**:
     - Distinguish between **must-have skills** and **good-to-have skills**.
     - Include specific technologies, programming languages, frameworks, and protocols mentioned.
   - **Experience**:
     - Capture both the experience level and specific years of experience required.
   - **Employment Details**:
     - Note specifics about employment type, contractor status, remote work, and any implications.
   - **Salary and Benefits**: Extract all relevant information, including paid time off, sick days, holidays, and instructions about salary requests.
   - **Application Instructions**: Any special instructions for applicants.

3. **Schema Adherence**: Ensure the output strictly follows the JSON schema provided. If a field is not present in the text, set its value to `null` or an empty list as appropriate.

4. **Data Formatting**:
   - Dates should be in `YYYY-MM-DD` format.
   - Normalize the `experience_level` to one of: "entry-level", "mid-level", or "senior-level".
   - Normalize skills and other list items to be consistent (e.g., 'Rust', 'Web3', 'Blockchain', 'Team Management').
   - For the `industry` field, use `"Technology"`.

5. **Output**: Provide only the JSON output without any additional commentary.

**Job Description Text:**

[JOB_DESCRIPTION_TEXT]
"""
