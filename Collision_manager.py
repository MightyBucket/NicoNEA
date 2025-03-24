from vpython import vector, cross, proj
from Particle_manager import Particle

class Collision_manager:
    def __init__(self, particleGroupObj, e):
        # Initialize collision system with particle group and restitution coefficient
        self.particles = particleGroupObj  # Particle group to manage
        self.e = e  # Coefficient of restitution (1 = perfectly elastic)
        self.hasJustCollided = self._setupCollisionCounter()  # Collision state tracker
        self.bounces = 0  # Total collision count

    def neutron_creation(self, p1, p2):
        # Special nuclear reaction case: convert collision into neutron
        Particle.delete_object(p2)  # Remove second particle
        # Transform first particle into neutron properties
        p1.charge, p1.mass, p1.colour = [0, 100, vector(0,1,0)]

    def _setupCollisionCounter(self):
        # Initialize collision tracking for all particle pairs
        collision_state = {}
        for pair in self.particles.particle_pairs:
            collision_state[pair] = False  # Start with no active collisions
        return collision_state

    def collisionDetection(self):
        # Main collision checking loop for all particle pairs
        for pa, pb in self.particles.particle_pairs:
            if pa.does_collide_with(pb):
                # Prevent duplicate collision handling
                if self.hasJustCollided[(pa, pb)]:
                    continue
                # Handle collision and update state
                self.collide(pa, pb)
                self.hasJustCollided[(pa, pb)] = True
                self.bounces += 1  # Increment global bounce counter
            else:
                # Reset collision state when particles separate
                if self.hasJustCollided[(pa,pb)]:
                    self.hasJustCollided[(pa,pb)] = False

    def collide(self, p1, p2):
        # Calculate collision response using momentum conservation
        rOriginal = p2.pos - p1.pos  # Vector between particle centers
        
        # Uncomment for special neutron creation logic
        # if self.bounces >= 2:
        #     self.neutron_creation(p1,p2)

        # Create local coordinate system for collision
        rHorzPerp = cross(rOriginal, vector(0,1,0))  # Horizontal perpendicular
        rVertPerp = cross(rHorzPerp, rOriginal)       # Vertical perpendicular

        # Decompose velocities into collision coordinate system components
        p1VelocitiesIJK = [
            proj(p1.velocity, rOriginal),   # Along collision axis
            proj(p1.velocity, rVertPerp),   # Vertical component
            proj(p1.velocity, rHorzPerp)    # Horizontal component
        ]
        p2VelocitiesIJK = [
            proj(p2.velocity, rOriginal),
            proj(p2.velocity, rVertPerp),
            proj(p2.velocity, rHorzPerp)
        ]

        # Process each velocity component separately
        for i in range(len(p1VelocitiesIJK)):
            # Store initial velocity for calculation
            p1InitialVelocity = p1VelocitiesIJK[i]
            
            # Conservation of momentum with restitution coefficient
            # Formula: v1' = [(m1 - e*m2)v1 + (1+e)m2v2] / (m1 + m2)
            p1VelocitiesIJK[i] = (1.15 * p1VelocitiesIJK[i] * (p1.mass - p2.mass * self.e)
                            + p2.mass * p2VelocitiesIJK[i] * (1 + self.e)) / (p1.mass + p2.mass)
            
            # Corresponding momentum transfer for second particle
            p2VelocitiesIJK[i] = (1.15 * p1InitialVelocity - p2VelocitiesIJK[i]) * self.e + p1VelocitiesIJK[i]

            # Reconstruct velocity vectors from components
            p1.velocity = sum(p1VelocitiesIJK)
            p2.velocity = sum(p2VelocitiesIJK)