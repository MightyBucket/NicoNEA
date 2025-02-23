from vpython import *
from Particle_manager import *

class Collision_Handler:
    def __init__(self, particleGroupObj, e):
        self.particles = particleGroupObj
        self.e = e  # E is always set to 1 in the project
        self.hasJustCollided = self._setupCollisionCounter()
        self.bounces = 0

    def neutron_creation(self,p1,p2): #this will not work for a few reasons: p1 hasn't loaded yet so it will be a neutron from the beginnig, p2 has not loaded yet so can't be deleted        Particle.delete_object(p2)
        Particle.delete_object(p2)
        p1.charge, p1.mass, p1.colour = [0,100,vector(0,1,0)]

    def _setupCollisionCounter(self):
        hasJustCollidedDict = {}
        for pair in self.particles.array_pairs:
            hasJustCollidedDict[pair] = False
        return hasJustCollidedDict

    def collisionDetection(self):
        for pa, pb in self.particles.array_pairs:
            if pa.does_collide_with(pb):
                if self.hasJustCollided[(pa, pb)]:
                    continue
                self.collide(pa, pb)
                self.hasJustCollided[(pa, pb)] = True
                self.bounces += 1
            else:
                if self.hasJustCollided[(pa,pb)]:
                    self.hasJustCollided[(pa,pb)] = False
    def collide(self,p1,p2):
        rOriginal = p2.pos-p1.pos

        #if self.bounces >=2:
        #    self.neutron_creation(p1,p2)

        rHorzPerp = cross(rOriginal, vector(0,1,0))
        rVertPerp = cross(rHorzPerp, rOriginal)

        p1VelocitiesIJK = [proj(p1.velocity, rOriginal), proj(p1.velocity, rVertPerp), proj(p1.velocity, rHorzPerp)]
        p2VelocitiesIJK = [proj(p2.velocity, rOriginal), proj(p2.velocity, rVertPerp), proj(p2.velocity, rHorzPerp)]

        for i in range(len(p1VelocitiesIJK)):
            p1InitialVelocity = p1VelocitiesIJK[i]
            p1VelocitiesIJK[i] = (1.15 * p1VelocitiesIJK[i] * (p1.mass - p2.mass * self.e) + p2.mass * p2VelocitiesIJK[i] * (
                1 + self.e))/(p1.mass + p2.mass)
            p2VelocitiesIJK[i] = (1.15 * p1InitialVelocity - p2VelocitiesIJK[i]) * self.e + p1VelocitiesIJK[i]

            p1.velocity = (p1VelocitiesIJK[0] + p1VelocitiesIJK[1] + p1VelocitiesIJK[2])
            p2.velocity = (p2VelocitiesIJK[0] + p2VelocitiesIJK[1] + p2VelocitiesIJK[2])