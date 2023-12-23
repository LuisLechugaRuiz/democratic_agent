from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Type
from logging import getLogger
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)  # Common interface for the tool calls, we can create our own class if needed.

from democratic_agent.chat.conversation import Conversation
from democratic_agent.chat.parser.pydantic_parser import PydanticParser
from democratic_agent.chat.parser.loggable_base_model import LoggableBaseModel
from democratic_agent.prompts.load import load_prompt
from democratic_agent.models.models_manager import ModelsManager


T = TypeVar("T", bound=LoggableBaseModel)

# TODO: Create our own logger.
LOG = getLogger(__name__)


class Chat(Generic[T]):
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        module_name: str,
        system_prompt_kwargs: Dict[str, Any] = {},
        containers: List[Type[T]] = [],
    ):
        self.model = None
        self.module_name = module_name

        # Load prompt depending on the module - Limitations of this approach: We force to have single system for each module, which I guess is fine.
        # This also enforces that we have only one kind of json schema for each module... TODO: Verify this.
        system_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        # TODO: Deprecate Pydantic containers for functions.
        # if containers:
        #     json_kwargs = {"schema": PydanticParser.get_json_schema(containers)}
        #     system_message += "\n" + self.load_prompt("json", args=json_kwargs)
        #     self.response_format = "json_object"
        # else:
        #     self.response_format = "text"
        # self.containers = containers

        self.conversation = Conversation(module_name, system_message)

    def add_tool_feedback(self, id: str, message: str):
        self.conversation.add_tool_message(id=id, message=message)

    def call(self, functions: List[Callable] = []):
        """Call the model to get a response."""

        if self.model is None:
            self.load_model()

        function_schemas = []
        for function in functions:
            function_schemas.append(PydanticParser.get_function_schema(function))

        response = self.model.get_response(
            conversation=self.conversation,
            functions=function_schemas,
        )
        if function_schemas:
            tool_calls = response.tool_calls
            if tool_calls is not None:
                # In case we are sending tools we should save them in the traces as OpenAI doesn't include them on prompt.
                self.conversation.add_assistant_tool_message(tool_calls)
                return tool_calls

        response = response.content
        self.conversation.add_assistant_message(response)
        return response

    def edit_system_message(self, system_prompt_kwargs: Dict[str, Any]):
        """Edit the system message."""
        system_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        self.conversation.edit_system_message(system_message)
        # TODO: Deprecate Pydantic containers for functions.
        # if self.containers:
        #     json_kwargs = {"schema": PydanticParser.get_json_schema(self.containers)}
        #     system_message += "\n" + self.load_prompt("json", args=json_kwargs)
        #     self.response_format = "json_object"
        # else:
        #     self.response_format = "text"

    def get_response(
        self,
        prompt_kwargs: Dict[str, Any],
        functions: List[Callable] = [],
        user_name: Optional[str] = None,
    ) -> str | List[T] | List[ChatCompletionMessageToolCall]:
        """Get a reponse from the model, can be a single string or a list of objects."""

        if self.model is None:
            self.load_model()

        prompt = self.load_prompt("user", self.module_name, prompt_kwargs)

        self.conversation.add_user_message(prompt, user_name)
        return self.call(functions)

    def load_model(self):
        self.model = ModelsManager().create_model(self.module_name)

    def load_prompt(
        self, prompt_name: str, path: Optional[str] = None, args: Dict[str, Any] = {}
    ):
        return load_prompt(prompt_name, path=path, **args)
