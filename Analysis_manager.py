from functools import lru_cache

class PhysicsCalculator:
    def __init__(self):
        # Measurement units for different physics quantities
        self.graph_units = {
            "Kinetic Energy": "Joules",
            "Speed": "Metres per second",
            "Net Force": "Newtons",
            "Net Acceleration": "Metres per second squared"
        }

        # Mapping of physics quantities to their calculation methods
        self.var_to_func = {
            "Kinetic Energy": self.get_KE,
            "Speed": self.get_speed,
            "Net Force": self.get_net_force,
            "Net Acceleration": self.get_net_acc
        }

    # Recursive sum for potential energy component calculations
    def _recursive_sum(self, arr):
        if not arr:
            return 0
        return arr[0] + self._recursive_sum(arr[1:])

    # Calculate magnitude of velocity vector with caching
    #@lru_cache(maxsize=1000)
    def v_size(self, vel_v):
        # Pythagorean theorem for 3D vector magnitude
        return (vel_v.x**2 + vel_v.y**2 + vel_v.z**2)**0.5
    
    # Kinetic energy calculation (½mv²)
    #@lru_cache(maxsize=1000)
    def get_KE(self, vel_v, mass, acc_v=None):
        return 0.5 * mass * self.v_size(vel_v)**2

    # Get speed from velocity vector magnitude
    def get_speed(self, vel_v, mass=None, acc_v=None):
        return self.v_size(vel_v)

    # Calculate net acceleration magnitude
    def get_net_acc(self, vel_v=None, mass=None, acc_v=None):
        return self.v_size(acc_v)

    # Newton's second law: F = ma
    def get_net_force(self, vel_v=None, mass=None, acc_v=None):
        return self.get_net_acc(vel_v=None, mass=None, acc_v=acc_v) * mass

class Analysis_manager(PhysicsCalculator):
    def __init__(self, SimulationState_obj):
        super(Analysis_manager, self).__init__()
        # Initialize simulation parameters from state object
        self.run_time = SimulationState_obj.sim_duration  # Total simulation time
        self.increment = SimulationState_obj.sim_increment  # Time step size
        self.masses = [par["Mass"] for par in SimulationState_obj.initial_conditions]
        self.pos_data = SimulationState_obj.pos_data  # Position history
        self.vel_data = SimulationState_obj.vel_data  # Velocity history
        self.acc_data = SimulationState_obj.acc_data  # Acceleration history

    # Process particle data for specified physical quantity
    def process_data(self, var_name):
        result_data = []
        calculation_func = self.var_to_func[var_name]
        
        # Calculate values for each particle over time
        for part_id in range(len(self.masses)):
            particle_history = []
            for time_step in range(len(self.vel_data[part_id])):
                # Calculate physics value for this time step
                value = calculation_func(
                    self.vel_data[part_id][time_step],
                    self.masses[part_id],
                    self.acc_data[part_id][time_step]
                )
                particle_history.append((time_step * self.increment, value))
            result_data.append(particle_history)
        return result_data

    # Merge sort implementation for finding extreme values
    def m_sort(self, arr):
        if len(arr) > 1:
            mid = len(arr) // 2
            left = arr[:mid]
            right = arr[mid:]

            # Recursive sorting of halves
            self.m_sort(left)
            self.m_sort(right)

            # Merge sorted halves
            i = j = k = 0
            while i < len(left) and j < len(right):
                if left[i][1] < right[j][1]:
                    arr[k] = left[i]
                    i += 1
                else:
                    arr[k] = right[j]
                    j += 1
                k += 1

            # Handle remaining elements
            while i < len(left):
                arr[k] = left[i]
                i += 1
                k += 1

            while j < len(right):
                arr[k] = right[j]
                j += 1
                k += 1

    # Find minimum and maximum values for a given quantity
    def find_min_max(self, var_name):
        extremes = {"Minimum": [], "Maximum": []}
        processed_data = self.process_data(var_name)
        
        for particle_data in processed_data:
            self.m_sort(particle_data)
            extremes["Minimum"].append(particle_data[0])   # First element after sort
            extremes["Maximum"].append(particle_data[-1])  # Last element after sort
        
        return extremes