"""Strategic Intelligence Pipeline Orchestrator.

This module implements the main pipeline that orchestrates all agents
and services to execute the full multi-stage strategic analysis workflow.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.agents.distiller_agent import DistillerAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.strategist_agent import StrategistAgent
from src.config.professions import Profession
from src.core.data_processor import DataProcessor
from src.core.llm_service import LLMService
from src.core.rss_service import RSSService
from src.report.report_generator import save_as_html
from src.utils.logger import summarize_total_usage, log_info

@dataclass
class PipelineOutput:
    """Structured output from the strategic intelligence pipeline.
    
    Attributes:
        raw_data: Aggregated raw feed data from RSS sources
        distilled_data: Condensed structured facts
        strategic_report: Full strategic intelligence analysis
        review_analysis: Critical peer review of the report
        full_report: Combined final report (ready for HTML export)
        html_file: Path to generated HTML report file
    """

    raw_data: str
    distilled_data: str
    strategic_report: str
    review_analysis: str
    full_report: str
    html_file: Optional[str] = None


class StrategicPipeline:
    """Orchestrator for the 4-stage strategic intelligence pipeline.
    
    Responsibility:
    - Coordinate all services and agents in correct sequence
    - Handle data flow between pipeline stages
    - Manage error handling and recovery
    - Log metrics and progress
    - Return structured output
    
    Pipeline Stages:
    1. FETCH: RSS feeds aggregation and filtering (RSSService)
    2. DISTILL: Extract structured facts (DistillerAgent)
    3. ANALYZE: Synthesize strategic insights (StrategistAgent)
    4. REVIEW: Critical peer analysis (ReviewerAgent)
    
    Attributes:
        rss_service: Service for RSS feed operations
        data_processor: Service for data transformation
        llm_service: Service for LLM model management
        distiller_agent: Agent for data distillation
        strategist_agent: Agent for strategic analysis
        reviewer_agent: Agent for critical review
    """

    def __init__(
        self,
        rss_service: Optional[RSSService] = None,
        data_processor: Optional[DataProcessor] = None,
        llm_service: Optional[LLMService] = None,
        profession: Profession = Profession.SOLO_DEVELOPER,
    ) -> None:
        """Initialize pipeline with dependencies (Dependency Injection).
        
        Args:
            rss_service: RSS aggregation service. Creates default if None.
            data_processor: Data transformation service. Creates default if None.
            llm_service: LLM model service. Creates default if None.
        """
        self.rss_service: RSSService = rss_service or RSSService(profession=profession)
        self.data_processor: DataProcessor = data_processor or DataProcessor()
        self.llm_service: LLMService = llm_service or LLMService()

        # Initialize agents with shared LLM service and profession
        self.distiller_agent: DistillerAgent = DistillerAgent(self.llm_service)
        self.strategist_agent: StrategistAgent = StrategistAgent(self.llm_service, profession)
        self.reviewer_agent: ReviewerAgent = ReviewerAgent(self.llm_service, profession)

        # Internal state for metric tracking
        self._agent_outputs: list = []

        # Configure logging
        logging.getLogger('asyncio').setLevel(logging.CRITICAL)

    async def execute(self) -> PipelineOutput:
        """Execute the full 4-stage strategic intelligence pipeline.
        
        Pipeline Flow:
        1. FETCH: Aggregate RSS feeds
        2. DISTILL: Extract structured facts
        3. ANALYZE: Build strategic report
        4. REVIEW: Peer-review and critique
        5. FINALIZE: Combine outputs and generate HTML
        
        Returns:
            PipelineOutput with all stage results.
        
        Raises:
            RuntimeError: If any pipeline stage fails.
        """
        try:
            
            log_info("\n" + "═" * 70)
            log_info("🚀 STRATEGIC INTELLIGENCE PIPELINE - STARTED")
            log_info("═" * 70)

            # Stage 1: FETCH
            raw_data: str = await self._stage_fetch()

            # Stage 2: DISTILL
            distilled_data: str = await self._stage_distill(raw_data)

            # Stage 3: ANALYZE
            strategic_report: str = await self._stage_analyze(distilled_data)

            # Stage 4: REVIEW
            review_analysis: str = await self._stage_review(strategic_report)

            # Stage 5: FINALIZE
            output: PipelineOutput = await self._stage_finalize(
                raw_data,
                distilled_data,
                strategic_report,
                review_analysis
            )

            log_info("\n" + "═" * 70)
            log_info("✅ PIPELINE COMPLETED SUCCESSFULLY")
            log_info("═" * 70)

            return output

        except Exception as e:
            self._handle_pipeline_error(e)

    async def _stage_fetch(self) -> str:
        """Stage 1: Fetch and aggregate RSS feeds.
        
        Returns:
            Raw aggregated feed data.
        
        Raises:
            RuntimeError: If feed aggregation fails.
        """
        log_info("\n📡 STAGE 1: Aggregating market feeds...")
        try:
            raw_data: str = await self.rss_service.fetch_all_feeds()
            log_info(f"✅ Stage 1 complete: {len(raw_data)} characters aggregated")
            return raw_data
        except Exception as e:
            raise RuntimeError(f"Stage 1 (FETCH) failed: {str(e)}") from e

    async def _stage_distill(self, raw_data: str) -> str:
        """Stage 2: Distill raw data into structured facts.
        
        Args:
            raw_data: Raw aggregated feed data.
        
        Returns:
            Distilled structured facts.
        
        Raises:
            RuntimeError: If distillation fails.
        """
        log_info("\n🧠 STAGE 2: Distilling insights...")
        try:
            distiller_response = await self.distiller_agent.execute(raw_data)
            self._agent_outputs.append(distiller_response)

            distilled_data: str = self.distiller_agent.get_distilled_text(distiller_response)
            log_info(f"✅ Stage 2 complete: {len(distilled_data)} characters distilled")
            log_info(f"\n--- DEBUG: Distilled Data ---\n{distilled_data[:1300]}...\n---\n")

            return distilled_data

        except Exception as e:
            raise RuntimeError(f"Stage 2 (DISTILL) failed: {str(e)}") from e

    async def _stage_analyze(self, distilled_data: str) -> str:
        """Stage 3: Synthesize strategic intelligence report.
        
        Args:
            distilled_data: Distilled facts from stage 2.
        
        Returns:
            Strategic intelligence report.
        
        Raises:
            RuntimeError: If analysis fails.
        """
        log_info("\n📊 STAGE 3: Building strategic report...")
        try:
            strategist_response = await self.strategist_agent.execute(distilled_data)
            self._agent_outputs.append(strategist_response)

            strategic_report: str = self.strategist_agent.get_report_text(strategist_response)
            log_info(f"✅ Stage 3 complete: {len(strategic_report)} characters analyzed")

            return strategic_report

        except Exception as e:
            raise RuntimeError(f"Stage 3 (ANALYZE) failed: {str(e)}") from e

    async def _stage_review(self, strategic_report: str) -> str:
        """Stage 4: Execute peer-review and critical analysis.
        
        Args:
            strategic_report: Strategic report from stage 3.
        
        Returns:
            Critical peer-review analysis.
        
        Raises:
            RuntimeError: If review fails.
        """
        log_info("\n🕵️ STAGE 4: Peer-reviewing strategy...")
        try:
            reviewer_response = await self.reviewer_agent.execute(strategic_report)
            self._agent_outputs.append(reviewer_response)

            review_analysis: str = self.reviewer_agent.get_review_text(reviewer_response)
            log_info(f"✅ Stage 4 complete: {len(review_analysis)} characters reviewed")

            return review_analysis

        except Exception as e:
            raise RuntimeError(f"Stage 4 (REVIEW) failed: {str(e)}") from e

    async def _stage_finalize(
        self,
        raw_data: str,
        distilled_data: str,
        strategic_report: str,
        review_analysis: str
    ) -> PipelineOutput:
        """Stage 5: Finalize outputs and generate HTML report.
        
        Args:
            raw_data: Raw aggregated data.
            distilled_data: Distilled facts.
            strategic_report: Strategic intelligence.
            review_analysis: Peer review.
        
        Returns:
            PipelineOutput with all results and HTML file path.
        
        Raises:
            RuntimeError: If finalization fails.
        """
        log_info("\n📄 STAGE 5: Finalizing outputs...")
        try:
            # Combine outputs into final report
            full_report: str = (
                f"{strategic_report}\n\n---\n"
                f"## 🕵️ Executive Review & Stress Test\n{review_analysis}"
            )

            # Generate HTML report
            timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_file: str = save_as_html(full_report, f"Strategy_Report_{timestamp}")

            # Log aggregated metrics
            summarize_total_usage(*self._agent_outputs)

            log_info(f"✅ Stage 5 complete: Report saved to {html_file}")

            return PipelineOutput(
                raw_data=raw_data,
                distilled_data=distilled_data,
                strategic_report=strategic_report,
                review_analysis=review_analysis,
                full_report=full_report,
                html_file=html_file
            )

        except Exception as e:
            raise RuntimeError(f"Stage 5 (FINALIZE) failed: {str(e)}") from e

    def _handle_pipeline_error(self, error: Exception) -> None:
        """Handle pipeline-level errors with context.
        
        Args:
            error: Exception that occurred.
        
        Raises:
            RuntimeError: Always re-raises with pipeline context.
        """
        error_msg = f"Pipeline execution failed: {str(error)}"
        from src.utils.logger import log_error
        log_error(f"\n❌ {error_msg}")
        raise RuntimeError(error_msg) from error

    def get_pipeline_info(self) -> dict[str, str]:
        """Get pipeline configuration and agent information.
        
        Returns:
            Dictionary with pipeline and agent metadata.
        """
        return {
            "pipeline": "StrategicPipeline",
            "distiller": self.distiller_agent.get_info(),
            "strategist": self.strategist_agent.get_info(),
            "reviewer": self.reviewer_agent.get_info(),
            "llm_config": str(self.llm_service.get_config()),
        }
