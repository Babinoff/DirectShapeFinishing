# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек----------------------
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")
sys.path.append("C:\\git\\DirectShapeFinishing")

import random
from random import randint

import clr
from clr import StrongBox

import System
from System import Byte, Type
clr.AddReference('System')
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import SpatialElement, SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementBoundarySubface, SpatialElementGeometryCalculator
from Autodesk.Revit.DB import BuiltInParameter, Color, DisplayUnitType, ElementId, Material, SetComparisonResult, UnitUtils, WallKind
from Autodesk.Revit.DB import Curve, CurveLoop, GeometryCreationUtilities, Line, SolidOptions, SubfaceType, Transform, XYZ
clr.AddReference('RevitAPIIFC')
from Autodesk.Revit.DB.IFC import ExporterIFCUtils

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from Autodesk.DesignScript.Geometry import Curve as DesignScript_Curve

import DirectShapeFunctions
from DirectShapeFunctions import get_wall_cut, get_wall_p_curve, get_wall_profil, get_wall_ds_type_material, get_wall_type_name, get_type_if_null_id
from DirectShapeFunctions import create_material, is_not_curtain_modelline, main_wall_by_id_work
from DirectShapeFunctions import boundary_filter, dublicate_separate_filter
from DirectShapeFunctions import RoomFinishing, TimeCounter
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

rooms = UnwrapElement(IN[0]) # noqa
link_doc = UnwrapElement(IN[1]) # noqa
room_height_enable = IN[2] # noqa
custom_hight = IN[3] # noqa
transform_Z_enable = IN[4] # noqa
move_z_value = IN[5] # noqa
wall_type_names_to_exclude = IN[6] # noqa
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


test_room_faces = []

# move_z = IN[5]*0.00328084 # noqa
move_z = UnitUtils.ConvertToInternalUnits(move_z_value, DisplayUnitType.DUT_MILLIMETERS) # noqa
transform_Z = Transform.CreateTranslation(XYZ(0, 0, move_z))

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
	# @@@-----------------------Боундари Элементс----------------------
		for boundarylist in room.GetBoundarySegments(options):
			b_s = []
			b_element1 = None
			b_element2 = None
			ds_type = "Finishing_BASE"
			for index, boundary in enumerate(boundarylist):
				crv = None
				wall_hight = room_height
				if str(boundary.ElementId) == "-1" and str(boundary.LinkElementId) == "-1":
					get_type_if_null_id(current_doc, boundary, room, boundarylist, index)
				elif str(boundary.ElementId) is not "-1":
					b_element1 = current_doc.GetElement(boundary.ElementId)
					boundary_filter(current_doc, b_element1, boundary, room, r_f)
				elif str(boundary.LinkElementId) is not "-1":
					b_element2 = link_doc.GetElement(boundary.LinkElementId)
					boundary_filter(current_doc, b_element2, boundary, room, r_f)
				r_f.boundary_level.append(room_level)
				# ----------------Включаем расчет по высоте стен--------------------------------------------------
				if crv is not None and transform_Z_enable: # noqa
					crv = crv.CreateTransformed(transform_Z).ToProtoType()
				elif crv is not None:
					crv = crv.ToProtoType()
				if room_height_enable: # noqa
					if crv is not None:
						if wall_hight > room_height:
							r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), room_height))
						else:
							r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), wall_hight))
						r_f.boundary_ds_type.append(ds_type)
				else:
					if crv is not None:
						r_f.boundary_surf.append(DesignScript_Curve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), custom_hight))
						r_f.boundary_ds_type.append(ds_type)
	# @@@-----------------------Боундари Фэйс----------------------
		for face in sp_geom_results.GetGeometry().Faces:
			inserts_by_wall = []
			# test_faces.append(face.ToProtoType())
			for bface in sp_geom_results.GetBoundaryFaceInfo(face):
				# test_faces.append(bface)
				inserts_by_wall = []
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
					test_faces.append((face.ToProtoType(), (host_id.IntegerValue == -1 and link_id.IntegerValue == -1), host_id, link_id, link_inst_id))
					# r_f.by_face_list.append(face.ToProtoType()[0])
					if host_id.IntegerValue == -1 and link_id.IntegerValue == -1:
						# if dublicate_separate_filter(r_f, face):
						r_f.by_face_list.append(face.ToProtoType()[0])
					elif str(host_id) is not "-1" and is_not_curtain_modelline(host_id, current_doc):
						# if dublicate_separate_filter(r_f, face):
							full_id_list.append(host_id)
							r_f.by_face_list.append(face.ToProtoType()[0])  # -------------Cобираем плоскость
							inserts_by_wall = main_wall_by_id_work(host_id, current_doc, face, wall_type_names_to_exclude)
							r_f.inserts.extend(inserts_by_wall)
					elif str(link_id) is not "-1" and is_not_curtain_modelline(link_id, link_doc):
						# if dublicate_separate_filter(r_f, face):
							full_id_list.append(link_id)
							r_f.by_face_list.append(face.ToProtoType()[0])  # ---------Cобираем плоскость
							inserts_by_wall = main_wall_by_id_work(link_id, link_doc, face, wall_type_names_to_exclude)
							r_f.inserts.extend(inserts_by_wall)
					else:
						# if dublicate_separate_filter(r_f, face):
							r_f.by_face_list.append(face.ToProtoType()[0])

		insertslist.append(r_f.inserts)
		surface_in_room = []
		for bs in r_f.by_face_list:
			new_bs = bs
			for ins in r_f.inserts:
				if ins and bs.DoesIntersect(ins):
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
time_rooms = timer_rooms.stop()
OUT = time_rooms, surface_list_all, boundary_ds_type_by_room,  # test_room_faces,  # [r_f.by_face_list for r_f in r_f_list]
