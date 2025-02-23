class SimulationCache:
    def __init__(self):
        self._cache = {}  # Hash table {sim_name: data_store_obj}
        self._max_size = 10
        
    def get(self, sim_name):
        return self._cache.get(sim_name)
    
    def add(self, sim_name, data_store):
        if len(self._cache) >= self._max_size:
            self._cache.popitem()
        self._cache[sim_name] = data_store
        
    def invalidate(self, sim_name):
        if sim_name in self._cache:
            del self._cache[sim_name]