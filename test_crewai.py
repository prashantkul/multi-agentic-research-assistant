#!/usr/bin/env python3
"""Test script for CrewAI with direct Vertex AI integrations."""
import os
import sys
from crewai import Agent, Task, Crew
from src.config.env import config
from src.utils.gemini_adapter import get_langchain_compatible_llm

def test_crewai_direct():
    """Test CrewAI with direct Vertex AI integration."""
    print("\n========== TESTING CREWAI WITH DIRECT VERTEX AI INTEGRATION ==========")
    config.validate()
    
    try:
        print("\n---------- Creating Agent with LangChain-compatible LLM ----------")
        llm = get_langchain_compatible_llm()
        
        # Create a simple agent
        researcher = Agent(
            role="Researcher",
            goal="Research a topic thoroughly",
            backstory="You are an expert researcher with a keen eye for detail.",
            verbose=True,
            llm=llm
        )
        print("✅ Agent creation successful!")
        
        # Create a simple task
        task = Task(
            description="Research the benefits of AI in healthcare and summarize the key points.",
            agent=researcher
        )
        print("✅ Task creation successful!")
        
        # Create a crew
        crew = Crew(
            agents=[researcher],
            tasks=[task],
            verbose=True
        )
        print("✅ Crew creation successful!")
        
        # Run the crew
        print("\n---------- Running CrewAI Execution ----------")
        result = crew.kickoff()

        # Handle CrewOutput object or string
        if hasattr(result, 'raw'):
            result_text = result.raw
        else:
            result_text = str(result)

        print(f"\nResult: {result_text[:200]}..." if len(result_text) > 200 else f"\nResult: {result_text}")
        print("✅ CrewAI execution successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_crewai_direct()