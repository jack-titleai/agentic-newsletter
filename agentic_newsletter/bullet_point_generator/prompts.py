"""Prompts for the bullet point generator module."""

BULLET_POINT_GENERATION_PROMPT = """You are an expert AI analyst tasked with extracting key information from a collection of articles about {category}. 

Your task is to create a series of bullet points that summarize the most important topics and events mentioned in the articles. Each bullet point should be 1-2 sentences about a specific topic or event.

IMPORTANT GUIDELINES:
1. Bullet points must be mutually exclusive - no two bullet points should cover the same topic or event
2. Bullet points should collectively cover all significant topics/events in the articles
3. A "topic/event" is a specific occurrence or development, not just a general category
4. Use simple, direct language without filler words that is accessible to both technical and non-technical audiences
5. PRIORITY: Include specific statistics, metrics, percentages, and numbers whenever they appear in the articles
6. PRIORITY: Include specific company names, technology names, model names, and version numbers
7. PRIORITY: If an article mentions performance improvements, include the exact metrics (e.g., "20% faster", "reduced errors by 15%")
8. EXTREMELY IMPORTANT: All information must come ONLY from the provided articles - do not add any external facts, figures, or details
9. EXTREMELY IMPORTANT: Do not make up or infer information not explicitly stated in the articles
10. EXTREMELY IMPORTANT: Only use information from the provided context - do not reference your general knowledge
11. EXTREMELY IMPORTANT: If you're unsure about a specific number or statistic, do not include it rather than guessing

For each bullet point, you must also provide two scores:
1. Frequency Score (1-10): How frequently this topic/event appears across the articles
   - 1 = Mentioned only once in a single article
   - 10 = Mentioned extensively across multiple articles
   
2. Impact Score (1-10): How impactful this topic/event is to the AI community (researchers, businesses, policy makers, etc.)
   - 1 = Minimal impact on the AI community
   - 10 = Highly significant impact on the AI community or a major subgroup within it

Your response must be a JSON object with the following structure:
{{
  "bullet_points": [
    {{
      "bullet_point": "1-2 sentence summary of a specific topic/event",
      "frequency_score": number between 1-10,
      "impact_score": number between 1-10
    }},
    ...
  ]
}}

Here are the articles about {category} for your analysis:

{articles}
"""

BULLET_POINT_RETRY_PROMPT = """Your previous response did not match the expected format or contained errors. Please try again with the following corrections:

{error_message}

Remember:
1. Your response must be valid JSON
2. Each bullet point must be 1-2 sentences about a specific topic/event
3. Bullet points must be mutually exclusive (no overlap in topics)
4. Include only information from the provided articles
5. Provide both frequency_score and impact_score for each bullet point (1-10)
6. Scores must be numbers between 1 and 10

Please provide a corrected response following the required JSON format.
"""
