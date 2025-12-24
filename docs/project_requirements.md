Build a langgraph Project with these features:

1. You must use langgraph as primary agentic impl
2. it should manage state using state Graph
3. all methods and variables should have types defined correctly
4. There should be agents folder in which agents specific folder will go
5. Each agent will have it's prompt in md file and tools in tools folder with proper decorator
6. Must use Groq for llm
7. create agents like: neo4j database agent, file system agent, generate agent
8. there should be supervisor and task planner agent
9. supervisor and task planner agents output should be pydantic object in fixed format
    - Supervisor will be used for analyzing the user intent, knows how many agents there are in the system
    - The planner agent should be used for selecting the plan and plan should have task already defined. knows how many agents there are in the system
    - Routing should be done based on the Task list.
    - Each task will have it's agent name and little description using which agent will performs the task.
    - Each agent after completing the task gets back to the supervisor then based on the task list supervisor again reroutes to another agent.
    - After completion of all task supervisor ENDS the workflow.

10. Logger that logs everything in a logs/timestamp_log.log should be used in all other files
11. for LLM there should be llm instance which will be used by all other files.
12. use .env for reading credentials and configurations.
13. All agents and tools should have functionality to provide status which agent which tools is being used.
14. result should be structured it should contains how many times agent/tool is being for a single user input. for better tracibility.
15. use pyproject.toml  (python 3.12 and above) file - use dependencies array with proper version like: >= 2.2.2
16. Create CLI tool feature - it should use rich for interactive console.
17. Create other required files like: readme, gitignore etc.
Note: 
    - status tracking is important 
    - use json file for task management if needed (task/task_1.json) only if needed

expected project structure:
root (already created):
    /src
        /models
        /llm
        /agents
            /agent1
                /tools
                    tool1.py
                prompt.md
                agent1.py
    /docs
    main.py
    cli.py
    ...


Example Flow::::

User input: analyze the graph and save the result in the analysis.md file
    |
Supervisor (route to planner as task list is not created)
    |
Plannner (Creates tasklist, this agent has knowledge of all available agent and thier capabilities)[{agent: neo4j, task: get few nodes from each label and analyze it}, {agent: filesysetm, task: get the analysis done by the neo4j agent and then write the result in the analysis.md file}] 
    |
NEo4j Agent (get the nodes by using available tools) 
    |
Supervisor [task done by neo4j, now route to filesystem]
    |
File system agent (write the file with content, using tools)
    |
Supervisor
    | <if all task done>
END the flow
    |
Result to the user

-----------------------
useful reference urls:
1. https://docs.langchain.com/oss/python/langgraph/overview
