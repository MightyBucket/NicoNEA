import sqlite3
import os.path
from Particle_manager import *
import json
import bcrypt

class File_Manager():
    def __init__(self):
        pass

    def export_file(self, file_loc, data_store_obj): # stores into JSON file
        with open(file_loc, "w") as file:
            json.dump(self._ds_to_JSON_D(data_store_obj), file, indent=4)

        return None

    # The data store object's values are put into a dictionary, as this can then be exported as a JSON file
    def _ds_to_JSON_D(self, data_store_obj):
        full_data = {
            "Sim_Name": data_store_obj.sim_name,
            "Rate": data_store_obj.sim_rate,
            "Increment": data_store_obj.sim_increment,
            "Duration": data_store_obj.sim_duration,
            "Particles": data_store_obj.initial_conditions,
            "Pos_Data": self._arrv_to_a(data_store_obj.pos_data),
            "Vel_Data": self._arrv_to_a(data_store_obj.vel_data),
            "Acc_Data": self._arrv_to_a(data_store_obj.acc_data)
        }

        # Changing all vectors in initial conditions to arrays
        for particle in full_data["Particles"]:
            for attribute in ["Velocity", "Position", "Acceleration", "Colour"]:
                particle[attribute] = self.v_to_a(particle[attribute])

        return full_data

    # This takes a JSON dictionary and turns it into data store object
    def _JSON_D_to_ds(self, jsd):
        # Ensure JSON keys match expected structure
        particles = []
        for dct in jsd["Particles"]:
            # Convert ALL vector attributes from arrays to vectors
            particle = Particle(
                charge=dct["Charge"],
                mass=dct["Mass"],
                initial_position=self.a_to_v(dct["Position"]),
                initial_velocity=self.a_to_v(dct["Velocity"]),
                initial_acceleration=self.a_to_v(dct["Acceleration"]),
                radius=dct["Radius"],
                colour=self.a_to_v(dct["Colour"])
            )
            particles.append(particle)
        
        # Create Data_store with the reconstructed particles
        ds = Data_store(particles)
        # Use the imported simulation parameters, NOT hardcoded values
        ds.build(
            jsd["Sim_Name"],
            jsd["Rate"],
            jsd["Increment"],
            jsd["Duration"]
        )
        # Convert nested arrays back to vectors
        ds.pos_data = self._arr_arrv(jsd["Pos_Data"])
        ds.vel_data = self._arr_arrv(jsd["Vel_Data"])
        ds.acc_data = self._arr_arrv(jsd["Acc_Data"])
        return ds

    # Changes a vector to an array
    def v_to_a(self, vct):
        return [vct.x, vct.y, vct.z]

    # Changes an array to a vector
    def a_to_v(self, arr):
        return vector(*arr)

    # Changes an array of vectors into an array of arrays
    def _arrv_to_a(self, vectarr):
        result = []
        for particle in vectarr:
            p_arr = []
            for data in particle:  # each vector
                p_arr.append(self.v_to_a(data))
            result.append(p_arr)
        return result

    # Changes an array of arrays into an array of vectors
    def _arr_arrv(self, arr):
        result = []
        for particle in arr:
            p_arr = []
            for data in particle:
                p_arr.append(self.a_to_v(data))
            result.append(p_arr)
        return result

    def import_file(self, file_loc):
        with open(file_loc, "r") as file:
            data = json.load(file)
        return self._JSON_D_to_ds(data)  # return data_store_obj

class Database_manager():
    def __init__(self):
        self.db_path = "ParticleDatabase.db"
        self.initialize_database()
        self.cache = {}
    
    def verify_user(self, username, password):
        """Check username/password against database"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT PasswordHash FROM Users WHERE Username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                return False  # User doesn't exist
                
            return self.check_password(password, result[0])
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        
    def get_user_id(self, username):
        """Get the User ID for a given username in the database"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT UserID FROM Users WHERE Username = ?
        """, (username,))
        return [row[0] for row in cursor.fetchall()][0]
        pass
    
    def get_user_simulations(self, username):
        """Get all simulations created by a user"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT Sim_Name FROM Simulations
            WHERE CreatorID = (SELECT UserID FROM Users WHERE Username = ?)
        """, (username,))
        return [row[0] for row in cursor.fetchall()]

    # This would be called when the database is being saved to
    def attach_store(self, data_store_obj):
        self.pos_data_raw = data_store_obj.pos_data
        self.vel_data_raw = data_store_obj.vel_data
        self.acc_data_raw = data_store_obj.acc_data
        self.par_data = data_store_obj.initial_conditions
        self.sim_data = {"Rate" : data_store_obj.sim_rate, 
                        "Run Time" : data_store_obj.sim_duration,
                        "Increment" : data_store_obj.sim_increment, 
                        "Sim_Name" : data_store_obj.sim_name,
                        "No_Pars" : len(self.par_data)}
        
    def eject_store(self):
        new_store = Data_store(self.particle_lst)
        new_store.build(self.sim_data["Sim_Name"], 
                        self.sim_data["Rate"],
                        self.sim_data["Increment"], 
                        self.sim_data["Run Time"])
        new_store.set_pos_data(self.pos_data_raw)
        new_store.set_vel_data(self.vel_data_raw)
        new_store.set_acc_data(self.acc_data_raw)
        return new_store

    def name_exists(self, sim_name):
        if not os.path.exists("ParticleDatabase.db"):
            return False
        connection = sqlite3.connect("ParticleDatabase.db")
        cursor = connection.cursor()
        cmd = "SELECT Sim_Name FROM Simulations"
        cursor.execute(cmd)
        simulations = cursor.fetchall()
        for result in simulations:
            if result[0] == sim_name:
                return True
        connection.close()
        return False

    def get_all_names(self):
        if os.path.exists("ParticleDatabase.db") is False:
            return []
        connection = sqlite3.connect("ParticleDatabase.db")
        cursor = connection.cursor()
        cmd = "SELECT Sim_Name FROM Simulations"
        cursor.execute(cmd)
        all_names = []
        for result in cursor:
            all_names.append(result[0])
        connection.close()
        return all_names

    def pull_from_db(self, sim_name):
        if sim_name in self.cache:
            print(f"Loading {sim_name} from cache...")
            return self.cache[sim_name]
        self.particle_lst = []
        if not os.path.exists("ParticleDatabase.db"):
            return NameError("The database file does not exist or has been moved")
        if not self.name_exists(sim_name):
            return NameError("The simulation under that name does not exist")
        connection = sqlite3.connect("ParticleDatabase.db")
        cursor = connection.cursor()

        # Pull row from Simulations where Sim_Name = sim_name
        cmd = "SELECT * FROM Simulations WHERE Sim_Name = '{}'".format(sim_name)
        sim_data_raw = list(cursor.execute(cmd)) # [('NewSim8', 4, 13000.2, 2.0, 1.0)]
        self.sim_data = {"Rate": sim_data_raw[0][2], "Run Time": sim_data_raw[0][3],
                        "Increment": sim_data_raw[0][4], "Sim_Name": sim_data_raw[0][0],
                        "No_Pars": sim_data_raw[0][1]}

        # Pull all rows from Particles where Sim_Name = sim_name
        cmd = "SELECT * FROM Particles WHERE Sim_Name = '{}'".format(sim_name)
        par_data_raw = list(cursor.execute(cmd)) # [(29, 'NewSim8', -0.001, 10.0, '<20, 1.5, 0>', '<-10, 0, 0>', 0.0, 0.5, '<0.275482, 0.486819, 0.313722>'), (30, 'NewSim8'...]
        self.par_data = [
            {"Charge": p[2],
            "Mass": p[3],
            "Position": self._text_to_vec(p[4]),
            "Velocity": self._text_to_vec(p[5]),
            "Acceleration": self._text_to_vec(p[6]),
            "Radius": p[7],
            "Colour": self._text_to_vec(p[8])} for p in par_data_raw
        ]

        par_ID_start = par_data_raw[0][0]
        # Pull all pos_data, vel_data and acc_data from Particles_Data where ParticleID = ParticleID of rows pulled above
        cmd = "SELECT Pos_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        pos_d_raw = list(cursor.execute(cmd))
        self.pos_data_raw = self._txt_to_arr(pos_d_raw)

        cmd = "SELECT Vel_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        vel_d_raw = list(cursor.execute(cmd))
        self.vel_data_raw = self._txt_to_arr(vel_d_raw)

        cmd = "SELECT Acc_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        acc_d_raw = list(cursor.execute(cmd))
        self.acc_data_raw = self._txt_to_arr(acc_d_raw)
        
        for data in self.par_data:
            self.particle_lst.append(Particle(data["Charge"], data["Mass"],
                                    data["Position"], data["Velocity"],
                                    data["Acceleration"], data["Radius"],
                                    data["Colour"]))
        
        self.cache[sim_name] = self.particle_lst
        return(self.particle_lst)

    def _text_to_vec(self, text):  # text = '<20, 1.5, 0>'
        str_lst = text.replace("<", "").replace(">", "").strip("[").strip("]").strip("'").split(",")
        flo_lst = [float(string) for string in str_lst]
        vec = vector(*flo_lst)  # same as inputting vector(1,2,3)
        return vec

    def _txt_to_arr(self, some_data):
        result = []
        for particle in some_data:
            particle = list(particle)
            particle[0] = particle[0].strip("[").strip("]").split(">,")

            particle = particle[0]
            lst = []
            count = 0
            for position in particle:
                if count != len(particle) - 1:
                    position += ">"
                lst.append(self._text_to_vec(position))
                count += 1
            result.append(lst)
        return result
    
    def initialize_database(self, db_name="ParticleDatabase.db"):
        try:
            # Establish connection (creates the file if it doesn't exist)
            connection = sqlite3.connect(db_name)
            cursor = connection.cursor()

            # Create tables using IF NOT EXISTS to avoid redundant checks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Simulations (
                Sim_Name TEXT PRIMARY KEY,
                UserID INTEGER,
                No_Particles INTEGER,
                Rate FLOAT,
                Duration FLOAT,
                Interval FLOAT
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Particles (
                ParticleID INTEGER PRIMARY KEY AUTOINCREMENT,
                Sim_Name TEXT,
                Charge FLOAT,
                Mass FLOAT,
                StartPos TEXT,
                StartVel TEXT,
                StartAcc TEXT,
                Radius FLOAT,
                Colour TEXT
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Particles_Data (
                ParticleID INTEGER,
                Pos_Data TEXT,
                Vel_Data TEXT,
                Acc_Data TEXT
            )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE,
                PasswordHash TEXT,
                LastLogin DATETIME
            )""")
    
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Simulation_Metadata (
                        Sim_Name TEXT PRIMARY KEY,
                        CreatorID INTEGER,
                        CreationDate DATETIME,
                        ParticleCount INTEGER,
                        FOREIGN KEY (CreatorID) REFERENCES Users(UserID)
                            )""")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY,
                Username TEXT UNIQUE,
                PasswordHash TEXT
            )""")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS SimulationDependencies (
                ChildSim TEXT PRIMARY KEY,
                ParentSim TEXT
            )""")
            # Commit changes and close connection
            connection.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while initializing the database: {e}")
        finally:
            connection.close()

    def dump_to_db(self, username):
        # Add creator tracking to simulations table
        creator_id = self.get_user_id(username)

        
        tblTemps = [(self.sim_data["Sim_Name"], creator_id,  # Added creator ID
                    self.sim_data["No_Pars"], self.sim_data["Rate"],
                    self.sim_data["Run Time"], self.sim_data["Increment"])]
        

        # check if database exists
        if not os.path.exists("ParticleDatabase.db"):
            # If the database doesn't already exist
            Database_manager.initialize_database()

        connection = sqlite3.connect("ParticleDatabase.db")
        cursor = connection.cursor()

                    
        cursor.executemany("""
            INSERT INTO Simulations VALUES (?,?,?,?,?,?)
        """, tblTemps)


        if self.name_exists(self.sim_data["Sim_Name"]):
            raise NameError("A simulation under this name already exists in the database")

        # Dump particle data into Particles Table
        tblTemps = [(self.sim_data["Sim_Name"], par["Charge"], par["Mass"], str(par["Position"]),
                    str(par["Velocity"]), str(par["Acceleration"]), par["Radius"], str(par["Colour"]))
                    for par in self.par_data]
        cursor.executemany("""INSERT INTO Particles (Sim_Name, Charge, Mass, StartPos,
        StartVel, StartAcc, Radius, Colour) VALUES (?,?,?,?,?,?,?,?)""", tblTemps)

        # Dump particle pos and vel data into Particles_Data Table
        tblTemps = [(str(self.pos_data_raw[i]), str(self.vel_data_raw[i]),
                    str(self.acc_data_raw[i])) for i in range(len(self.par_data))]
        cursor.executemany("INSERT INTO Particles_Data (Pos_Data, Vel_Data, Acc_Data) VALUES (?,?,?)", tblTemps)

        connection.commit()
        connection.close()

    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password
    
    def check_password(self, password_to_check, hashed_password):
        return bcrypt.checkpw(password_to_check.encode('utf-8'), hashed_password)
    
    def create_user(self, username, password):
        if not username or not password:
            return False
        # Hash password
        hashed = self.hash_password(password)
        
        try:
            #print(f"DB path is {self.db_path}")
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)", 
                        (username, hashed))
            connection.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username already exists.")
            return False