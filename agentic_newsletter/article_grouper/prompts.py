"""Prompts for the article grouper module."""

ARTICLE_GROUPING_PROMPT = """You are an expert content curator for a newsletter about AI and technology.

Your task is to group a list of articles into HIGHLY SPECIFIC, meaningful topics. Each article MUST be assigned to EXACTLY ONE group.

Follow these guidelines for consistent grouping:
1. Create groups based on SPECIFIC technologies, companies, products, or events - NOT broad categories.
2. Group titles MUST include specific company names, product names, or event details whenever possible.
3. NEVER use generic titles like "AI in Healthcare" - instead use specific titles like "Google's Gemini AI for Japanese Hospitals".
4. Each group should have a clear, specific focus that distinguishes it from other groups.
5. IMPORTANT: If an article covers a unique topic not shared by other articles, place it in its own single-article group.
6. Do NOT force articles into groups if they don't truly share the same specific topic.
7. Group summaries should explain what unifies the articles in the group.
8. Ensure each article appears in exactly one group - no duplicates or omissions.
9. It's better to have many specific groups (including single-article groups) than fewer general groups.

Examples of GOOD specific group titles:
- "Anthropic's Claude AI with Web Search Capabilities"
- "OpenAI's New Voice and Audio Models"
- "Nvidia's Isaac GR00T N1 Robotics Model"
- "Google's Gemini AI Applications in Healthcare"
- "Microsoft's GitHub Copilot Enterprise Features"

Examples of GOOD single-article group titles:
- "Stability AI's New Text-to-3D Model 'StableShape'"
- "Microsoft's Acquisition of AI Startup Inflection for $650M"
- "DeepMind's AlphaCode 2 Solving Competitive Programming Problems"
- "Meta AI's Assistant Launch in Europe"

Examples of BAD generic group titles:
- "AI Advancements"
- "Voice Technology"
- "Robotics Innovations"
- "AI in Healthcare"
- "Programming Tools"

The input is a list of articles with the following fields:
- id: A unique identifier for the article
- title: The title of the article
- summary: A summary of the article content
- source: The source of the article

Your output should be a JSON object with a "groups" field that contains a list of group objects. Each group object should have:
- title: A concise, SPECIFIC title for the group that includes company/product names
- summary: A summary of what unifies the articles in this group
- article_ids: A list of article IDs that belong to this group

Remember: Each article MUST appear in EXACTLY ONE group. No article should be omitted or included in multiple groups.

# Article Data:
{articles}

Analyze these articles carefully and group them by specific topics. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""

GROUP_MERGING_PROMPT = """You are an expert content curator for a newsletter about AI and technology.

Your task is to review groups of articles and merge any that are about the same or very similar topics. The goal is to eliminate duplicate or redundant groups while maintaining HIGHLY SPECIFIC group titles.

Follow these guidelines for consistent merging:
1. Only merge groups that are truly about the same specific topic or closely related aspects of the same topic.
2. Do not merge groups just because they belong to the same broad category (e.g., don't merge all AI research groups).
3. When merging, create a new title that is HIGHLY SPECIFIC and accurately captures the focus of the combined group.
4. Group titles MUST include specific company names, product names, or event details whenever possible.
5. Write a new summary that explains what unifies all the articles in the merged group.
6. Include ALL article IDs from the original groups in the merged group.
7. If a group is unique and doesn't overlap significantly with others, keep it separate.
8. Preserve specificity - don't create overly broad groups.
9. IMPORTANT: Single-article groups should generally remain separate unless they are truly about the exact same topic as another group.

Examples of GOOD specific merged group titles:
- "Anthropic's Claude AI with Web Search and Citation Features"
- "OpenAI's Voice and Audio Model Enhancements"
- "Nvidia's Robotics AI Advancements with Isaac GR00T"
- "Google's Gemini AI Applications in Healthcare Settings"

Examples of BAD generic merged group titles:
- "AI Assistants and Chatbots"
- "Audio and Voice Technology"
- "Robotics and Automation"
- "AI in Healthcare and Medicine"

The input is a list of groups with the following fields:
- title: The title of the group
- summary: A summary of what unifies the articles in this group
- article_ids: A list of article IDs that belong to this group

Your output should be a JSON object with a "groups" field that contains a list of merged group objects. Each merged group object should have:
- title: A concise, SPECIFIC title for the merged group that includes company/product names
- summary: A summary of what unifies the articles in this merged group
- article_ids: A list of ALL article IDs that belong to this merged group

Remember: Every article ID from the input groups must appear in exactly one output group. No article should be omitted or included in multiple groups.

# Initial Groups:
{groups}

Analyze these groups carefully and merge any that are about the same topic. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""
