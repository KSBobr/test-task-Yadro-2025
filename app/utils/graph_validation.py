from collections import defaultdict, deque

def validate_dag(nodes: list[dict], edges: list[dict]) -> bool:
    adjacency = defaultdict(list)
    in_degree = {node['name']: 0 for node in nodes}
    
    for edge in edges:
        adjacency[edge['source']].append(edge['target'])
        in_degree[edge['target']] += 1
    
    queue = deque([node['name'] for node in nodes if in_degree[node['name']] == 0])
    visited = 0
    
    while queue:
        current = queue.popleft()
        visited += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return visited == len(nodes)