# -*- coding: utf-8 -*-
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
# from System.Diagnostics import Process, Stopwatch

clr.AddReference('RevitAPI')
import Autodesk
# from Autodesk.Revit.DB import SpatialElement, SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementBoundarySubface, SpatialElementGeometryCalculator
from Autodesk.Revit.DB import BuiltInParameter, BuiltInCategory, Color, DisplayUnitType, ElementId, FilteredElementCollector, Material, SetComparisonResult, UnitUtils, WallKind
from Autodesk.Revit.DB import Curve, CurveLoop, ElementTransformUtils, GeometryCreationUtilities, Line, SolidOptions, SolidUtils, SubfaceType, Transform, XYZ
from Autodesk.Revit.DB import UV
clr.AddReference('RevitAPIIFC')
from Autodesk.Revit.DB.IFC import ExporterIFCUtils


# from Revit.Elements import Elements


clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

# clr.AddReference('ProtoGeometry')
# from Autodesk.DesignScript.Geometry import *

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import BoundingBox, Surface
from Autodesk.DesignScript.Geometry import Curve as DSCurve

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)
from Revit.Elements import Element as DSElement
clr.ImportExtensions(Revit.GeometryConversion)
# -----------------------Импоорт библиотек----------------------


incopenings, incshadows, incwalls, incshared = True, False, True, True


# -----------------------Класс для хранения информации
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


class ElementTransformByLinkInstance():
	link_instance_transform_total = None
	transform_if_point_move = None
	transform_on = False
	transform_rotate_on = False
	transform_rotate = 0
	z_line = None
	_doc = None

	def __init__(self, doc, link_instance):
		self._doc = doc
		self.link_instance_transform_total = link_instance.GetTotalTransform()
		# doc_project_bas_point_collector_ilist = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).ToElements()
		# if doc_project_bas_point_collector_ilist and len(doc_project_bas_point_collector_ilist) > 0:
		# 	doc_project_bas_point = doc_project_bas_point_collector_ilist[0]
		# 	link_instance_transform = link_instance.GetTransform()
		# 	self.link_instance_transform_total = link_instance.GetTotalTransform()
		# 	vector_x_of_instance = link_instance_transform.OfVector(link_instance_transform.BasisX)

		# 	if (doc_project_bas_point.SharedPosition.DistanceTo(link_instance_transform.Origin) != 0):
		# 		base_vector = link_instance_transform.Origin
		# 		self.transform_if_point_move = base_vector
		# 		self.transform_on = True
		# 		self.z_line = Line.CreateBound(link_instance_transform.Origin, link_instance_transform.Origin + XYZ(0, 0, 1))
		# 		self.transform_rotate = link_instance_transform.BasisX.AngleOnPlaneTo(vector_x_of_instance, link_instance_transform.BasisZ)
		# 		if (self.transform_rotate != 0):
		# 			self.transform_rotate_on = True

	def transform_to_current_doc(self, inserts_solid_by_wall):
		return [SolidUtils.CreateTransformed(new_geom, self.link_instance_transform_total) for new_geom in inserts_solid_by_wall]
		# if (self.transform_on is True):

		# 	# ElementTransformUtils.MoveElements(self._doc, new_elements_ids, self.transform_if_point_move)
		# if (self.transform_rotate_on is True):
		# 	# ElementTransformUtils.RotateElements(self._doc, new_elements_ids, self.z_line, self.transform_rotate)
		# 	Geometry.Rotate(new_geom, )


# -----------------------Функции----------------------
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


def wall_profil(face_host_id, current_doc, face):
	"""Find wall profil."""
	b_element = current_doc.GetElement(face_host_id)
	if b_element.GetType().Name == "Wall":
		return b_element.GetGeometryObjectFromReference(face.Reference)


def main_face_filter(host_id, link_id, current_doc, link_doc, face, wall_type_names_to_exclude, transformer):
	"""Filter to remove all what not needet."""
	id_minus_one = ElementId(-1)
	b_element, inserts_solid_by_wall = None, []
	if host_id != id_minus_one:
		if is_not_curtain_modelline(host_id, current_doc):
			b_element = current_doc.GetElement(host_id)
			inserts_solid_by_wall = get_inserts_solid_cuboid_from_wall(b_element, current_doc, current_doc, face, wall_type_names_to_exclude)
	elif link_id != id_minus_one:
		if is_not_curtain_modelline(link_id, link_doc):
			b_element = link_doc.GetElement(link_id)
			inserts_solid_by_wall = get_inserts_solid_cuboid_from_wall(b_element, current_doc, link_doc, face, wall_type_names_to_exclude)
			inserts_solid_by_wall = transformer.transform_to_current_doc(inserts_solid_by_wall)
	return b_element, inserts_solid_by_wall


def is_not_curtain_modelline(id, doc):
	"""Wall is curtain test."""
	wall = doc.GetElement(id)
	if wall and wall.GetType().Name != "DirectShape":
		if wall.GetType().Name == "Wall" and wall.WallType.Kind == WallKind.Curtain:
			return False
		elif wall.GetType().Name == "ModelLine":
			return False
		else:
			return True


def get_inserts_solid_cuboid_from_wall(b_element, current_doc, _doc, face, wall_type_names_to_exclude):
	"""Choosing wall destiny by ID."""
	inserts_solids_by_wall = []
	if b_element.GetType().Name == "Wall":
		wall_type = _doc.GetElement(b_element.GetTypeId())
		type_name = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if type_name in wall_type_names_to_exclude:
			pass
		else:
			inserts_id_list = b_element.FindInserts(incopenings, incshadows, incwalls, incshared)
			if not inserts_id_list:
				pass
			else:
				for insert_id in inserts_id_list:
					item = _doc.GetElement(insert_id)
					# x = BoundingBox.ToCuboid(DSElement.BoundingBox(UnwrapElement(item)))
					# if item.GetType().Name == "Opening":
					# 	pass
					# else:
					# item = _doc.GetElement(insert_id)
					solid = None
					if item.GetType().Name == "FamilyInstance":
						solid = get_wall_cut(current_doc, item, b_element, face)
					elif item.GetType().Name == "Wall":
						solid = get_wall_profil(item, b_element, face)
					else:
						solid = bbox_to_solid(item.get_BoundingBox(current_doc.ActiveView))
						# x = BoundingBox.ToCuboid(item.get_BoundingBox(current_doc.ActiveView).ToProtoType())
					inserts_solids_by_wall.append(solid)
	return inserts_solids_by_wall


def main_wall_by_id_work(face_host_id, current_doc, face, wall_type_names_to_exclude):
	"""Choosing wall destiny by ID."""
	# global curtain_list
	# global full_id_list
	# global inserts_by_wall
	inserts_by_wall = []
	# full_id_list.append(face_host_id)
	b_element = current_doc.GetElement(face_host_id)
	if b_element.GetType().Name == "Wall":
		wall_type = current_doc.GetElement(b_element.GetTypeId())
		type_name = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if type_name in wall_type_names_to_exclude:
			pass
		else:
			inserts_list = b_element.FindInserts(incopenings, incshadows, incwalls, incshared)
			if not inserts_list:
				pass
			else:
				for insert in inserts_list:
					if current_doc.GetElement(insert).GetType().Name == "Opening":
						pass
					else:
						item = current_doc.GetElement(insert)
						x = None
						if item.GetType().Name == "FamilyInstance":
							x = get_wall_cut(item, b_element, face)
						elif item.GetType().Name == "Wall":
							x = get_wall_profil(item, b_element, face)
						else:
							x = BoundingBox.ToCuboid(item.get_BoundingBox(current_doc.ActiveView).ToProtoType())
						inserts_by_wall.append(x)
	return inserts_by_wall


def get_wall_cut(current_doc, item, wall, _face):
	"""Get wall cunt."""
	_doc = item.Document
	current_dir = StrongBox[XYZ](wall.Orientation)
	try:
		curve_loop1 = ExporterIFCUtils.GetInstanceCutoutFromWall(_doc, wall, item, current_dir)
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
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(icurve_loop, extr_vector, wall.Width * 2)#.ToProtoType()
		return geom
	except:
		geom = bbox_to_solid(item.get_BoundingBox(current_doc.ActiveView))
		# geom = BoundingBox.ToCuboid(item.get_BoundingBox(current_doc.ActiveView))#.ToProtoType())
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
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(i_list_crv_loop, extr_vector, host_wall.Width)#.ToProtoType()
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


def get_wall_ds_type_material(current_doc, b_element, room, concrete_mat_prfx="елезобетон"):
	"""Select DS material by structurual material of wall type."""
	# room_func = room.LookupParameter(room_param_name).AsString()
	room_func = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
	ds_mat_name = "Finishing_BASE"
	mat_name = ""
	if current_doc.GetElement(b_element.GetTypeId()) and current_doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM):
		mat_name = current_doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString()
		if concrete_mat_prfx in str(mat_name):
			ds_mat_name = "Finishing_CONCRETE ({}) ({})".format(room_func, mat_name)
			create_material(current_doc, ds_mat_name)
		else:
			ds_mat_name = "Finishing_brickwork ({}) ({})".format(room_func, mat_name)
			create_material(current_doc, ds_mat_name)
	else:
		ds_mat_name = "Finishing_brickwork ({}) ({})".format(room_func, mat_name)
		create_material(current_doc, ds_mat_name)
	# if b_element.GetType().Name is not "RevitLinkInstance":
	# 	mat_name = current_doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString()
	# 	if concrete_mat_prfx in mat_name:
	# 		ds_mat_name = "Finishing_CONCRETE ({})".format(room_func)
	# 		create_material(current_doc, ds_mat_name)
	# 	else:
	# 		ds_mat_name = "Finishing_MASONRY ({})".format(room_func)
	# 		create_material(current_doc, ds_mat_name)
	# else:
	# 	ds_mat_name = "Finishing_MASONRY ({})".format(room_func)
	# 	create_material(current_doc, ds_mat_name)
	return ds_mat_name


def create_material(current_doc, mat_name):
	"""Create material, or find exist, by name."""
	if Material.IsNameUnique(current_doc, mat_name):
		mat = Material.Create(current_doc, mat_name)
		current_doc.GetElement(mat).Color = Autodesk.Revit.DB.Color(Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))))


def get_type_if_null_id(current_doc, boundary, room, boundarylist, index):
	"""Try find nearest element to chose type."""
	global ds_type
	try:
		ds_type = get_wall_type_material(current_doc, boundary, room)
	except:
		pass
	if index + 1 < len(boundarylist):
		try:
			ds_type = get_wall_type_material(current_doc, current_doc.GetElement(boundarylist[index + 1].ElementId), room)
		except:
			pass
	elif index - 1 >= 0:
		try:
			ds_type = get_wall_type_material(current_doc, current_doc.GetElement(boundarylist[index - 1].ElementId), room)
		except:
			pass


def get_wall_type_name(current_doc, b_element):
	"""Get symbol name."""
	return current_doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()


def boundary_filter(current_doc, b_element, boundary, room, r_f):
	"""Find only correct walls."""
	global ds_type
	global crv
	global wall_hight
	if b_element.GetType().Name == "ModelLine":
		r_f.separator_list.append(boundary.GetCurve())
	elif b_element.GetType().Name == "Wall" and b_element.WallType.Kind == WallKind.Curtain:
		r_f.separator_list.append(boundary.GetCurve())
# ---------------Убираем тип стены из расчёта ------------
	elif b_element.GetType().Name == "Wall":
		wall_box = b_element.get_BoundingBox(current_doc.ActiveView)
		wall_hight = (wall_box.Max.Z - wall_box.Min.Z) * 304.8
		ds_type = get_wall_ds_type_material(current_doc, b_element, room)
		crv = boundary.GetCurve()
	else:
		try:
			ds_type = get_wall_ds_type_material(current_doc, b_element, room)
		except:
			pass
		crv = boundary.GetCurve()


def dublicate_separate_filter(by_face_list, face):
	"""Find only correct face."""
	test_list_dubl = []
	# test_list_separate = []
	center_uv = UV(0.5, 0.5)
	face_point = face.Evaluate(center_uv)
	for b_f in by_face_list:
		if face_point.ToString() == b_f.Evaluate(center_uv).ToString():
			test_list_dubl.append(True)
		else:
			test_list_dubl.append(False)

	# for b_f in r_f.by_face_list:
	# 	if face.Equals(b_f):
	# 		test_list_dubl.append(True)
	# 	else:
	# 		test_list_dubl.append(False)

	# for s_l in r_f.separator_list:
	# 	if str(face.Intersect(s_l)) == "Disjoint":
	# 		test_list_separate.append(False)
	# 	else:
	# 		test_list_separate.append(True)

	if any(test_list_dubl):
		return False
	else:
		return True
