#  __init__.py (c) 2016 Mattias Fredriksson
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

#Addon info
bl_info = {
	'name': "Projection Operators",
	'author': "Mattias Fredriksson ",
	'version': (0, 9, 3),
	'blender': (2, 77, 0),
	'location': "3DView > Objectmode: Project Mesh onto UV Surface, Mirror Mesh over Defined Surface, Project Mesh(es) onto Active, Align Selection to View",
	'warning': "Bugs can exist, beware of using operators outside the usecase",
	'description': "4 Operators containing functionality for mirroring and projection mesh objects over/onto a mesh surface",
	'wiki_url': "",
	'tracker_url': "",
	'category': 'Mesh'}

import sys
def force_reload():
	import importlib
	try:
		from . import funcs_blender, funcs_math, funcs_tri, proj_data, bound, partition_grid, uv_project, project, mesh_mirror_script, align_to_view, plane, axis_align
		importlib.reload(funcs_blender)
		importlib.reload(funcs_math)
		importlib.reload(funcs_tri)
		importlib.reload(proj_data)
		importlib.reload(bound)
		importlib.reload(partition_grid)
		importlib.reload(uv_project)
		importlib.reload(project)
		importlib.reload(mesh_mirror_script)
		importlib.reload(align_to_view)
		importlib.reload(plane)
		importlib.reload(axis_align)
	except:
		print('Error:', sys.exc_info())
#end force_reload()
def reload():
	#Script reloading
	if "bpy" in locals():
		force_reload()
	#Script loading
	else:
		try:
			from . import funcs_blender, funcs_math, funcs_tri, proj_data, bound, partition_grid, uv_project, project, mesh_mirror_script, align_to_view, plane, axis_align
		except:
			print('Error:', sys.exc_info())
#end reload()
reload()


try:
	import bpy
	from .uv_project import UVProjectMesh
	from .project import ProjectMesh
	from .mesh_mirror_script import MirrorMesh
	from .align_to_view import AlignSelection
except:
	print('Error:', sys.exc_info())



# Register the operator
def register():
	pass
	bpy.utils.register_class(UVProjectMesh)
	bpy.utils.register_class(ProjectMesh)
	bpy.utils.register_class(MirrorMesh)
	bpy.utils.register_class(AlignSelection)

def unregister():
	pass
	bpy.utils.unregister_class(UVProjectMesh)
	bpy.utils.unregister_class(ProjectMesh)
	bpy.utils.unregister_class(MirrorMesh)
	bpy.utils.unregister_class(AlignSelection)



if __name__ == "__main__":
	register()
