from typing import List

from democratic_agent.architecture.helpers.tool import Tool


class Step:
    def __init__(self, step: str, tools: List[str]):
        self.step = step
        self.tools = [Tool(name=tool) for tool in tools]

    def get_feedback(self):
        feedback = ""
        for tool in self.tools:
            feedback += f"\nExecuted tool: {tool.name}, feedback: {tool.feedback}"
        return feedback
