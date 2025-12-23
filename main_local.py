import os
import asyncio
import logging
import feedparser
import config

# BeeAI Güncel Importlar
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.backend import ChatModel, ChatModelParameters
from beeai_framework.tools.think import ThinkTool
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool

# Kendi logger yardımcımız
from logger_utils import log_token_usage


async def get_strategic_feeds():
    """RSS feeds focused on high-level strategy and software trends."""
    sources = {
        "McKinsey": "https://www.mckinsey.com/insights/rss",
        "Forrester": "https://www.forrester.com/blogs/feed/",
        "MIT_Tech_Review": "https://www.technologyreview.com/feed/"
    }
    content = ""
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries: continue
            content += f"\n--- Source: {name} ---\n"
            for entry in feed.entries[:2]:
                summary = getattr(entry, 'summary', entry.get('description', ''))
                content += f"Title: {entry.title}\nDescription: {summary[:250]}...\n"
        except Exception as e:
            print(f"⚠️ Feed error ({name}): {e}")
    return content

async def run_strategic_intelligence():
    """
    RequirementAgent with Systematic Reasoning for Software House Strategy
    """
    
    # 1. Groq Backend Setup via env.local
    # Groq API anahtarını kütüphane otomatik çevre değişkenlerinden okur.
    llm = await ChatModel.from_name(
        config.GROQ_MODEL_NAME, 
        ChatModelParameters(temperature=0)
    )
    
    # 2. Strategic System Instructions (English for deeper reasoning)
    SYSTEM_INSTRUCTIONS = """You are an elite Strategic Technology Advisor for a software development company CEO.

Your methodology:
1. Systematically analyze technology trends for business viability.
2. Evaluate technical debt vs. innovation ROI.
3. Identify specific market shifts that require immediate strategic pivoting.
4. Provide structured, high-impact recommendations for a software house owner."""
    
    # 3. Enhanced Agent with Reasoning + Research
    # Adding ThinkTool for internal monologue and Wikipedia for context.
    agent = RequirementAgent(
        llm=llm,
        tools=[ThinkTool()],
        memory=UnconstrainedMemory(),
        instructions=SYSTEM_INSTRUCTIONS,
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        requirements=[
            ConditionalRequirement(ThinkTool, max_invocations=2),
        ]
    )
    
    # 4. Data Preparation & Query
    raw_data = await get_strategic_feeds()
    
    ANALYSIS_QUERY = f"""Based on the following global tech trends, provide a strategic briefing 
for the upcoming quarter. Focus on software engineering investments and market opportunities.

Data Input:
{raw_data}

Required Output:
- Top 3 Strategic Pillars
- Risk Assessment (Technical Debt & Resource Allocation)
- Immediate Action Items for the CEO"""
    
    print("🐝 BeeAI Strategy Agent is thinking and analyzing...")
    
    try:
        result = await agent.run(ANALYSIS_QUERY)
        
        # 5. Token Usage Logging (Crucial for budget tracking)
        log_token_usage(result, task_name="Enhanced_Reasoning_Strategy")

        print("\n🧠 STRATEGIC ANALYSIS REPORT:")
        print("="*40)
        # RequirementAgent yapısında yanıt result.answer.text içindedir
        print(result.answer.text)
        print("="*40)
        
    except Exception as err:
        print(f"❌ Execution Error: {err}")

async def main() -> None:
    # Minimal logging for clean terminal output
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    await run_strategic_intelligence()

if __name__ == "__main__":
    asyncio.run(main())