# Import required modules
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
from tksheet import Sheet
from Dependency_graph import DependencyGraph
from Simulation_manager import *
from Database_manager import *
from os import listdir
from os.path import isfile, join
import pathlib
import traceback

# Define color constant
black = "#000000"

class UI_Manager_class:
    def __init__(self):
        # Initialize main application window
        self.root = Tk()
        self.root.title("Particle Dynamics in Fields")
        self.root.geometry("1280x720")

        # Define font styles
        self.fonts = {
            "button": ("Helvetica", 24, "bold")
        }

        # Simulation-related variables
        self.simulation = None          # Active simulation instance
        self.parent_particles = []      # Particles from base simulation
        self.store = None               # Current simulation data storage
        self.current_user = None        # Authenticated user
        self.db_manager = Database_manager()  # Database interaction handler
        self.sim_increment = 0.00001    # Fixed physics time step
        self.dependency_graph = DependencyGraph()  # Simulation version tracking

        # Input validation setup
        self.validate_int = (self.root.register(lambda P: str.isdigit(P) or P == ""))
        def isFloat(P):
            try:
                return True if P == "" or P == "0" or P == "0." else float(P)
            except:
                return False
        self.validate_float = (self.root.register(isFloat))

        # Color to vector mapping for particle visualization
        self.colour_mapping = {
            "white": vector(1, 1, 1),
            "red": vector(1, 0, 0),
            "green": vector(0, 1, 0),
            "blue": vector(0, 0, 1),
            "orange": vector(1, 0.6, 0),
            "purple": vector(0.4, 0.2, 0.6),
            "black": vector(0, 0, 0),
            "yellow": vec(1,1,0),
            "copper": vector(1,0.7,0.2)
        }

    def clear_window(self):
        # Remove all widgets from root window
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_filenames(self):
        # Get list of valid simulation files in current directory
        return [name for name in listdir(pathlib.Path().absolute()) 
                if isfile(join(pathlib.Path().absolute(), name)) 
                and name[-2:] not in ["py", "db"]]

    def exit(self):
        # Terminate application
        self.root.destroy()

    def start_simulation(self):
        # Close configuration UI and launch simulation
        self.exit()

        # Initialize appropriate simulation type based on analysis selection
        if self.with_analysis:
            self.simulation = SimulationVisualiser(self.store, 
                                                  E=self.sim_electric_on,
                                                  M=self.sim_magnetic_on,
                                                  G=self.sim_gravity_on,
                                                  with_minmax=self.with_minmax)
            self.simulation.load_graphs(self.selected_graphs)
        else:
            self.simulation = Sim(self.store, 
                                E=self.sim_electric_on,
                                M=self.sim_magnetic_on,
                                G=self.sim_gravity_on)
                
        # Precompute simulation data and run
        self.simulation.pre_compute()
        if self.with_minmax:
            self.simulation.calc_and_display_minmax()
        self.simulation.Run()

    def parse_vector(self, inp):
        # Convert various input formats to vpython vector
        if type(inp) == tuple:
            x, y, z = inp
            return vector(x, y, z)
        else:
            parts = inp.strip("()").split(",")
            x, y, z = map(float, parts)
            return vector(x, y, z)
    
    def start(self):        
        # Start application main loop
        self.authentication()
        self.root.mainloop()

    # Authentication flow methods
    def authentication(self):
        # School code verification screen
        Label(self.root, text="Particle Dynamics in Fields", 
             font=("Helvetica", 50, "bold")).pack()
        Label(self.root, text="Enter school code to begin: ",
             font=("Helvetica", 30, "bold")).pack(pady=20)

        # School code input field
        code_entry = Entry(self.root, font=("Helvetica", 32, "bold"))
        code_entry.pack()
        code_entry.bind("<Return>", lambda event: check_school_code(code_entry.get()))
        code_entry.focus()

        # Submission button
        submit_button = Button(self.root, text="Submit", 
                              font=("Helvetica", 32, "bold"),
                              command=lambda: check_school_code(code_entry.get()),
                              width=8)
        submit_button.pack(pady=10)

        def check_school_code(code):
            # Validate institutional access code
            if code == "Hampton":
                self.login_or_register()
            else:
                messagebox.showerror("Error", "Invalid school code")

    def login_or_register(self):
        # User authentication screen
        self.clear_window()
        Label(self.root, text="Please log in or register", 
             font=("Helvetica", 40, "bold")).pack()

        # Username input
        Label(self.root, text="Username:", font=self.fonts["button"]).pack(pady=10)
        username_entry = Entry(self.root, font=self.fonts["button"])
        username_entry.pack()
        username_entry.focus()

        # Password input
        Label(self.root, text="Password:", font=self.fonts["button"]).pack(pady=10)
        password_entry = Entry(self.root, font=self.fonts["button"], show="*")
        password_entry.pack()
        password_entry.bind("<Return>", lambda event: validate_login(username_entry.get(), 
                                                                    password_entry.get()))

        # Action buttons
        Button(self.root, text="Login", font=self.fonts["button"], 
              command=lambda: validate_login(username_entry.get(), 
                                            password_entry.get())).pack(pady=5)
        Button(self.root, text="Register", font=self.fonts["button"],
             command=lambda: validate_registration(username_entry.get(), 
                                                  password_entry.get())).pack(pady=5)

        def validate_login(username, password):
            # Database authentication check
            if self.db_manager.verify_user(username, password):
                self.current_user = username
                self.main_menu()
            else:
                messagebox.showerror("Invalid login", "Invalid credentials or user doesn't exist")

        def validate_registration(username, password):
            # New user account creation
            if self.db_manager.create_user(username, password):
                self.current_user = username
                self.main_menu()
            else:
                messagebox.showerror("Error", "Registration error - username likely exists")

    # Main application interface
    def main_menu(self):
        # Primary navigation screen
        self.clear_window()
        Label(self.root, text="What would you like to do", 
             font=("Helvetica", 40, "bold")).pack()

        # Main action buttons
        Button(self.root, text="Start new simulation",
             font=self.fonts["button"], command=self.new_simulation).pack(pady=5)
        Button(self.root, text="Load simulation",
             font=self.fonts["button"], command=self.load_simulation).pack(pady=5)
        Button(self.root, text="Exit",
             font=self.fonts["button"], command=self.exit).pack(pady=5)

    # New simulation configuration flow
    def new_simulation(self):
        # Simulation setup wizard
        self.clear_window()

        def toggle_parent_entry():
            # Handle base simulation selection UI state
            if base_sim_var.get() == "No":
                parent_dropdown.config(state=DISABLED)
            elif base_sim_var.get() == "Database":
                parent_dropdown['values'] = db_sims
                parent_dropdown.config(state=NORMAL)
            elif base_sim_var.get() == "File":
                parent_dropdown['values'] = file_sims
                parent_dropdown.config(state=NORMAL)
            parent_dropdown.delete(0, END)
        
        # Simulation rate controls
        def update_rate_entry(val):
            rate_entry.delete(0, END)
            rate_entry.insert(0, str(int(float(val))))
        
        def update_rate_slider(event):
            rate_slider.set(int(rate_entry.get()))

        # Simulation duration controls
        def update_duration_entry(val):
            duration_entry.delete(0, END)
            duration_entry.insert(0, str(float(val)))
        
        def update_duration_slider(event):
            duration_slider.set(float(duration_entry.get()))
        
        # Simulation name input
        Label(self.root, text="Simulation Name:").pack()
        name_entry = Entry(self.root)
        name_entry.pack()

        # Base simulation selection
        Label(self.root, text="Base this on an existing simulation?").pack()
        base_sim_var = StringVar(value="No")
        base_frame = Frame(self.root)
        base_frame.pack()
        Radiobutton(base_frame, text="No", variable=base_sim_var, 
                   value="No", command=toggle_parent_entry).pack(side=LEFT)
        Radiobutton(base_frame, text="From database", variable=base_sim_var,
                   value="Database", command=toggle_parent_entry).pack(side=LEFT)
        Radiobutton(base_frame, text="From file", variable=base_sim_var,
                   value="File", command=toggle_parent_entry).pack(side=LEFT)

        # Dropdown for existing simulations
        db_sims = self.db_manager.get_all_names()
        file_sims = self.get_filenames()
        parent_var = StringVar()
        parent_dropdown = Combobox(self.root, textvariable=parent_var, values=db_sims)
        parent_dropdown.pack()
        parent_dropdown.config(state=DISABLED)

        # Physics parameter controls
        Label(self.root, text="Simulation Rate (1-20):").pack()
        rate_frame = Frame(self.root)
        rate_frame.pack()
        rate_entry = Entry(rate_frame, width=5, validate="all", 
                          validatecommand=(self.validate_int, '%P'))
        rate_entry.pack(side=LEFT)
        rate_entry.insert(0, "10")
        rate_entry.bind("<Return>", update_rate_slider)
        rate_slider = Scale(rate_frame, from_=1, to=20, orient=HORIZONTAL,
                           command=update_rate_entry)
        rate_slider.set(10)
        rate_slider.pack(side=LEFT)

        Label(self.root, text="Simulation Duration (0-5 sec):").pack()
        duration_frame = Frame(self.root)
        duration_frame.pack()
        duration_entry = Entry(duration_frame, width=5, validate="all",
                              validatecommand=(self.validate_float, '%P'))
        duration_entry.pack(side=LEFT)
        duration_entry.insert(0, "2.5")
        duration_entry.bind("<Return>", update_duration_slider)
        duration_slider = Scale(duration_frame, from_=0, to=5, resolution=0.1,
                               orient=HORIZONTAL, command=update_duration_entry)
        duration_slider.set(2.5)
        duration_slider.pack(side=LEFT)

        # Field activation checkboxes
        fields_frame = Frame(self.root)
        fields_frame.pack()
        electric_var = BooleanVar()
        magnetic_var = BooleanVar()
        gravity_var = BooleanVar()
        Checkbutton(fields_frame, text="Enable electric fields",
                   variable=electric_var).pack(anchor=W)
        Checkbutton(fields_frame, text="Enable magnetic fields",
                   variable=magnetic_var).pack(anchor=W)
        Checkbutton(fields_frame, text="Enable gravitational fields",
                   variable=gravity_var).pack(anchor=W)

        def next_page():
            # Validate inputs and proceed to particle configuration
            self.sim_name = name_entry.get()
            self.sim_rate = float(rate_entry.get())
            self.sim_duration = float(duration_entry.get())
            self.sim_electric_on = electric_var.get()
            self.sim_magnetic_on = magnetic_var.get()
            self.sim_gravity_on = gravity_var.get()

            # Check for existing simulation name
            if self.db_manager.name_exists(self.sim_name):
                messagebox.showerror("Error", "Simulation name already exists")
                return

            # Handle base simulation selection
            if base_sim_var.get() != "No":
                parent_sim = parent_dropdown.get()
                self.dependency_graph.add_dependency(parent_sim, self.sim_name)
                
                if base_sim_var.get() == "Database":
                    try:
                        num_particles = self.db_manager.get_particle_count(parent_sim)
                        messagebox.showinfo("Particles added", 
                                          f"{num_particles} particles added from base")
                        particle_store = self.db_manager.pull_from_db(parent_sim)
                        self.parent_particles = particle_store
                    except Exception as e:
                        messagebox.showerror("Error", f"Database error: {e}")
                        return
                elif base_sim_var.get() == "File":
                    try:
                        SimulationState = File_Manager().import_file(parent_sim)
                        self.parent_particles = SimulationState.particles
                    except Exception as e:
                        messagebox.showerror("Error", f"File error: {e}")
                        return

            self.particles_page()

        Button(self.root, text="Next", command=next_page).pack()

    # Particle configuration screen
    def particles_page(self):
        self.clear_window()
        Label(self.root, text="Particle Information:").pack()
        
        # Spreadsheet-style particle input
        sheet_frame = Frame(self.root)
        sheet_frame.pack()
        sheet = Sheet(sheet_frame,
                     headers=["Charge", "Mass", "Position (X,Y,Z)", 
                             "Velocity (X,Y,Z)", "Radius", "Colour"],
                     width=600,
                     height=250)
        sheet.set_column_widths([70, 70, 120, 120, 70, 70])
        sheet.pack()
        sheet.enable_bindings()

        # Preload particles from base simulation
        for particle in self.parent_particles:
            colour = next(key for key, value in self.colour_mapping.items() 
                         if value == particle.colour)
            position = (particle.pos.x, particle.pos.y, particle.pos.z)
            velocity = (particle.velocity.x, particle.velocity.y, particle.velocity.z)
            sheet.insert_row([particle.charge, particle.mass, position, 
                            velocity, particle.radius, colour])
        
        # Initialize empty row if needed
        if len(sheet.get_sheet_data()) == 0:
            sheet.insert_row(["", "", "", "", "", ""])
        
        # Spreadsheet manipulation functions
        def add_row(charge="1", mass="1", pos=(0, 0, 0), 
                   vel=(0, 0, 0), radius="0.25", colour="red"):
            sheet.insert_row([charge, mass, pos, vel, radius, colour])
        
        def remove_selected_row():
            selected_rows = list(sheet.get_selected_rows())
            if selected_rows:
                for row in reversed(selected_rows):
                    sheet.delete_row(row)
            else:
                messagebox.showwarning("No selection", "Select rows to delete")
            
        def add_particle_from_text():
            # Command-line style particle input
            if (sheet.get_sheet_data() == ["", "", "", "", "", ""]):
                sheet.delete_row(0)

            try:
                data = particle_input.get()
                if data:
                    values = data.split()
                    if len(values) == 6:
                        sheet.insert_row(values)
                else:
                    raise Exception("Empty input")
            except:
                message = """Input format:
                CHARGE MASS INITIAL_POSITION INITIAL_VELOCITY RADIUS COLOUR
                Example: 0.25 100 (0,0,0) (0,0,0) 0.25 red"""
                messagebox.showerror("Error", message)
                
            particle_input.delete(0, END)

        def submit():
            # Process spreadsheet data into particles
            particles = []
            try:
                existing_positions = []
                for row in sheet.get_sheet_data():
                    charge = float(row[0])
                    mass = float(row[1])
                    pos_vector = self.parse_vector(row[2])
                    vel_vector = self.parse_vector(row[3])
                    radius = float(row[4])
                    colour = self.colour_mapping[row[5].lower()]

                    if mass <= 0.0 or radius <= 0.0:
                        messagebox.showerror("Error", "Invalid mass/radius")
                        return

                    if pos_vector in existing_positions:
                        messagebox.showerror("Error", "Duplicate positions")
                        return
                    
                    existing_positions.append(pos_vector)
                    particles.append(Particle(charge, mass, pos_vector, 
                                            vel_vector, vector(0,0,0), 
                                            radius, colour))
                
                # Create simulation state
                self.store = SimulationState(particles)
                self.store.build(self.sim_name, self.sim_rate, 
                                self.sim_increment, self.sim_duration)
                self.graphs_page()
                
            except Exception as e:
                messagebox.showerror("Error", f"Invalid particle data: {str(e)}")
        
        # UI controls
        button_frame = Frame(self.root)
        button_frame.pack()
        Button(button_frame, text="Add Particle", 
              command=lambda: add_row("", "", "", "", "", "")).pack(side=LEFT, padx=5)
        Button(button_frame, text="Remove Particle(s)", 
              command=remove_selected_row).pack(side=LEFT)

        # Preset particles
        Label(self.root, text="Particle presets:").pack()
        presets_frame = Frame(self.root)
        presets_frame.pack()
        Button(presets_frame, text="Add Proton", command=lambda: add_row(charge="0.25", mass="100", colour="red")).pack(side=LEFT)
        Button(presets_frame, text="Add Electron", command=lambda: add_row(charge="-0.25", mass="10", colour="blue")).pack(side=LEFT)
        Button(presets_frame, text="Add Neutron", command=lambda: add_row(charge="0", mass="100", colour="green")).pack(side=LEFT)

        Label(self.root, text="Or add particles using the command-line style in the following format:").pack()
        Label(self.root,
                        text="CHARGE MASS INITIAL_POSITION INITIAL_VELOCITY RADIUS COLOUR",
                        font=("Courier New", 14, "bold")).pack()
        
        input_frame = Frame(self.root)
        input_frame.pack()
        particle_input = Entry(input_frame, width=50)
        particle_input.pack(side=LEFT, padx=5)
        particle_input.bind("<Return>", lambda event: add_particle_from_text())
        Button(input_frame, text="Add", command=add_particle_from_text).pack(side=LEFT)
        
        Button(self.root, text="Next", command=submit).pack()

    def graphs_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        def toggle_graphs_frame():
            if analysis_var.get() == "Yes":
                minmax_checkbox.config(state=NORMAL)
                for child in graph_frame.winfo_children():
                    child.config(state=NORMAL)
            else:
                minmax_checkbox.config(state=DISABLED)
                for child in graph_frame.winfo_children():
                    child.config(state=DISABLED)

        
        Label(self.root, text="Include graphs and analysis?").pack()
        analysis_var = StringVar(value="No")
        analysis_frame = Frame(self.root)
        analysis_frame.pack()
        Radiobutton(analysis_frame, text="Yes", variable=analysis_var, value="Yes", command=toggle_graphs_frame).pack(side=LEFT)
        Radiobutton(analysis_frame, text="No", variable=analysis_var, value="No", command=toggle_graphs_frame).pack(side=LEFT)

        minmax_var = BooleanVar(value=True)
        minmax_checkbox = Checkbutton(self.root, text="Calculate min/max values?", variable=minmax_var)
        minmax_checkbox.pack()
        
        graph_frame = Frame(self.root)
        graph_frame.pack()
        Label(graph_frame, text="Graphs to include:").pack()

        kinetic_var = BooleanVar()
        speed_var = BooleanVar()
        force_var = BooleanVar()
        acceleration_var = BooleanVar()
        
        Checkbutton(graph_frame, text="Kinetic Energy", variable=kinetic_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Speed", variable=speed_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Net Force", variable=force_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Net Acceleration", variable=acceleration_var).pack(anchor=W)

        toggle_graphs_frame()
        
        Label(self.root, text="Save Simulation Data?").pack()
        save_var = StringVar(value="None")
        save_frame = Frame(self.root)
        save_frame.pack()

        def toggle_filename_entry():
            if(save_var.get() == "File"):
                filename_entry.config(state=NORMAL)
            else:
                filename_entry.config(state=DISABLED)

        Radiobutton(save_frame, text="Don't Save", variable=save_var, value="None", command=toggle_filename_entry).pack(anchor=W)
        Radiobutton(save_frame, text="Save to Database", variable=save_var, value="Database", command=toggle_filename_entry).pack(anchor=W)
        Radiobutton(save_frame, text="Save to File", variable=save_var, value="File", command=toggle_filename_entry).pack(anchor=W)
        
        fileinput_frame = Frame(self.root)
        fileinput_frame.pack()
        Label(fileinput_frame, text="Filename: ").pack(side=LEFT)
        filename_entry = Entry(fileinput_frame, width=20, state=DISABLED)
        filename_entry.pack(side=LEFT)

        
        def finalize():
            save_data = save_var.get()
            filename = filename_entry.get() if save_data == "File" else ""
            self.with_analysis = analysis_var.get() == "Yes"
            self.with_minmax = minmax_var.get()

            if save_data == "Database":
                dsm = Database_manager()
                dsm.attach_store(self.store)
                dsm.dump_to_db(self.current_user)
                pass

            if save_data == "File":
                fm = File_Manager()
                if filename in self.get_filenames():
                    messagebox.showerror("Invalid filename", "The filename you entered to save the simulation to already exists")
                    return
                
                fm.export_file(filename, self.store)
                pass

            self.selected_graphs = []

            if self.with_analysis:
                if kinetic_var.get():
                    self.selected_graphs.append("Kinetic Energy")
                if speed_var.get():
                    self.selected_graphs.append("Speed")
                if force_var.get():
                    self.selected_graphs.append("Net Force")
                if acceleration_var.get():
                    self.selected_graphs.append("Net Acceleration")

                self.with_minmax = minmax_var.get()

            self.start_simulation()

            
            
        Button(self.root, text="Start simulation", command=finalize).pack()


    def load_simulation(self):
        self.clear_window()
        Label(self.root, text="Select a simulation to load from the database:").pack()
        
        # Dropdown for database simulations
        db_sims = self.db_manager.get_all_names()  # Fetch saved simulations
        db_sim_var = StringVar()
        db_sim_dropdown = Combobox(self.root, textvariable=db_sim_var, values=db_sims, state="readonly")
        db_sim_dropdown.pack()
        
        Label(self.root, text="Or enter a filename to load from file:").pack()
        
        # Combobox for file-based simulations
        file_sims = self.get_filenames()
        file_sim_var = StringVar()
        file_sim_dropdown = Combobox(self.root, textvariable=file_sim_var, values=file_sims)
        file_sim_dropdown.pack()

        Label(self.root, text="Simulation settings:").pack()

        def update_rate_entry(val):
            rate_entry.delete(0, END)
            rate_entry.insert(0, str(int(float(val))))
        
        def update_rate_slider(event):
            rate_slider.set(int(rate_entry.get()))

        def update_duration_entry(val):
            duration_entry.delete(0, END)
            duration_entry.insert(0, str(float(val)))
        
        def update_duration_slider(event):
            duration_slider.set(float(duration_entry.get()))

        Label(self.root, text="Simulation Rate (1-20):").pack()
        
        rate_frame = Frame(self.root)
        rate_frame.pack()
        rate_entry = Entry(rate_frame, width=5, validate="all", validatecommand=(self.validate_int, '%P'))
        rate_entry.pack(side=LEFT)
        rate_entry.insert(0, "10")
        rate_entry.bind("<Return>", update_rate_slider)
        rate_slider = Scale(rate_frame, from_=1, to=20, orient=HORIZONTAL, command=update_rate_entry)
        rate_slider.set(10)
        rate_slider.pack(side=LEFT)

        Label(self.root, text="Simulation Duration (0-5 sec):").pack()
        duration_frame = Frame(self.root)
        duration_frame.pack()
        duration_entry = Entry(duration_frame, width=5, validate="all", validatecommand=(self.validate_float, '%P'))
        duration_entry.pack(side=LEFT)
        duration_entry.insert(0, "2.5")
        duration_entry.bind("<Return>", update_duration_slider)
        duration_slider = Scale(duration_frame, from_=0, to=5, resolution=0.1, orient=HORIZONTAL, command=update_duration_entry)
        duration_slider.set(2.5)
        duration_slider.pack(side=LEFT)

        fields_frame = Frame(self.root)
        fields_frame.pack()
        
        electric_var = BooleanVar()
        magnetic_var = BooleanVar()
        gravity_var = BooleanVar()
        
        Checkbutton(fields_frame, text="Enable electric fields", variable=electric_var).pack(anchor=W)
        Checkbutton(fields_frame, text="Enable magnetic fields", variable=magnetic_var).pack(anchor=W)
        Checkbutton(fields_frame, text="Enable gravitational fields", variable=gravity_var).pack(anchor=W)

        def toggle_graphs_frame():
            if analysis_var.get() == "Yes":
                minmax_checkbox.config(state=NORMAL)
                for child in graph_frame.winfo_children():
                    child.config(state=NORMAL)
            else:
                minmax_checkbox.config(state=DISABLED)
                for child in graph_frame.winfo_children():
                    child.config(state=DISABLED)
        
        Label(self.root, text="Include graphs and analysis?").pack()
        analysis_var = StringVar(value="No")
        analysis_frame = Frame(self.root)
        analysis_frame.pack()
        Radiobutton(analysis_frame, text="Yes", variable=analysis_var, value="Yes", command=toggle_graphs_frame).pack(side=LEFT)
        Radiobutton(analysis_frame, text="No", variable=analysis_var, value="No", command=toggle_graphs_frame).pack(side=LEFT)

        minmax_var = BooleanVar(value=True)
        minmax_checkbox = Checkbutton(self.root, text="Calculate min/max values?", variable=minmax_var)
        minmax_checkbox.pack()
        
        graph_frame = Frame(self.root)
        graph_frame.pack()

        Label(graph_frame, text="Graphs to include:").pack()

        kinetic_var = BooleanVar()
        speed_var = BooleanVar()
        force_var = BooleanVar()
        acceleration_var = BooleanVar()
        
        Checkbutton(graph_frame, text="Kinetic Energy", variable=kinetic_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Speed", variable=speed_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Net Force", variable=force_var).pack(anchor=W)
        Checkbutton(graph_frame, text="Net Acceleration", variable=acceleration_var).pack(anchor=W)
        toggle_graphs_frame()

        def load_selected_simulation():
            db_sim = db_sim_var.get()
            file_sim = file_sim_var.get()
            self.with_analysis = analysis_var.get() == "Yes"
            self.with_minmax = minmax_var.get()

            self.sim_rate = float(rate_entry.get())
            self.sim_duration = float(duration_entry.get())
            self.sim_electric_on = electric_var.get()
            self.sim_magnetic_on = magnetic_var.get()
            self.sim_gravity_on = gravity_var.get()

            self.selected_graphs = []
            if self.with_analysis:
                if kinetic_var.get():
                    self.selected_graphs.append("Kinetic Energy")
                if speed_var.get():
                    self.selected_graphs.append("Speed")
                if force_var.get():
                    self.selected_graphs.append("Net Force")
                if acceleration_var.get():
                    self.selected_graphs.append("Net Acceleration")

            if db_sim and file_sim:
                messagebox.showerror("Error", "Both database and file fields are populated. Please clear one of them to continue.")
                return
            
            if db_sim:
                self.sim_name = db_sim
                particle_store = self.db_manager.pull_from_db(db_sim)
                self.store = SimulationState(particle_store)
                self.store.build(db_sim, self.sim_rate, 0.00001, self.sim_duration)
            elif file_sim:
                try:
                    # Load the SimulationState from file
                    self.store = File_Manager().import_file(file_sim)
                except Exception as e:
                    messagebox.showerror("Error", f"Error while loading file: {e}")
                    return
            else:
                messagebox.showwarning("No Selection", "Please select a simulation to load.")
                return
            

            self.start_simulation()
            
                
        Button(self.root, text="Load simulation", command=load_selected_simulation).pack()

        


#manager = UI_Manager_class()


#manager.authentication()
#manager.load_simulation()
#manager.particles_page()
#manager.new_simulation()

# Run the Tkinter event loop
#manager.root.mainloop()