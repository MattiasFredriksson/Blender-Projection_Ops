#  align_to_view.py (c) 2016 Mattias Fredriksson
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bpy, sys

from math import *
from mathutils import *
from .funcs_math import *
from .funcs_blender import *
from .axis_align import *
from bpy.props import * #Property objects
	
class AlignSelection(bpy.types.Operator):
	bl_idname = "mesh.align_selection_view"
	bl_label = "Align Selection to View"
	bl_info = "Aligns the mesh rotation to the current view"
	bl_options = {'REGISTER', 'UNDO'}
	
	
	rot_type_enum = [
		("Z", "Z", "Selection will be rotated so the Z axis is facing the camera", 0),
		("Y", "Y", "Selection will be rotated so the Y axis is facing the camera", 1),
		("X", "X", "Selection will be rotated so the X axis is facing the camera", 2),
		("AXISALIGNED", "Axis Aligned", "Selection's XYZ axis will be aligned with the closest camera axis", 3),
		("CLOSEST", "Closest", "Selection will be rotated so that the closest axis to the camera will face it", 4),
		]
	parent_obj_enum = [
		("VERTCOUNT", "Vertex Count", "Use the object with the most vertices", 0),
		("VOLUME", "Volume", "Use the object with largest bounding box", 1),
		("ACTIVE", "Active", "Use the active object as the parent", 2),
		]
	rot_type = EnumProperty(items=rot_type_enum, 
			name = "Alignment",
            description="Determines the axis of the parent object that will be aligned to the camera view. ",
			default = 'CLOSEST',)
	parent_obj = EnumProperty(items=parent_obj_enum, 
			name = "Selection Parent",
            description="Determines which selected object that the other objects alignment will relate to",
			default = 'ACTIVE',)
	exclude_active = BoolProperty(name = "Exclude active object",
            description="Exclude the active object from selection, and disallows it from parenting the selection (usefull if it's a projection target selection)",
			default=False)
			
	def invoke(self, context, event) :
		
		return self.execute(context)
	
	def execute(self, context):
		
		#Fetch camera orientations:
		self.cameraRot = findViewRotation(context) 
		self.cameraRotInv = self.cameraRot.transposed()
		self.cameraPos = findViewPos(context)
		self.ortho = viewTypeOrtho(context)
		
		ob_list = context.selected_objects
		#Remove active object now (no need to check for it later...)
		if self.exclude_active :
			try : #Check if it's there
				ob_list.remove(context.active_object)
			except:
				pass #Not there...
		parent, child_list = self.findParent(context, ob_list)
		
		#Invert parent world matrix
		parent_world_inv = parent.matrix_world.inverted()
		#Find parent orientation
		parent_mat = self.parent_orientation(parent)
		for ob in child_list :
			ob.matrix_world = self.orientation(ob, parent_world_inv, parent_mat)
		parent.matrix_world = parent_mat
	
		return {'FINISHED'}
		
	def parent_orientation(self, ob) :
		"""
		Finds the orientation matrix of the parent object.
		"""
		
		loc, meshRot, sca = ob.matrix_world.decompose()
		meshRot = meshRot.to_matrix()
		#Calc rotation
		if self.rot_type == 'AXISALIGNED' :
			rot = self.cameraRot * axisAlignRotationMatrix(self.cameraRotInv * meshRot)
		#Axis alignements: Axis Rot is rotated with the objects rotation difference on the plane parallell to cameras XY plane,
		#This generates the rotation in the cameras rotation space (camera rotation is applied last).
		elif self.rot_type == 'Z' : 
			rot = Matrix.Identity(3) #Mesh face inverse camera
			rot = calculateRotXYPlane_baseX(meshRot,self.cameraRot) * rot #Find rotation difference on XY plane
			rot = self.cameraRot * rot #Rotate to camera space
		elif self.rot_type == 'Y' :
			#Find rotation difference to camera, could use quats and rotation_difference(quat)
			rot = Matrix.Rotation(half_pi, 3, Vector((1,0,0))) #Rotate Y facing upward
			rot = calculateRotXYPlane_baseX(meshRot, self.cameraRot) * rot #Find rotation difference on ZX plane
			rot = self.cameraRot * rot #Move rotation to camera space
		elif self.rot_type == 'X' :
			rot =  Matrix.Rotation(-half_pi, 3, Vector((0,1,0))) #Rotate X facing up
			rot = calculateRotXYPlane_baseY(meshRot, self.cameraRot) * rot #Find rotation difference on YZ plane
			rot = self.cameraRot * rot #Move rotation to camera space
		else : # self.rot_type == 'CLOSEST' :
			rot = self.cameraRot * alignRotationMatrix(self.cameraRotInv * meshRot)
		#Assemble orientation matrix:
		return Matrix.Translation(loc) * (rot * scaleMatrix(sca, 3)).to_4x4()
		
	def orientation(self, object, parent_world_inv, parent_mat) :
		"""
		Func finding the orientation in relation to the parent object.
		object:				Object to calculate matrix for
		parent_world_inv:	Parent objects world matrix inverse
		parent_mat:			Calculated final transform for parent object
		"""		
		return parent_mat * parent_world_inv * object.matrix_world
		
	
	def findParent(self, context, ob_list) :
		"""
		Finds the parent deppending on setting
		"""
		#Compare value
		value = sys.float_info.min
		parent_ob = None
		#Parent: Obj with most vertices
		if self.parent_obj == 'VERTCOUNT' :
			for ob in ob_list :
				if len(ob.data.verts) > value :
					value = len(ob.bmesh.vertices)
					parent_ob = ob
		#Parent:Active
		elif self.parent_obj == 'ACTIVE' and not self.exclude_active and context.active_object is not None:
			parent_ob = context.active_object
		#Parent: Obj with largest OBB Volume
		else : #self.parent_obj == 'VOLUME' :
			for ob in ob_list :
				volume = getBoundBoxVolume(ob) 
				if volume > value :
					value = volume
					parent_ob = ob
		#Generate a list with only child objects:
		child_list = []
		for ob in ob_list :
			if ob is not parent_ob :
					child_list.append(ob)
		#Store info
		return parent_ob, child_list

def calculateRotXYPlane_baseX(meshAxis, camAxis) :
	""" Finds the rotation on the camera X,Y plane by calculating the angle to mesh X axis projected onto the plane 
	"""
	#Project onto XY plane and normalize
	xAxis = meshAxis.col[0] -  meshAxis.col[0].dot(camAxis.col[2]) * camAxis.col[2]
	xAxis.normalize()
	#Calc angle to x axis
	x = xAxis.dot(camAxis.col[0])
	y = xAxis.dot(camAxis.col[1])
	angle = atan2(y,x)
	#Rotate around Z axis to same angle for X
	return Matrix.Rotation(angle, 3, Vector((0,0,1))) #Use camAxis[2] if not in camera space.
def calculateRotXYPlane_baseY(meshAxis, camAxis) :
	""" Finds the rotation on the camera X,Y plane by calculating the angle to mesh Y axis projected onto the plane
	"""
	yAxis = meshAxis.col[1] - meshAxis.col[1].dot(camAxis.col[2]) * camAxis.col[2]
	yAxis.normalize()
	x = yAxis.dot(camAxis.col[0])
	y = yAxis.dot(camAxis.col[1])
	
	angle = atan2(y,x)
	return Matrix.Rotation(angle - half_pi, 3, Vector((0,0,1)))  #Use camAxis[2] if not in camera space.
	
def alignRotationMatrix(rotMat) :
	"""
	Aligns the axis with largest Z component to (0,0,1) and orthonormalizes the other two axes.
	"""
	#Find axis with largest Z component and orthonormalize the other basis vectors to it:
	if abs(rotMat.col[2][2]) > max(abs(rotMat.col[1][2]), abs(rotMat.col[0][2])) :
		#Z axis is depth:
		rotMat.col[2] = Vector((0,0,sign(rotMat.col[2][2])))
		rotMat.col[2], rotMat.col[0], rotMat.col[1] = orthoNormalizeVec3(rotMat.col[2], rotMat.col[0], rotMat.col[1])
	elif abs(rotMat.col[1][2]) > abs(rotMat.col[0][2]) :
		#Y axis is depth:
		rotMat.col[1] = Vector((0,0,sign(rotMat.col[1][2])))
		rotMat.col[1], rotMat.col[0], rotMat.col[2] = orthoNormalizeVec3(rotMat.col[1], rotMat.col[0], rotMat.col[2])
	else :
		#X axis is depth:
		rotMat.col[0] = Vector((0,0,sign(rotMat.col[0][2])))
		rotMat.col[0], rotMat.col[1], rotMat.col[2] = orthoNormalizeVec3(rotMat.col[0], rotMat.col[1], rotMat.col[2])
	return rotMat
	
