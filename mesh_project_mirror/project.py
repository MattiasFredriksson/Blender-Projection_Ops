#  uv_project.py (c) 2016 Mattias Fredriksson
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

import bpy, time, sys

from math import *
from mathutils import *
from .funcs_math import *
from .funcs_blender import *
from bpy.props import * #Property objects


class ProjectMesh(bpy.types.Operator):
	bl_idname = "mesh.project_onto_selected_mesh"
	bl_label = "Project Mesh(es) onto Active"
	bl_info = "Projects a selected mesh(es) onto the active mesh"
	bl_options = {'REGISTER', 'UNDO'}
	
	proj_type_enum = [
		("AXISALIGNED", "Axis Aligned", "The projected mesh(es) will be rotated so it's axis with the smallest angel toward the camera will face the it", 1),
		("CAMERA", "Camera View", "The mesh will be projected as is, where each vertice distance from the projection surface will be determined by the furthest point from the camera (plane)", 2),
		("ZISUP", "Z is Up", "The projected mesh(es) will be rotated so the Z axis will face the camera", 3),
		]
	
	displayExecutionTime = False
	
	proj_type = EnumProperty(items=proj_type_enum, 
			name = "Projection Alignment",
            description="Determines how the mesh will be aligned related to camera view before projection onto the surface. ",)
	depthOffset = FloatProperty(name="Depth Offset",
            description="Move the projection closer/away from target surface by a fixed amount",
            default=0, min=-sys.float_info.max, max=sys.float_info.max, step=1)
	bias = FloatProperty(name="Intersection Bias",
            description="Error marginal for intersection tests, can solve intersection problems",
            default=0.0001, min=0.0001, max=1, step=3)
	
	def invoke(self, context, event) :
		""" 
		Invoke stage, gathering information of the projection objects:
		"""
		start_time = time.time()
		#Fetch camera orientations:
		self.cameraRot = findViewRotation(context) 
		self.cameraRotInv = self.cameraRot.transposed()
		self.camAxis = findViewAxis(context)
		self.camPos = findViewPos(context)
		self.ortho = viewTypeOrtho(context)
		self.lastOffset = self.depthOffset
	
		target_ob = context.active_object
		self.generate_BVH(target_ob, context.scene)
		self.target_ob = target_ob.name
		
		self.ob_list = []
		for ob in context.selected_objects :
			if ob.type == 'MESH' and ob != target_ob :
				self.ob_list.append(SourceMesh(ob))
		
		if ProjectMesh.displayExecutionTime :
			self.report({'INFO'}, "Finished, invoke stage execution time: %.2f seconds ---" % (time.time() - start_time))
		return self.execute(context)
	
	def execute(self, context):
		"""
		Project each mesh onto active object
		"""
		start_time = time.time()
		
		if  self.depthOffset != self.lastOffset:
			self.lastOffset = self.depthOffset
			#If only depth changed, move it on z axis:
			self.depthChange(context.scene)
		else:
			self.report({'INFO'}, "Executing: Mesh Projection")
			#Project the meshes with the gathered information
			self.project(context.scene)
			#Finished
			if ProjectMesh.displayExecutionTime :
				self.report({'INFO'}, "Finished, project stage execution time: %.2f seconds ---" % (time.time() - start_time))
		return {'FINISHED'}
		
	def depthChange(self, scene) :
		"""	Moves the objects along camera z axis
		"""
		mat = Matrix.Translation(self.camAxis[2] * -self.depthOffset)
		for ob in self.ob_list : 
			if ob.bmesh_gen is not None:
				setNamedMesh(ob.bmesh_gen, ob.name, scene, Matrix.Translation(self.camAxis[2] * -self.depthOffset))
	
	def generate_BVH(self, target_ob, scene) :
		#Can't create from object, transformation not applied
		bmesh = createBmesh(target_ob, target_ob.matrix_world, True, scene, True)
		self.bvh = bvhtree.BVHTree.FromBMesh(bmesh, epsilon = self.bias) 
		bmesh.free()
	
	def project(self, scene) :
		"""	Project the mesh(es) onto the target
		"""
		for ob in self.ob_list : 
			#Create a bm mesh copy of the mesh!
			bmesh = ob.bmesh.copy()
			(vMin, vMax) = findMinMax(bmesh)
			mat = self.orientation(ob)
			#createMesh(bmesh, scene, mat) #Generate a aligned debug mesh
			#Find the furthest point of the mesh along camera forward 
			depthDist = max(self.camAxis[2].dot(mat * vMin), self.camAxis[2].dot(mat * vMax))
			#Project the vertices:
			count = 0
			for vert in bmesh.verts :
				count += self.projectVert(mat, vert, depthDist)
			#Finalize the projection by assigning the bmesh into the blender object 
			#Validate one vert was projected first:
			
			if count > 0 :
				ob.bmesh_gen = bmesh
				setNamedMesh(bmesh, ob.name, scene, Matrix.Translation(self.camAxis[2] * -self.depthOffset))
				nonProjCount = len(bmesh.verts) - count
				if nonProjCount != 0:
					self.report({'WARNING'}, "Mesh: %s has %d vertices that did not project succesfully. Validate that the mesh is covered by the target" %(ob.name, nonProjCount))
			else :
				self.report({'WARNING'}, "Mesh: %s had no vertices projected onto the target. Validate that the mesh is covered by the target" %(ob.name))
	#Done
	
	
	def projectVert(self, transMat, vert, depthDist) :
		"""	Calculate the projection of a single vert (also sets the vert.co)
		transMat:	Object transformation matrix
		vert:		Vert being updated
		"""
		co =  transMat * vert.co
		#Find the distance offset to the max point of the mesh along camera axis
		depthOffset = -(depthDist - self.camAxis[2].dot(co))
		dir = self.getCameraAxis(co)
		#Ray cast:
		(loc, nor, ind, dist) = self.bvh.ray_cast(co, dir, 100000)
		#If intersection occured project it
		if loc is not None:
			vert.co = loc + dir * (depthOffset + self.depthOffset)
			return True
		return False
	
	def orientation(self, ob) :
		loc, meshRot, sca = ob.matrix_world.decompose()
		meshRot = meshRot.to_matrix()
		
		#Calc rotation
		if self.proj_type == 'AXISALIGNED' :
			rot = self.cameraRot * alignRotationMatrix(self.cameraRotInv * meshRot)
		elif self.proj_type == 'ZISUP' :
			rot = self.cameraRot * calculateXYPlaneRot(meshRot.transposed(), self.camAxis)
		else : #self.proj_type == 'CAMERA' :
			rot = meshRot
		#Assemble orientation matrix:
		mat = Matrix.Translation(loc) * (rot * scaleMatrix(sca, 3)).to_4x4()
		#mat[3].xyz = loc
		return mat
		
	def getCameraAxis(self, target) :
		"""	Calculates the projection ray direction
		"""
		if self.ortho :
			return self.camAxis[2]
		else :
			dir = target - self.cameraPos
			dir.normalize()
			return dir	
			
class SourceMesh :
	def __init__(self, object):
		self.name = object.name
		self.matrix_world = object.matrix_world.copy()
		self.bmesh = createBmesh(object)
		self.bmesh_gen = None
	
	def __del__(self) :
		if self.bmesh_gen is not None :
			self.bmesh_gen.free()
		self.bmesh.free()
def calculateXYPlaneRot(meshAxis, camAxis) :
	"""	Finds the rotation of the mesh on the camera X,Y plane 
	"""
	xAxis = meshAxis[0] - meshAxis[0].dot(camAxis[2]) * camAxis[2]
	xAxis.normalize()
	x = xAxis.dot(camAxis[0])
	y = xAxis.dot(camAxis[1])
	
	angle = atan2(y,x)
	return Matrix.Rotation(angle, 3, Vector((0,0,1))) #Use camAxis[2] if the rotation is applied in world space opposed to camera space
	
def alignRotationMatrix(rotMat) :
	"""
	Aligns the axis with largest Z component to (0,0,1) and orthonormalizes the other two axes.
	"""
	#Find axis with largest Z component and orthonormalize the other basis vectors to it:
	if abs(rotMat[2][2]) > max(abs(rotMat[1][2]), abs(rotMat[0][2])) :
		#Z axis is depth:
		rotMat[2] = Vector((0,0,sign(rotMat[2][2])))
		rotMat[2], rotMat[0], rotMat[1] = orthoNormalizeVec3(rotMat[2], rotMat[0], rotMat[1])
	elif abs(rotMat[1][2]) > abs(rotMat[0][2]) :
		#Y axis is depth:
		rotMat[1] = Vector((0,0,sign(rotMat[1][2])))
		rotMat[1], rotMat[0], rotMat[2] = orthoNormalizeVec3(rotMat[1], rotMat[0], rotMat[2])
	else :
		#X axis is depth:
		rotMat[0] = Vector((0,0,sign(rotMat[0][2])))
		rotMat[0], rotMat[1], rotMat[2] = orthoNormalizeVec3(rotMat[0], rotMat[1], rotMat[2])
	return rotMat			
					