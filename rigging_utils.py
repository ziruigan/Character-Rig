import maya.cmds as mc
import maya.mel as mel
import maya.api.OpenMaya as om
import re


def add_shape_between_string_and_suffix(input_string, shape="Shape"):
    # Use regular expression to find the suffix number
    match = re.search(r'(\d+)$', input_string)

    if match:
        # Extract the suffix number
        suffix_number = match.group(0)
        # Insert the shape before the suffix number
        modified_string = input_string[:match.start()] + shape + suffix_number + input_string[match.end():]
        return modified_string
    else:
        # No suffix number found, just append the shape to the input string
        return input_string + shape


def get_joint_chain(start_joint, end_joint):
    """
    Finds the joint chain between a start joint and an end joint.

    Args:
        startJoint(str): the name of the start joint.
        endJoint(str): the name of the end joint.

    Returns:
        A list of joint names, from the start joint to the end joint.
    """
    children_joints = mc.listRelatives(start_joint, allDescendents=True, type='joint')

    if end_joint not in children_joints:
        return

    joint_chain = [end_joint]
    parentJoint = mc.listRelatives(end_joint, parent=True, type='joint')[0]
    joint_chain.append(parentJoint)
    while parentJoint != start_joint:
        parentJoint = mc.listRelatives(parentJoint, parent=True, type='joint')[0]
        joint_chain.append(parentJoint)

    joint_chain.reverse()
    return joint_chain


def create_zero_group(node, group_name=None, group_type="transform"):
    if not group_name:
        group_name = node.replace("Control", "ControlGroup")

    if group_type == "transform":
        group = mc.group(empty=True, world=True, name=group_name)
    else:
        mc.select(clear=True)
        group = mc.joint(name=group_name)
        mc.setAttr("{0}.drawStyle".format(group), 2)

    mc.matchTransform(group, node)
    node_parent = mc.listRelatives(node, parent=True)
    if node_parent:
        mc.parent(group, node_parent)
    mc.parent(node, group)
    return group


def create_space_switch(node, spaces=None):
    space_switch_group = node + "_SpaceSwitchGroup1"
    space_switch_group = create_zero_group(node, space_switch_group)
    if not spaces:
        spaces.append("mainControl1")
        spaces.append("rootControl1")

    for space in spaces:
        mc.group(em=True, w=True, name=node + space)


def get_shape(obj, shapeTypes=None, longNames=False):
    if shapeTypes is None:
        shapeTypes = ['mesh', 'nurbsCurve', 'nurbsSurface']

    ntype = mc.objectType(obj)
    if ntype in shapeTypes:
        return obj

    shapes = mc.listRelatives(obj, shapes=True, noIntermediate=True, f=longNames)
    if shapes and ntype == 'transform' and mc.objectType(shapes[0]) in shapeTypes:
        return shapes[0]

    return None


def create_control(shape_name="octagonPoint", control_name="FKControl1"):
    control = mel.eval('createControlShapes("' + shape_name + '");')
    control_transform = create_zero_group(control, group_name=control_name, group_type="joint")
    control_shape = get_shape(control)
    mc.parent(control_shape, control_transform, relative=True, shape=True)
    mc.delete(control)
    mc.rename(control_shape, add_shape_between_string_and_suffix(control_name))
    mc.setAttr("{0}.drawStyle".format(control_transform), 2)
    return control_transform


def mirrorControlShapes(side="Left"):
    """
    Mirrors control shapes. Default parameter is "Left" for left to right.
    Provide "Right" as parameter for mirring right to left.
    """
    if side == "Left":
        otherSide = "Right"
    else:
        otherSide = "Left"

    selectedNodes = mc.ls(sl=True, type='transform')
    if not len(selectedNodes):
        selectedNodes = mc.ls(side + '*Control*', type='transform')

    for s in selectedNodes:
        shapes = mc.listRelatives(s, shapes=True)
        if shapes:
            leftShape = shapes[0]
            rightShape = mc.ls(str(leftShape).replace(side, otherSide))
            if len(rightShape):
                rightShape = rightShape[0]
            else:
                continue

            spans = mc.getAttr(f'{leftShape}.spans')
            degrees = mc.getAttr(f'{leftShape}.degree')
            print(leftShape)
            numCVs = spans + degrees
            print(spans, degrees)
            print(numCVs)
            for i in range(numCVs):
                cv = mc.pointPosition(f'{leftShape}.cv[{i}]', local=True)
                cv[0] = cv[0] * -1
                mc.xform(f'{rightShape}.cv[{i}]', objectSpace=True, translation=cv)


def scaleControlShape(controls=None, scaleValue=None):
    ''' Takes a list of controls and a float scale value.
        Scales the cvs and vtxs of a controls shapes.
    '''

    if not controls:
        controls = mc.ls(selection=True)

    if scaleValue is None:
        scaleValue = .6

    if isinstance(controls, str) or isinstance(controls, str):
        controls = [controls]

    originalSelection = mc.ls(selection=True)
    for control in controls:
        shapes = mc.listRelatives(control, children=True, shapes=True, path=True) or []

        for shape in shapes:
            cvs = mc.ls(shape + '.cv[:]', flatten=True)
            vtx = mc.ls(shape + '.vtx[:]', flatten=True)

            mc.select(cvs + vtx, replace=True)

            mc.scale(scaleValue, scaleValue, scaleValue, relative=True)

    mc.select(originalSelection, replace=True)


def exportControlShape():
    pass


def create_control_on_node(node, shape_name="octagonPoint"):
    str_number = node[-1]
    control_name = node.replace("JO", "")[: -1] + "Control" + str_number
    control = create_control(shape_name, control_name=control_name)
    zero_group = create_zero_group(control, group_type="joint")
    mc.matchTransform(zero_group, node)
    return zero_group, control


def create_fkchain(start_joint, end_joint):
    joint_chain = get_joint_chain(start_joint, end_joint)
    fk_control = None
    fk_controls = []
    for joint in joint_chain:
        temp_group, temp_control = create_control_on_node(joint)

        mc.parentConstraint(temp_control, joint, maintainOffset=False, weight=1)

        if fk_control:
            mc.parent(temp_group, fk_control)
        fk_control = temp_control
        fk_controls.append(fk_control)

    return fk_controls


def mirrorNrubsSurface(side="Left"):
    """
    Mirrors control shapes. Default parameter is "Left" for left to right.
    Provide "Right" as parameter for mirring right to left.
    """
    if side == "Left":
        otherSide = "Right"
    else:
        otherSide = "Left"

    selectedNodes = mc.ls(sl=True, type='transform')

    for s in selectedNodes:
        shapes = mc.listRelatives(s, shapes=True)
        if shapes:
            leftShape = shapes[0]
            rightShape = mc.ls(str(leftShape).replace(side, otherSide))
            if len(rightShape):
                rightShape = rightShape[0]
            else:
                continue

            spans = mc.getAttr(f'{leftShape}.spansUV')[0]
            degrees = mc.getAttr(f'{leftShape}.degreeUV')[0]
            numCVs_U = spans[0] + degrees[0]
            numCVs_V = spans[1] + degrees[1]
            for u in range(numCVs_U):
                for v in range(numCVs_V):
                    cv = mc.pointPosition(f'{leftShape}.cv[{u}][{v}]', local=True)
                    print(f'{leftShape}.cv[{u}{v}]')
                    print(f'{rightShape}.cv[{numCVs_U - u - 1}{v}]')
                    cv[0] = cv[0] * -1
                    mc.xform(f'{rightShape}.cv[{numCVs_U - u - 1}][{v}]', worldSpace=True, translation=cv)


def mirrorNurbsSurfaceInOne():
    #mirror within one single NurbsSurface
    selectedNodes = mc.ls(sl=True, type='transform')

    for s in selectedNodes:
        shapes = mc.listRelatives(s, shapes=True)
        if shapes:
            Shape = shapes[0]
            spans = mc.getAttr(f'{Shape}.spansUV')[0]
            degrees = mc.getAttr(f'{Shape}.degreeUV')[0]
            numCVs_U = spans[0] + degrees[0]
            numCVs_V = spans[1] + degrees[1]
            num_midpoint = numCVs_U / 2
            for u in range(int(num_midpoint)):
                for v in range(numCVs_V):
                    cv = mc.pointPosition(f'{Shape}.cv[{u}][{v}]', local=True)
                    print(f'{Shape}.cv[{u}{v}]')
                    print(f'{Shape}.cv[{numCVs_U- 1}{v}]')
                    cv[0] = cv[0] * -1
                    mc.xform(f'{Shape}.cv[{numCVs_U - 1}][{v}]', objectSpace=True, translation=cv)

def addFlagsToControl(control):
    if not mc.attributeQuery("controlLocation", node=control, exists=True):
        mc.addAttr(control, longName="controlLocation", attributeType="enum", enumName="Left:Right:Center",
                   keyable=False)
    if not mc.attributeQuery("controlType", node=control, exists=True):
        mc.addAttr(control, longName="controlType", attributeType="enum",
                         enumName="UpperBody:LowerBody:Main:Face:Hand:Slider",keyable=False)



def getClosestUVAtPoint(point, geometry, uvSet=None):
    point = om.MPoint(point)
    mSelectionList = om.MSelectionList()
    mSelectionList.add(geometry)
    mDagPath = mselection.getDagPath(0)

    if mDagPath.apiType() == om.MFn.kMesh:
        mfnMesh = om.MFnMesh(mDagPath)
        u, v, polyID = mfnMesh.getUVAtPoint(point, space=om.MSpace.kWorld, uvSet=uvSet)
        return u, v

    elif nDagPath.apiType() == om.MFn.kNurbSurface:
        mfnNurbs = om.MFnNurbsSurface(mDagPath)
        point, u, v = mfnNurbs.closestPoint(point, space=om.MSpace.kWorld)
        return u, v

    else:
        raise TypeError(f"Unsupported geometry type: {geometry}")


def getPointAtUv(uv, mesh, uvSet=None):
    mSelectionList = om.MSelectionList()
    mSelectionList.add(mesh)
    mDagPath = mselection.getDagPath(0)
    mItMeshPolygon = om.MItMeshPolygon(mDagPath)

    while not mItMeshPolygon.isDone():
        try:
            point = mItMeshPolygon.getPointAtUV(uv, space=om.MSpace.kWorld, uvSet=uvSet)
        except:
            pass
        mItMeshPolygon.next()

    return point

def mirrorJoint(jnt, geo):
    mc.xform(jnt, translation=True, worldSpace=True, query=True)
    u, v = getClosestUvAtPoint(jnt, geo, uvSet="map1")
    mirrorPoint = getPointAtUv([1-u, v], geo, uvSet="map1")
    mirrorJoint = jnt.replace("Left", "Right")
    mc.xform(mirrorJoint, translation=(mirrorPoint.x, mirrorPoint.y, mirrorPoint.z), worldSpace=True)





