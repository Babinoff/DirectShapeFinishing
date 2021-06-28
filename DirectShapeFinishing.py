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
# from Revit.Elements import Elements


clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

# clr.AddReference('ProtoGeometry')
# from Autodesk.DesignScript.Geometry import *

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from Autodesk.DesignScript.Geometry import Curve as DSCurve

from .DirectShapeFunctions import get_wall_cut, get_wall_p_curve, get_wall_profil, get_wall_type_material
from .DirectShapeFunctions import create_material, is_not_curtain, main_wall_by_id_work
# -----------------------Импоорт библиотек----------------------


# -----------------------Класс для хранения информации----------------------
class RoomFinishing():
	"""Main roomfinishing class for information collect."""

	separator_list = []
	by_face_list = []
	inserts = []
	curve_from_boundary_list = []
	elem_list = []
	inserts_by_wall = []
	boundary_surf = []
	boundary_curvs = []
	boundary_type = []
	boundary_level = []

	def __init__(self, doc, link_doc, room):
		"""Main parameters for room finishing construction."""
		self.doc = doc
		self.link_doc = link_doc
		self.room = room
# -----------------------Класс для хранения информации----------------------


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
wall_type_names_to_exclude = IN[6] # noqa
link_doc = UnwrapElement(IN[1]) # noqa
size_param = 1000
# incopenings, incshadows, incwalls, incshared = True, False, True, True
rooms = UnwrapElement(IN[0]) # noqa
custom_hight = IN[3] # noqa
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
x = 0
test3 = []
boundary_type_by_room = []
boundary_by_room_level = []

# move_z = IN[5]*0.00328084 # noqa
move_z = UnitUtils.ConvertToInternalUnits(IN[5], DisplayUnitType.DUT_MILLIMETERS) # noqa
transform_Z = Transform.CreateTranslation(XYZ(0, 0, move_z))

# @@@-----------------------Room params----------------------
for room in rooms:
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	room_height = room_volume / room_area * 304.8
	room_level = doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID).AsElementId())

	r_f = RoomFinishing(doc, link_doc, room)
	# separator_list = []
	# by_face_list = []
	# inserts = []
	# curve_from_boundary_list = []
	# elem_list = []
	results = calculator.CalculateSpatialElementGeometry(room)
	# roomSolid = results.GetGeometry()
	# inserts_by_wall = []
	# boundary_surf = []
	# boundary_curvs = []
	# boundary_type = []
	# boundary_level = []

# @@@-----------------------Боундари Элементс----------------------
	for boundarylist in room.GetBoundarySegments(options):
		b_s = []
		b_element1 = None
		b_element2 = None
		for i, boundary in enumerate(boundarylist):
			crv = None
			wall_hight = room_height
			if str(boundary.ElementId) == "-1" and str(boundary.LinkElementId) == "-1":
				pass
				# crv = boundary.GetCurve()
				# try:
				# 	type = get_wall_type_material_and_select_material_for_ds(doc, boundary, room)
				# except:
				# 	type = "АБН_Отделка стен"
				# if i + 1 < len(boundarylist):
				# 	try:
				# 		type = get_wall_type_material_and_select_material_for_ds(doc, doc.GetElement(boundarylist[i + 1].ElementId), room)
				# 	except:
				# 		type = "АБН_Отделка стен"
				# 		"""
				# 		try:
				# 			type = get_wall_type_material_and_select_material_for_ds(doc,doc.GetElement(boundarylist[i-1].ElementId),room)
				# 		except:
				# 			type = "АБН_Отделка стен"
				# 		"""
				# elif i - 1 >= 0:
				# 	try:
				# 		type = get_wall_type_material_and_select_material_for_ds(doc, doc.GetElement(boundarylist[i - 1].ElementId), room)
				# 	except:
				# 		type = "АБН_Отделка стен"
				# 		"""try:
				# 			type = get_wall_type_material_and_select_material_for_ds(doc,doc.GetElement(boundarylist[i+1].ElementId),room)
				# 		except:
				# 		type = "where is my type dude2"""
				# else:
				# 	type = "where is my type dude3"
			elif str(boundary.ElementId) is not "-1":
				b_element1 = doc.GetElement(boundary.ElementId)
				if b_element1.GetType().Name == "ModelLine":
					r_f.separator_list.append(boundary.GetCurve())  # !!!!!!!!!!!!!!!!boundary.GetCurve() вместо поиска геометрии у элементов!!!!!!!!!!
				elif b_element1.GetType().Name == "Wall" and b_element1.WallType.Kind == WallKind.Curtain:
					r_f.separator_list.append(boundary.GetCurve())
# ---------------Убираем тип стены из расчёта -----------------------------------------------------------------------------------
				elif b_element1.GetType().Name == "Wall" and doc.GetElement(b_element1.GetTypeId()).get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Ограждение МХМТС":
					pass
# -------------------------------------------------------------------------------------------------------------------------------------------
				elif b_element1.GetType().Name == "Wall":
					wall_box = b_element1.get_BoundingBox(doc.ActiveView)
					wall_hight = (wall_box.Max.Z - wall_box.Min.Z) * 304.8
					type = get_wall_type_material(doc, b_element1, room)
					crv = boundary.GetCurve()
				else:
					try:
						type = get_wall_type_material(doc, b_element1, room)
					except:
						type = "АБН_Отделка стен"
					crv = boundary.GetCurve()
			elif str(boundary.LinkElementId) is not "-1":
				b_element2 = link_doc.GetElement(boundary.LinkElementId)
				if b_element2.GetType().Name == "ModelLine":
					r_f.separator_list.append(boundary.GetCurve())
				elif b_element2.GetType().Name == "Wall" and b_element2.WallType.Kind == WallKind.Curtain:
					r_f.separator_list.append(boundary.GetCurve())
			r_f.boundary_level.append(room_level)
# ------------------------------------------------------Включаем расчет по высоте стен--------------------------------------------------
			if crv is not None and IN[4]: # noqa
				crv = crv.CreateTransformed(transform_Z).ToProtoType()
			elif crv is not None:
				crv = crv.ToProtoType()
			if IN[2]: # noqa
				if crv is not None:
					if wall_hight > room_height:
						r_f.boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), room_height))
					else:
						r_f.boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), wall_hight))
					r_f.boundary_type.append(type)
			else:
				if crv is not None:
					r_f.boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), custom_hight))
					r_f.boundary_type.append(type)

# @@@-----------------------Боундари Фэйс----------------------
	for face in results.GetGeometry().Faces:
		inserts_by_wall = []
		for bface in results.GetBoundaryFaceInfo(face):
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
				if str(host_id) is not "-1" and is_not_curtain(host_id, doc):
					r_f.by_face_list.append(face)  # -------------Cобираем плоскость
					by_face_h = face
					main_wall_by_id_work(host_id, doc, by_face_h)
					r_f.inserts.extend(inserts_by_wall)
				else:
					link_id = bface.SpatialBoundaryElement.LinkedElementId
					if str(link_id) is not "-1" and is_not_curtain(link_id, link_doc):
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
							elif bface.SubfaceArisesFromElementFace:  # ------Убираем плоскости витражей
								pass
							else:
								r_f.by_face_list.append(face)  # ------Cобираем торцевые плоскости
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
	boundary_type_by_room.append(r_f.boundary_type)
	boundary_by_room_level.append(r_f.boundary_level)

OUT = surface_list_all, boundary_type_by_room, boundary_by_room_level, r_f.separator_list
