from math import *
from mathutils import *

class Plane :
	"""
	Plane object with a few basic operations:
	"""
	def __init__(self, normal, point) :
		"""
		Initiates a plane from a normalized vector and a point in the plane
		"""
		self.normal = normal 
		self.d = -normal.dot(point)
		
	def distance(self, point) :
		"""
		Returns the signed distance to the plane in relation to normal
		"""
		return self.normal.dot(point) + self.d
	
	def transformed(matrix) :
		"""
		Returns a transformed plane
		"""
		pos = (-self.d * self.normal)
		pos = matrix * Vector((pos.x, pos.y, pos.z, 1))
		norm = matrix * Vector((self.normal.x, self.normal.y, self.normal.z, 0))
		norm.normalize() #Incase scaling is applied
		return Plane(norm, pos)