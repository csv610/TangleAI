import os
import logging
import sys
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Union

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tangle'))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_knowledge_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("daily_knowledge_bot")


class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class DailyFactService:
    """Service to manage retrieval and storage of daily facts."""

    def __init__(self, client: PerplexityClient, output_dir: Path = None):
        """
        Initialize the daily fact service.

        Args:
            client: Perplexity API client
            output_dir: Directory to save fact files
        """
        self.client = client
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(exist_ok=True)

        # Default topics
        self.topics = [
            "astronomy",
            "history",
            "biology",
            "technology",
            "psychology",
            "ocean life",
            "ancient civilizations",
            "quantum physics",
            "art history",
            "culinary science"
        ]

        # Model configuration for fact generation
        self.model_config = ModelConfig(
            model="sonar",
            max_tokens=150,
            temperature=0.7
        )
    
    def load_topics_from_file(self, filepath: Union[str, Path]) -> None:
        """
        Load topics from a configuration file.
        
        Args:
            filepath: Path to the topics file (one topic per line)
        """
        try:
            topics_file = Path(filepath)
            if topics_file.exists():
                with open(topics_file, "r") as f:
                    topics = [line.strip() for line in f if line.strip()]
                
                if topics:
                    self.topics = topics
                    logger.info(f"Loaded {len(topics)} topics from {filepath}")
                else:
                    logger.warning(f"No topics found in {filepath}, using defaults")
            else:
                logger.warning(f"Topics file {filepath} not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading topics file: {e}")
    
    def get_daily_topic(self) -> str:
        """
        Select a topic for today.
        
        Returns:
            The selected topic
        """
        day = datetime.now().day
        # Prevent index errors with modulo and ensure we don't get -1 on the last day
        topic_index = day % len(self.topics)
        if topic_index == 0 and len(self.topics) > 0:
            topic_index = len(self.topics) - 1
        else:
            topic_index -= 1
            
        return self.topics[topic_index]
    
    def get_random_topic(self) -> str:
        """
        Select a random topic as a fallback.
        
        Returns:
            A randomly selected topic
        """
        return random.choice(self.topics)
    
    def get_and_save_daily_fact(self) -> Dict[str, str]:
        """
        Get today's fact and save it to a file.

        Returns:
            Dictionary with topic, fact, and file information
        """
        # Try to get the daily topic, fall back to random if there's an error
        try:
            topic = self.get_daily_topic()
        except Exception as e:
            logger.error(f"Error getting daily topic: {e}")
            topic = self.get_random_topic()

        logger.info(f"Getting today's fact about: {topic}")

        try:
            # Create model input for fact generation
            system_prompt = "You are a helpful assistant that provides interesting, accurate, and concise facts. Respond with only one fascinating fact, kept under 100 words."
            user_prompt = f"Tell me an interesting fact about {topic} that most people don't know."

            model_input = ModelInput(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )

            response = self.client.generate_content(model_input, self.model_config)
            fact = response.choices[0].message.content

            # Save the fact
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = self.output_dir / f"daily_fact_{timestamp}.txt"

            with open(filename, "w") as f:
                f.write(f"DAILY FACT - {timestamp}\n")
                f.write(f"Topic: {topic}\n\n")
                f.write(fact)

            logger.info(f"Fact saved to {filename}")

            return {
                "topic": topic,
                "fact": fact,
                "filename": str(filename)
            }
        except Exception as e:
            logger.error(f"API error: {e}")
            raise


def load_config() -> Dict[str, str]:
    """
    Load configuration from environment variables.

    Returns:
        Dictionary of configuration values
    """
    # Get output directory from environment variables or use default
    output_dir = os.environ.get("OUTPUT_DIR", "./facts")

    # Get topics file path from environment variables
    topics_file = os.environ.get("TOPICS_FILE", "./topics.txt")

    return {
        "output_dir": output_dir,
        "topics_file": topics_file
    }


def main():
    """Main function that runs the daily knowledge bot."""
    try:
        # Load configuration
        config = load_config()

        # Initialize API client
        client = PerplexityClient()

        # Create output directory
        output_dir = Path(config["output_dir"])
        output_dir.mkdir(exist_ok=True)

        # Initialize service
        fact_service = DailyFactService(client, output_dir)

        # Load custom topics if available
        if config["topics_file"]:
            fact_service.load_topics_from_file(config["topics_file"])

        # Get and save today's fact
        result = fact_service.get_and_save_daily_fact()

        # Display the results
        print(f"\nToday's {result['topic']} fact: {result['fact']}")
        print(f"Saved to: {result['filename']}")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
