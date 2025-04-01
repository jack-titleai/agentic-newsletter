#!/usr/bin/env python
"""Script to generate a markdown newsletter from bullet points."""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.bullet_point import BulletPoint
from agentic_newsletter.database.bullet_point_log import BulletPointLog


def setup_logging(verbose: bool = False) -> None:
    """Set up logging.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_most_recent_bullet_point_log(db_manager: DatabaseManager) -> Optional[BulletPointLog]:
    """Get the most recent bullet point log.
    
    Args:
        db_manager (DatabaseManager): The database manager.
        
    Returns:
        Optional[BulletPointLog]: The most recent bullet point log, or None if no logs exist.
    """
    with db_manager.get_session() as session:
        from sqlalchemy import select
        from sqlalchemy.sql import desc
        
        query = select(BulletPointLog).order_by(desc(BulletPointLog.timestamp)).limit(1)
        log = session.execute(query).scalar_one_or_none()
        return log


def get_bullet_points_from_latest_run(db_manager: DatabaseManager) -> Tuple[List[BulletPoint], datetime]:
    """Get all bullet points from the latest generation run.
    
    Args:
        db_manager (DatabaseManager): The database manager.
        
    Returns:
        Tuple[List[BulletPoint], datetime]: A tuple containing the list of bullet points and the timestamp of the run.
    """
    # Get the most recent bullet point log
    log = get_most_recent_bullet_point_log(db_manager)
    if not log:
        logging.error("No bullet point logs found in the database.")
        return [], datetime.now()
    
    # Calculate the time window for the run
    # Assuming bullet points were generated within a short time window around the log timestamp
    start_time = log.timestamp - timedelta(minutes=10)
    end_time = log.timestamp + timedelta(minutes=10)
    
    # Get all bullet points from the database within this time window
    all_bullet_points = []
    
    # Get available categories from the config
    config_loader = db_manager.config_loader
    categories = config_loader.get_article_categories()
    
    for category in categories:
        bullet_points = db_manager.get_bullet_points_by_category(
            category=category,
            start_date=start_time,
            end_date=end_time
        )
        all_bullet_points.extend(bullet_points)
    
    return all_bullet_points, log.timestamp


def calculate_combined_score(bullet_point: BulletPoint) -> float:
    """Calculate a combined score for a bullet point.
    
    Args:
        bullet_point (BulletPoint): The bullet point.
        
    Returns:
        float: The combined score (average of impact and frequency).
    """
    return (bullet_point.impact_score + bullet_point.frequency_score) / 2


def generate_markdown_newsletter(bullet_points: List[BulletPoint], timestamp: datetime) -> str:
    """Generate a markdown newsletter from bullet points.
    
    Args:
        bullet_points (List[BulletPoint]): The bullet points to include in the newsletter.
        timestamp (datetime): The timestamp of the bullet point generation run.
        
    Returns:
        str: The markdown newsletter content.
    """
    # Group bullet points by category
    bullet_points_by_category: Dict[str, List[BulletPoint]] = {}
    for bp in bullet_points:
        if bp.assigned_category not in bullet_points_by_category:
            bullet_points_by_category[bp.assigned_category] = []
        bullet_points_by_category[bp.assigned_category].append(bp)
    
    # Sort bullet points in each category by combined score
    for category in bullet_points_by_category:
        bullet_points_by_category[category].sort(
            key=calculate_combined_score,
            reverse=True  # Highest score first
        )
    
    # Define category mapping for renaming and ordering
    category_mapping = {
        "computer vision": "Computer Vision",
        "large language models and/or natural language processing": "LLMs",
        "healthcare AI / healthcare analytics / healthcare technology": "Healthcare AI",
        "hardware for AI and GPUs": "Hardware",
        "AI policy": "AI Policy",
        "other topics": "Miscellaneous"
    }
    
    # Generate markdown content
    markdown = []
    
    # Add title and date
    markdown.append(f"# AI Weekly Recap")
    markdown.append("")
    
    # Add table of contents
    markdown.append("## Topics")
    markdown.append("")
    
    # Add categories in the specified order
    ordered_categories = ["Healthcare AI", "Computer Vision", "LLMs", "Hardware", "AI Policy"]
    
    # Track which categories actually have content
    categories_with_content = []
    
    # Check which categories have content
    for display_category in ordered_categories:
        # Find the original category name that maps to this display category
        original_categories = [cat for cat, disp in category_mapping.items() if disp == display_category]
        
        # Check if any matching original categories have bullet points
        has_content = False
        for original_category in original_categories:
            if original_category in bullet_points_by_category and bullet_points_by_category[original_category]:
                has_content = True
                categories_with_content.append(display_category)
                break
    
    # Only add categories with content to the table of contents
    for display_category in categories_with_content:
        markdown.append(f"- {display_category}")
    
    markdown.append("")
    
    # Add sections for each category in the specified order
    for display_category in categories_with_content:
        # Find the original category name that maps to this display category
        original_categories = [cat for cat, disp in category_mapping.items() if disp == display_category]
        
        # Combine bullet points from all matching original categories
        category_bullet_points = []
        for original_category in original_categories:
            if original_category in bullet_points_by_category:
                category_bullet_points.extend(bullet_points_by_category[original_category])
        
        # Sort combined bullet points by score
        category_bullet_points.sort(key=calculate_combined_score, reverse=True)
        
        markdown.append(f"## {display_category}")
        markdown.append("")
        
        # Add bullet points
        for bp in category_bullet_points:
            bullet_text = bp.bullet_point.strip()
            
            # Add source URL if available
            if bp.source_url:
                markdown.append(f"- {bullet_text} [Source]({bp.source_url})")
            else:
                markdown.append(f"- {bullet_text}")
        
        markdown.append("")
    
    return "\n".join(markdown)


def save_newsletter(content: str, timestamp: datetime) -> str:
    """Save the newsletter to a file.
    
    Args:
        content (str): The newsletter content.
        timestamp (datetime): The timestamp to use in the filename.
        
    Returns:
        str: The path to the saved file.
    """
    # Create the newsletters directory if it doesn't exist
    newsletters_dir = Path("./data/newsletters")
    newsletters_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate filename with current datetime
    filename = f"newsletter_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
    file_path = newsletters_dir / filename
    
    # Write content to file
    with open(file_path, "w") as f:
        f.write(content)
    
    return str(file_path)


def generate_newsletter() -> None:
    """Generate a markdown newsletter from the most recent bullet points."""
    # Create database manager
    db_manager = DatabaseManager()
    
    # Get bullet points from the latest run
    bullet_points, timestamp = get_bullet_points_from_latest_run(db_manager)
    
    if not bullet_points:
        logging.error("No bullet points found for the latest run.")
        return
    
    logging.info(f"Found {len(bullet_points)} bullet points from the latest run.")
    
    # Generate markdown newsletter
    markdown_content = generate_markdown_newsletter(bullet_points, timestamp)
    
    # Save newsletter to file
    file_path = save_newsletter(markdown_content, datetime.now())
    
    logging.info(f"Newsletter saved to {file_path}")


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Generate a markdown newsletter from bullet points.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Generate newsletter
    generate_newsletter()


if __name__ == "__main__":
    main()
