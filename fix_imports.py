import os

files = [
    'graph/graph.py', 'graph/nodes.py', 'graph/edges.py', 'graph/state.py',
    'llm/client.py', 'tools/executor.py', 'tools/search.py', 'tools/docs.py',
    'memory/store.py', 'tracing/langsmith.py', 'api/main.py'
]

for f in files:
    with open(f, 'r') as fh:
        content = fh.read()
    content = content.replace('from agentcoder.', 'from ')
    content = content.replace('import agentcoder.', 'import ')
    with open(f, 'w') as fh:
        fh.write(content)
    print(f'Fixed: {f}')