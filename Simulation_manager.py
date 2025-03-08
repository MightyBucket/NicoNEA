from Collision_manager import *
from Database_manager import *
from Analysis_manager import *
from Particle_manager import *

from vpython import canvas, button, slider, wtext, rate, vector

class Sim(Collision_Handler):
    def __init__(self, data_store_obj, e=1, E=True, M=True, G=True):
        # Initialize the particle group and handle collisions
        parGroup = Particle_Group(data_store_obj.particles)
        super(Sim, self).__init__(parGroup, e)
        
        # Set up simulation parameters from the data store object
        self.name = data_store_obj.sim_name
        self.rate = data_store_obj.sim_rate
        self.scene = canvas(
            title="Fields Simulator", width=1000, height=800, center=vector(0, 0, 0),
            align="left", background=vector(1, 1, 1)
        )
        self.scene.userspin = True
        self.scene.userpan = True
        self.particles = parGroup
        self.t = 0
        self.dt = data_store_obj.sim_increment
        self.run_time = data_store_obj.sim_duration

        # Data store setup
        self.store = data_store_obj
        self.store.sim_rate = self.rate
        self.store.sim_increment = self.dt
        self.store.sim_duration = self.run_time
        self.store.sim_name = self.name
        self.E = E
        self.M = M
        self.G = G

        # Acceleration update functions
        self.acc_update_funcs = []
        self._field_calc()
        self.particles._precompute_pair_data()  # Initial precompute
        
        # Add flag for live updates
        self.live_update = True

        # Pause/Resume control
        self.running = False
        button(text="Run", pos=self.scene.title_anchor, bind=self.toggle_run)

        # Add sliders for each particle
        self._add_particle_sliders()

        # Add time slider
        self.time_slider = None
        self.frames_left = int(self.run_time / self.dt)
        self._add_time_slider()

        # Add checkboxes for fields
        self._add_field_checkboxes()

    def toggle_run(self, b):
        """Toggle the running state of the simulation."""
        self.running = not self.running
        if self.running:
            b.text = "Pause"
        else:
            b.text = "Run"

    def _add_particle_sliders(self):
        """Create individual sliders for each particle's mass and charge."""
        self.scene.append_to_caption("\nAdjust properties for each particle: \n\n")
        self.sliders = []

        for i, particle in enumerate(self.particles.array_particles):
            self.scene.append_to_caption(f"Particle {i+1} Mass: ")
            mass_slider = slider(
                min=0, max=10, value=particle.mass, length=220,
                bind=lambda s, p=particle: self.set_mass(s, p), right=15
            )
            mass_text = wtext(text='{:1.2f}'.format(mass_slider.value))
            self.scene.append_to_caption('\n')

            self.scene.append_to_caption(f"Particle {i+1} Charge: ")
            charge_slider = slider(
                min=-10, max=10, value=particle.charge, length=220,
                bind=lambda s, p=particle: self.set_charge(s, p), right=15
            )
            charge_text = wtext(text='{:1.2f}'.format(charge_slider.value))
            self.scene.append_to_caption('\n\n')

            self.sliders.append({
                "mass_slider": mass_slider,
                "mass_text": mass_text,
                "charge_slider": charge_slider,
                "charge_text": charge_text,
            })

    def set_mass(self, s, particle):
        particle.mass = s.value
        # Trigger immediate physics update
        self.live_update = True
        # Update displayed value
        slider_data = next(sl for sl in self.sliders 
                          if sl["mass_slider"] == s)
        slider_data["mass_text"].text = f'{s.value:.2f}'

    def set_charge(self, s, particle):
        particle.charge = s.value
        # Trigger immediate physics update
        self.live_update = True
        # Update displayed value
        slider_data = next(sl for sl in self.sliders 
                          if sl["charge_slider"] == s)
        slider_data["charge_text"].text = f'{s.value:.2f}'

    def _add_time_slider(self):
        """Add a time slider to move forward and backward in time."""
        self.scene.append_to_caption("\nAdjust Time:\n\n")
        self.time_slider = slider(
            min=0, max=self.frames_left, value=0, length=400,
            bind=self.update_time
        )
        self.time_text = wtext(text=f"Frame: {self.time_slider.value}/{self.frames_left - 1}")

    def update_time(self, s):
        """Update the time frame of the simulation."""
        if not self.running:  # Only allow manual updates when the simulation is paused
            frame = int(s.value)  # Get the slider's current frame value
            self.time_text.text = f"Frame: {frame}"

            # Update particle positions for the selected frame
            particle_index = -1
            for particle in self.particles.array_particles:
                particle_index = (particle_index + 1) % self.particles.array_size
                particle.pos = self.store.pos_data[particle_index][frame]
                particle.update_obj_position()

    def _add_field_checkboxes(self):
        """Add checkboxes to enable/disable electric, magnetic, and gravitational fields."""
        self.scene.append_to_caption("\nToggle Fields:\n\n")

        self.e_checkbox = checkbox(
            bind=self.toggle_electric_field, text='Electric Field', checked=self.E
        )
        self.scene.append_to_caption("\n")

        self.m_checkbox = checkbox(
            bind=self.toggle_magnetic_field, text='Magnetic Field', checked=self.M
        )
        self.scene.append_to_caption("\n")

        self.g_checkbox = checkbox(
            bind=self.toggle_gravitational_field, text='Gravitational Field', checked=self.G
        )
        self.scene.append_to_caption("\n")

    def toggle_electric_field(self, evt):
        self.E = evt.checked
        self._update_acc_update_funcs()
        self.live_update = True  # Force recompute

    def toggle_magnetic_field(self, evt):
        """Toggle the magnetic field on or off."""
        self.M = evt.checked
        self._update_acc_update_funcs()

    def toggle_gravitational_field(self, evt):
        """Toggle the gravitational field on or off."""
        self.G = evt.checked
        self._update_acc_update_funcs()
        self.live_update = True  # Force recompute

    def _update_acc_update_funcs(self):
        """Rebuild the acceleration update functions list based on enabled fields."""
        self.acc_update_funcs = []
        self._field_calc()

    def _field_calc(self):
        if self.E:
            self.acc_update_funcs.append(self.particles.E_Acceleration_Update)
        if self.M:
            self.acc_update_funcs.append(self.particles.M_Acceleration_Update)
        if self.G:
            self.acc_update_funcs.append(self.particles.G_Acceleration_Update)

    def _loadParticles(self):
        count = -1
        for particle in self.particles.array_particles:
            count = (count + 1) % self.particles.array_size
            particle.generate()

    def _compute_frame(self):
        if self.live_update:
            # Force recompute of particle pairs with latest positions
            self.particles._precompute_pair_data()

        for func in self.acc_update_funcs:
            func()

        self.collisionDetection() 
        count = -1
        dt = self.dt  # Accessing `self.dt` once outside the loop for efficiency
        size = self.particles.array_size  # Similarly, pre-fetch size to avoid repeated lookups
        particles = self.particles.array_particles  # Pre-fetch the particle array

        # Use enumerate to handle count updates and perform operations
        for count, particle in enumerate(particles):
            particle.velocity += particle.acceleration * dt
            particle.pos += particle.velocity * dt

            # Store updated values in one go for each particle
            self.store.add_to_pos(count % size, particle.pos)
            self.store.add_to_vel(count % size, particle.velocity)
            self.store.add_to_acc(count % size, particle.acceleration)

        self.t += dt

        self.particles.resetAccelerations()

    def pre_compute(self): 
        while self.t < self.run_time: 
            self._compute_frame()

        for func in self.acc_update_funcs: 
            func()

        count = -1 
        for particle in self.particles.array_particles:
            count = (count + 1) % self.particles.array_size 
            self.store.add_to_acc(count, particle.acceleration)

    def handle_mouse_down(self):
        for particle in self.particles.array_particles:
            particle.handle_mouse_down(self.scene)

    def handle_mouse_drag(self):
        for particle in self.particles.array_particles:
            particle.handle_mouse_drag(self.scene)

    def handle_mouse_up(self):
        for particle in self.particles.array_particles:
            particle.handle_mouse_up(particle)


    def Run(self):
        frames_left = int(self.run_time / self.dt)

        # Initialize all particle positions in a single batch operation
        initial_positions = [pos[0] for pos in self.store.pos_data]
        for particle, pos in zip(self.particles.array_particles, initial_positions):
            particle.pos = pos

        self._loadParticles()

        # Start from the slider’s position
        iter_count = int(self.time_slider.value) - 1

        # Precompute reusable data
        #particle_count = len(self.particles.array_particles)
        #masses = [self.store.initial_conditions[i]["Mass"] for i in range(particle_count)]

        # Bind mouse events for all particles (avoiding repeated calls during pause)
        self.scene.bind("mousedown", lambda evt: self.handle_mouse_down())
        self.scene.bind("mousemove", lambda evt: self.handle_mouse_drag())
        self.scene.bind("mouseup", lambda evt: self.handle_mouse_up())

        # Main simulation loop
        while iter_count < frames_left - 1:
            if self.running:  # Run the simulation only if not paused
                Sim._update_acc_update_funcs(self)
                rate(self.rate)
                iter_count += 1

                # Update the slider's value
                self.time_slider.value = iter_count

                # Batch extraction of frame data
                frame_pos_data = [pos[iter_count] for pos in self.store.pos_data]

                # Batch update of particle positions
                for particle, pos in zip(self.particles.array_particles, frame_pos_data):
                    particle.pos = pos
                    particle.update_obj_position()
            else:  # Paused state
                rate(10)  # Reduce processing frequency to save resources

        # Reduce pos_data to the last frame's positions (batch operation)
        self.store.pos_data = [pos[-1] for pos in self.store.pos_data]






class Sim_With_Analysis(Sim, Analysis_methods):
    # Inherits SIM class and overrides the Run()
    def __init__(self, data_store_obj, e=1, E=True, M=True, G=True):
        super(Sim_With_Analysis, self).__init__(data_store_obj, e, E, M, G)
        self.graph_units = Analysis_methods().graph_units
        self.var_to_func = Analysis_methods().var_to_func

    def load_graphs(self, arr_vars):
        for variable in arr_vars:
            if variable not in self.graph_units.keys():
                return NameError("The variable given is not one of the options")

        self.Graphs = {}
        self.Lines = {}
        for variable in arr_vars:

            self.Graphs[variable] = graph(width=1000, height=600, align="left", title="{} vs Time".format(variable), xtitle="Time /s", ytitle=self._get_axis_title(variable), foreground=color.black, background=color.white)
            self.Lines[variable] = [gcurve(graph=self.Graphs[variable], color=par_desc["Colour"]) for par_desc in self.store.initial_conditions]

    def _get_axis_title(self, att):
        return "{} /{}".format(att, self.graph_units[att])

    def Run(self):
        frames_left = int(self.run_time / self.dt)
        time = 0
        self._loadParticles()

        # Initialize all particle positions in a single step
        for particle, pos_data in zip(self.particles.array_particles, self.store.pos_data):
            particle.pos = pos_data[0]

        iter_count = 0

        # Precompute constants and avoid repetitive dictionary lookups
        masses = [self.store.initial_conditions[i]["Mass"] for i in range(self.particles.array_size)]

        # Main simulation loop
        while iter_count < frames_left:
            #if not self.running:
            #    rate(self.rate)  # Ensures smooth rendering while paused
            #    continue
            time += self.dt
            rate(self.rate)

            # Extract frame-specific data for all particles in one step
            frame_pos_data = [pos[iter_count] for pos in self.store.pos_data]
            frame_vel_data = [vel[iter_count] for vel in self.store.vel_data]
            frame_acc_data = [acc[iter_count] for acc in self.store.acc_data]

            # Update all particles
            for idx, (particle, pos, vel, acc, mass) in enumerate(
                zip(self.particles.array_particles, frame_pos_data, frame_vel_data, frame_acc_data, masses)
            ):
                particle.pos = pos
                particle.velocity = vel
                particle.acceleration = acc

                particle.update_obj_position()

                # Update lines for each variable using the external index
                for variable, line_array in self.Lines.items():
                    dependent_d = self.var_to_func[variable](vel_v=vel, mass=mass, acc_v=acc)
                    line_array[idx].plot(time, dependent_d)

            iter_count += 1