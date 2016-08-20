
import sys

from math import *
from mathutils import *

class Point :
	"""
	Point containing integers
	"""
	def __init__(self, x, y) :
		self.X = x
		self.Y = y

#Lerp between value a->b with specified factor
def lerp(a, b, factor) :
	return (1-factor) * a + factor * b

#Find the minimum and maximum point in the mesh
#Returns (min, max)
def findMinMax(mesh) :
	vMin = Vector((sys.float_info.max, sys.float_info.max, sys.float_info.max))
	vMax = Vector((-sys.float_info.max, -sys.float_info.max, -sys.float_info.max))
	for vert in mesh.verts:
		vMin = minVec(vert.co, vMin)
		vMax = maxVec(vert.co, vMax)
	return (vMin, vMax)
		
#Compare and return the minimal vector combination:
def minVec(v0, v1) :
	vLen = min(len(v0), len(v1))
	v = Vector((0,)*vLen)
	for i in range(vLen) :
		v[i] = min(v0[i], v1[i])
	return v
#Compare and return the minimal vector combination:
def minVec_x3(v0, v1, v2) :
	vLen = min(len(v0), len(v1), len(v2))
	v = Vector((0,)*vLen)
	for i in range(vLen) :
		v[i] = min(v0[i], v1[i], v2[i])
	return v

#Compare and return the maximal vector combination:
def maxVec(v0, v1) :
	vLen = min(len(v0), len(v1))
	v = Vector((0,)*vLen)
	for i in range(vLen) :
		v[i] = max(v0[i], v1[i])
	return v
#Compare and return the maximal vector combination:
def maxVec_x3(v0, v1, v2) :
	vLen = min(len(v0), len(v1), len(v2))
	v = Vector((0,)*vLen)
	for i in range(vLen) :
		v[i] = max(v0[i], v1[i], v2[i])
	return v
	
def rotateVec2(vec, angle) :
	"""	Rotate CCW by angle
	"""
	theta = radians(angle);
	cs = cos(theta);
	sn = sin(theta);
	return Vector((vec.x * cs - vec.y * sn, vec.x * sn + vec.y * cs))

def orthoNormalizeVec2(vecA, vecB) :
	"""	
	Ortho-normalize the vectors using Gram-Smith. 	
	Making vecB orthogonal to vecA (and  vice versa) and normalize both.
	Returns: Touple of the vectors in same order.
	"""
	vecA.normalize()
	vecB = vecB - vecB.dot(vecA) * vecA
	return (vecA, vecB / vecB.length)

def orthoNormalizeVec3(vecA, vecB, vecC) :
	"""	
	Ortho-normalize the vectors using Gram-Smith. 	
	Returns: Touple of the vectors in same order.
	"""
	vecA.normalize()
	vecB = vecB - vecB.dot(vecA) * vecA
	vecB /= vecB.length
	
	vecC = vecC - vecC.dot(vecB) * vecB - vecC.dot(vecA) * vecA
	vecC /= vecC.length
	return (vecA, vecB, vecC)

#Return the signed component of the value:
def sign(value):
	if value > 0 :
		return 1
	elif value < 0 :
		return -1
	return 0
	
def scaleMatrix(scaleVec, size = 4) :
	"""
	Generate a scaling matrix from a vector defining the scale on each axis
	"""
	mat = Matrix.Identity(size)
	mat[0].x = scaleVec.x
	mat[1].y = scaleVec.y
	if size > 2 :
		mat[2].z = scaleVec.z
	return mat