"""CLI Entry Point for Strategic Intelligence Agent.

This module provides the command-line interface for running the strategic
intelligence pipeline. It orchestrates all agents and services using dependency
injection for clean architecture and testability.

Environment: Uses .env.local for API keys and configuration.
"""

import argparse
import asyncio
import logging

from src.config.professions import Profession
from src.pipelines.strategic_pipeline import StrategicPipeline, PipelineOutput


async def main() -> None:
    """Main entry point for the strategic intelligence pipeline.
    
    Initializes the pipeline with all dependencies and executes the full
    4-stage analysis workflow:
    1. Fetch & aggregate RSS feeds
    2. Distill raw data into structured facts
    3. Synthesize strategic intelligence report
    4. Execute peer-review and critical analysis
    
    Outputs:
    - Console progress and metrics
    - HTML report file in reports/ directory
    - Token/cost tracking via agent_usage.log
    """
    # Suppress asyncio debug logs
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)

    # CLI argument for profession selection
    parser = argparse.ArgumentParser(description="Run Strategic Intelligence Pipeline")
    parser.add_argument(
        "--profession",
        type=str,
        default=Profession.SOLO_DEVELOPER.value,
        choices=[p.value for p in Profession],
        help="Profession domain for analysis."
    )
    args = parser.parse_args()
    profession = Profession(args.profession)

    # Initialize pipeline with selected profession
    pipeline: StrategicPipeline = StrategicPipeline(profession=profession)

    # Execute the full pipeline
    output: PipelineOutput = await pipeline.execute()

    # Display results
    print(f"\n✅ HTML Report: {output.html_file}")
    print(f"📊 Total output size: {len(output.full_report)} characters")


if __name__ == "__main__":
    asyncio.run(main())
