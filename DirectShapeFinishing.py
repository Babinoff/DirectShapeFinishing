# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек----------------------
import clr
# from random import randint
# # import random
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
from DirectShapeFunctions import SolidTransformByLinkInstance, TimeCounter
from DirectShapeFunctions import main_face_filter, dublicate_separate_filter
from DirectShapeFunctions import create_material
from DirectShapeFunctions import get_wall_ds_type_material

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import Revit
clr.ImportExtensions(Revit.Elements)  # ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)
from Autodesk.Revit.DB import UV
from Autodesk.Revit.DB import SolidOptions, SubfaceType, Transform, XYZ
from Autodesk.Revit.DB import BuiltInParameter, DisplayUnitType, ElementId, UnitUtils
from Autodesk.Revit.DB import SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementBoundarySubface, SpatialElementGeometryCalculator
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
link_doc, rvt_instance_element = IN[1][0][0], IN[1][2][0]  # noqa
# room_height_enable = IN[2]  # noqa
# custom_hight = IN[3]  # noqa
# transform_Z_enable = IN[4]  # noqa
# move_z_value = IN[5]  # noqa
wall_type_names_to_exclude = IN[6]  # noqa
# surf_by_room = []
# element_by_room = []
# full_id_list = []
# curtain_list = []
# insertslist = []
# surface_in_room = []
surface_list_all = []
# surf_from_bound_curvs = []
# boundarylist = []
# blist = []
# boundary_ds_type_by_room = []
# boundary_by_room_level = []
# r_f_list = []
wall_type_mat_names_all = []

# OUT = link_doc, rvt_instance_element
# """
test_room_faces = []

id_minus_one = ElementId(-1)
transformer = SolidTransformByLinkInstance(current_doc, rvt_instance_element)

# move_z = UnitUtils.ConvertToInternalUnits(move_z_value, DisplayUnitType.DUT_MILLIMETERS)  # noqa
# transform_Z = Transform.CreateTranslation(XYZ(0, 0, move_z))

TransactionManager.Instance.EnsureInTransaction(current_doc)
ds_type_material = "Finishing_BASE"
create_material(current_doc, ds_type_material)
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
		inserts_solid_by_wall = []
		by_face_list = []
		wall_type_mat_names = []
		for face in sp_geom_results.GetGeometry().Faces:
			bface = sp_geom_results.GetBoundaryFaceInfo(face)[0]
			if str(bface.SubfaceType) is str(SubfaceType.Side) and dublicate_separate_filter(by_face_list, face):
				sbe_id = bface.SpatialBoundaryElement
				host_id = sbe_id.HostElementId
				link_id = sbe_id.LinkedElementId
				link_inst_id = sbe_id.LinkInstanceId
				if host_id == id_minus_one and link_id == id_minus_one:
					by_face_list.append(face)
					# wall_type_mat_names.append(ds_type_material)
				else:
					b_element, inserts_solid_by_wall, ds_type_material = main_face_filter(room, host_id, link_id, current_doc, link_doc, face, wall_type_names_to_exclude, transformer)
					if b_element:
						create_material(current_doc, ds_type_material)
						wall_type_mat_names.append(ds_type_material)
						new_bs = face.ToProtoType()[0]
						test_inserts_solid = []
						for ins in inserts_solid_by_wall:
							ins = ins.ToProtoType()
							test_inserts_solid.append(ins)
							if ins and new_bs.DoesIntersect(ins):
								new_bs = new_bs.SubtractFrom(ins)[0]  # -------------------ВЫРЕЗАЕТ ИЗ ПЛОСКОСТИ СТЕНЫ ЕСЛИ ДВЕРЬ ПРИМЫКАЕТ К НЕЙ ТОРЦОМ, ИСПРАВИТЬ -------------------
								# -------------------нужен метот для получения плоскости стены с изминёным профилем
						surface_in_room.append(new_bs)
					if link_id != id_minus_one:
						test_faces.append((ds_type_material, host_id, link_id, b_element, test_inserts_solid))
		surface_list_all.append(surface_in_room)
		wall_type_mat_names_all.append(wall_type_mat_names)
		test_room_faces.append(test_faces)
time_rooms = timer_rooms.stop()

TransactionManager.Instance.ForceCloseTransaction()

OUT = time_rooms, surface_list_all, wall_type_mat_names_all  #, test_room_faces
# """
