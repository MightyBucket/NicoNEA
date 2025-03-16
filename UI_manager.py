from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
from tksheet import Sheet
from Simulation_manager import *
from Database_manager import *
from os import listdir
from os.path import isfile, join
import pathlib

orange = "#cd9448"
black = "#000000"

text_colour = black

# Create the main window
#self.root = Tk()
#self.root.title("NEA Particle simulator")
#self.root.geometry("1280x720")

class UI_Manager_class:

    def __init__(self):
        self.root = Tk()
        self.root.title("NEA Particle simulator")
        self.root.geometry("1280x720")

        self.fonts = {
            "button": ("Helvetica", 24, "bold")
        }

        # Simulation variables
        self.simulation = None
        self.store = None
        self.current_user = None
        self.db_manager = Database_manager()
        #self.dependency_graph = DependencyGraph() 


    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_filenames(self):
        return [name for name in listdir(pathlib.Path().absolute()) if isfile(join(pathlib.Path().absolute(), name)) and name[-2:] not in ["py", "db"]]

    def exit(self):
        self.root.destroy()

    def authentication(self):
        # Create a welcome sign
        welcome_label1 = Label(self.root,
                            text="NEA Particle simulator",
                            font=("Helvetica", 50, "bold"))
        welcome_label1.pack()

        welcome_label2 = Label(self.root,
                            text="Enter school code to begin: ",
                            font=("Helvetica", 30, "bold"))
        welcome_label2.pack(pady=20)


        # School code controls
        code_entry = Entry(self.root, font=("Helvetica", 32, "bold"))
        code_entry.pack()

        submit_button = Button(self.root,
                            text="Submit",
                            font=("Helvetica", 32, "bold"),
                            command=lambda: check_school_code(code_entry.get()),
                            width=8)
        submit_button.pack(pady=10)

        def check_school_code(code):
            if code == "Hampton":
                messagebox.showinfo("Success", "Valid school code. Please login or register to continue.")
                login_or_register()

            else:
                messagebox.showerror("Error", "Invalid school code")


    def login_or_register(self):
        self.clear_window()

        # Create labels and entry fields for username and password
        welcome_label = Label(self.root,
                            text="Please log in or register",
                            font=("Helvetica", 40, "bold"))
        welcome_label.pack()

        username_label = Label(self.root,
                            text="Username:",
                            font=self.fonts["button"])
        username_label.pack(pady=10)
        username_entry = Entry(self.root,
                            font=self.fonts["button"])
        username_entry.pack()

        password_label = Label(self.root,
                            text="Password:",
                            font=self.fonts["button"])
        password_label.pack(pady=10)
        password_entry = Entry(self.root,
                            font=self.fonts["button"],
                            show="*")
        password_entry.pack()

        login_button = Button(self.root,
            text="Login",
            font=self.fonts["button"],
            command=lambda: validate_login(username_entry.get(), password_entry.get()))
        login_button.pack(pady=5)

        register_button = Button(self.root,
            text="Register",
            font=self.fonts["button"],
            command=lambda: validate_registration(username_entry.get(), password_entry.get()))
        register_button.pack(pady=5)

        def validate_login(username, password):
            if self.db_manager.verify_user(username, password):
                messagebox.showinfo("Success", "Login successful")
                self.current_user = username
                self.main_menu()
            else:
                messagebox.showerror("Invalid login", "Invalid credentials or user doesn't exist")
        pass

        def validate_registration(username, password):
            if self.db_manager.create_user(username, password):
                messagebox.showinfo("Success", f"Welcome {username}!")
                self.current_user = username
                self.main_menu()
            else:
                messagebox.showerror("Error", "An error occured while registering. The user you entered most likely doesn't exist")


    def main_menu(self):
        self.clear_window()

        welcome_label = Label(self.root,
                            text="What would you like to do",
                            font=("Helvetica", 40, "bold"))
        welcome_label.pack()

        new_sim_button = Button(self.root,
            text="Start new simulation",
            font=self.fonts["button"],
            command=self.new_simulation)
        new_sim_button.pack(pady=5)

        load_sim_button = Button(self.root,
            text="Load simulation",
            font=self.fonts["button"],
            command=self.load_simulation)
        load_sim_button.pack(pady=5)

        exit_button = Button(self.root,
            text="Exit",
            font=self.fonts["button"],
            command=self.exit)
        exit_button.pack(pady=5)

    def new_simulation(self):
        self.clear_window()

        def toggle_parent_entry():
            if base_sim_var.get() == "Yes":
                parent_entry.config(state=NORMAL)
            else:
                parent_entry.config(state=DISABLED)
                parent_entry.delete(0, END)
        
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

        def graphs_page():
            for widget in self.root.winfo_children():
                widget.destroy()
            
            Label(self.root, text="Select Graphs to Include:").pack()
            graph_frame = Frame(self.root)
            graph_frame.pack()
            
            kinetic_var = BooleanVar()
            speed_var = BooleanVar()
            force_var = BooleanVar()
            acceleration_var = BooleanVar()
            
            Checkbutton(graph_frame, text="Kinetic Energy", variable=kinetic_var).pack(anchor=W)
            Checkbutton(graph_frame, text="Speed", variable=speed_var).pack(anchor=W)
            Checkbutton(graph_frame, text="Net Force", variable=force_var).pack(anchor=W)
            Checkbutton(graph_frame, text="Net Acceleration", variable=acceleration_var).pack(anchor=W)
            
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
                selected_graphs = []
                if kinetic_var.get():
                    selected_graphs.append("Kinetic Energy")
                if speed_var.get():
                    selected_graphs.append("Speed")
                if force_var.get():
                    selected_graphs.append("Net Force")
                if acceleration_var.get():
                    selected_graphs.append("Net Acceleration")
                
                save_data = save_var.get()
                filename = filename_entry.get() if save_data == "File" else ""
                messagebox.showinfo("Setup Complete", f"Graphs: {', '.join(selected_graphs)}\nSave Data: {save_data}\nFilename: {filename}")
                self.root.destroy()
                
            Button(self.root, text="Finish", command=finalize).pack()
        
        def particles_page():
            for widget in self.root.winfo_children():
                widget.destroy()
            
            Label(self.root, text="Particle Information:").pack()
            
            sheet_frame = Frame(self.root)
            sheet_frame.pack()
            
            sheet = Sheet(sheet_frame,
                          headers=["Charge", "Mass", "Position (X,Y,Z)", "Velocity (X,Y,Z)", "Radius", "Colour"],
                          width=600,
                          height=250)
            sheet.set_column_widths([70, 70, 120, 120, 70, 70])
            sheet.pack()
            sheet.enable_bindings()  # Allow direct cell editing
            
            sheet.insert_row(["", "", "", "", "", ""])
            
            def add_row():
                sheet.insert_row(["", "", "", "", "", ""])
            
            def remove_selected_row():
                selected_rows = list(sheet.get_selected_rows())
                if selected_rows != []:
                    for row in reversed(selected_rows):
                        sheet.delete_row(row)
                else:
                    messagebox.showwarning("No particles selected", "You must select the entire particle row. Click the row numbers to select its row")
                
            def add_particle_from_text():
                data = particle_input.get()
                try:
                    if data:
                        values = data.split()
                        if len(values) == 6:
                            sheet.insert_row(values)
                    else:
                        raise Exception("Input field is empty")
                except:
                    message = """
                    Please enter the attributes in the following format: 
                    CHARGE MASS INITIAL_POSITION INITIAL_VELOCITY RADIUS COLOUR
                    
                    For example: 
                    0.25 100 (0,0,0) (0,0,0) 0.25 red 
                    """

                    messagebox.showerror("Error", message)
                    
                particle_input.delete(0, END)
                
            def submit():
                particles = []
                for row in sheet.get_sheet_data():  # Get updated values
                    if any(row):  # Only process rows with data
                        particles.append(row)
                #messagebox.showinfo("Success", "Simulation setup completed with particles added!")
                graphs_page()
            
            button_frame = Frame(self.root)
            button_frame.pack()
            Button(button_frame, text="Add Particle", command=add_row).pack(side=LEFT, padx=5)
            Button(button_frame, text="Remove Particle(s)", command=remove_selected_row).pack(side=LEFT)

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
        
        Label(self.root, text="Simulation Name:").pack()
        name_entry = Entry(self.root)
        name_entry.pack()

        Label(self.root, text="Base this on an existing simulation?").pack()
        base_sim_var = StringVar(value="No")
        base_frame = Frame(self.root)
        base_frame.pack()
        Radiobutton(base_frame, text="Yes", variable=base_sim_var, value="Yes", command=toggle_parent_entry).pack(side=LEFT)
        Radiobutton(base_frame, text="No", variable=base_sim_var, value="No", command=toggle_parent_entry).pack(side=LEFT)
        
        Label(self.root, text="Existing Simulation Name:").pack()
        parent_entry = Entry(self.root, state=DISABLED)
        parent_entry.pack()

        Label(self.root, text="Simulation Rate (1-20):").pack()
        rate_frame = Frame(self.root)
        rate_frame.pack()
        rate_entry = Entry(rate_frame, width=5)
        rate_entry.pack(side=LEFT)
        rate_entry.insert(0, "10")
        rate_entry.bind("<Return>", update_rate_slider)
        rate_slider = Scale(rate_frame, from_=1, to=20, orient=HORIZONTAL, command=update_rate_entry)
        rate_slider.set(10)
        rate_slider.pack(side=LEFT)

        Label(self.root, text="Simulation Duration (0-5 sec):").pack()
        duration_frame = Frame(self.root)
        duration_frame.pack()
        duration_entry = Entry(duration_frame, width=5)
        duration_entry.pack(side=LEFT)
        duration_entry.insert(0, "2.5")
        duration_entry.bind("<Return>", update_duration_slider)
        duration_slider = Scale(duration_frame, from_=0, to=5, resolution=0.1, orient=HORIZONTAL, command=update_duration_entry)
        duration_slider.set(2.5)
        duration_slider.pack(side=LEFT)

        Button(self.root, text="Next", command=particles_page).pack()


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

        
        
        def load_selected_simulation():
            db_sim = db_sim_var.get()
            file_sim = file_sim_var.get()
            
            if db_sim:
                particle_store = dsm.pull_from_db(sim_name)
                self.store = Data_store(particle_store)
                self.store.build(sim_name, self.rate, 0.00001, 5)
            elif file_sim:
                messagebox.showinfo("Loading", f"Loading simulation from file: {file_sim}")
            else:
                messagebox.showwarning("No Selection", "Please select a simulation to load.")
                
        Button(self.root, text="Load", command=load_selected_simulation).pack()



    
manager = UI_Manager_class()

#manager.login_or_register()
#manager.main_menu()
#manager.new_simulation()
manager.load_simulation()

# Run the Tkinter event loop
manager.root.mainloop()