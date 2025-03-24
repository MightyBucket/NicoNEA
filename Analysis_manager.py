from functools import lru_cache

class Analysis_methods():
    def __init__(self):
        # Dictionary that returns the units for the variable the graph displays
        self.graph_units = {
            "Kinetic Energy": "Joules",
            "Speed": "Metres per second",
            "Net Force": "Newtons",
            "Net Acceleration": "Metres per second squared"
        }

        # Dictionary that returns the functions for the variable the user wants
        self.var_to_func = {
            "Kinetic Energy": self.get_KE,
            "Speed": self.get_speed,
            "Net Force": self.get_net_force,
            "Net Acceleration": self.get_net_acc
            # *** ADD ACC_DATA TO DATASTORE IN FUTURE
        }
    def _recursive_sum(self, arr):
        """Recursively sum array elements (demo for nested energy components)"""
        if not arr:
            return 0
        return arr[0] + self._recursive_sum(arr[1:])


    #@lru_cache(maxsize=1000)
    def v_size(self, vel_v):
        return (vel_v.x**2 + vel_v.y**2 + vel_v.z**2)**0.5
    
    #@lru_cache(maxsize=1000)
    def get_KE(self, vel_v, mass, acc_v=None):
        return 0.5 * mass * self.v_size(vel_v)**2

    # The following functions take the same inputs, because these will be returned as values from the dictionary
    def get_speed(self, vel_v, mass=None, acc_v=None):
        return self.v_size(vel_v)

    def get_net_acc(self, vel_v=None, mass=None, acc_v=None):
        return self.v_size(acc_v)

    def get_net_force(self, vel_v=None, mass=None, acc_v=None):
        return self.get_net_acc(vel_v=None, mass=None, acc_v=acc_v) * mass

class Analysis_handler(Analysis_methods):
    def __init__(self, data_store_obj):
        super(Analysis_handler, self).__init__()
        self.run_time = data_store_obj.sim_duration
        self.increment = data_store_obj.sim_increment
        self.masses = [par["Mass"] for par in data_store_obj.initial_conditions]
        self.pos_data = data_store_obj.pos_data
        self.vel_data = data_store_obj.vel_data
        self.acc_data = data_store_obj.acc_data

    # Performs one of the functions such as get_KE on the array of particle data to get an array of datapoints
    def process_data(self, var_name):
        result_data = []
        func = self.var_to_func[var_name]
        for i in range(len(self.masses)):
            par_data = []
            for j in range(len(self.vel_data[i])):
                # func is one of the functions returned from the var_to_func dictionary
                data = func(self.vel_data[i][j], self.masses[i], self.acc_data[i][j])
                par_data.append((i, data))
            result_data.append(par_data)
        return result_data

    # Couples timestamps with datapoints - returns an array such as [[[time, value], (...),...] for each particle]
    def _add_time(self, data):
        # coupling the data points in data with time
        for particle in data:
            for i in range(len(particle)):
                particle[i] = (i*self.increment, particle[i])

    # Utilises the mergesort algorithm to get the first and last values after the processed data is sorted
    def find_min_max(self, var_name):
        minmax_dct = {"Minimum": [], "Maximum": []}
        for particlelst in self.process_data(var_name):
            self.m_sort(particlelst)
            minmax_dct["Minimum"].append(particlelst[0])
            minmax_dct["Maximum"].append(particlelst[-1])
        return minmax_dct

    def m_sort(self, arr):
        if len(arr) > 1:
            midpoint = len(arr)//2
            # Array is split
            left = arr[:midpoint]
            right = arr[midpoint:]
            # Halves are sorted
            self.m_sort(left)
            self.m_sort(right)

            i = j = k = 0
            # Data is copied
            while i < len(left) and j < len(right):
                if left[i][1] < right[j][1]:
                    arr[k] = left[i]
                    i += 1
                else:
                    arr[k] = right[j]
                    j += 1
                k += 1

            # Any remaining data is copied
            while i < len(left):
                arr[k] = left[i]
                i += 1
                k += 1

            while j < len(right):
                arr[k] = right[j]
                j += 1
                k += 1
