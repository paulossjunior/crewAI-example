"""DinnerCrew: three agents, each grounded on a different recommender library, run sequentially."""

from __future__ import annotations

import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from dinner_crew.tools.recommender_tools import FoodLightFMTool, RestaurantSurpriseTool, WineImplicitTool


def build_llm() -> LLM:
    """Build the LLM shared by all agents.

    The model comes from the ``OPENAI_MODEL`` env var (default ``gpt-4o-mini``).

    Returns:
        A configured CrewAI ``LLM``.
    """
    # temperature=0 reduces narrative variance; the recommendations themselves come from the tools.
    return LLM(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


@CrewBase
class DinnerCrew:
    """Dinner-planning crew: dish -> wine pairing -> restaurant -> host summary, run sequentially.

    Agents and tasks are configured in ``config/agents.yaml`` and ``config/tasks.yaml``. The three
    specialists each get exactly one recommender tool; the host has none and only rewrites their
    answers into the final plan. Task-to-task ``context`` chaining is defined in the YAML.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def food_sommelier(self) -> Agent:
        """Agent that picks the dish using the LightFM food tool."""
        return Agent(config=self.agents_config["food_sommelier"], tools=[FoodLightFMTool()], llm=build_llm())

    @agent
    def wine_sommelier(self) -> Agent:
        """Agent that pairs a wine with the dish using the implicit (ALS) wine tool."""
        return Agent(config=self.agents_config["wine_sommelier"], tools=[WineImplicitTool()], llm=build_llm())

    @agent
    def concierge(self) -> Agent:
        """Agent that picks the restaurant using the Surprise (KNN) tool."""
        return Agent(config=self.agents_config["concierge"], tools=[RestaurantSurpriseTool()], llm=build_llm())

    @agent
    def host(self) -> Agent:
        """Agent with no tool that turns the three answers into a human summary."""
        return Agent(config=self.agents_config["host"], llm=build_llm())

    @task
    def recommend_dish(self) -> Task:
        """First task: recommend the dish."""
        return Task(config=self.tasks_config["recommend_dish"])

    @task
    def pair_wine(self) -> Task:
        """Second task: pair a wine with the recommended dish."""
        return Task(config=self.tasks_config["pair_wine"])

    @task
    def recommend_restaurant(self) -> Task:
        """Third task: recommend a restaurant for the dish's cuisine."""
        return Task(config=self.tasks_config["recommend_restaurant"])

    @task
    def write_summary(self) -> Task:
        """Final task: the host writes the human summary and the detailed plan."""
        return Task(config=self.tasks_config["write_summary"])

    @crew
    def crew(self) -> Crew:
        """Assemble the crew; sequential process runs tasks in method-definition order.

        Returns:
            The configured ``Crew``.
        """
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=False)
