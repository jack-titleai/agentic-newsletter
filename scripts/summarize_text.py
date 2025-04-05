#!/usr/bin/env python
"""
Simple script to send text from a file to OpenAI's GPT-4o model for summarization.
"""

import os
import argparse
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def summarize_text(
    file_path: str, 
    model: str = "gpt-4o", 
    api_key: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    verbose: bool = False
) -> str:
    """
    Summarize text from a file using OpenAI's API.
    
    Args:
        file_path: Path to the text file to summarize
        model: OpenAI model to use
        api_key: OpenAI API key (if None, uses OPENAI_API_KEY from environment)
        max_tokens: Maximum tokens for the response
        temperature: Temperature for the model (0.0 to 1.0)
        verbose: Whether to print detailed information
        
    Returns:
        The summarized text
    """
    # Get API key from environment if not provided
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Read the text file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise
    
    # Log information if verbose
    if verbose:
        logger.info(f"Read {len(text)} characters from {file_path}")
        logger.info(f"Using model: {model}")
        logger.info(f"Max tokens: {max_tokens}")
        logger.info(f"Temperature: {temperature}")
    
    # Create a more detailed prompt for better summarization
    prompt = (
        "Please provide a comprehensive summary of the following text. "
        "Include the main ideas, key points, and important details. "
        "Structure the summary with clear sections and bullet points where appropriate.\n\n"
        f"{text}"
    )
    
    # Log the API call
    logger.info(f"Sending request to OpenAI API...")
    
    try:
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates detailed, well-structured summaries of text."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Extract the summary
        summary = response.choices[0].message.content
        
        # Log token usage and cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # Calculate cost (accurate for GPT-4o)
        input_cost_per_1k = 0.01  # $0.01 per 1K tokens for GPT-4o input
        output_cost_per_1k = 0.03  # $0.03 per 1K tokens for GPT-4o output
        input_cost = (prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (completion_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        logger.info(f"API call successful")
        logger.info(f"Token usage: {total_tokens} tokens (input: {prompt_tokens}, output: {completion_tokens})")
        logger.info(f"Estimated cost: ${total_cost:.4f}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error making API call: {e}")
        raise

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Summarize text using OpenAI's GPT-4o model.")
    parser.add_argument(
        "file_path", 
        type=str,
        help="Path to the text file to summarize"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        default=None,
        help="OpenAI API key (default: use OPENAI_API_KEY from environment)"
    )
    parser.add_argument(
        "--max-tokens", 
        type=int, 
        default=4000,
        help="Maximum tokens for the response (default: 4000)"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.7,
        help="Temperature for the model, 0.0 to 1.0 (default: 0.7)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Print detailed information"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Output file to save the summary (default: print to console)"
    )
    
    args = parser.parse_args()
    
    try:
        # Summarize the text
        summary = summarize_text(
            file_path=args.file_path,
            model=args.model,
            api_key=args.api_key,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            verbose=args.verbose
        )
        
        # Output the summary
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(summary)
            logger.info(f"Summary saved to {args.output}")
        else:
            print("\nSummary:")
            print("=" * 80)
            print(summary)
            print("=" * 80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
