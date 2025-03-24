from Simulation_manager import *
from Database_manager import *
from os import listdir
from os.path import isfile, join
import pathlib
from Dependency_graph import DependencyGraph

class Interfacemanager_class:
    def __init__(self):
        self.invalid_msg = "INVALID INPUT - PLEASE TRY AGAIN"
        self.start_msg = """
        ***OPTIONS MENU*** --> UI will be moved to simulation page soon

        START NEW SIMULATION (1)
        LOAD FROM DATABASE (2)
        LOAD FROM FILE (3)
        EXIT (4)

        ENTER 1, 2, 3 or 4 : """
        self.sim_name_msg = "ENTER SIMULATION NAME : "
        self.sim_rate_msg = "ENTER SIMULATION RATE(~20) : "
        self.sim_dur_msg = "ENTER SIMULATION DURATION IN SECONDS (0-50) : "
        self.sim_isE_msg = "TURN ELECTRIC FIELDS ON (y/n) : "
        self.sim_isM_msg = "TURN MAGNETIC EFFECTS ON (y/n) : "
        self.sim_isG_msg = "TURN GRAVITATIONAL FIELDS ON (y/n) : "
        self.enter_par_msg = """
        ***PARTICLE INFORMATION***
        
        PLEASE 
        EITHER PUT IN PROTON/ELECTRON/NEUTRON INITIAL_POSITION

        OR ENTER YOUR PARTICLE'S:

        CHARGE MASS INITIAL_POSITION INITIAL_VELOCITY RADIUS COLOUR

        1. REPRESENTING POSITION AND VELOCITY LIKE SO:(X_VALUE,Y_VALUE,Z_VALUE)
        2. CHOOSING A COLOUR FROM: red, orange, green, blue, purple, black, white

        example choice: 0.25 100 (0,0,0) 0.25 red (0,0,0)

        PRESS ENTER TO ADD ANOTHER PARTICLE
        PRESS ENTER TWICE TO STOP ADDING PARTICLES
        """
        self.ask_analys_msg = "INCLUDE GRAPHS? (y/n) : "
        self.analys_options = """
        ***WHICH GRAPH(s)?***

        KINETIC ENERGY (1)
        SPEED (2)
        NET FORCE (3)
        NET ACCELERATION (4)
        ENTER NUMBERS SEPARATED WITH SPACES

        """
        self.compute_complete_msg = "SIMULATION DATA COMPLETE"
        self.ask_run_msg = "ENTER y TO RUN OR n TO SKIP RUNNING: "
        self.ask_minmax_msg = "FIND MIN/MAX VALUES OF GRAPHS? (y/n): "
        self.ask_save_msg = "SAVE SIMULATION DATA? (y/n): "
        self.save_options_msg = "ENTER 1 TO SAVE TO DATABASE, ENTER 2 TO SAVE TO FILE: "
        self.sim_exists_msg = "A SIMULATION UNDER THE SAME NAME ALREADY EXISTS IN DATABASE"
        self.enter_new_name_msg = "ENTER NEW NAME: "
        self.db_save_success_msg = "SAVED SUCCESSFULLY TO DATABASE"
        self.file_exist_msg = "THESE FILES ALREADY EXIST IN THIS DIRECTORY: "
        self.enter_new_filename_msg = "ENTER NEW FILENAME TO SAVE UNDER: "
        self.file_save_success_msg = "SAVED SUCCESSFULLY TO FILE"
        self.db_empty_msg = "THE SIMULATION DATABASE IS CURRENTLY EMPTY"
        self.file_no_files_msg = "THERE ARE NO FILES IN THE PROGRAM DIRECTORY"
        self.sim_names_exist_msg = "SIMULATIONS UNDER THE FOLLOWING NAMES EXIST IN THE DATABASE"

        self.import_from_msg = "ENTER SIMULATION NAME TO IMPORT FROM: "
        self.sim_not_exist_msg = "A SIMULATION UNDER THAT NAME DOES NOT EXIST"
        self.sim_loaded_msg = "SIMULATION LOADED"

        self.show_dir_msg = "THESE ARE THE FILES IN THE CURRENT DIRECTORY"
        self.import_from_file_msg = "ENTER FILENAME TO IMPORT FROM: "
        self.file_not_exist_msg = "A FILE UNDER THAT NAME DOES NOT EXIST"
        self.enter_options_error_msg = "PLEASE ENTER EITHER 1, 2, 3 OR 4"
        self.invalid_number_msg = "INVALID - RATE MUST BE A REAL NUMBER"

        self.simulation = None
        self.store = None
        self.current_user = None
        self.db_manager = Database_manager()
        self.dependency_graph = DependencyGraph() 


    def start(self):
        if not self._authenticate_user():
            return
        new_sim = input(self.start_msg).strip()
        if new_sim == "1":
            self.new_simulation()
        elif new_sim == "2":
            self.load_from_database()
        elif new_sim == "3":
            self.load_from_file()
        elif new_sim == "4":
            return
        else:
            print(self.enter_options_error_msg)

    def _authenticate_user(self):
        """Handles login/registration with error checking"""
        print("\n=== AUTHENTICATION ===")
        while True:
            if input("ENTER SCHOOL CODE: ") == "Hampton":
                choice = input("1. Login\n2. Register\nChoice (1/2): ").strip()
                username = input("Username: ").strip()
                password = input("Password: ").strip()

                if choice == "1":
                    if self.db_manager.verify_user(username, password):
                        self.current_user = username
                        return True
                    print("Invalid credentials or user doesn't exist")
                elif choice == "2":
                    if self.db_manager.create_user(username, password):
                        print(f"Welcome {username}! Please login now")
                        self.current_user = username
                        return True
                else:
                    print("Invalid choice. Try again.")

    def new_simulation(self):
        name = input(self.sim_name_msg)
        parent_sim = input("Base this on existing simulation? (Leave blank if new): ")
        if parent_sim:
            self.dependency_graph.add_dependency(parent_sim, name)

        self.rate = self.real_num_inp(self.sim_rate_msg)
        increment = 0.00001
        duration = self.real_num_inp(self.sim_dur_msg)
        isE, isM, isG = (self.y_n_input(msg) for msg in [self.sim_isE_msg, self.sim_isM_msg, self.sim_isG_msg])

        print(self.enter_par_msg)
        particle_lst = self.par_desc_inp()
        self.store = Data_store(particle_lst)
        self.store.build(name, self.rate, increment, duration)

        with_analysis = self.y_n_input(self.ask_analys_msg)
        graph_variables = self.analysis_var_input() if with_analysis else None
        
        if self.y_n_input(self.ask_save_msg):
            self.save_simulation()

        with_minmax = False
        if with_analysis:
            with_minmax = self.y_n_input(self.ask_minmax_msg)
        self.simulation = Sim_With_Analysis(self.store, E=isE, M=isM, G=isG, with_minmax=with_minmax) if with_analysis else Sim(self.store, E=isE, M=isM, G=isG)

        print(f"Graph variables: {graph_variables}")
        if with_analysis:
            self.simulation.load_graphs(graph_variables)

            
        self.simulation.pre_compute()

        if with_minmax:
            self.simulation.calc_and_display_minmax()

        self.simulation.Run()

    def save_simulation(self):
        save_choice = self.bin_option(self.save_options_msg)
        if save_choice == "1":
            self.save_to_database()
        elif save_choice == "2":
            self.save_to_file()

    def save_to_database(self):
        #try:
            print("Attempting to save")
            dsm = Database_manager()
            dsm.attach_store(self.store)
            print("Saving to DB...")
            dsm.dump_to_db(self.current_user)
            print(self.db_save_success_msg)
            """
        except NameError:
            print("A SIMULATION UNDER THIS NAME ALREADY EXISTS IN THE DATABASE")
            name = input("ENTER NEW NAME:")
            self.store.build(name, self.rate, 0.0001, 5)
            """
    def save_to_file(self):
        fm = File_Manager()
        print(self.file_exist_msg, self.get_filenames())
        filename = input(self.enter_new_filename_msg)
        fm.export_file(filename, self.store)
        print(self.file_save_success_msg)

    def load_from_database(self):
        dsm = Database_manager()
        sim_names = dsm.get_all_names()

        if not sim_names:
            print(self.db_empty_msg)
            return

        print(self.sim_names_exist_msg, sim_names)
        while True:
            sim_name = input(self.import_from_msg)
            self.rate = self.real_num_inp(self.sim_rate_msg)
            particle_store = dsm.pull_from_db(sim_name)
            self.store = Data_store(particle_store)
            self.store.build(sim_name, self.rate, 0.00001, 5)
            #particle_store = dsm.eject_store()
            print(self.sim_loaded_msg)
            self.run_sim_options()
            break

    def load_from_file(self):
        print(self.show_dir_msg)
        filenames = self.get_filenames()
        if not filenames:
            print(self.file_no_files_msg)
            return

        print(filenames)
        while True:
            file_name = input(self.import_from_file_msg)
            try:
                # Load the Data_store from file
                self.store = File_Manager().import_file(file_name)
                print(self.sim_loaded_msg)
                self.run_sim_options()
                break
            except Exception as e:
                print(f"Error loading file: {e}")

    def run_sim_options(self):

        isE, isM, isG = (self.y_n_input(msg) for msg in [self.sim_isE_msg, self.sim_isM_msg, self.sim_isG_msg])
        with_analysis = self.y_n_input(self.ask_analys_msg)
        graph_variables = self.analysis_var_input() if with_analysis else None

        if with_analysis and self.y_n_input(self.ask_minmax_msg):
            analysis = Analysis_handler(self.store)
            for variable in graph_variables:
                print(analysis.find_min_max(variable))
            stats = self.db_manager.get_simulation_stats()
            print(f"""
            Simulation Statistics:
            - Total Particles in Database: {stats['total_particles']}
            - Average Mass: {stats['avg_mass']:.2f} kg
            - Max Charge: {stats['max_charge']} C
            """)

        self.simulation = Sim_With_Analysis(self.store, E=isE, M=isM, G=isG) if with_analysis else Sim(self.store, E=isE, M=isM, G=isG)
        self.simulation.pre_compute()
        self.simulation.Run()

    def get_filenames(self):
        return [name for name in listdir(pathlib.Path().absolute()) if isfile(join(pathlib.Path().absolute(), name)) and name[-2:] not in ["py", "db"]]

    def bin_option(self, msg):
        while True:
            variable = input(msg)
            if variable in ["1", "2"]:
                return variable
            print(self.invalid_msg)

    def y_n_input(self, msg):
        while True:
            variable = input(msg).lower()
            if variable in ["y", "n"]:
                return variable == "y"
            print(self.invalid_msg)

    def analysis_var_input(self):
        while True:
            print(self.analys_options)
            numbers_input = input("ENTER : ").split()
            if all(num in ["1", "2", "3", "4"] for num in numbers_input) and len(numbers_input) == len(set(numbers_input)):
                return ["Kinetic Energy", "Speed", "Net Force", "Net Acceleration"][:len(numbers_input)]
            print(self.invalid_msg)

    def par_desc_inp(self):
        particles_lst = []
        positions_taken = []
        color_mapping = {
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

        while True:
            par_desc = input()
            if not par_desc:
                return particles_lst

            par_desc = par_desc.split()
            if par_desc[0].lower() in ["proton", "electron", "neutron"]:
                particle_properties = {
                    "proton": (0.25, 100, vector(0, 0, 0), "red", 0.25),
                    "electron": (-0.25, 10, vector(0, 0, 0), "blue", 0.12),
                    "neutron": (0, 100, vector(0, 0, 0), "green", 0.25),
                }
                charge, mass, vel_vector, color_name, radius = particle_properties[par_desc[0].lower()]
                pos_vector = self.valid_vector_inp(par_desc[1])

            else:
                try:
                    charge, mass, pos_vector, vel_vector, radius, color_name = float(par_desc[0]), float(par_desc[1]), self.valid_vector_inp(par_desc[2]), self.valid_vector_inp(par_desc[3]),float(par_desc[4]), par_desc[5].lower()
                except:
                    print(self.invalid_msg)
                    continue
            if color_name not in color_mapping or pos_vector in positions_taken:
                print(self.invalid_msg)
                continue
            chosen_color = color_mapping[color_name]
                

            positions_taken.append(pos_vector)
            particles_lst.append(Particle(charge, mass, pos_vector, vel_vector, vector(0, 0, 0), radius, chosen_color))

    def valid_vector_inp(self, inp):
        try:
            x, y, z = map(int, inp.strip("()").split(","))
            return vector(x, y, z)
        except:
            return "INVALID"

    def real_num_inp(self, msg):
        while True:
            try:
                return float(input(msg))
            except:
                print(self.invalid_number_msg)