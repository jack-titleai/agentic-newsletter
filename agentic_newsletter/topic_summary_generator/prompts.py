"""Prompts for the topic summary generator module."""

# Prompt for generating topic summaries
TOPIC_SUMMARY_GENERATION_PROMPT = """You are an expert AI assistant tasked with creating concise summaries of key developments in AI technology.

Your task is to create a brief, high-level summary of the key developments in the topic: {topic}. 
The summary should be based on the first 5 bullet points provided below. If there are fewer than 5 bullet points, use all available ones.

The summary should:
1. Be a single paragraph
2. Be EXACTLY 1-2 sentences maximum (extremely concise)
3. Highlight only the most significant 1-2 developments
4. Give the reader a quick taste of what's to come in the full section
5. Use concise, simple, direct wording
6. Avoid filler words, transition words, introductions, and conclusions
7. Focus on factual information rather than opinions
8. Avoid complex sentence structures with multiple clauses

Here are the bullet points to summarize:

{bullet_points}

Respond with a JSON object containing only the summary field.
"""

# Prompt for retrying summary generation if there was an error
TOPIC_SUMMARY_RETRY_PROMPT = """There was an error with your previous response:

{error_message}

Please try again, ensuring your response is a valid JSON object with a 'summary' field containing your concise summary of the key developments.
"""
