python -c "
import os
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', '')
from graph.graph import agent
from langchain_core.messages import HumanMessage
result = agent.invoke({
    'user_input': 'write hello world',
    'messages': [HumanMessage(content='write hello world')],
    'plan': [],
    'current_step': 0,
    'selected_tool': None,
    'tool_input': None,
    'tool_result': None,
    'error_log': [],
    'iteration_count': 0,
    'final_output': None,
})
print(result)
"