# -----------------------Импоорт библиотек-----------------------
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


incopenings, incshadows, incwalls, incshared = True, False, True, True


# -----------------------Функции----------------------
def main_wall_by_id_work(self, face_host_id, doc, face, wall_type_names_to_exclude):
	"""Choosing wall destiny by ID."""
	global curtain_list
	global full_id_list
	global inserts_by_wall
	full_id_list.append(face_host_id)
	b_element = doc.GetElement(face_host_id)
	if b_element.GetType().Name == "Wall":
		wall_type = doc.GetElement(b_element.GetTypeId())
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
					if doc.GetElement(insert).GetType().Name == "Opening":
						pass
					else:
						item = doc.GetElement(insert)
						x = None
						if item.GetType().Name == "FamilyInstance":
							x = get_wall_cut(item, b_element, face)
						elif item.GetType().Name == "Wall":
							x = get_wall_profil(item, b_element, face)
						else:
							x = BoundingBox.ToCuboid(item.get_BoundingBox(doc.ActiveView).ToProtoType())
						inserts_by_wall.append(x)


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


def get_wall_profil(insert_wall, host_wall, face):
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
	"""Create lines for policurve."""
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

		g_crv_list = [crv11, crv22, crv33, crv44]
		return g_crv_list
	else:
		return None


def get_wall_type_material(doc, b_element, room, room_param_name="Имя"):
	"""Select DS material by structurual material of wall type."""
	room_func = room.LookupParameter(room_param_name).AsString()
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
	"""Create material, or find exist, by name."""
	global doc
	if Material.IsNameUnique(doc, mat_name):
		mat = Material.Create(doc, mat_name)
		doc.GetElement(mat).Color = Autodesk.Revit.DB.Color(Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))))
