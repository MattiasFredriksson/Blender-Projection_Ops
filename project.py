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
from .plane import *
from bpy.props import * #Property objects


class ProjectMesh(bpy.types.Operator):
	bl_idname = "mesh.project_onto_selected_mesh"
	bl_label = "Project Mesh(es) onto Active"
	bl_info = "Projects a selected mesh(es) onto the active mesh"
	bl_options = {'REGISTER', 'UNDO'}
	
	depth_axis_enum = [
		("Z", "Z", "The objects Z axis will be used", 0),
		("Y", "Y", "The objects Y axis will be used", 1),
		("X", "X", "The objects X axis will be used", 2),
		("CAMERA", "View", "The camera forward axis will determine the offset from the surface", 3),
		("CLOSEST", "Closest Axis", "The closest local axis to the camera view will determine the surface offset", 4),
		]
	largest_obj_enum = [
		("VOLUME", "Volume", "The object with the largest bounding box volume", 1),
		("VERTCOUNT", "Vertex Count", "The object with the most vertices", 2),
		]
	
	displayExecutionTime = False
	
	depth_axis = EnumProperty(items=depth_axis_enum, 
			name = "Depth Axis",
            description="Select the axis that determines the offset from the surface for each vertex (local axis is related to parent object). ",
			default = 'CLOSEST',)
	largest_obj = EnumProperty(items=largest_obj_enum, 
			name = "Selection Parent",
            description="Determines which object's depth/offset axis is used with a local axis setting",)
	depthOffset = FloatProperty(name="Surface Offset",
            description="Move the projection closer/away from target surface by a fixed amount (along neg. view forward axis)",
            default=0, min=-sys.float_info.max, max=sys.float_info.max, step=1)
	bias = FloatProperty(name="Intersection Bias",
            description="Error marginal for intersection tests, can solve intersection problems",
            default=0.00001, min=0.00001, max=1, step=1, precision=4)
	
	def invoke(self, context, event) :
		""" 
		Invoke stage, gathering information of the projection objects:
		"""
		start_time = time.time()
		#Fetch camera orientations:
		self.cameraRot = findViewRotation(context) 
		self.cameraRotInv = self.cameraRot.transposed()
		self.cameraForward = -self.cameraRot.col[2]
		self.cameraPos = findViewPos(context)
		self.ortho = viewTypeOrtho(context)
		self.lastOffset = self.depthOffset
		
		#Params that will be set:
		self.ob_list = None #Objects that will be projected
		self.child_list = None #List of child objects transformed around the parent.
		self.parent_ob = None #The parent object
	
		target_ob = context.active_object
		#Verify target
		if not target_ob:
			self.report({'ERROR'}, "No active mesh object found to use as projection target.")
			return {'CANCELLED'}
		elif target_ob.type != 'MESH':
			self.report({'ERROR'}, "Active object was not a mesh. Select an appropriate mesh object as projection target")
			return {'CANCELLED'}
		ob_sources = context.selected_objects
		#Verify selection
		self.ob_list = []
		#Cull non-mesh and active objects:
		for ob in ob_sources :
			if ob.type == 'MESH' and ob != target_ob :
				self.ob_list.append(SourceMesh(ob, self))
		if len(self.ob_list) == 0 :
			if len(ob_sources) > 0 :
				self.report({'ERROR'}, "Only mesh objects can be projected, need atleast one project source and an active object as projection target")
			else :
				self.report({'ERROR'}, "No selection to project found, make sure to select one project source and an active object as projection target")
			return {'CANCELLED'}
		#Generate projection info
		bvh = generate_BVH(target_ob, context.scene, self.bias)
		self.target_ob = target_ob.name
		
		#Generate project data
		for ob in self.ob_list :
			if self.ortho :
				ob.projectVertOrtho(self.cameraForward, bvh)
			else :
				ob.projectVertPersp(self.cameraPos, bvh)
		
		if ProjectMesh.displayExecutionTime :
			self.report({'INFO'}, "Finished, invoke stage execution time: %.2f seconds ---" % (time.time() - start_time))
		return self.execute(context)
	
	def execute(self, context):
		"""
		Project each mesh onto active object
		"""
		start_time = time.time()
		
		offset_change =  self.depthOffset != self.lastOffset
		
		self.lastOffset = self.depthOffset
		if not offset_change:
			self.report({'INFO'}, "Executing: Mesh Projection")
			#Project the meshes with the gathered information
			self.project(context.scene)
			#Finished
			if ProjectMesh.displayExecutionTime :
				self.report({'INFO'}, "Finished, project stage execution time: %.2f seconds ---" % (time.time() - start_time))
		#Set offset move it on camera forward axis:
		self.depthChange(context.scene)
		return {'FINISHED'}
		
	def depthChange(self, scene) :
		"""	Moves the objects along camera z axis
		"""
		mat = Matrix.Translation(self.cameraForward * -self.depthOffset)
		for ob in self.ob_list : 
			if ob.bmesh is not None:
				setNamedMesh(ob.bmesh, ob.name, scene, mat)
	
	def project(self, scene) :
		"""	Project the mesh(es) onto the target
		"""
		
		#Find our parent object
		parent_ob, child_list = self.findParent()
		
		#Find the depth axis
		depth_axis = self.getDepthAxis(parent_ob)
		#Calculate the offset of each vertex
		min_offset = self.calcOffset(depth_axis)
						
		for ob in self.ob_list : 			
			#Project the vertices:
			count = 0
			used_closest = 0
			for vert in ob.bmesh.verts :
				success, used_con = self.projectVert(ob, vert, min_offset)
				count += success
				used_closest += used_con
			
			#Finalize the projection by assigning the bmesh into the blender object 
			if count > 0 :
				ob.bmesh.select_flush(False)
				setNamedMesh(ob.bmesh, ob.name, scene, Matrix.Translation(self.cameraForward * -self.depthOffset))
				if used_closest > 0:
					self.report({'WARNING'}, "Mesh: %s has %d vertices that failed to project and used neighbouring vertex result instead. Verify selected verts is projected OK" %(ob.name, used_closest))
				nonProjCount = len(ob.bmesh.verts) - (count)
				if nonProjCount != 0:
					self.report({'WARNING'}, "Mesh: %s has %d vertices that did not project succesfully. Validate that the mesh is covered by the target" %(ob.name, nonProjCount))
			else :
				self.report({'WARNING'}, "Mesh: %s had no vertices projected onto the target. Validate that the mesh is covered by the target" %(ob.name))
	#Done
	
	def findParent(self) :
		"""
		Finds the parent deppending on setting
		"""
		#Compare value
		value = sys.float_info.min
		parent_ob = None
		#Compare volume
		if self.largest_obj == 'VOLUME' :
			for ob in self.ob_list :
				if ob.volume > value :
					value = ob.volume
					parent_ob = ob
		#Compare vert count
		else :
			for ob in self.ob_list :
				if len(ob.bmesh.verts) > value :
					value = len(ob.bmesh.verts)
					parent_ob = ob
		#Generate a list with only child objects:
		child_list = []
		for ob in self.ob_list :
			if ob is not parent_ob :
				child_list.append(ob)
		#Store info
		return parent_ob, child_list
	#End
	
	def calcOffset(self, depthAxis) :
		"""
		Calculates the offset of each vert 
		"""
		min_val = sys.float_info.max
		for ob in self.ob_list :
			min_val = ob.calcOffset(depthAxis, min_val)
		return min_val
				
	def getDepthAxis(self, object) :
		"""
		Finds the axis in world space used that determines the depth offset.
		Note that the depth is measured in the direction of the axis (offset increases with distance on axis)
		"""
		if self.depth_axis == 'CLOSEST' :
			return findClosestAxis(object.rotation, -self.cameraForward)
		elif self.depth_axis == 'X' :
			return object.rotation.col[0]
		elif self.depth_axis == 'Y' :
			return object.rotation.col[1]
		elif self.depth_axis == 'Z' :
			return object.rotation.col[2]
		else : #self.depth_axis == 'CAMERA' :
			return -self.cameraForward
		
	
	def projectVert(self, ob_info, vert, depth_min) :
		"""	Calculate the projection of a single vert (also sets the vert.co)
		transMat:	Object transformation matrix
		vert:		Vert being updated
		"""
		#Fetch project location:
		loc = ob_info.proj_info[vert.index][0]
		#Fetch project dir:
		if self.ortho :
			dir = self.cameraForward
		else :
			dir = (ob_info.position_data[vert.index] - self.cameraPos)
			dir.normalize()
		
		offset = (ob_info.vert_offset[vert.index] - depth_min)
		
		#Deselect all
		vert.select_set(False)
		#If intersection occured project it
		if loc is not None:
			vert.co = loc - dir * offset
			return True, False #Projection success
		else:
			#If projection failed search edges and see if connect projection point can be used instead:
			for edge in vert.link_edges :
				o_vert_ind = edge.other_vert(vert).index
				loc = ob_info.proj_info[o_vert_ind][0]
				if loc is not None : #Loc is none if the vert projection failed
					nor = ob_info.proj_info[o_vert_ind][1] #Normal of the face projected onto
					rel = nor.dot(dir) #Relation between ray dir and plane normal.
					if abs(rel) <  self.bias:
						continue #No face perpendicular to our projection dir
					#Plane d value:
					d = -nor.dot(loc)
					#Calculate distance to plane
					vert_pos = ob_info.position_data[vert.index]
					dist_plane = (-d - nor.dot(vert_pos)) / rel
					vert.co = vert_pos + dir * (dist_plane - offset)
					#Select verts that used closest
					vert.select_set(True)
					return True, True #Projected but used connected projection value todo so
		return False, False #Projection failed
					
class SourceMesh :
	def __init__(self, object, settings):
		self.name = object.name
		self.translation, self.rotation, self.scale = object.matrix_world.decompose()
		self.rotation = self.rotation.to_matrix()
		self.bmesh = createBmesh(object, object.matrix_world)
		if_scaleInversedFlipNormals(self.bmesh, self.scale)
		#Store position info in world space
		self.position_data = [vert.co.copy() for vert in self.bmesh.verts]
		self.AABB = getBoundBox(object)
		self.volume = getBoundBoxVolume(object)
		self.vert_offset = None #List of vert offsets from base
		self.proj_info = None #Vert projection result
		
	def calcOffset(self, depthAxis, min_val) :
		"""
		Calculate the distance from each vertex to a defined plane, stores it in an array.
		"""
		#Do the depth comparison in local space
		self.vert_offset = [depthAxis.dot(pos) for pos in self.position_data]
		for dist in self.vert_offset :
			min_val = min(dist, min_val)
		return min_val
	
	def projectVertOrtho(self, dir, bvh) :
		"""
		Gathers projection data using orthogonal setting
		"""
		#Ray cast: (loc, nor, ind, dist) 
		self.proj_info = [ bvh.ray_cast(loc, dir, 100000) for loc in self.position_data]
	def projectVertPersp(self, camPos, bvh) :
		"""
		Gathers projection data using perspective setting
		"""
		#Ray cast: (loc, nor, ind, dist) 
		self.proj_info = [bvh.ray_cast(loc, (loc - camPos).normalized(), 100000) for loc in self.position_data]
	
	
	def __del__(self) :
		self.bmesh.free()
def findClosestAxis(meshRot, axis) :
	"""
	Finds the mesh rot axis closest to the defined axis
	"""
	x = axis.dot(meshRot.col[0])
	y = axis.dot(meshRot.col[1])
	z = axis.dot(meshRot.col[2])
	
	if abs(x) > max(abs(y), abs(z)) :
		return meshRot.col[0] * sign(x)
	elif abs(y) > abs(z) :
		return meshRot.col[1] * sign(y)
	else :
		return meshRot.col[2] * sign(z)
	
					