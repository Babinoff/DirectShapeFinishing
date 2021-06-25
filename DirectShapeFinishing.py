# -*- coding: utf-8 -*-

#  -----------------------Импоорт библиотек----------------------
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
# -----------------------Импоорт библиотек----------------------


wall_type_names_to_exclude = IN[5] # noqa


# -----------------------Функции----------------------
def main_wall_by_id_work(_id, _doc, _face):
	"""Choosing wall destiny by ID."""
	full_id_list.append(_id)
	b_element = _doc.GetElement(_id)
	if b_element.GetType().Name == "Wall":
		wall_type = _doc.GetElement(b_element.GetTypeId())
		type_name = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if type_name in wall_type_names_to_exclude:
			pass
		elif wall_type.Kind == WallKind.Curtain:
			curtain_list.append(b_element)
		else:
			inserts_list = b_element.FindInserts(incopenings, incshadows, incwalls, incshared)
			if not inserts_list:
				pass
			else:
				for insert in inserts_list:
					if _doc.GetElement(insert).GetType().Name == "Opening":
						pass
					else:
						item = _doc.GetElement(insert)
						x = None
						if item.GetType().Name == "FamilyInstance":
							x = get_wall_cut(item, b_element, _face)
						elif item.GetType().Name == "Wall":
							x = get_wall_profil(item, b_element, _face)
						else:
							x = BoundingBox.ToCuboid(item.get_BoundingBox(doc.ActiveView).ToProtoType())
						inserts_by_wall.append(x)
	else:
		pass


def is_not_curtain(_id, _doc):
	"""Wall is curtain test."""
	wall = _doc.GetElement(_id)
	if wall.GetType().Name == "Wall":
		if wall.WallType.Kind == WallKind.Curtain:
			return False
		else:
			return True
	else:
		return True


def get_wall_cut(fi, wall, _face):
	"""Get wall cunt."""
	doc = fi.Document
	current_dir = StrongBox[XYZ](wall.Orientation)
	try:
		curve_loop1 = ExporterIFCUtils.GetInstanceCutoutFromWall(doc, wall, fi, current_dir)
		multpl = wall.Width
		w_vector = wall.Orientation
		f_vector = fi.FacingOrientation
		for c in curve_loop1:
			test_curv = c
		if _face.Intersect(test_curv) == SetComparisonResult.Subset:
			move = Transform.CreateTranslation(w_vector.Multiply(multpl))
			extr_vector = -w_vector
		else:
			if w_vector.IsAlmostEqualTo(f_vector):
				move = Transform.CreateTranslation(XYZ(0, 0, 0))
				extr_vector = w_vector
			else:
				move = Transform.CreateTranslation(XYZ(0, 0, 0))
				extr_vector = f_vector
		curv_move = [cl.CreateTransformed(move) for cl in curve_loop1]
		curve_loop2 = CurveLoop()
		for cm in curv_move:
			curve_loop2.Append(cm)
		icurve_loop = List[CurveLoop]([curve_loop2])
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(icurve_loop, extr_vector, wall.Width * 2).ToProtoType()
		return geom
	except:
		geom = BoundingBox.ToCuboid(fi.get_BoundingBox(doc.ActiveView).ToProtoType())
		return geom


def get_wall_profil(insert_wall, host_wall, _face):
	u"""Get wall Profil. Расположение точек в линиях должно быть последовательным для курвелооп."""
	g_curve_list = get_wall_p_curve(insert_wall)
	if g_curve_list is not None:
		icurve = List[Autodesk.Revit.DB.Curve](g_curve_list)
		i_crv_loop = CurveLoop.Create(icurve)
		i_list_crv_loop = List[CurveLoop]([i_crv_loop])
		wh_vector = host_wall.Orientation
		# iw_vector = insert_wall.Orientation
		f_vector = face.FaceNormal
		if wh_vector.IsAlmostEqualTo(f_vector):
			extr_vector = insert_wall.Orientation
		else:
			extr_vector = host_wall.Orientation
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(i_list_crv_loop, extr_vector, host_wall.Width).ToProtoType()
		return geom


def get_wall_p_curve(u_wall):
	u"""Create lines for policurve."""
	if u_wall.GetType().Name == "Wall":
		loc = u_wall.Location
		crv = loc.Curve
		bo = u_wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
		wh = u_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
		move_bo = Transform.CreateTranslation(XYZ(0, 0, bo))
		move_wh = Transform.CreateTranslation(XYZ(0, 0, wh))
		crv1 = crv.CreateTransformed(move_bo)
		crv2 = crv1.CreateTransformed(move_wh)

		crv11 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(0), crv2.GetEndPoint(0))
		crv22 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(0), crv2.GetEndPoint(1))
		crv33 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(1), crv1.GetEndPoint(1))
		crv44 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(1), crv1.GetEndPoint(0))
		"""
		crv11 = CreateBound(crv1.GetEndPoint(0),crv2.GetEndPoint(0))
		crv22 = CreateBound(crv2.GetEndPoint(0),crv2.GetEndPoint(1))
		crv33 = CreateBound(crv2.GetEndPoint(1),crv1.GetEndPoint(1))
		crv44 = CreateBound(crv1.GetEndPoint(1),crv1.GetEndPoint(0))
		"""
		g_crv_list = [crv11, crv22, crv33, crv44]
		return g_crv_list
	else:
		return None


def get_wall_type_material_and_select_material_for_ds(doc, b_element, room):
	"""Select DS material by structurual material of wall type."""
	room_func = room.LookupParameter("Имя").AsString()
	if room_func == "Мойка автомобилей":
		room_func = "Автостоянка"
	if b_element.GetType().Name is not "RevitLinkInstance":
		mat_name = doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString()
		if "елезобетон" in mat_name:
			out = "АБН_Отделка стен железобетон ({})".format(room_func)
			create_material(out)
		else:
			out = "АБН_Отделка стен кладка ({})".format(room_func)
			create_material(out)
	else:
		out = "АБН_Отделка стен кладка ({})".format(room_func)
		create_material(out)
	return out


def create_material(mat_name):
	"""Create material, or finde exist, by name."""
	if Material.IsNameUnique(doc, mat_name):
		mat = Material.Create(doc, mat_name)
		doc.GetElement(mat).Color = Autodesk.Revit.DB.Color(Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))))

# -----------------------АПИ параметры----------------------
doc = DocumentManager.Instance.CurrentDBDocument
link_doc = UnwrapElement(IN[1]) # noqa
custom_hight = IN[3] # noqa
# uiapp = DocumentManager.Instance.CurrentUIApplication
# app = uiapp.Application
# version = app.VersionNumber
options = SpatialElementBoundaryOptions()
options.StoreFreeBoundaryFaces = True
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
calculator = SpatialElementGeometryCalculator(doc, options)
trnsf = Transform.CreateTranslation(XYZ(0, 0, 100))
s_options = SolidOptions(ElementId(-1), ElementId(-1))

# -----------------------Рабочие параметры----------------------
size_param = 1000
incopenings, incshadows, incwalls, incshared = True, False, True, True
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

# @@@-----------------------Начало Скрипта----------------------
for room in rooms:
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	room_height = room_volume / room_area * 304.8
	room_level = doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID).AsElementId())

	separator_list = []
	by_face_list = []
	inserts = []
	curve_from_boundary_list = []
	elem_list = []
	results = calculator.CalculateSpatialElementGeometry(room)
	roomSolid = results.GetGeometry()
	inserts_by_wall = []
	boundary_surf = []
	boundary_curvs = []
	boundary_type = []
	boundary_level = []

# @@@-----------------------Боундари Элементс----------------------
	for boundarylist in room.GetBoundarySegments(options):
		b_s = []
		b_element1 = None
		b_element2 = None
		for i, boundary in enumerate(boundarylist):
			crv = None
			wall_hight = room_height
			if str(boundary.ElementId) == "-1" and str(boundary.LinkElementId) == "-1":
				crv = boundary.GetCurve()
				if i + 1 < len(boundarylist):
					try:
						type = get_wall_type_material_and_select_material_for_ds(doc, doc.GetElement(boundarylist[i + 1].ElementId), room)
					except:
						type = "АБН_Отделка стен"
						"""
						try:
							type = get_wall_type_material_and_select_material_for_ds(doc,doc.GetElement(boundarylist[i-1].ElementId),room)
						except:
							type = "АБН_Отделка стен"
						"""
				elif i - 1 >= 0:
					try:
						type = get_wall_type_material_and_select_material_for_ds(doc, doc.GetElement(boundarylist[i - 1].ElementId), room)
					except:
						type = "АБН_Отделка стен"
						"""try:
							type = get_wall_type_material_and_select_material_for_ds(doc,doc.GetElement(boundarylist[i+1].ElementId),room)
						except:
						type = "where is my type dude2"""
				else:
					type = "where is my type dude3"
			elif str(boundary.ElementId) is not "-1":
				b_element1 = doc.GetElement(boundary.ElementId)
				if b_element1.GetType().Name == "ModelLine":
					separator_list.append(boundary.GetCurve())  # !!!!!!!!!!!!!!!!boundary.GetCurve() вместо поиска геометрии у элементов!!!!!!!!!!
				elif b_element1.GetType().Name == "Wall" and b_element1.WallType.Kind == WallKind.Curtain:
					separator_list.append(boundary.GetCurve())
# ---------------Убираем тип стены из расчёта -----------------------------------------------------------------------------------
				elif b_element1.GetType().Name == "Wall" and doc.GetElement(b_element1.GetTypeId()).get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Ограждение МХМТС":
					pass
# -------------------------------------------------------------------------------------------------------------------------------------------
				elif b_element1.GetType().Name == "Wall":
					wall_box = b_element1.get_BoundingBox(doc.ActiveView)
					wall_hight = (wall_box.Max.Z - wall_box.Min.Z) * 304.8
					type = get_wall_type_material_and_select_material_for_ds(doc, b_element1, room)
					crv = boundary.GetCurve()
				else:
					try:
						type = get_wall_type_material_and_select_material_for_ds(doc, b_element1, room)
					except:
						type = "АБН_Отделка стен"
					crv = boundary.GetCurve()
			elif str(boundary.LinkElementId) is not "-1":
				b_element2 = link_doc.GetElement(boundary.LinkElementId)
				if b_element2.GetType().Name == "ModelLine":
					separator_list.append(boundary.GetCurve())
				elif b_element2.GetType().Name == "Wall" and b_element2.WallType.Kind == WallKind.Curtain:
					separator_list.append(boundary.GetCurve())
			boundary_level.append(room_level)
# ------------------------------------------------------Включаем расчет по высоте стен--------------------------------------------------
			if crv is not None and IN[4]: # noqa
				crv = crv.CreateTransformed(transform_Z).ToProtoType()
			elif crv is not None:
				crv = crv.ToProtoType()
			if IN[2]: # noqa
				if crv is not None:
					if wall_hight > room_height:
						boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), room_height))
					else:
						boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), wall_hight))
					boundary_type.append(type)
			else:
				if crv is not None:
					boundary_surf.append(DSCurve.Extrude(crv, Autodesk.Revit.DB.XYZ(0, 0, 1).ToVector(), custom_hight))
					boundary_type.append(type)

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
					by_face_list.append(face)  # -------------Cобираем плоскость
					by_face_h = face
					main_wall_by_id_work(host_id, doc, by_face_h)
					inserts.extend(inserts_by_wall)
				else:
					link_id = bface.SpatialBoundaryElement.LinkedElementId
					if str(link_id) is not "-1" and is_not_curtain(link_id, link_doc):
						by_face_list.append(face)  # ---------Cобираем плоскость
						by_face_l = face
						inserts.extend(inserts_by_wall)
					else:
						# @@@-----------------------Тут убираем дубликаты плоскостей----------------------
						for b_f in by_face_list:
							if face.Equals(b_f):
								test_list.append(True)
							else:
								test_list.append(False)
						if any(test_list):
							pass
						else:
							# @@@-----------------------Тут убираем разделители----------------------
							for s_l in separator_list:
								if str(face.Intersect(s_l)) == "Disjoint":
									test_list2.append(False)
								else:
									test_list2.append(True)
							if any(test_list2):
								pass
							elif bface.SubfaceArisesFromElementFace:  # ------Убираем плоскости витражей
								pass
							else:
								by_face_list.append(face)  # ------Cобираем торцевые плоскости
								by_face = face
								inserts.extend(inserts_by_wall)
	insertslist.append(inserts)
	surface_in_room = []
	for bs in boundary_surf:
		new_bs = bs
		for ins in inserts:
			if ins and bs.DoesIntersect(ins):
				try:
					# -------------------ВЫРЕЗАЕТ ИЗ ПЛОСКОСТИ СТЕНЫ ЕСЛИ ДВЕРЬ ПРИМЫКАЕТ К НЕЙ ТОРЦОМ, ИСПРАВИТЬ -------------------
					# -------------------нужен метот для получения плоскости стены с изминёным профилем -------------------
					new_bs = new_bs.SubtractFrom(ins)[0]
				except:
					pass
		surface_in_room.append(new_bs)
	surface_list_all.append(surface_in_room)
	boundary_type_by_room.append(boundary_type)
	boundary_by_room_level.append(boundary_level)
OUT = surface_list_all, boundary_type_by_room, boundary_by_room_level, separator_list
