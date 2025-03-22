"""Prompts for the article grouper module."""

ARTICLE_GROUPING_PROMPT = """You are an expert at analyzing articles and grouping them by specific topics. Your task is to analyze a list of articles and group them based on their specific topics.

# Instructions:
1. Group articles that discuss the EXACT SAME specific topic, event, product, or announcement.
2. Create highly specific, descriptive titles for each group that capture the exact topic shared by the articles.
3. Write a 1-3 sentence summary for each group that explains the specific topic.
4. IMPORTANT: Each article must be assigned to EXACTLY ONE group. No article should appear in multiple groups.
5. Create single-article groups when an article covers a unique topic not shared by other articles.
6. Groups should be VERY specific - focus on particular events, announcements, or developments.
7. Group titles should include specific company names, product names, or event details whenever possible.

# Examples of Good Groups:
- "Meta's New AI Assistant 'MetaAI' Outperforms Competitors in Benchmark Tests" (specific product announcement)
- "Twitter's Algorithm Change Reduces Engagement for News Content by 23%" (specific platform change)
- "Anthropic Raises $450M in Series C Funding Led by Google" (specific funding event)
- "Nvidia's H200 GPU Doubles AI Training Performance" (specific product announcement)
- "OpenAI Releases GPT-5 with Enhanced Reasoning Capabilities" (specific product announcement)
- "Google's New Gemma Training Method Reduces Training Time by 50%" (specific technology announcement)

# Examples of Bad Groups (Too General):
- "AI Developments" (too broad)
- "Tech Company News" (too broad)
- "Social Media Updates" (too broad)
- "AI in Healthcare" (too broad)
- "AI in Financial Services" (too broad)
- "AI Models and Research" (too broad)

# Single Article Group Examples:
- "Stability AI Releases New Text-to-3D Model 'StableShape'" (single article about a specific product)
- "Microsoft Acquires AI Startup Inflection for $650M" (single article about a specific acquisition)
- "DeepMind's AlphaCode 2 Solves Competitive Programming Problems at Expert Level" (single article about a specific achievement)

# Article Data:
{articles}

Analyze these articles carefully and group them by specific topics. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""

GROUP_MERGING_PROMPT = """You are an expert at analyzing and consolidating article groups. Your task is to review the initial groups created and merge any that are clearly about the same broader topic.

# Instructions:
1. Analyze the provided groups and identify any that are about the same broader topic or company announcement.
2. Merge groups that are clearly duplicates or highly related (e.g., different aspects of the same product announcement).
3. Create a new title for each merged group that captures the broader topic while still being specific.
4. Write a comprehensive summary for each merged group that incorporates the key points from all merged groups.
5. IMPORTANT: Each article must be assigned to EXACTLY ONE group after merging. No article should appear in multiple groups.
6. Do NOT merge groups that are genuinely about different topics, even if they involve the same company.
7. The final groups should be balanced - not too specific (causing duplicates) and not too general (losing important distinctions).

# Examples of Groups to Merge:
- "OpenAI's New Voice Models for Developers" and "OpenAI's Voice AI with Personality Boost" → "OpenAI's Advanced Voice Models with Enhanced Capabilities"
- "Nvidia's AI Initiatives in Robotics" and "Nvidia's Cosmos-Transfer1 for Robot Training" → "Nvidia's Robotics AI Advancements with Cosmos-Transfer1"
- "Google's Gemini AI for Healthcare" and "Google's Gemini AI in Japanese Hospitals" → "Google's Gemini AI Applications in Healthcare Settings"

# Examples of Groups NOT to Merge:
- "Microsoft's Azure AI Updates" and "Microsoft's GitHub Copilot Enhancements" (different products)
- "Meta's AI Assistant Launch" and "Meta's VR Hardware Announcement" (different topics)
- "OpenAI's GPT-5 Release" and "OpenAI's Regulatory Proposals" (different topics)

# Initial Groups:
{groups}

Analyze these groups carefully and merge any that are about the same topic. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""
