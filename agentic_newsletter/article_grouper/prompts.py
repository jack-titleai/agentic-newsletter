"""Prompts for the article grouper module."""

ARTICLE_GROUPING_PROMPT = """You are an expert at analyzing articles and grouping them by specific topics. Your task is to analyze a list of articles and group them based on their specific topics.

# Instructions:
1. Group articles that discuss the EXACT SAME specific topic, event, product, or announcement.
2. Create highly specific, descriptive titles for each group that capture the exact topic shared by the articles.
3. Write a 1-3 sentence summary for each group that explains the specific topic.
4. Every article must be assigned to at least one group.
5. IMPORTANT: Create single-article groups when an article covers a unique topic not shared by other articles.
6. Groups should be VERY specific - focus on particular events, announcements, or developments.
7. Prefer creating more groups with fewer articles each rather than fewer groups with many articles.
8. Group titles should include specific company names, product names, or event details whenever possible.

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
