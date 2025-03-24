from collections import defaultdict, deque

class DependencyGraph:
    def __init__(self):
        self.graph = defaultdict(list)
    
    def add_dependency(self, parent_sim, child_sim):
        self.graph[parent_sim].append(child_sim)
    
    def get_all_dependencies(self, sim_name):
        """Get ALL simulations dependent on `sim_name` using BFS."""
        visited = set()
        queue = deque([sim_name])
        
        while queue:
            current = queue.popleft()
            if current not in visited:
                visited.add(current)
                queue.extend(self.graph[current])
        return list(visited)