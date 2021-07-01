# -*- coding: utf-8 -*-

# -----------------------Импоорт библиотек----------------------
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")

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
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает00 без
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from Autodesk.DesignScript.Geometry import Curve as DesignScript_Curve

from .DirectShapeFunctions import get_wall_cut, get_wall_p_curve, get_wall_profil, get_wall_ds_type_material, get_wall_type_name, get_type_if_null_id
from .DirectShapeFunctions import create_material, is_not_curtain_modelline, main_wall_by_id_work
from .DirectShapeFunctions import boundary_filter
from .DirectShapeFunctions import RoomFinishing, TimeCounter
# -----------------------Импоорт библиотек----------------------


# -----------------------АПИ параметры----------------------
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
version = app.VersionNumber
options = SpatialElementBoundaryOptions()
options.StoreFreeBoundaryFaces = True
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
calculator = SpatialElementGeometryCalculator(doc, options)
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

# move_z = IN[5]*0.00328084 # noqa
move_z = UnitUtils.ConvertToInternalUnits(move_z_value, DisplayUnitType.DUT_MILLIMETERS) # noqa
transform_Z = Transform.CreateTranslation(XYZ(0, 0, move_z))

# @@@-----------------------Room params----------------------
rooms_timer = TimeCounter()
for room in rooms:
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	room_height = room_volume / room_area * 304.8
	room_level = doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID).AsElementId())
	sp_geom_results = calculator.CalculateSpatialElementGeometry(room)
	roomSolid = sp_geom_results.GetGeometry()
	r_f = RoomFinishing(doc, link_doc, room)
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
				get_type_if_null_id(doc, boundary, room, boundarylist, index)
			elif str(boundary.ElementId) is not "-1":
				b_element1 = doc.GetElement(boundary.ElementId)
				boundary_filter(b_element1, boundary, room)
			elif str(boundary.LinkElementId) is not "-1":
				b_element2 = link_doc.GetElement(boundary.LinkElementId)
				boundary_filter(b_element2, boundary, room)
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
		for bface in sp_geom_results.GetBoundaryFaceInfo(face):
			inserts_by_wall = []
			test_list = []
			test_list2 = []
			link_id = 0
			by_face_h = False
			by_face_l = False
			if bface.SubfaceType is not SubfaceType.Side:
				pass
			else:
				host_id = bface.SpatialBoundaryElement.HostElementId
				if str(host_id) is not "-1" and is_not_curtain_modelline(host_id, doc):
					r_f.by_face_list.append(face)  # -------------Cобираем плоскость
					by_face_h = face
					main_wall_by_id_work(host_id, doc, by_face_h, wall_type_names_to_exclude)
					r_f.inserts.extend(inserts_by_wall)
				else:
					link_id = bface.SpatialBoundaryElement.LinkedElementId
					if str(link_id) is not "-1" and is_not_curtain_modelline(link_id, link_doc):
						r_f.by_face_list.append(face)  # ---------Cобираем плоскость
						by_face_l = face
						r_f.inserts.extend(inserts_by_wall)
					else:
						# @@@-----------------------Тут убираем дубликаты плоскостей----------------------
						for b_f in r_f.by_face_list:
							if face.Equals(b_f):
								test_list.append(True)
							else:
								test_list.append(False)
						if any(test_list):
							pass
						else:
							# @@@-----------------------Тут убираем разделители----------------------
							for s_l in r_f.separator_list:
								if str(face.Intersect(s_l)) == "Disjoint":
									test_list2.append(False)
								else:
									test_list2.append(True)
							if any(test_list2):
								pass
							elif bface.SubfaceArisesFromElementFace:  # <------Убираем плоскости витражей
								pass
							else:
								r_f.by_face_list.append(face)  # <------Cобираем торцевые плоскости
								by_face = face
								r_f.inserts.extend(inserts_by_wall)
	insertslist.append(r_f.inserts)
	surface_in_room = []
	for bs in r_f.boundary_surf:
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
rooms_time = rooms_timer.stop()
OUT = surface_list_all, boundary_ds_type_by_room, boundary_by_room_level, r_f.separator_list
