# Development tracker

## --- 14/12 ---

### Do we need affordance?
We will send to the tool executor a list of functions so he can decide which is the correct one to use.. the affordance can be a simple mechanism inside the rag system to filter by similarity.

What happens then if we need to create a function?
First idea is that the tool executor can call a function: <create_tool(name: str, description: str)> indicating which is the tool that will be used for the task. This way we can have a closed loop creator - executor!

Implemented!

### New super interesting paper!! 
[FunSearch](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)
Very similar to our idea, but using a self-improvement loop.

We need a:
Test function.
Evaluator.
Multiple generations.

This can be the way to create truly amazing code which can do almost anything... exciting times to be alive.

We might fuse it with [Chain-of-Code](https://chain-of-code.github.io/) to add the LLM as an option to solve abstract tasks.

### Discoveries

- ToolExecutor is not a good builder to create the right tool, we need another model that is able to decide the scope of the function. This is not a trivial task as it should fine the tradeoff between generalization and specialization. It should understand when to use inputs as arguments instead of creating a too specific function. i.e: Who is the richest person in the world? Can be answered with a function that specifically search for richest person search_richest_person or by search_on_google("Who is the richest person?"). Ideally we should prioritize the second solution, but we need a very good reasoner to help us on this task. We have implemented the self-improvement loop, to create really strong functions that help us solve general problems (somebady said AGI?).

## --- 15 / 12 ---

### A distributed system, solving the biggest pain

Inspired by:
https://petals.dev/

And specially the new paper https://arxiv.org/pdf/2312.08361.pdf showing that is factible to run LLMs over the internet distributed on several devices, this opens the door for the next step: A distributed ecosystem where people share their GPU to obtain a better general performance.

Why people would do it?
We need to setup the right incentives (a credit system), where the users will get credit depending on the compute that they share. They will be able to use this credits to run stronger models than the one that they can afford on their devices. This would be similar to the future internet, where the models are running all over the web and everyone can access them.

As we are building a framework to run on any new model architecture the adoption of our framework means that we can have users sharing their GPUs by default as we provide lot of features (run any new model automatically, the system framework where the agent creates tool and use them, future events, automatic fine-tuning and personalized models....). This features make our framework very attractive, solving the actual pain of petals -> User adoption. Once that we start scaling it lot of users will be sharing GPU. Most of the time the GPUs are unused, with this mechanism everyone will have incentives to let other people use them (we can even have a store in the future to exchange the credits by bitcoins or other coins...).

A new decentralized internet of LLMs is comming!

I have been investigating the petals framework and there are some limitations:
- They have a custom logic, only some architectures are supported, this limits our possibility to run any new huggingface model. I'm investigating ways to generalize it, hopefully being able to run most of transformers architectures.
- They save catche on server side, which limits the possibility of multiple users using the same transformer -> This is the main limitation IMO, has even when we can do the hard effort of solve the model abstractions this limitation will block multiple users sharing same architecture, we might need to find a good way to solve this along the way...

Is not going to be an easy path, if we achieve the point where the ecosystem is adopted and most of the people select the option to contribute, then everyone would be able to run the strongest models even with small hardware, from their phones or other locations. The moment where LLMs become a commodity would be very close, as this would suppose the integration of most of the ongoing efforts.

## --- 16 / 12 ---

Building stability, injected user and planner in the flow, we are able to make requests now.

Talk with Nestor, preparing a clear scope for demo.

## --- 17 / 12 ---

Two core ideas today:
- Implement OpenAI API to ease development until we verify the full architecture.
- Tool Execution means -> Executing code. This will be useful to automate direct tasks, but we need to move to next level of automation VLA (Visual Language Action), Visual Language Models combined with different actions, in this case a keyboard and mouse to be able to interact with any device. The planner should be able to determine if we should use the visual or code tools. There is a new super intersting paper: [CogAgent](https://arxiv.org/pdf/2312.08914.pdf) releasing a 18B VLM fine-tuned for visual agents, I can't run it on my RTX 4080, but I will try to find the best way to run it.

Refactored to run private models (Only OpenAI for now, but should be trivial to add other APIs). Started a future implementation to ensure that running different OpenSource LLMs doesn't crash the system.

The implementation is naive at the moment. We are creating a new Chat() everytime we call each model, this function will call create_models at ModelsManager and it will stop all OSModels that are currently running. We should do better, but for this we need to calculate compatibility at start to ensure that the models are not running at the same time.


## --- 19 / 12 ---
Lot of papers pointing in the same direction.

We should fine-tune small models based on GPT-4 traces. For now one we should always save traces (ETA - TODAY.)

Potential OS models:
chat: https://huggingface.co/TheBloke/SOLAR-10.7B-Instruct-v1.0-uncensored-GPTQ

---

Plan:
- Make the full flow GPT-4 compatible, ensure that we can run all the steps.

Considerations:

### We need affordance before planner.

Some way to ask which kinds of tool would you use to solve this, explain. Then we grab them and send back to planner so he understand the current API.
Consider that a task can be achieved using very different methods depending on the granularity of the tools in hand.

Thinking if we should use "outlines" or "instructor" for our types... but none of them fits enough.

instructor:
- Doesn't provide tools format from functions (only pydantic classes....)

outlines:
- Provides the format but takes control over the model execution, which is not good at all...

At the end I implemented it from scratch trying to make it general enough so we can convert any OSS to the OpenAI format.

Lot of questions...
We have Planner - ToolExecutor - ToolCreator.

The difference between ToolCreator and the rest is very clear, same with user.

So we have: User -> (Planner - ToolExecutor) -> ToolCreator.

Two important things: Before planner we need a Affordance to generate a query and fetch the best tools.
Then on planner is not clear the difference between planning or just calling tools... Looks like one should be planning and another one executing but from Chain of Code paper from Deepmind we can inference that planning can be a symbolic representation of multiple function calls. Continuing tomorrow, getting closer to something that we can test, trying to make it generic enough to move from interaction user -> chatbot to a creation -> execution of any tool.

# --- 20/12 ---
Preparing system / user communication based on sockets naive implementation.

Main idea:
User will receive a Callable function to create/update requests.
System will receive a Callable function to update the status of a specific request - It should also be able to ask for missing info (important part, to clarify request).

I think an optimal solution can be: We have Status for each Request:
- NOT_STARTED
- IN_PROGRESS
- WAITING_FEEDBACK
- SUCCEEDED
- FAILED
- (CANCELED?) -> For future updates based on the mechanism that we use to update.

Lets start simple.
A common Network protocol that receives a Class that will call run and we link externally send/receive

New workflow:
1. User fill the Request as: Objective, Requirements, Contraints.
2. Based on Request search prepares queries for:
   1.  Relevant data: general queries for content related to the request
   2.  Past outcomes: previous similar requests.
   3.  User preferences.
3. Summarize info preparing a "Context" that grounds the request on "data", "user preferences" and "previous experiences".
4. Plan creates hypothetical approaches and provide "Potential tools", similar to a "blind affordance", we fetch from database and iterate until finding the correct tools.
5. Execute use the tools to achieve next step.


(ON STEP 4 PLAN CAN REQUEST OUR MODEL TO MAKE A TOOL TO ACHIEVE OUR OBJECTIVE.)
---
Very good improvements today, the abstractions on top of OpenAI based on Parser -> Conversation -> Chat are paying back. Now scaling the system. So far the chatbot is making requests and the planner is iterating until finding the right tools (affordance - planning). The executor has been refactored based on the new api from OpenAI where we can send tools as part of the completion.

Next steps:
1. Test the full flow with hardcoded tools.
2. Implement the vector database: The decision is very important. I have been working previously with REDISS and WEAVIATE, but QDRANT looks like a good alternative. Needs to be OS and have a big team working on improving the capabilities, also have the possibility to search by metadata and use a interesting algorithm (HNSW?), lets check performance from existing literature as this is one of the most important topics. I will also start designing the user - chatbot interaction where we will store info from the user that later will be useful for future tasks and a more personal treatment.

One of the limitations of current approach is that chatbot is slow, asking to GPT-4 to use tools increase the latency, to be investigated as an approach of streaming to get the response from user and later composing the JSON might be very interesting for our case. More and better comming soon, this is starting to look quite good!