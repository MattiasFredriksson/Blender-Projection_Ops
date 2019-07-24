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
	'warning': "",
	'description': "4 Operators containing functionality for mirroring and projection mesh objects over/onto a mesh surface",
	'wiki_url': "",
	'tracker_url': "",
	'category': 'Mesh'}

import sys, bpy, traceback, glob, importlib
from os.path import dirname, basename, isfile, join, split

# Goble package module files
directory = dirname(__file__)
package = split(directory)[-1]
modules = glob.glob(join(directory, '*.py'))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

############
# Script functions
############
def force_reload():
	try:
		for mod_name in __all__:
			mod = importlib.import_module(package + '.' + mod_name)
			importlib.reload(mod)
	except:
		print('Reloading all package modules failed with error:')
		traceback.print_exc()
#end force_reload()
def load_modules():
	for mod_name in __all__:
		mod = importlib.import_module(package + '.' + mod_name)
#end load_modules()
def to_op_id(obj):
	"""
	Convert a suitable object to an operator id string.
	"""
	if not isinstance(obj, str):
		return obj.bl_idname
	# elif: string
	return obj
#end op_id()
def op_exist(op_id):
	"""
	Verify if an operator has been registered in 'bpy.ops'.
	----
	Params:
	op_id:		Operator to check for or a string used to identify it (relevant
				string id is defined in the operator's 'bl_idname' attribute).
	----
	Return: 	'True' if an operator with the id is registered, 'False' if no operator with the id exist.
	"""
	op_id = to_op_id(op_id)
	op_type, delim, op_name = op_id.rpartition('.')
	# There is no operator 'type' specified
	if op_type is '':
		return op_name in dir(bpy.ops)
	return op_name in dir(getattr(bpy.ops, op_type))
#end op_exist()
def get_op(op_id):
	"""
	Find the registered operator class with the bl_idname.
	There must! exist some better way of doing this directly converting the bl_idname....
	"""
	op_id = to_op_id(op_id)
	# Search through all bpy.types and math the bl_idname
	for type_str in dir(bpy.types):
		try:
			# May or may not be RNAMeta type
			RNAMeta = getattr(bpy.types, type_str)
			if RNAMeta.bl_idname == op_id:
				return RNAMeta
		except:
			pass
	return None
#end get_op()

#######################
# Import Package
#######################
if "bpy" in locals():
	force_reload() # Reload modules if necessary
load_modules()

#######################
# Register Package
#######################

# List of operator classes in the package
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
		if op_exist(op.bl_idname):
			reg_op = get_op(op.bl_idname)
			bpy.utils.unregister_class(reg_op)
	#efor
#end unregister()
if __name__ == "__main__":
	register()
