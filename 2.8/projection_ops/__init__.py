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

import sys, bpy, traceback
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
		print('Reloading all package modules failed with error:')
		traceback.print_exc()
#end force_reload()

#Script reloading
if "bpy" in locals():
	force_reload()

from . import funcs_blender, funcs_math, funcs_tri, proj_data, bound, partition_grid, uv_project, project, mesh_mirror_script, align_to_view, plane, axis_align



operators = [uv_project.UVProjectMesh, project.ProjectMesh, mesh_mirror_script.MirrorMesh, align_to_view.AlignSelection]

# Register the operator
def register():
	for op in operators:
		bpy.utils.register_class(op)
#end register()
def unregister():
	# Try to unregister all operators
	for op in operators:
		# Only thing left to test
		if hasattr(bpy.types, op.bl_idname):
			bpy.utils.unregister_class(op)
	#efor
#end unregister()


if __name__ == "__main__":
	register()
