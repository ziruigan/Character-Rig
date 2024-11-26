import maya.cmds as mc
import FingerRigTool as frt
import maya.api.OpenMaya as om
import rigging_utils as ru
import pose_library as pl
import importlib
importlib.reload(frt)
importlib.reload(pl)
importlib.reload(ru)
from functools import wraps

import math

FACS_HUB = "FACS_HUB"


def createBlendNode(control):
    blend_node = control.replace("Control", "BlendNode")

    blend_group = frt.create_zero_group(control, group_name=blend_node, group_type="transform")

    return blend_group


def getCorrespondingBlendNode(control):
    blend_node = control.replace("Control", "BlendNode")
    return blend_node

def getCorrespondingConstrainNode(control):
    constrain_node = control.replace("Control", "CON")
    return constrain_node


def getObjectLocalTransformation(object, world_matrix):
    inverse_ParentMatrix = mc.getAttr(f"{object}.parentInverseMatrix")
    localMatrix = om.MMatrix(world_matrix) * om.MMatrix(inverse_ParentMatrix)

    #decompose the local matrix to get the translation, rotation and scale
    translation, angles, scale = decomposeMatrix(localMatrix)
    return translation, angles, scale


def decomposeMatrix(matrix):
    """
    decompose transformation matrix and extract the translation/rotation/scale component
    Args:
        matrix (MMatrix): A transformation matrix (orthogonal matrix)

    Returns:
        decompsed element for translation, rotation and scale

    """
    transformationMatrix = om.MTransformationMatrix(matrix)
    translation = transformationMatrix.translation(om.MSpace.kWorld)
    rotation = transformationMatrix.rotation().asVector()
    eulerAngles = [rotation.x / math.pi * 180, rotation.y / math.pi * 180, rotation.z / math.pi * 180]
    scale = transformationMatrix.scale(om.MSpace.kObject)
    return translation, eulerAngles, scale


def zeroOutTransformation(node):
    mc.setAttr(f"{node}.translate", 0, 0, 0)
    mc.setAttr(f"{node}.rotate", 0, 0, 0)
    mc.setAttr(f"{node}.scale", 1, 1, 1)



def transferFromControlToBlendNode(control):
    """
        transfer the transformation information from the control to the corresponding blend node
        the transformation data for the control should be all zero
        Args:
            control (string) : the control need to be operated to transfer the transformation information

        Returns:
        """

    world_matrix_control = mc.xform(control, matrix=True, query=True, worldSpace=True)
    blend_node = getCorrespondingBlendNode(control)
    translation, rotation, scale = getObjectLocalTransformation(blend_node, world_matrix_control)

    mc.setAttr(f"{blend_node}.translate", *translation)
    mc.setAttr(f"{blend_node}.rotate", *rotation)
    mc.setAttr(f"{blend_node}.scale", *scale)

    zeroOutTransformation(control)


def storeTransformationBackToControl(control):
    controlWorldMatrix = mc.xform(control, matrix=True, query=True, worldSpace=True)
    # reset blendNode's transformation
    blendNode = getCorrespondingBlendNode(control)
    if mc.ls(blendNode):
        zeroOutTransformation(blendNode)

    constrainNode = getCorrespondingConstrainNode(control)
    if mc.ls(constrainNode):
        zeroOutTransformation(constrainNode)

    translation, rotation, scale = getObjectLocalTransformation(control, controlWorldMatrix)
    mc.setAttr(f"{control}.translate", *translation)
    mc.setAttr(f"{control}.rotate", *rotation)
    mc.setAttr(f"{control}.scale", *scale)



def undo_chunk(func):

    """
    wrap the function together for undo execution
    make sure to reevaluate values with following command line: mc.dgdirty(a=True)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        mc.undoInfo(openChunk=True)
        try:
            return func(*args, **kwargs)
        except:
            raise
        finally:
            mc.undoInfo(closeChunk=True)

    return wrapper

@undo_chunk
def addControlsToShape(controls, shape):
    """
            Create the shape if it doesn't exist in the FACS_HUB network node
            set driven key at the neutral position of the blend node
            Args:
                controls (list) : list of controls which would be contributing to a particular shape in FACS_HUB
                shape (string) : the FACS shape controlled by the controls in the list

            Returns:
            """
    driverAttr = f"{FACS_HUB}.{shape}"
    if mc.ls(driverAttr):
        connection = mc.listConnections(driverAttr, source=True, destination=False, connections=True, plugs=True)
        if connection:
            mc.disconnectAttr(connection[1], connection[0])
    if not mc.ls(driverAttr):
        mc.addAttr(FACS_HUB, longName=shape, attributeType='float', minValue=0.0, maxValue=1.0, defaultValue=0.0, keyable=True)
    mc.setAttr(driverAttr, 0)
    for control in controls:
        blendNode = getCorrespondingBlendNode(control)
        zeroOutTransformation(blendNode)
        for tfm in "trs":
            for axis in "xyz":
                drivenAttr = f"{blendNode}.{tfm}{axis}"
                mc.setDrivenKeyframe(drivenAttr, currentDriver=driverAttr, inTangentType="linear",
                                     outTangentType="linear")

    if mc.ls(driverAttr):
        connection = mc.listConnections(driverAttr, source=True, destination=False, connections=True, plugs=True)
        if connection:
            mc.connectAttr(connection[1], connection[0])

@undo_chunk
def bakeTransformationToShape(controls, shape):
    """
                after changing the controls in to good deforming condition,
                transfer the transformation information to blend node
                set driven key at the pose while the driver attribute is set at 1
                Args:
                    controls (list) : list of controls which would be contributing to a particular shape in FACS_HUB
                    shape (string) : the FACS shape controlled by the controls in the list

                Returns:
                """
    driverAttr = f"{FACS_HUB}.{shape}"
    if not mc.ls(driverAttr):
        mc.addAttr(FACS_HUB, longName=shape, attributeType='float', minValue=0.0, maxValue=1.0, defaultValue=0.0, keyable=True)
    mc.setAttr(driverAttr, 1)
    for control in controls:
        blendNode = getCorrespondingBlendNode(control)
        transferFromControlToBlendNode(control)
        for tfm in "trs":
            for axis in "xyz":
                drivenAttr = f"{blendNode}.{tfm}{axis}"
                mc.setDrivenKeyframe(drivenAttr, currentDriver=driverAttr, inTangentType="linear",
                                     outTangentType="linear")

@undo_chunk
def editShape(controls, shape):
    for control in controls:
        storeTransformationBackToControl(control)
    driverAttr = f"{FACS_HUB}.{shape}"
    #grab the connection and disconnect to be able to set the attribute
    connection = mc.listConnections(driverAttr, source=True, destination=False, connections=True, plugs=True)
    if connection:
        mc.disconnectAttr(connection[1], connection[0])
    mc.setAttr(driverAttr, 1)
    for control in controls:
        blendNode = getCorrespondingBlendNode(control)
        #clear out the old data
        zeroOutTransformation(blendNode)
        transferFromControlToBlendNode(control)
        for tfm in "trs":
            for axis in "xyz":
                drivenAttr = f"{blendNode}.{tfm}{axis}"
                mc.setDrivenKeyframe(drivenAttr, currentDriver=driverAttr, inTangentType="linear",
                                     outTangentType="linear")
    if connection:
        mc.connectAttr(connection[1], connection[0])


@undo_chunk
def createCorrectivePose(shape):
    if "Left" in shape:
        maskFaceControls(side="Left")
    elif "Right" in shape:
        maskFaceControls(side="Right")
    else:
        side="Center"
    driverAttr = f"{FACS_HUB}.{shape}"
    controls = getControlsFromFACSAttr(driverAttr)
    for control in controls:
        storeTransformationBackToControl(control)

    pose_data_target = pl.collect_pose_data(controls)

    resetAllControls()
    #get sub poses
    sub_poses = shape.split("_")
    connections = []
    for sub_pose in sub_poses:
        if sub_pose not in mc.listAttr(FACS_HUB, userDefined=True):
            raise RuntimeError(f"Failed to find {sub_pose} in registered poses")

        connection = mc.listConnections(f"{FACS_HUB}.{sub_pose}", source=True, destination=False, connections=True,
                                        plugs=True)
        connections.append(connection)
        if connection:
            mc.disconnectAttr(connection[1], connection[0])

    pose_data_orig = pl.collect_pose_data(controls)
    for sub_pose in sub_poses:
        mc.setAttr(f"{FACS_HUB}.{sub_pose}", 0.0)
    pl.apply_pose_data(pose_data_orig, space="world")

    for control in controls:
        deltas_translate = (om.MPoint(pose_data_target.get(control).get("localTrs")[0]) - om.MPoint(
            mc.getAttr(f"{control}.translate")[0]))
        deltas_rotate = (om.MPoint(pose_data_target.get(control).get("localTrs")[1]) - om.MPoint(
            mc.getAttr(f"{control}.rotate")[1]))

        mc.setAttr(f"{control}.translate", *deltas_translate)
        mc.setAttr(f"{control}.rotate", *deltas_rotate)

    editShape(controls, shape)
    for connection in connections:
        mc.connectAttr(connection[1], connection[0])

    #reevaluate all plugs
    mc.dgdirty(allPlugs=True)

    mix_node = mc.createNode('multiplyDivide', name= shape + "_corrective_blend")

    #multiply
    mc.setAttr(f"{mix_node}.operation", 1)

    mc.connectAttr(f"{FACS_HUB}.{sub_poses[0]}", f"{mix_node}.input1X")
    mc.connectAttr(f"{FACS_HUB}.{sub_poses[1]}", f"{mix_node}.input2X")

    mc.connectAttr(f"{mix_node}.outputX", f"{FACS_HUB}.{shape}")



def createSliderGroup(topGroup, shapeName):
    groupName = shapeName + "SliderGroup1"
    groupName = mc.rename(topGroup, groupName)
    arrowShape = mc.listRelatives(groupName, type="mesh", allDescendents=True, fullPath=True)
    arrowTransform = mc.listRelatives(arrowShape, parent=True, fullPath=True)
    arrowName = shapeName + "Slider"
    mc.rename(arrowTransform, arrowName)
    if shapeName.startswith("Left"):
        shapeName = shapeName[len("Left"):]
    elif shapeName.startswith("Right"):
        shapeName = shapeName[len("Right"):]

    mc.aliasAttr(shapeName, f"{arrowName}.translateZ")


def getControlsFromFACSAttr(facsAttr):
    blendNodes = set()
    outputs = mc.listConnections(facsAttr, source=False, destination=True, type="animCurve")
    for animCurve in outputs:
        dst = mc.listConnections(animCurve, source=False, destination=True)
        for d in dst:
            if mc.objectType(d) == "transform":
                blendNodes.add(d)
            elif mc.objectType(d) == "blendWeighted":
                blendNodes.add(mc.listConnections(d, source=False, destination=True, type="transform")[0])

    blendNodes = list(blendNodes)
    controls = []
    for blendNode in blendNodes:
        controls.append(mc.listRelatives(blendNode, children=True, type="transform")[0])
    return controls

@undo_chunk
def assumePose(poseName):
    driverAttr = f"{FACS_HUB}.{poseName}"
    connection = mc.listConnections(driverAttr, source=True, destination=False, connections=True, plugs=True)
    if connection:
        mc.disconnectAttr(connection[1], connection[0])
    mc.setAttr(driverAttr, 1)
    controls = getControlsFromFACSAttr(driverAttr)
    for ctrl in controls:
        storeTransformationBackToControl(ctrl)
    mc.setAttr(driverAttr, 0)
    if connection:
        mc.connectAttr(connection[1], connection[0])


def getFaceControls():
    controls = mc.ls("*.controlType", objectsOnly=True)
    #return if is Face control
    return [control for control in controls if mc.getAttr(f"{control}.controlType") == 3]

@undo_chunk
def resetAllControls():
    faceControls = getFaceControls()
    for control in faceControls:
        zeroOutTransformation(control)

@undo_chunk
def mirrorPose(side="Left"):
    #driverAttr = f"{FACS_HUB}.{poseName}"
    #controls = getControlsFromFACSAttr(driverAttr)
    controls = getFaceControls()
    pl.mirror_pose(controls, mirror_function="orientation", side=side)


def mirrorJoint(jnt, geo):
    mc.xform(jnt, translation=True, worldSpace=True, query=True)
    u, v = ru.getClosestUvAtPoint(jnt, geo, uvSet="map1")
    mirrorPoint = ru.getPointAtUv([1-u, v], geo, uvSet="map1")
    mirrorJnt = jnt.replace("Left", "Right")
    mc.xform(mirrorJnt, translation=(mirrorPoint.x, mirrorPoint.y, mirrorPoint.z), worldSpace=True)


def createFaceControls(faceJoint):
    zero_group, control = ru.create_control_on_node(faceJoint, shape_name="eyeControl")
    ru.addFlagsToControl(control)
    mc.setAttr(f"{control}.controlType", 3)

    if "Left" in faceJoint:
        mc.setAttr(f"{control}.controlLocation", 0)
    elif "Right" in faceJoint:
        mc.setAttr(f"{control}.controlLocation", 1)
    else:
        mc.setAttr(f"{control}.controlLocation", 2)

    blendNode = createBlendNode(control)
    conNodeName = control.replace("Control", "CON")
    conNode = ru.create_zero_group(blendNode, group_name=conNodeName, group_type="transform")
    return control


def maskFaceControls(side="Left"):
    sideIndex = ["Left", "Right", "Center"].index(side)
    allFaceControls = getFaceControls()
    for faceControl in allFaceControls:
        if mc.getAttr(f"{faceControl}.controlLocation") == (1 - sideIndex):
            zeroOutTransformation(faceControl)
        elif mc.getAttr(f"{faceControl}.controlLocation") == 2:
            # half the value as blend
            translation = mc.getAttr(f"{faceControl}.translate")[0]
            rotation = mc.getAttr(f"{faceControl}.rotate")[0]
            mc.setAttr(f"{faceControl}.translate", translation[0]/2, translation[1]/2, translation[2]/2)
            mc.setAttr(f"{faceControl}.rotate", rotation[0]/2, rotation[1]/2, rotation[2]/2)

# alternative way to use NurbsSurface to make the controls follow
def wrapControls(node, surf):
    locName = node.replace("Control", "LOC")
    loc = mc.spaceLocator(name=locName)
    mc.matchTransform(loc, node)

    mc.select(surf, loc)
    mc.UVPin()
    mc.parentConstraint(loc, node, maintainOffset=True)