

def wall_by_id_work(_id, _doc, _face):
	full_id_list.append(_id)
	b_element = _doc.GetElement(_id)
	#test3.append([b_element,b_element.GetType().Name])
	if b_element.GetType().Name == "Wall":	
		wallType = _doc.GetElement(b_element.GetTypeId())
		type_name = wallType.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if type_name == "Ограждение МХМТС": 
			pass
		elif "(автомойка)" in type_name:
			pass
		elif wallType.Kind == WallKind.Curtain:
			curtain_list.append(b_element)
		else:
			#blist.append(b_element)
			inserts_list = b_element.FindInserts(incopenings,incshadows,incwalls,incshared)
			if not inserts_list:
				pass
			else:
				for insert in inserts_list:
					if _doc.GetElement(insert).GetType().Name == "Opening":
						pass
					else:
						item = _doc.GetElement(insert)
						x = None
						#x = item.GetType().Name
						if item.GetType().Name == "FamilyInstance":
							x = GetWallCut(item,b_element,_face)
						elif item.GetType().Name == "Wall":
							x = GetWallProfil(item,b_element,_face)
						else:
							x = BoundingBox.ToCuboid(item.get_BoundingBox(doc.ActiveView).ToProtoType())
						inserts_by_wall.append(x)
	else:
		pass
	
def is_not_curtain(_id,_doc):
	wall = _doc.GetElement(_id)
	#wallType = wall.WallType#doc.GetElement(wall.GetTypeId())
	if wall.GetType().Name == "Wall": 
		if wall.WallType.Kind == WallKind.Curtain:	
			return False
		else:
			return True
	else:
		return True
		return True
		return True
	
def GetWallCut(fi,wall,_face):
	doc = fi.Document
	cutDir = StrongBox[XYZ](wall.Orientation)
	try:
		curveLoop1 = ExporterIFCUtils.GetInstanceCutoutFromWall(doc, wall, fi, cutDir)
		multpl = wall.Width
		w_vector = wall.Orientation
		f_vector = fi.FacingOrientation
		for c in curveLoop1:
			test_curv = c
		if _face.Intersect(test_curv) == SetComparisonResult.Subset:
			move = Transform.CreateTranslation(w_vector.Multiply(multpl))
			extr_vector = -w_vector
		else:
			if w_vector.IsAlmostEqualTo(f_vector):
				move = Transform.CreateTranslation(XYZ(0,0,0))
				extr_vector = w_vector
			else:
				move = Transform.CreateTranslation(XYZ(0,0,0))
				extr_vector = f_vector
		curv_move = [cl.CreateTransformed(move) for cl in curveLoop1]
		curveLoop2 = CurveLoop()
		for cm in curv_move:
			curveLoop2.Append(cm)
		icurveLoop = List[CurveLoop]([curveLoop2])
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(icurveLoop,extr_vector,wall.Width*2).ToProtoType()
		#loops = [i.ToProtoType() for i in curveLoop1] # - профиль сгенерированый Експортером
		return geom#[loops,geom]
	except:
		geom = BoundingBox.ToCuboid(fi.get_BoundingBox(doc.ActiveView).ToProtoType())
		return geom

def GetWallProfil(insert_wall,host_wall,_face):	
	#uw_geom = Element.Geometry(u_wall.ToDSType(True)) #ToDSType не работает без clr.ImportExtensions(Revit.Elements)
	g_curve_list = GetW_P_curve(insert_wall)
	if g_curve_list != None:
		icurve = List[Autodesk.Revit.DB.Curve](g_curve_list)
		#--- Расположение точек в линиях должно быть последовательным для курвелооп
		i_crv_loop = CurveLoop.Create(icurve)
		i_list_crv_loop = List[CurveLoop]([i_crv_loop])
		wh_vector = host_wall.Orientation
		iw_vector = insert_wall.Orientation
		f_vector = face.FaceNormal 
		if wh_vector.IsAlmostEqualTo(f_vector):
			extr_vector = insert_wall.Orientation
		else:
			extr_vector = host_wall.Orientation
		geom = GeometryCreationUtilities.CreateExtrusionGeometry(i_list_crv_loop,extr_vector,host_wall.Width).ToProtoType()
		#loops = [i.ToProtoType() for i in g_id_list]
		#p_crv = PolyCurve.ByJoinedCurves([crv1,crv2,crv3,crv4])		
		return geom#[loops,geom]#[i.ToPoint() for i in test]
	
def GetW_P_curve(u_wall):
	if u_wall.GetType().Name == "Wall":
		loc = u_wall.Location
		crv = loc.Curve
		bo = u_wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()#/0.3048#*size_param
		wh = u_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()#/0.3048#*size_param
		move_bo = Transform.CreateTranslation(XYZ(0,0,bo))
		move_wh = Transform.CreateTranslation(XYZ(0,0,wh))
		crv1 = crv.CreateTransformed(move_bo)
		crv2 = crv1.CreateTransformed(move_wh)

		crv11 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(0),crv2.GetEndPoint(0))
		crv22 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(0),crv2.GetEndPoint(1))
		crv33 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(1),crv1.GetEndPoint(1))
		crv44 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(1),crv1.GetEndPoint(0))
		"""
		crv11 = CreateBound(crv1.GetEndPoint(0),crv2.GetEndPoint(0))
		crv22 = CreateBound(crv2.GetEndPoint(0),crv2.GetEndPoint(1))
		crv33 = CreateBound(crv2.GetEndPoint(1),crv1.GetEndPoint(1))
		crv44 = CreateBound(crv1.GetEndPoint(1),crv1.GetEndPoint(0))
		"""
		g_crv_list = [crv11,crv22,crv33,crv44]
		return g_crv_list
	else:
		return None
		
def Get_walltype_ctruct_mat_name(doc,b_element,room):
	room_func = room.LookupParameter("Имя").AsString()
	if room_func == "Мойка автомобилей":
		room_func = "Автостоянка"
	if b_element.GetType().Name != "RevitLinkInstance":
		mat_name = doc.GetElement(b_element.GetTypeId()).get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString()#b_element.WallType.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsValueString()
		if "елезобетон" in mat_name:
			out = "АБН_Отделка стен железобетон"+"("+room_func+")"
			Create_Material(out)
		else:
			out = "АБН_Отделка стен кладка"+"("+room_func+")"
			Create_Material(out)
	else:
		out = "АБН_Отделка стен кладка"+"("+room_func+")"
		Create_Material(out)
	return out
	
def Create_Material(mat_name):
	if Material.IsNameUnique(doc,mat_name):
		mat = Material.Create(doc,mat_name)
		doc.GetElement(mat).Color = Autodesk.Revit.DB.Color(Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))), Byte.Parse(str(randint(0, 255))))
