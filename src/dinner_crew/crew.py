"""DinnerCrew: three agents, each grounded on a different recommender library, run sequentially."""

from __future__ import annotations

import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from dinner_crew.tools.recommender_tools import FoodLightFMTool, RestaurantSurpriseTool, WineImplicitTool


def build_llm() -> LLM:
    return LLM(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


@CrewBase
class DinnerCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def food_sommelier(self) -> Agent:
        return Agent(config=self.agents_config["food_sommelier"], tools=[FoodLightFMTool()], llm=build_llm())

    @agent
    def wine_sommelier(self) -> Agent:
        return Agent(config=self.agents_config["wine_sommelier"], tools=[WineImplicitTool()], llm=build_llm())

    @agent
    def concierge(self) -> Agent:
        return Agent(config=self.agents_config["concierge"], tools=[RestaurantSurpriseTool()], llm=build_llm())

    @task
    def recommend_dish(self) -> Task:
        return Task(config=self.tasks_config["recommend_dish"])

    @task
    def pair_wine(self) -> Task:
        return Task(config=self.tasks_config["pair_wine"])

    @task
    def recommend_restaurant_and_compose_plan(self) -> Task:
        return Task(config=self.tasks_config["recommend_restaurant_and_compose_plan"])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=False)
