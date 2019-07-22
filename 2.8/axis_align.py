from math import *
from mathutils import *
from .funcs_math import *

def axisAlignRotationMatrix(rotMat) :
	"""	Align the rotation matrix to the closest axis (1,0,0), (0,1,0), (0,0,1), (-1,0,0),...
	"""
	rotMat.col[0]  = findAxisAlignment_X(rotMat.col[0])
	rotMat.col[1] = findAxisAlignment_Y(rotMat.col[1])
	if abs(rotMat.col[0].dot(rotMat.col[1])) < 0.9999 : #Both rot axis can have equal angle to an axis
		rotMat.col[2] = rotMat.col[0].cross(rotMat.col[1])
	else : #If equal axis:
		rotMat.col[2] = findAxisAlignment_Z(rotMat[2])
		rotMat.col[1] = rotMat.col[2].cross(rotMat.col[0])
	return rotMat
	
def findAxisAlignment_X(axis) :
	""" 
	Finds the largest component of the axis and returns it as a axis aligned unit vector.
	Also identifies the the relative axis index.
	"""
	if abs(axis[0]) >= max(abs(axis[1]), abs(axis[2])) :
		return Vector((sign(axis[0]),0,0))
	elif abs(axis[1]) >= abs(axis[2]) :
		return Vector((0,sign(axis[1]),0))
	return Vector((0,0,sign(axis[2])))
	
def findAxisAlignment_Y(axis) :
	""" 
	Finds the largest component of the axis and returns it as a axis aligned unit vector.
	Also identifies the the relative axis index.
	"""
	if abs(axis[1]) >= max(abs(axis[0]), abs(axis[2])) :
		return Vector((0,sign(axis[1]),0))
	elif abs(axis[2]) >= abs(axis[0]) :
		return Vector((0,0,sign(axis[2])))
	return Vector((sign(axis[0]),0,0))
	
def findAxisAlignment_Z(axis) :
	""" 
	Finds the largest component of the axis and returns it as a axis aligned unit vector.
	Also identifies the the relative axis index.
	"""
	if abs(axis[2]) >= max(abs(axis[0]), abs(axis[1])) :
		return Vector((0,0,sign(axis[2])))
	elif abs(axis[0]) >= abs(axis[1]) :
		return Vector((sign(axis[0]),0,0))
	return Vector((0,sign(axis[1]),0))