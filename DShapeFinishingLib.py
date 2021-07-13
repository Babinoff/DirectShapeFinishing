# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек-----------------------
import clr
from clr import StrongBox
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")

clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIIFC')
clr.AddReference("RevitServices")
clr.AddReference('ProtoGeometry')
clr.AddReference("RevitNodes")

import Revit
clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

from Autodesk.Revit.DB.IFC import ExporterIFCUtils
from Autodesk.Revit.DB import UV
from Autodesk.Revit.DB import BooleanOperationsUtils, BooleanOperationsType, Curve, CurveLoop, GeometryCreationUtilities, Line, SolidOptions, SolidUtils, Transform, XYZ
from Autodesk.Revit.DB import BuiltInParameter, ElementId, Material, SetComparisonResult, WallKind
import Autodesk
import System
from System.Collections.Generic import List
from System import Byte

from random import randint
# -----------------------Импоорт библиотек----------------------
incopenings, incshadows, incwalls, incshared = True, False, True, True


# -----------------------Классы
class TimeCounter:
	"""C# timer."""
	def __init__(self, name="timer"):
		"""Start timer."""
		self.name = name
		self.time = System.Diagnostics.Stopwatch.StartNew()
		self.time.Start()

	def stop(self):
		"""Stop timer."""
		self.time.Stop()
		return self.time.Elapsed


class SolidTransformByLinkInstance():
	link_instance_transform_total = None

	def __init__(self, link_instance):
		if link_instance:
			self.link_instance_transform_total = link_instance.GetTotalTransform()

	def transform_to_current_doc(self, inserts_solid_by_wall):
		if self.link_instance_transform_total:
			return [SolidUtils.CreateTransformed(new_geom, self.link_instance_transform_total) for new_geom in inserts_solid_by_wall]
# -----------------------Классы


# -----------------------Функции----------------------
def create_material(current_doc, mat_name):
	"""Create material, or find exist, by name."""
	if Material.IsNameUnique(current_doc, mat_name):
		mat = Material.Create(current_doc, mat_name)
		current_doc.GetElement(mat).Color = Autodesk.Revit.DB.Color(Byte.Parse(str(randint(
			0, 255))), Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))))


def dublicate_separate_filter(by_face_list, face):
	"""Find only correct face."""
	test_list_dubl = []
	center_uv = UV(0.5, 0.5)
	face_point = face.Evaluate(center_uv)
	for b_f in by_face_list:
		if face_point.ToString() == b_f.Evaluate(center_uv).ToString():
			test_list_dubl.append(True)
		else:
			test_list_dubl.append(False)
	if any(test_list_dubl):
		return False
	else:
		return True


def main_face_filter(list_of_concrete_mat_prfx, room, host_id, link_id, current_doc, link_doc, face, wall_type_names_to_exclude, transformer):
	"""Filter to remove all what not needet."""
	id_minus_one = ElementId(-1)
	b_element = None
	inserts_solid_by_wall = []
	ds_type_material = "Finishing_BASE"
	if host_id != id_minus_one:
		if this_is_not_element_your_looking_for(host_id, current_doc, wall_type_names_to_exclude):
			b_element = current_doc.GetElement(host_id)
			ds_type_material = get_wall_ds_type_material(current_doc, b_element, room, list_of_concrete_mat_prfx)
			inserts_solid_by_wall = get_inserts_solid_cuboid_from_wall(b_element, current_doc, current_doc, face)
	elif link_id != id_minus_one:
		if this_is_not_element_your_looking_for(link_id, link_doc, wall_type_names_to_exclude):
			b_element = link_doc.GetElement(link_id)
			ds_type_material = get_wall_ds_type_material(link_doc, b_element, room, list_of_concrete_mat_prfx)
			inserts_solid_by_wall = get_inserts_solid_cuboid_from_wall(b_element, current_doc, link_doc, face)
			inserts_solid_by_wall = transformer.transform_to_current_doc(inserts_solid_by_wall)
	return b_element, inserts_solid_by_wall, ds_type_material


def this_is_not_element_your_looking_for(id, doc, wall_type_names_to_exclude):
	"""Wall is curtain test."""
	wall = doc.GetElement(id)
	wall_type = doc.GetElement(wall.GetTypeId())
	if wall_type:
		type_name = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if wall and wall.GetType().Name != "DirectShape":
			if wall.GetType().Name == "Wall" and wall.WallType.Kind == WallKind.Curtain:
				return False
			elif wall.GetType().Name == "ModelLine":
				return False
			elif type_name in wall_type_names_to_exclude:
				return False
			else:
				return True
	else:
		return False


def get_wall_ds_type_material(current_doc, b_element, room, list_of_concrete_mat_prfx):
	"""Select DS material by structurual material of wall type."""
	room_func = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
	ds_mat_name = "Finishing_BASE"
	mat_name = "none"
	if current_doc.GetElement(b_element.GetTypeId()) and current_doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM):
		mat_name = current_doc.GetElement(b_element.GetTypeId()).get_Parameter(
			BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString().replace('<', '').replace('>', '')
		ds_mat_name = "Finishing_brickwork ({}) ({})".format(room_func, mat_name)
		for concrete_mat_prfx in list_of_concrete_mat_prfx:
			if concrete_mat_prfx.lower() in str(mat_name).lower():
				ds_mat_name = "Finishing_CONCRETE ({}) ({})".format(
					room_func, mat_name)
	else:
		ds_mat_name = "Finishing_brickwork ({}) ({})".format(
			room_func, mat_name)
	return ds_mat_name


def get_inserts_solid_cuboid_from_wall(b_element, current_doc, _doc, face):
	"""Choosing wall destiny by ID."""
	inserts_solids_by_wall = []
	if b_element.GetType().Name == "Wall":
		inserts_id_list = b_element.FindInserts(incopenings, incshadows, incwalls, incshared)
		if not inserts_id_list:
			pass
		else:
			for insert_id in inserts_id_list:
				item = _doc.GetElement(insert_id)
				# host_id = item.Host.Id.IntegerValue
				solid = None
				if item.GetType().Name == "FamilyInstance":
					if b_element.Id.IntegerValue == item.Host.Id.IntegerValue:
						solid = get_wall_cut(current_doc, item, b_element, face)
				elif item.GetType().Name == "Wall":
					solid = get_wall_profil(item, b_element, face)
				else:
					solid = bbox_to_solid(item.get_BoundingBox(current_doc.ActiveView))
				inserts_solids_by_wall.append(solid)
	return inserts_solids_by_wall


def get_wall_cut(current_doc, item, wall, _face):
	"""Get wall cunt."""
	_doc = item.Document
	current_dir = StrongBox[XYZ](wall.Orientation)
	try:
		curve_loop1 = ExporterIFCUtils.GetInstanceCutoutFromWall(
			_doc, wall, item, current_dir)
		multpl = wall.Width
		w_vector = wall.Orientation
		f_vector = item.FacingOrientation
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
		geom1 = GeometryCreationUtilities.CreateExtrusionGeometry(
			icurve_loop, extr_vector, wall.Width * 2)
		geom2 = GeometryCreationUtilities.CreateExtrusionGeometry(
			icurve_loop, -extr_vector, wall.Width * 2)
		geom = BooleanOperationsUtils.ExecuteBooleanOperation(geom1, geom2, BooleanOperationsType.Union)
		return geom
	except:
		geom = bbox_to_solid(item.get_BoundingBox(current_doc.ActiveView))
		return geom


def get_wall_profil(insert_wall, host_wall, face):
	u"""Get wall Profil. Расположение точек в линиях должно быть последовательным для курвелооп."""
	g_curve_list = get_wall_p_curve(insert_wall)
	if g_curve_list is not None:
		icurve = List[Autodesk.Revit.DB.Curve](g_curve_list)
		i_crv_loop = CurveLoop.Create(icurve)
		i_list_crv_loop = List[CurveLoop]([i_crv_loop])
		wh_vector = host_wall.Orientation
		f_vector = face.FaceNormal
		if wh_vector.IsAlmostEqualTo(f_vector):
			extr_vector = insert_wall.Orientation
		else:
			extr_vector = host_wall.Orientation
		geom1 = GeometryCreationUtilities.CreateExtrusionGeometry(
			i_list_crv_loop, extr_vector, host_wall.Width)
		geom2 = GeometryCreationUtilities.CreateExtrusionGeometry(
			i_list_crv_loop, -extr_vector, host_wall.Width)
		geom = BooleanOperationsUtils.ExecuteBooleanOperation(geom1, geom2, BooleanOperationsType.Union)
		return geom


def get_wall_p_curve(u_wall):
	"""Create lines for policurve."""
	if u_wall.GetType().Name == "Wall":
		loc = u_wall.Location
		crv = loc.Curve
		bo = u_wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
		wh = u_wall.get_Parameter(
			BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
		move_bo = Transform.CreateTranslation(XYZ(0, 0, bo))
		move_wh = Transform.CreateTranslation(XYZ(0, 0, wh))
		crv1 = crv.CreateTransformed(move_bo)
		crv2 = crv1.CreateTransformed(move_wh)

		crv11 = Autodesk.Revit.DB.Line.CreateBound(
			crv1.GetEndPoint(0), crv2.GetEndPoint(0))
		crv22 = Autodesk.Revit.DB.Line.CreateBound(
			crv2.GetEndPoint(0), crv2.GetEndPoint(1))
		crv33 = Autodesk.Revit.DB.Line.CreateBound(
			crv2.GetEndPoint(1), crv1.GetEndPoint(1))
		crv44 = Autodesk.Revit.DB.Line.CreateBound(
			crv1.GetEndPoint(1), crv1.GetEndPoint(0))

		g_crv_list = [crv11, crv22, crv33, crv44]
		return g_crv_list
	else:
		return None


def bbox_to_solid(bbox):
	solid_opt = SolidOptions(ElementId.InvalidElementId, ElementId.InvalidElementId)
	bottom_z_offset = 0.1
	bbox.Min = XYZ(bbox.Min.X, bbox.Min.Y, bbox.Min.Z - bottom_z_offset)
	b1 = XYZ(bbox.Min.X, bbox.Min.Y, bbox.Min.Z)
	b2 = XYZ(bbox.Max.X, bbox.Min.Y, bbox.Min.Z)
	b3 = XYZ(bbox.Max.X, bbox.Max.Y, bbox.Min.Z)
	b4 = XYZ(bbox.Min.X, bbox.Max.Y, bbox.Min.Z)
	bbox_height = bbox.Max.Z - bbox.Min.Z

	lines = List[Curve]()
	lines.Add(Line.CreateBound(b1, b2))
	lines.Add(Line.CreateBound(b2, b3))
	lines.Add(Line.CreateBound(b3, b4))
	lines.Add(Line.CreateBound(b4, b1))
	rectangle = [CurveLoop.Create(lines)]

	extrusion = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop](rectangle),
																																XYZ.BasisZ,
																																bbox_height,
																																solid_opt)
	return extrusion
