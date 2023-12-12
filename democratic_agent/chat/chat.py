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
        if containers:
            json_kwargs = {"schema": PydanticParser.get_json_schema(containers)}
            system_message += "\n" + self.load_prompt("json", args=json_kwargs)
            self.containers = containers
            self.response_format = "json_object"
        else:
            self.containers = []
            self.response_format = "text"

        self.conversation = Conversation(module_name, system_message)

    def add_tool_feedback(self, id: str, message: str):
        self.conversation.add_tool_message(id=id, message=message)

    def get_response(
        self,
        prompt_kwargs: dict,
        functions: List[Callable] = [],
        retries: int = 2,  # TODO: Move to cfg
        fix_retries: int = 0,  # TODO: Move to cfg and solve me..
    ) -> str | List[T] | List[ChatCompletionMessageToolCall]:
        """Get a reponse from the model, can be a single string or a list of objects."""

        if self.model is None:
            self.load_model()

        if functions and self.containers:
            raise Exception(
                "So far we can ask for tools explicitely or for a JSON format to transform the response into containers, but not both!!"
            )

        prompt = self.load_prompt("user", self.module_name, prompt_kwargs)
        function_schemas = []
        for function in functions:
            function_schemas.append(PydanticParser.get_function_schema(function))
            # In case we are sending tools we should save them in the traces as OpenAI does it internally.

        self.conversation.add_user_message(prompt)
        response = self.model.get_response(
            conversation=self.conversation,
            functions=function_schemas,
            response_format=self.response_format,
        )
        self.conversation.add_assistant_message(response)

        if self.containers:
            parser = PydanticParser(model=self.model)
            return parser.parse_response(
                conversation=self.conversation,
                response=response,
                containers=self.containers,
                retries=retries,
                fix_retries=fix_retries,
            )
        return response

    def load_model(self):
        self.model = ModelsManager().create_model(self.module_name)

    def load_prompt(
        self, prompt_name: str, path: Optional[str] = None, args: Dict[str, Any] = {}
    ):
        return load_prompt(prompt_name, path=path, **args)
