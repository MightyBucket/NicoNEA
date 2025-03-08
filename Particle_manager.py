from vpython import *

class Particle:
    def __init__(self, charge, mass, initial_position, initial_velocity, initial_acceleration, radius, colour):
        self.pos = initial_position
        self.radius = radius
        self.colour = colour
        self.make_trail = False
        
        self.trail_type = "points"
        self.interval = 20
        self.retain = 100
        
        self.charge = charge
        self.mass = mass
        self.velocity = initial_velocity
        self.acceleration = initial_acceleration
        
        self.object = None
        self.is_dragging = False

        # Variables to manage dragging
        self.dragging = False
        self.drag_offset = vector(0, 0, 0)
        self.drag_plane_normal = vector(0, 0, 1)  # will be updated on drag start
        self.drag_plane_point = vector(0, 0, 0)

    def get_desc(self):
        return {
            "Charge": self.charge,
            "Mass": self.mass,
            "Position": self.pos,
            "Velocity": self.velocity,
            "Acceleration": self.acceleration,
            "Radius": self.radius,
            "Colour": self.colour,
        }

    def generate(self):
        if self.object is None:
            self.object = simple_sphere(
                pos=self.pos, radius=self.radius, make_trail=self.make_trail,
                trail_type=self.trail_type, interval=self.interval, retain=self.retain,
                color=self.colour
            )

    def delete_object(self):
        self.visible = False
        del self

    def does_collide_with(self, second_par):
        return mag(self.pos - second_par.pos) < (self.radius + second_par.radius)

    def update_position(self, new_pos):
        self.pos = new_pos
        if self.object:
            self.object.pos = new_pos

    def update_obj_position(self):
        self.object.pos = self.pos

    def is_clicked(self, click_pos):
        return mag(self.pos - click_pos) <= self.radius

    def handle_mouse_down(self, scene):
        # Use scene.mouse.pick to get the object that was clicked
        picked = scene.mouse.pick
        #print(f"Picked is {picked} while I am {particle.object}")
        if picked is self.object:
            self.dragging = True
            # Define the drag plane to be perpendicular to the current view
            self.drag_plane_normal = scene.forward
            self.drag_plane_point = self.object.pos
            # Project the mouse ray onto the drag plane
            proj = scene.mouse.project(normal=self.drag_plane_normal, d=dot(self.drag_plane_normal, self.drag_plane_point))
            if proj:
                self.drag_offset = self.object.pos - proj
                

    def handle_mouse_drag(self, scene):
        if self.dragging:
            # Project the current mouse position onto the drag plane
            proj = scene.mouse.project(normal=self.drag_plane_normal, d=dot(self.drag_plane_normal, self.drag_plane_point))
            if proj:
                self.object.pos = proj + self.drag_offset

    def handle_mouse_up(self):
        self.dragging = False

    

    def bind_mouse_events(self, scene):
        scene.bind("mousedown", lambda evt: self.handle_mouse_down(evt, self))
        scene.bind("mousemove", lambda evt: self.handle_mouse_drag(evt, self))
        scene.bind("mouseup", lambda evt: self.handle_mouse_up(self))
        print("Functions bound")


class Data_store:
    def __init__(self, par_desc):
        self.particles = par_desc
        self.initial_conditions = [particle.get_desc() for particle in par_desc]
        self.sim_name = None
        self.sim_rate = None
        self.sim_increment = None
        self.sim_duration = None
        
        self.pos_data = [[] for _ in par_desc]
        self.vel_data = [[] for _ in par_desc]
        self.acc_data = [[] for _ in par_desc]

    def build(self, sim_name, rate, increment, duration):
        self.sim_name = sim_name
        self.sim_rate = rate
        self.sim_increment = increment
        self.sim_duration = duration

        for i in range(len(self.particles)):
            self.add_to_pos(i, self.particles[i].pos)
            self.add_to_vel(i, self.particles[i].velocity)

    def set_pos_data(self, new_pos_data):
        self.pos_data = new_pos_data

    def set_vel_data(self, new_vel_data):
        self.vel_data = new_vel_data

    def set_acc_data(self, new_acc_data):
        self.acc_data = new_acc_data

    def add_to_pos(self, par_index, data):
        self.pos_data[par_index].append(data)

    def add_to_vel(self, par_index, data):
        self.vel_data[par_index].append(data)

    def add_to_acc(self, par_index, data):
        self.acc_data[par_index].append(data)

class Particle_Group:
    def __init__(self, list_particle_objs):
        self.array_particles = list_particle_objs
        self.array_size = len(self.array_particles)
        self.array_pairs = self._calc_par_pairs()
        self.precomputed_pairs = []  # Store precomputed values for reuse
        self._precompute_pair_data()

    def _calc_par_pairs(self):
        return [(self.array_particles[i], self.array_particles[j]) for i in range(self.array_size) for j in range(i + 1, self.array_size)]
    
    def _precompute_pair_data(self):
        """Precompute r_vec and direction for all pairs once per timestep"""
        epsilon = 1e-9
        self.precomputed_pairs = []
        for i, j in self.array_pairs:
            p1 = i
            p2 = j
            r_vec = p1.pos - p2.pos
            r = mag(r_vec) + epsilon
            direction = r_vec / r
            self.precomputed_pairs.append( (i, j, r_vec, r, direction) )

    def resetAccelerations(self):
        for p in self.array_particles:
            p.acceleration = vector(0,0,0)

    def E_Acceleration_Update(self):
        k = 8.99e9
        for p1, p2, r_vec, r, dir in self.precomputed_pairs:
            force = (k * p1.charge * p2.charge) / r**2 * dir
            p1.acceleration += force / p1.mass
            p2.acceleration -= force / p2.mass

    def G_Acceleration_Update(self):
        G = 6.67e-11
        for p1, p2, r_vec, r, dir in self.precomputed_pairs:
            force = (G * p1.mass * p2.mass) / r**2 * -dir
            p1.acceleration += force / p1.mass
            p2.acceleration += force / p2.mass

    def M_Acceleration_Update(self):
        k = 1e-7
        for i, j, r_vec, r, dir in self.precomputed_pairs:
            p1 = i
            p2 = j
            
            # Force on p2 from p1's field
            B = (k * p1.charge * cross(p1.velocity, dir)) / r**2
            force_p2 = p2.charge * cross(p2.velocity, B)
            p2.acceleration += force_p2 / p2.mass
            
            # Force on p1 from p2's field (reciprocal)
            B_recip = (k * p2.charge * cross(p2.velocity, -dir)) / r**2
            force_p1 = p1.charge * cross(p1.velocity, B_recip)
            p1.acceleration += force_p1 / p1.mass