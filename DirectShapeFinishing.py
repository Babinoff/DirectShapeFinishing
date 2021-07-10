# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек----------------------
import clr
from random import randint
# import random
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")
sys.path.append("C:\\git\\DirectShapeFinishing")

clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIIFC')
clr.AddReference("RevitNodes")
clr.AddReference("RevitServices")
clr.AddReference('ProtoGeometry')

# import DirectShapeFunctions
from DirectShapeFunctions import main_face_filter, TimeCounter, wall_profil
from DirectShapeFunctions import boundary_filter, dublicate_separate_filter
from DirectShapeFunctions import create_material, is_not_curtain_modelline, main_wall_by_id_work
from DirectShapeFunctions import get_wall_cut, get_wall_p_curve, get_wall_profil, get_wall_ds_type_material, get_wall_type_name, get_type_if_null_id

# from Autodesk.DesignScript.Geometry import Curve as DesignScript_Curve
# from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# import RevitServices
import Revit
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
from Autodesk.Revit.DB import UV
from Autodesk.Revit.DB import SolidOptions, SubfaceType, Transform, XYZ
from Autodesk.Revit.DB import BuiltInParameter, DisplayUnitType, ElementId, UnitUtils
from Autodesk.Revit.DB import SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementBoundarySubface, SpatialElementGeometryCalculator
# from System.Collections.Generic import List
# from clr import StrongBox
# -----------------------Импоорт библиотек----------------------


# -----------------------АПИ параметры----------------------
current_doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
version = app.VersionNumber
options = SpatialElementBoundaryOptions()
options.StoreFreeBoundaryFaces = True
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
calculator = SpatialElementGeometryCalculator(current_doc, options)
trnsf = Transform.CreateTranslation(XYZ(0, 0, 100))
s_options = SolidOptions(ElementId(-1), ElementId(-1))
# -----------------------АПИ параметры----------------------


# -----------------------Рабочие параметры----------------------

rooms = UnwrapElement(IN[0])  # noqa
link_doc = UnwrapElement(IN[1])  # noqa
room_height_enable = IN[2]  # noqa
custom_hight = IN[3]  # noqa
transform_Z_enable = IN[4]  # noqa
move_z_value = IN[5]  # noqa
wall_type_names_to_exclude = IN[6]  # noqa
surf_by_room = []
element_by_room = []
full_id_list = []
curtain_list = []
insertslist = []
surface_in_room = []
surface_list_all = []
surf_from_bound_curvs = []
boundarylist = []
blist = []
# x = 0
# test3 = []
boundary_ds_type_by_room = []
boundary_by_room_level = []
r_f_list = []
wall_type_mat_names_all = []

test_room_faces = []

id_minus_one = ElementId(-1)

# move_z = IN[5]*0.00328084 # noqa
move_z = UnitUtils.ConvertToInternalUnits(move_z_value, DisplayUnitType.DUT_MILLIMETERS)  # noqa
transform_Z = Transform.CreateTranslation(XYZ(0, 0, move_z))

TransactionManager.Instance.EnsureInTransaction(current_doc)
ds_type = "Finishing_BASE"
create_material(current_doc, ds_type)
# @@@-----------------------Room params----------------------
timer_rooms = TimeCounter()
for room in rooms:
	test_faces = []
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	if room_volume > 0:
		surface_in_room = []
		room_height = room_volume / room_area * 304.8
		room_level = current_doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID).AsElementId())
		sp_geom_results = calculator.CalculateSpatialElementGeometry(room)
		roomSolid = sp_geom_results.GetGeometry()
		# r_f = RoomFinishing(current_doc, link_doc, room)
		# r_f.boundary_surf = sp_geom_results.GetGeometry().Faces
		inserts_by_wall = []
		by_face_list = []
		wall_type_mat_names = []
		for face in sp_geom_results.GetGeometry().Faces:
			ds_type = "Finishing_BASE"
			bface = sp_geom_results.GetBoundaryFaceInfo(face)[0]
			if str(bface.SubfaceType) is str(SubfaceType.Side) and dublicate_separate_filter(by_face_list, face):
				sbe_id = bface.SpatialBoundaryElement
				host_id = sbe_id.HostElementId
				link_id = sbe_id.LinkedElementId
				link_inst_id = sbe_id.LinkInstanceId
				if host_id == id_minus_one and link_id == id_minus_one:
					by_face_list.append(face)
					wall_type_mat_names.append(ds_type)
				else:
					b_element, inserts_by_wall = main_face_filter(host_id, link_id, current_doc, link_doc, face, wall_type_names_to_exclude)
					if b_element:
						ds_type = get_wall_ds_type_material(current_doc, b_element, room)
						# by_face_list.append(face)
						wall_type_mat_names.append(ds_type)
						new_bs = face.ToProtoType()[0]
						for ins in inserts_by_wall:
							if ins and new_bs.DoesIntersect(ins):
								new_bs = new_bs.SubtractFrom(ins)[0]
						surface_in_room.append(new_bs)
				# elif host_id == id_minus_one and link_id == id_minus_one:
				# 	by_face_list.append(face)
				# 	wall_type_mat_names.append(ds_type)
					test_faces.append((host_id, link_id, b_element, inserts_by_wall))
		# for bs in by_face_list:
		# 	new_bs = bs.ToProtoType()[0]
		# 	for ins in inserts_by_wall:
		# 		if ins and new_bs.DoesIntersect(ins):
		# 			new_bs = new_bs.SubtractFrom(ins)[0]
							# try:
									# -------------------ВЫРЕЗАЕТ ИЗ ПЛОСКОСТИ СТЕНЫ ЕСЛИ ДВЕРЬ ПРИМЫКАЕТ К НЕЙ ТОРЦОМ, ИСПРАВИТЬ -------------------
									# -------------------нужен метот для получения плоскости стены с изминёным профилем -------------------
									# new_bs = new_bs.SubtractFrom(ins)[0]
						# except:
						# 		pass
			# surface_in_room.append(new_bs)
		surface_list_all.append(surface_in_room)
		# boundary_ds_type_by_room.append(r_f.boundary_ds_type)
		# boundary_by_room_level.append(r_f.boundary_level)
		test_room_faces.append(test_faces)
		# r_f_list.append(r_f)
		wall_type_mat_names_all.append(wall_type_mat_names)
time_rooms = timer_rooms.stop()
# , boundary_ds_type_by_room, test_room_faces

TransactionManager.Instance.ForceCloseTransaction()

OUT = time_rooms, surface_list_all, wall_type_mat_names_all#, test_room_faces
