import sqlite3
import os.path
from Particle_manager import *
import json
import bcrypt

class File_Manager():
    def __init__(self):
        pass

    # Export simulation data to JSON file
    def export_file(self, file_loc, SimulationState_obj):
        # Convert SimulationState to JSON-compatible dictionary and write to file
        with open(file_loc, "w") as file:
            json.dump(self._ds_to_JSON_D(SimulationState_obj), file, indent=4)

        return None

    # Convert SimulationState object to JSON-serializable format
    def _ds_to_JSON_D(self, SimulationState_obj):
        # Package all simulation data into dictionary
        full_data = {
            "Sim_Name": SimulationState_obj.sim_name,
            "Rate": SimulationState_obj.sim_rate,
            "Increment": SimulationState_obj.sim_increment,
            "Duration": SimulationState_obj.sim_duration,
            "Particles": SimulationState_obj.initial_conditions,  # Particle configurations
            "Pos_Data": self._arrv_to_a(SimulationState_obj.pos_data),  # Position history
            "Vel_Data": self._arrv_to_a(SimulationState_obj.vel_data),  # Velocity history
            "Acc_Data": self._arrv_to_a(SimulationState_obj.acc_data)   # Acceleration history
        }

        # Convert vector objects to lists for JSON serialization
        for particle in full_data["Particles"]:
            for attribute in ["Velocity", "Position", "Acceleration", "Colour"]:
                particle[attribute] = self.v_to_a(particle[attribute])

        return full_data

    # Reconstruct SimulationState from JSON dictionary
    def _JSON_D_to_ds(self, jsd):
        # Rebuild particles from JSON data
        particles = []
        for dct in jsd["Particles"]:
            # Convert stored lists back to vector objects
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
        
        # Recreate full simulation state
        ds = SimulationState(particles)
        # Apply original simulation parameters
        ds.build(
            jsd["Sim_Name"],
            jsd["Rate"],
            jsd["Increment"],
            jsd["Duration"]
        )
        # Restore vector data from serialized arrays
        ds.pos_data = self._arr_arrv(jsd["Pos_Data"])
        ds.vel_data = self._arr_arrv(jsd["Vel_Data"])
        ds.acc_data = self._arr_arrv(jsd["Acc_Data"])
        return ds

    # Convert vector to 3-element list
    def v_to_a(self, vct):
        return [vct.x, vct.y, vct.z]

    # Convert list to vector object
    def a_to_v(self, arr):
        return vector(*arr)

    # Convert array of vectors to 2D array of lists
    def _arrv_to_a(self, vectarr):
        result = []
        for particle in vectarr:
            p_arr = []
            for data in particle:  # Process each vector in trajectory
                p_arr.append(self.v_to_a(data))
            result.append(p_arr)
        return result

    # Convert 2D array of lists to array of vectors
    def _arr_arrv(self, arr):
        result = []
        for particle in arr:
            p_arr = []
            for data in particle:
                p_arr.append(self.a_to_v(data))
            result.append(p_arr)
        return result

    # Load simulation state from JSON file
    def import_file(self, file_loc):
        with open(file_loc, "r") as file:
            data = json.load(file)
        return self._JSON_D_to_ds(data)  # Return reconstructed SimulationState


class Database_manager():
    def __init__(self):
        self.db_path = "ParticleDatabase.db"
        self.initialize_database()  # Ensure database schema exists
        self.cache = {}  # For storing recently accessed simulations
    
    # Authenticate user against database
    def verify_user(self, username, password):
        """Check username/password against database"""
        try:
            # Use parameterized query to prevent SQL injection
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT PasswordHash FROM Users WHERE Username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                return False  # User doesn't exist
                
            # Verify password against bcrypt hash
            return self.check_password(password, result[0])
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        
    # Get internal user ID for operations
    def get_user_id(self, username):
        """Get the User ID for a given username in the database"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT UserID FROM Users WHERE Username = ?
        """, (username,))
        return [row[0] for row in cursor.fetchall()][0]
    
    # Get list of user's simulations
    def get_user_simulations(self, username):
        """Get all simulations created by a user"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT Sim_Name FROM Simulations
            WHERE CreatorID = (SELECT UserID FROM Users WHERE Username = ?)
        """, (username,))
        return [row[0] for row in cursor.fetchall()]
    
    # Get particle count for a simulation
    def get_particle_count(self, sim_name):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT Count(*) FROM Particles WHERE Sim_Name = ?", (sim_name,))
        return [row[0] for row in cursor.fetchall()][0]

    # Prepare simulation data for database storage
    def attach_store(self, SimulationState_obj):
        self.pos_data_raw = SimulationState_obj.pos_data  # Position history
        self.vel_data_raw = SimulationState_obj.vel_data  # Velocity history
        self.acc_data_raw = SimulationState_obj.acc_data  # Acceleration history
        self.par_data = SimulationState_obj.initial_conditions  # Particle configs
        self.sim_data = {"Rate" : SimulationState_obj.sim_rate, 
                        "Run Time" : SimulationState_obj.sim_duration,
                        "Increment" : SimulationState_obj.sim_increment, 
                        "Sim_Name" : SimulationState_obj.sim_name,
                        "No_Pars" : len(self.par_data)}  # Simulation metadata
        
    # Reconstruct SimulationState from database data
    def eject_store(self):
        new_store = SimulationState(self.particle_lst)
        new_store.build(self.sim_data["Sim_Name"], 
                        self.sim_data["Rate"],
                        self.sim_data["Increment"], 
                        self.sim_data["Run Time"])
        new_store.set_pos_data(self.pos_data_raw)
        new_store.set_vel_data(self.vel_data_raw)
        new_store.set_acc_data(self.acc_data_raw)
        return new_store

    # Check if simulation name exists in database
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

    # Get list of all simulation names
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

    # Load simulation from database with caching
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

        # Retrieve simulation metadata
        cmd = "SELECT * FROM Simulations WHERE Sim_Name = '{}'".format(sim_name)
        sim_data_raw = list(cursor.execute(cmd))
        self.sim_data = {"Rate": sim_data_raw[0][2], "Run Time": sim_data_raw[0][3],
                        "Increment": sim_data_raw[0][4], "Sim_Name": sim_data_raw[0][0],
                        "No_Pars": sim_data_raw[0][1]}

        # Retrieve particle configurations
        cmd = "SELECT * FROM Particles WHERE Sim_Name = '{}'".format(sim_name)
        par_data_raw = list(cursor.execute(cmd))
        self.par_data = [
            {"Charge": p[2],
            "Mass": p[3],
            "Position": self._text_to_vec(p[4]),
            "Velocity": self._text_to_vec(p[5]),
            "Acceleration": self._text_to_vec(p[6]),
            "Radius": p[7],
            "Colour": self._text_to_vec(p[8])} for p in par_data_raw
        ]

        # Retrieve trajectory data
        par_ID_start = par_data_raw[0][0]
        cmd = "SELECT Pos_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        pos_d_raw = list(cursor.execute(cmd))
        self.pos_data_raw = self._txt_to_arr(pos_d_raw)

        cmd = "SELECT Vel_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        vel_d_raw = list(cursor.execute(cmd))
        self.vel_data_raw = self._txt_to_arr(vel_d_raw)

        cmd = "SELECT Acc_Data FROM Particles_Data WHERE ParticleID >= {}".format(par_ID_start)
        acc_d_raw = list(cursor.execute(cmd))
        self.acc_data_raw = self._txt_to_arr(acc_d_raw)
        
        # Rebuild particle objects
        for data in self.par_data:
            self.particle_lst.append(Particle(data["Charge"], data["Mass"],
                                    data["Position"], data["Velocity"],
                                    data["Acceleration"], data["Radius"],
                                    data["Colour"]))
        
        # Cache loaded simulation
        self.cache[sim_name] = self.particle_lst
        return(self.particle_lst)

    # Convert string representation to vector
    def _text_to_vec(self, text):
        # Parse vector string "<x,y,z>" to vector object
        str_lst = text.replace("<", "").replace(">", "").strip("[").strip("]").strip("'").split(",")
        flo_lst = [float(string) for string in str_lst]
        vec = vector(*flo_lst)
        return vec

    # Convert text-based trajectory data to vector arrays
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
    
    # Initialize database schema
    def initialize_database(self, db_name="ParticleDatabase.db"):
        try:
            # Create tables if they don't exist
            connection = sqlite3.connect(db_name)
            cursor = connection.cursor()

            # Simulations metadata table
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
            # Particle configurations table
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
            # Trajectory data storage
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Particles_Data (
                ParticleID INTEGER,
                Pos_Data TEXT,
                Vel_Data TEXT,
                Acc_Data TEXT
            )
            """)
            # User authentication table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE,
                PasswordHash TEXT,
                LastLogin DATETIME
            )""")
    
            # Additional experimental tables
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Simulation_Metadata (
                        Sim_Name TEXT PRIMARY KEY,
                        CreatorID INTEGER,
                        CreationDate DATETIME,
                        ParticleCount INTEGER,
                        FOREIGN KEY (CreatorID) REFERENCES Users(UserID)
                            )""")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS SimulationDependencies (
                ChildSim TEXT PRIMARY KEY,
                ParentSim TEXT
            )""")

            connection.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
        finally:
            connection.close()

    # Save simulation to database
    def dump_to_db(self, username):
        creator_id = self.get_user_id(username)

        # Prepare simulation metadata
        tblTemps = [(self.sim_data["Sim_Name"], creator_id,
                    self.sim_data["No_Pars"], self.sim_data["Rate"],
                    self.sim_data["Run Time"], self.sim_data["Increment"])]
        
        if not os.path.exists("ParticleDatabase.db"):
            self.initialize_database()

        connection = sqlite3.connect("ParticleDatabase.db")
        cursor = connection.cursor()
                    
        # Insert simulation metadata
        cursor.executemany("""
            INSERT INTO Simulations VALUES (?,?,?,?,?,?)
        """, tblTemps)

        if self.name_exists(self.sim_data["Sim_Name"]):
            raise NameError("Simulation name already exists")

        # Insert particle configurations
        tblTemps = [(self.sim_data["Sim_Name"], par["Charge"], par["Mass"], str(par["Position"]),
                    str(par["Velocity"]), str(par["Acceleration"]), par["Radius"], str(par["Colour"]))
                    for par in self.par_data]
        cursor.executemany("""INSERT INTO Particles (Sim_Name, Charge, Mass, StartPos,
        StartVel, StartAcc, Radius, Colour) VALUES (?,?,?,?,?,?,?,?)""", tblTemps)

        # Insert trajectory data
        tblTemps = [(str(self.pos_data_raw[i]), str(self.vel_data_raw[i]),
                    str(self.acc_data_raw[i])) for i in range(len(self.par_data))]
        cursor.executemany("INSERT INTO Particles_Data (Pos_Data, Vel_Data, Acc_Data) VALUES (?,?,?)", tblTemps)

        connection.commit()
        connection.close()

    # Password hashing utilities
    def hash_password(self, password):
        # Generate salted password hash
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def check_password(self, password_to_check, hashed_password):
        # Verify password against stored hash
        return bcrypt.checkpw(password_to_check.encode('utf-8'), hashed_password)
    
    # User account creation
    def create_user(self, username, password):
        if not username or not password:
            return False
            
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            # Store hashed password, not plain text
            cursor.execute("INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)", 
                        (username, self.hash_password(password)))
            connection.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username already exists.")
            return False