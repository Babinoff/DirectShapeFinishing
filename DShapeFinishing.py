# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек----------------------
import clr
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")
"""Путь к файлам библиотек"""
sys.path.append(IN[0])

# import DirectShapeFunctions
from DShapeLib import SolidTransformByLinkInstance, TimeCounter
from DShapeLib import main_face_filter, dublicate_separate_filter, create_material

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import Revit
clr.ImportExtensions(Revit.GeometryConversion)
from Autodesk.Revit.DB import SubfaceType
from Autodesk.Revit.DB import BuiltInParameter, ElementId
from Autodesk.Revit.DB import SpatialElementBoundaryLocation, SpatialElementBoundaryOptions, SpatialElementGeometryCalculator
# -----------------------Импоорт библиотек----------------------


# -----------------------АПИ параметры----------------------
current_doc = DocumentManager.Instance.CurrentDBDocument
options = SpatialElementBoundaryOptions()
options.StoreFreeBoundaryFaces = True
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
calculator = SpatialElementGeometryCalculator(current_doc, options)
# -----------------------АПИ параметры----------------------


# -----------------------Рабочие параметры----------------------
rooms = UnwrapElement(IN[1])  # noqa
link_doc, rvt_instance_element = IN[2][0][0], IN[2][2][0]  # noqa
wall_type_names_to_exclude = IN[3]  # noqa
list_of_concrete_mat_prfx = IN[4]  # noqa
surface_list_all = []
wall_type_mat_names_all = []

test_room_faces = []
fail_face = []

id_minus_one = ElementId(-1)
transformer = SolidTransformByLinkInstance(rvt_instance_element)

TransactionManager.Instance.EnsureInTransaction(current_doc)
ds_type_material = "Finishing_BASE"
create_material(current_doc, ds_type_material)

timer_rooms = TimeCounter()
for room in rooms:
	test_faces = []
	room_area = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
	room_volume = room.get_Parameter(BuiltInParameter.ROOM_VOLUME).AsDouble()
	if room_volume > 0:
		surface_in_room = []
		by_face_list = []
		wall_type_mat_names = []
		sp_geom_results = calculator.CalculateSpatialElementGeometry(room)
		for face in sp_geom_results.GetGeometry().Faces:
			inserts_solid_by_wall = []
			bface = sp_geom_results.GetBoundaryFaceInfo(face)[0]
			if str(bface.SubfaceType) is str(SubfaceType.Side) and dublicate_separate_filter(by_face_list, face):
				sbe_id = bface.SpatialBoundaryElement
				host_id = sbe_id.HostElementId
				link_id = sbe_id.LinkedElementId
				link_inst_id = sbe_id.LinkInstanceId
				if host_id == id_minus_one and link_id == id_minus_one:
					by_face_list.append(face)
				else:
					b_element, inserts_solid_by_wall, ds_type_material = main_face_filter(list_of_concrete_mat_prfx, room, host_id, link_id, current_doc, link_doc, face, wall_type_names_to_exclude, transformer)
					if b_element:
						create_material(current_doc, ds_type_material)
						wall_type_mat_names.append(ds_type_material)
						test_inserts_solid = []
						try:  # необходим поскольку конвертация .ToProtoType() может быть не успешной, если face очень маленький, или имеет форму не допустимую в Динамо
							new_bs = face.ToProtoType()[0]
							for ins in inserts_solid_by_wall:
								if ins:
									ins = ins.ToProtoType()
									test_inserts_solid.append(ins)
									if ins and new_bs.DoesIntersect(ins):
										new_bs = new_bs.SubtractFrom(ins)[0]
						except Exception as e:
							tb2 = sys.exc_info()[2]
							line = tb2.tb_lineno
							fail_face.append((room, face, "{0} Has failure {1}".format(str(line), str(e))))
						surface_in_room.append(new_bs)
						test_faces.append((ds_type_material, host_id, link_id, b_element, test_inserts_solid))
		surface_list_all.append(surface_in_room)
		wall_type_mat_names_all.append(wall_type_mat_names)
		test_room_faces.append(test_faces)
time_rooms = timer_rooms.stop()

TransactionManager.Instance.ForceCloseTransaction()

OUT = time_rooms, fail_face, surface_list_all, wall_type_mat_names_all  # , test_room_faces
