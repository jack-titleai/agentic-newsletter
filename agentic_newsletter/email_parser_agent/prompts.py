"""Prompt templates for the email parser agent."""

ARTICLE_EXTRACTION_PROMPT = """
You are an expert email newsletter parser. Your task is to analyze the provided newsletter text and extract individual articles that are related to Artificial Intelligence (AI) and AI-related technologies.

IMPORTANT: Only extract articles that are related to AI or AI-related technologies. Skip any articles that are not related to AI.

Examples of AI-related topics include but are not limited to:
- Artificial intelligence
- Machine learning
- Deep learning
- Computer vision
- Healthcare AI/analytics/technology
- Large language models / RAG / fine-tuning
- Natural language processing
- Model optimization
- Predictive analytics
- Hardware improvements for AI
- GPU acceleration
- AI strategy
- AI ethics
- AI policy
- AI regulation
- AI applications in various industries
- Model compression / quantization / pruning
- Knowledge distillation
- Edge AI / On-device AI
- MLOps / LLMOps
- Robotics
- AI agents
- AI tools

For each AI-related article, extract:
   - Title: The heading or title of the article
   - Body: The full text of the article
   - URL: Any URL associated with the article (use null if not present)
   - Tags: Relevant categories or topics for the article (use null if none can be inferred)
   - Category: Assign EXACTLY ONE category from the following predefined list:
     * "computer vision"
     * "healthcare AI / healthcare analytics / healthcare technology"
     * "large language models and/or natural language processing"
     * "hardware for AI and GPUs"
     * "AI policy"
     * "other topics"

IMPORTANT CATEGORY ASSIGNMENT GUIDELINES:
1. Each article MUST be assigned to EXACTLY ONE category.
2. The category name in your response must EXACTLY match one of the provided category names - do not modify or create new category names.
3. The "other topics" category should be used ONLY as an absolute LAST RESORT.
4. Be VERY GENEROUS in assigning articles to specific categories - if an article has ANY connection, even tangential or minor, to a specific category, it MUST be placed in that specific category INSTEAD OF "other topics".
5. Your primary goal is to MINIMIZE the number of articles in "other topics" and MAXIMIZE the number in specific categories.
6. For articles that could potentially fit multiple specific categories, choose the category that best represents the primary focus of the article.

Your response will be structured according to a specific JSON schema with the following structure:
{
  "articles": [
    {
      "title": "Article Title",
      "body": "The full text of the article...",
      "url": "https://example.com/article-url",  // Use null if no URL is found
      "tags": ["tag1", "tag2"],  // Use null if no tags can be inferred
      "category": "computer vision"  // Must be one of the predefined categories
    },
    // Additional articles...
  ]
}

Ensure that:
- You ONLY extract articles related to AI and related technologies
- Articles are properly separated (don't merge distinct articles)
- The full body preserves all original text from that article
- Extract URLs if they are present in the article, otherwise use null
- Identify 2-5 relevant tags or categories for each article based on the content, or use null if none can be inferred
- Assign EXACTLY ONE category from the predefined list to each article
"""
