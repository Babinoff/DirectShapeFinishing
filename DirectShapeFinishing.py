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
from DirectShapeFunctions import RoomFinishing, TimeCounter, wall_profil
from DirectShapeFunctions import boundary_filter, dublicate_separate_filter
from DirectShapeFunctions import create_material, is_not_curtain_modelline, main_wall_by_id_work
from DirectShapeFunctions import get_wall_cut, get_wall_p_curve, get_wall_profil, get_wall_ds_type_material, get_wall_type_name, get_type_if_null_id
# from DirectShapeFinishing import main_face_filter

from Autodesk.DesignScript.Geometry import Curve as DesignScript_Curve
from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# import RevitServices
import Revit
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)
from Autodesk.Revit.DB.IFC import ExporterIFCUtils
from Autodesk.Revit.DB import UV
from Autodesk.Revit.DB import Curve, CurveLoop, GeometryCreationUtilities, Line, SolidOptions, SubfaceType, Transform, XYZ
from Autodesk.Revit.DB import BuiltInParameter, Color, DisplayUnitType, ElementId, Material, SetComparisonResult, UnitUtils, WallKind
from Autodesk.Revit.DB import SpatialElement, SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementBoundarySubface, SpatialElementGeometryCalculator
# import Autodesk
from System.Collections.Generic import List
from System import Byte, Type
# import System
from clr import StrongBox
import clr
# from random import randint
# import random
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")
sys.path.append("C:\\git\\DirectShapeFinishing")


clr.AddReference('System')

clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIIFC')

clr.AddReference("RevitNodes")
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")

clr.AddReference('ProtoGeometry')

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

# @@@-----------------------Room params----------------------
timer_rooms = TimeCounter()
for room in rooms:
	test_faces = []
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	if room_volume > 0:
		room_height = room_volume / room_area * 304.8
		room_level = current_doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID).AsElementId())
		sp_geom_results = calculator.CalculateSpatialElementGeometry(room)
		roomSolid = sp_geom_results.GetGeometry()
		r_f = RoomFinishing(current_doc, link_doc, room)
		r_f.boundary_surf = sp_geom_results.GetGeometry().Faces
		inserts = []
		by_face_list = []
		wall_type_mat_names = []
		ds_type = "Finishing_BASE"
		create_material(current_doc, ds_type)
# @@@-----------------------Боундари Элементс----------------------
		# for boundarylist in room.GetBoundarySegments(options):
		# 	b_s = []
		# 	b_element1 = None
		# 	b_element2 = None
		# 	ds_type = "Finishing_BASE"
		# 	for index, boundary in enumerate(boundarylist):
		# 		crv = None
		# 		wall_hight = room_height
		# 		if str(boundary.ElementId) == "-1" and str(boundary.LinkElementId) == "-1":
		# 			get_type_if_null_id(current_doc, boundary, room, boundarylist, index)
		# 		elif str(boundary.ElementId) is not "-1":
		# 			b_element1 = current_doc.GetElement(boundary.ElementId)
		# 			boundary_filter(current_doc, b_element1, boundary, room, r_f)
		# 		elif str(boundary.LinkElementId) is not "-1":
		# 			b_element2 = link_doc.GetElement(boundary.LinkElementId)
		# 			boundary_filter(current_doc, b_element2, boundary, room, r_f)
		# 		r_f.boundary_level.append(room_level)
		# 		# ----------------Включаем расчет по высоте стен--------------------------------------------------
		# 		if crv is not None and transform_Z_enable: # noqa
		# 			crv = crv.CreateTransformed(transform_Z).ToProtoType()
		# 		elif crv is not None:
		# 			crv = crv.ToProtoType()
		# 		if room_height_enable: # noqa
		# 			if crv is not None:
		# 				if wall_hight > room_height:
		# 					r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), room_height))
		# 				else:
		# 					r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), wall_hight))
		# 				r_f.boundary_ds_type.append(ds_type)
		# 		else:
		# 			if crv is not None:
		# 				r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), custom_hight))
		# 				r_f.boundary_ds_type.append(ds_type)
# @@@-----------------------Боундари Фэйс----------------------
		for face in sp_geom_results.GetGeometry().Faces:
			inserts_by_wall = []
			# test_faces.append(face.ToProtoType())
			# for bface in sp_geom_results.GetBoundaryFaceInfo(face):
			bface = sp_geom_results.GetBoundaryFaceInfo(face)[0]
			# test_faces.append(bface)
			# test_list_dubl = []
			# test_list_separate = []
			link_id = 0
			# by_face_h = False
			# by_face_l = False
			# test_faces.append((bface.SubfaceType, SubfaceType.Side, str(bface.SubfaceType) is str(SubfaceType.Side)))
			if str(bface.SubfaceType) is str(SubfaceType.Side):
				sbe_id = bface.SpatialBoundaryElement
				host_id = sbe_id.HostElementId
				link_id = sbe_id.LinkedElementId
				link_inst_id = sbe_id.LinkInstanceId
				if main_face_filter(host_id, link_id, current_doc, link_doc):
					test_faces.append((dublicate_separate_filter(by_face_list, face), face.ToProtoType(
					), (host_id.IntegerValue == -1 and link_id.IntegerValue == -1), host_id, link_id, link_inst_id))
					if dublicate_separate_filter(by_face_list, face):
						b_element = current_doc.GetElement(host_id)
						if b_element:
								ds_type = get_wall_ds_type_material(current_doc, b_element, room)
						# full_id_list.append((host_id.ToString(), face.Evaluate(UV(0.5, 0.5)), by_face_list))
						by_face_list.append(face)
						wall_type_mat_names.append(ds_type)
						# r_f.by_face_list.append(face.ToProtoType()[0])  # -------------Cобираем плоскость
						inserts_by_wall = main_wall_by_id_work(host_id, current_doc, face, wall_type_names_to_exclude)
					elif host_id == id_minus_one and link_id == id_minus_one:
						if dublicate_separate_filter(by_face_list, face):
							by_face_list.append(face)
							wall_type_mat_names.append(ds_type)
									# else:
									# 	if dublicate_separate_filter(by_face_list, face):
									# 			by_face_list.append(face)
									# 			wall_type_mat_names.append(ds_type)
									# 			test_faces.extend((bface.SubfaceType, SubfaceType.Side, str(bface.SubfaceType) is str(SubfaceType.Side)))

				# insertslist.append(r_f.inserts)
		surface_in_room = []
		for bs in by_face_list:
			new_bs = bs.ToProtoType()[0]
			for ins in inserts:
				if ins and new_bs.DoesIntersect(ins):
						try:
								# -------------------ВЫРЕЗАЕТ ИЗ ПЛОСКОСТИ СТЕНЫ ЕСЛИ ДВЕРЬ ПРИМЫКАЕТ К НЕЙ ТОРЦОМ, ИСПРАВИТЬ -------------------
								# -------------------нужен метот для получения плоскости стены с изминёным профилем -------------------
								new_bs = new_bs.SubtractFrom(ins)[0]
						except:
								pass
			surface_in_room.append(new_bs)
		surface_list_all.append(surface_in_room)
		boundary_ds_type_by_room.append(r_f.boundary_ds_type)
		boundary_by_room_level.append(r_f.boundary_level)
		test_room_faces.append(test_faces)
		r_f_list.append(r_f)
		wall_type_mat_names_all.append(wall_type_mat_names)
time_rooms = timer_rooms.stop()
# , boundary_ds_type_by_room, test_room_faces

TransactionManager.Instance.ForceCloseTransaction()

OUT = time_rooms, surface_list_all, wall_type_mat_names_all
