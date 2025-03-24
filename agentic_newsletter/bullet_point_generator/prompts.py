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
8. PRIORITY: Emphasize the importance and impact of each topic/event - state why the event is significant and important, not just what it is
9. EXTREMELY IMPORTANT: Use simple, easy to read, and direct language.  Keep sentences short and do not use filler words - prioritize statistics, metrics, company names, technology names, and other key terms specified above.
10. EXTREMELY IMPORTANT: All information must come ONLY from the provided articles - do not add any external facts, figures, or details
11. EXTREMELY IMPORTANT: Do not make up or infer information not explicitly stated in the articles
12. EXTREMELY IMPORTANT: Only use information from the provided context - do not reference your general knowledge
13. EXTREMELY IMPORTANT: If you're unsure about a specific number or statistic, do not include it rather than guessing
14. EXTREMELY IMPORTANT: For each bullet point, include the URL of the most relevant source article if available
15. EXTREMELY IMPORTANT: Only use URLs that are explicitly provided in the article context - do not make up or generate URLs

MARKDOWN FORMATTING:
16. EXTREMELY IMPORTANT: Use markdown bold formatting (**term**) for key terms in each bullet point. Bold the following types of information:
    - Company names (e.g., **OpenAI**, **Google**, **Microsoft**)
    - Product names (e.g., **ChatGPT**, **Gemini**, **Claude**)
    - Model names and versions (e.g., **GPT-4**, **Llama 3**, **Gemini 1.5 Pro**)
    - Technical terms (e.g., **large language models**, **transformers**, **fine-tuning**)
    - Performance metrics (e.g., **87.5% accuracy**, **2x faster**, **reduced errors by 15%**)
    - Numerical data (e.g., **$7 billion**, **75-85%**, **2026**)
    - Technologies (e.g., **computer vision**, **natural language processing**, **reinforcement learning**)
17. Do not overuse bold formatting - only bold the most important 1-3 terms in each bullet point
18. Make sure the markdown syntax is correct - use double asterisks (**term**) for bold text

For each bullet point, you must also provide three scores:
1. Frequency Score (1-10): How frequently this topic/event appears across the articles
   - 1 = Mentioned only once in a single article
   - 10 = Mentioned extensively across multiple articles
   
2. Impact Score (1-10): How impactful this topic/event is to the AI community (researchers, businesses, policy makers, etc.)
   - 1 = Minimal impact on the AI community
   - 10 = Highly significant impact on the AI community or a major subgroup within it

3. Specificity Score (1-10): How specific and detailed the bullet point is
   - 1 = Very general statement with no specific details (e.g., "AI is advancing")
   - 5 = Moderate specificity with some details (e.g., "Google released a new language model")
   - 10 = Highly specific with precise details (e.g., "Google's PaLM 2 model achieved 87.5% accuracy on the MMLU benchmark, outperforming GPT-4 by 2.3%")

Your response must be a JSON object with the following structure:
{{
  "bullet_points": [
    {{
      "bullet_point": "1-2 sentence summary of a specific topic/event with **key terms** in bold",
      "frequency_score": number between 1-10,
      "impact_score": number between 1-10,
      "specificity_score": number between 1-10,
      "source_url": "URL of the source article supporting this bullet point, or null if not available"
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
5. Provide frequency_score, impact_score, and specificity_score for each bullet point (1-10)
6. Include source_url for each bullet point when available (must be from the article context, not made up)
7. Set source_url to null if no relevant URL is available in the context
8. Scores must be numbers between 1 and 10
9. Use markdown bold formatting (**term**) for key terms like company names, product names, model names, technical terms, and metrics

Please provide a corrected response following the required JSON format.
"""
