import maya.cmds as mc
import maya.api.OpenMaya as om
import math

def createJoint(jointName, parent=None, radius=1.0):
    mc.select(clear=True)
    jnt = mc.joint(name=jointName)
    mc.setAttr(f"{jnt}.radius", radius)
    if parent:
        mc.parent(jnt, parent)
        mc.setAttr(f"{jnt}.t", 0, 0, 0)
        mc.setAttr(f"{jnt}.r", 0, 0, 0)
        mc.setAttr(f"{jnt}.jo", 0, 0, 0)

    return jnt

def createSpaceLocator(scalaValue, **kwargs):
    loc = mc.spaceLocator(**kwargs)[0]
    for axis in 'XYZ':
        mc.setAttr(f"{loc}.localScale{axis}", scalaValue)
    return loc


def offsetLoc(loc, begin, end, ratio, offset=0.0):

    endPos = mc.xform(end, translation=True, query=True, worldSpace=True)
    beginPos = mc.xform(begin, translation=True, query=True, worldSpace=True)

    newPos = om.MPoint(beginPos) + ratio * (om.MPoint(endPos) - om.MPoint(beginPos))

    worldMatrix = om.MMatrix(mc.xform(begin, matrix=True, query=True, worldSpace=True))
    upVec = om.MVector([worldMatrix.getElement(2,0), worldMatrix.getElement(2,1), worldMatrix.getElement(2,2)])

    newPos = newPos + upVec * offset
    mc.xform(loc, translation=(newPos.x, newPos.y, newPos.z), worldSpace=True)


class MuscleJoint(object):

    def __init__(self, muscleName, muscleLength, compressionFactor, stretchFacator,
                 stretchOffset=None, compressionOffset=None):

        self.muscleName = muscleName
        self.muscleLength = muscleLength
        self.compressionFactor = compressionFactor
        self.stretchFactor = stretchFacator
        self.stretchOffset = stretchOffset
        self.compressionOffset = compressionOffset
        self.allJoints = []
        self.originAttachObj = None
        self.insertionAttachObj = None

        self.create()
        self.edit()


    def create(self):

        self.muscleOrigin = createJoint(f"{self.muscleName}.muscleOrigin")

        self.muscleInsertion = createJoint(f"{self.muscleName}.muscleInsertion")

        mc.setAttr(f"{self.muscleInsertion}.tx", 0)

        mc.delete(mc.aimConstraint(self.muscleInsertion, self.muscleOrigin, aimVector=(0, 1, 0),
                                   upVector=(1, 0, 0), worldUpType="scene"))

        self.muscleBase = createJoint(f"{self.muscleName}.muscleBase", radius=0.5)
        mc.pointConstraint(self.muscleOrigin, self.muscleBase, maintainOffset=False)

        self.mainAimConstrain = mc.aimConstraint(self.muscleInsertion, self.muscleBase,
                                                 aimVector=(0, 1, 0),
                                                 upVector=(1, 0, 0),
                                                 worldUpType="objectrotation",
                                                 worldUpObject=self.muscleOrigin,
                                                 worldUpVector=(1, 0, 0))

        self.muscleTip = createJoint(f"{self.muscleName}.muscleTip", parent=self.muscleBase, radius=0.5)
        mc.pointConstraint(self.muscleInsertion, self.muscleTip, maintainOffset=False)

        self.muscleDriver = createJoint(f"{self.muscleName}.muscleDriver", parent=self.muscleBase, radius=0.5)
        self.mainPointConstraint = mc.pointConstraint(self.muscleBase, self.muscleTip, self.muscleDriver,
                                                      maintainOffset=False)

        mc.parent(self.muscleBase, self.muscleOrigin)
        self.muscleOffset = createJoint(f"{self.muscleName}.muscleOffset", parent=self.muscleDriver, radius=0.75)
        self.JOmuscle = createJoint(f"{self.muscleName}.JOmuscle", parent=self.muscleOffset)
        mc.setAttr(f"{self.JOmuscle}.segmentScaleCompensate", 0)

        self.allJoints.extend([self.muscleOrigin, self.muscleBase, self.muscleDriver, self.muscleOffset,
                               self.JOmuscle, self.muscleTip, self.muscleInsertion])

        self.addSDK()



    def addSDK(self):
        xzSquashScale = math.sqrt(1.0/ self.compressionFactor)
        xzStretchScale = math.sqrt(1.0/ self.stretchFactor)

        if self.stretchOffset is None:
            self.stretchOffset = [0.0, 0.0, 0.0]
        if self.compressionOffset is None:
            self.compressionOffset = [0.0, 0.0, 0.0]

        restLength = mc.getAttr(f"{self.muscleTip}.translateY")

        for index, axis in enumerate("XYZ"):
            #in natural state
            mc.setAttr(f"{self.JOmuscle}.scale{axis}", 1.0)
            mc.setAttr(f"{self.JOmuscle}.translate{axis}", 0.0)
            mc.setDrivenKeyframe(f"{self.JOmuscle}.scale{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")

            mc.setDrivenKeyframe(f"{self.JOmuscle}.translate{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")

            #in stretch
            mc.setAttr(f"{self.muscleTip}.translateY", restLength * self.stretchFactor)

            if axis == "Y":
                mc.setAttr(f"{self.JOmuscle}.scale{axis}", self.stretchFactor)
            else:
                mc.setAttr(f"{self.JOmuscle}.scale{axis}", xzStretchScale)
                mc.setAttr(f"{self.JOmuscle}.translate{axis}", self.stretchOffset[index])

            mc.setDrivenKeyframe(f"{self.JOmuscle}.scale{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")

            mc.setDrivenKeyframe(f"{self.JOmuscle}.translate{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")


            #in compression
            mc.setAttr(f"{self.muscleTip}.translateY", restLength * self.compressionFactor)

            if axis == "Y":
                mc.setAttr(f"{self.JOmuscle}.scale{axis}", self.compressionFactor)
            else:
                mc.setAttr(f"{self.JOmuscle}.scale{axis}", xzSquashScale)
                mc.setAttr(f"{self.JOmuscle}.translate{axis}", self.compressionOffset[index])

            mc.setDrivenKeyframe(f"{self.JOmuscle}.scale{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")
            mc.setDrivenKeyframe(f"{self.JOmuscle}.translate{axis}", currentDriver=f"{self.muscleTip}.translateY",
                                 inTangentType="linear",
                                 outTangentType="linear")

            mc.setAttr(f"{self.muscleTip}.translateY", restLength)

    def edit(self):


        mc.setAttr(f"{self.muscleOrigin}.overrideEnabled",1)
        mc.setAttr(f"{self.muscleOrigin}.overrideDisplayType", 1)
        mc.setAttr(f"{self.muscleInsertion}.overrideEnabled", 1)
        mc.setAttr(f"{self.muscleInsertion}.overrideDisplayType", 1)

        self.pointConstraint_tmp = []
        self.originLoc = createSpaceLocator(0.25, name=f"{self.muscleName}.muscleOrigin_loc")
        if self.originAttachObj:
            mc.parent(self.originLoc, self.originAttachObj)
        mc.delete(mc.pointConstraint(self.muscleOrigin, self.originLoc, maintainOffset=False))
        self.pointConstraint_tmp.append(mc.pointConstraint(self.originLoc, self.muscleOrigin, maintainOffset=False)[0])
        self.insertionLoc = createSpaceLocator(0.25, name=f"{self.muscleName}.muscleInsertion_loc")
        if self.insertionAttachObj:
            mc.parent(self.insertionLoc, self.insertionAttachObj)

        # make locator move along the muscle more easily
        mc.aimConstraint(self.insertionLoc, self.originLoc, aimVector=(0, 1, 0),
                         upVector=(1, 0, 0), worldUpType="scene", offset=(0, 0, 0))
        mc.aimConstraint(self.originLoc, self.insertionLoc, aimVector=(0, -1, 0),
                         upVector=(1, 0, 0), worldUpType="scene", offset=(0, 0, 0))

        mc.delete(mc.pointConstraint(self.muscleInsertion, self.insertionLoc, maintainOffset=False))
        self.pointConstraint_tmp.append(mc.pointConstraint(self.insertionLoc, self.muscleInsertion, maintainOffset=False)[0])

        driverGrp = mc.group(name=f"{self.muscleName}.muscleCenter_grp", empty=True)
        self.centerLoc = createSpaceLocator(0.25, name=f"{self.muscleName}.muscleCenter_loc")
        mc.parent(self.centerLoc, driverGrp)
        mc.delete(mc.pointConstraint(self.muscleDriver, driverGrp, maintainOffset=False))
        mc.parent(driverGrp, self.originLoc)
        mc.pointConstraint(self.originLoc, self.insertionLoc, driverGrp, maintainOffset=True)
        mc.setAttr(f"{driverGrp}.r", 0, 0, 0)
        mc.delete(self.mainPointConstraint)
        self.pointConstraint_tmp.append(mc.pointConstraint(self.centerLoc, self.muscleDriver, maintainOffset=False)[0])


    def update(self):
        for pointConstraint_temp in self.pointConstraint_tmp:
            if mc.objExists(pointConstraint_temp):
                mc.delete(pointConstraint_temp)

        for loc in [self.originLoc, self.insertionLoc, self.centerLoc]:
            if mc.objExists(loc):
                mc.delete(loc)

        mc.setAttr(f"{self.muscleOrigin}.overrideEnabled", 0)
        mc.setAttr(f"{self.muscleOrigin}.overrideDisplayType", 0)
        mc.setAttr(f"{self.muscleInsertion}.overrideEnabled", 0)
        mc.setAttr(f"{self.muscleInsertion}.overrideDisplayType", 0)

        baseWorldMatrix = mc.xform(self.muscleBase, matrix=True, query=True, worldSpace=True)

        mc.delete(self.mainAimConstrain)

        self.mainPointConstraint = mc.pointConstraint(self.muscleBase, self.muscleTip, self.muscleDriver,
                                                      maintainOffset=True)[0]

        mc.delete(mc.aimConstraint(self.muscleInsertion, self.muscleOrigin, aimVector=(0, 1, 0),
                                      upVector=(1, 0, 0), worldUpType="scene", offset=(0, 0, 0)))

        mc.xform(self.muscleOrigin, matrix=baseWorldMatrix, worldSpace=True)
        mc.xform(self.muscleBase, matrix=baseWorldMatrix, worldSpace=True)


        mc.mainAimConstraint = mc.aimConstraint(self.muscleInsertion, self.muscleBase,
                                                 aimVector=(0, 1, 0),
                                                 upVector=(1, 0, 0),
                                                 worldUpType="objectrotation",
                                                 worldUpObject=self.muscleOrigin,
                                                 worldUpVector=(1, 0, 0))[0]

        animCurveNodes = mc.ls(mc.listConnections(self.JOmuscle, s=True, d=False), type=("animCurveUU", "animCurveUL"))
        mc.delete(animCurveNodes)
        self.addSDK()

        self.createDataNode()

    def createDataNode(self):
        dataNodeName = self.muscleName + "_dataNode"
        if mc.ls(dataNodeName):
            mc.delete(dataNodeName)

        dataNode = mc.createNode("network", name=dataNodeName)
        # create attributes
        mc.addAttr(dataNode, longName="name", niceName="Name", dataType="string")
        mc.addAttr(dataNode, longName="type", niceName="Type", dataType="string")
        mc.addAttr(dataNode, longName="restLength", niceName="Muscle Length", attributeType="double")
        mc.addAttr(dataNode, longName="compressionFactor", niceName="Compression Factor", attributeType="double")
        mc.addAttr(dataNode, longName="stretchFactor", niceName="Stretch Factor", attributeType="double")
        mc.addAttr(dataNode, longName="compressionOffset", niceName="Compression Offset", attributeType="float3")
        mc.addAttr(dataNode, longName="compressionOffsetX", attributeType="float", parent="compressionOffset")
        mc.addAttr(dataNode, longName="compressionOffsetY", attributeType="float", parent="compressionOffset")
        mc.addAttr(dataNode, longName="compressionOffsetZ", attributeType="float", parent="compressionOffset")
        mc.addAttr(dataNode, longName="stretchOffset", niceName="Stretch Offset", attributeType="float3")
        mc.addAttr(dataNode, longName="stretchOffsetX", attributeType="float", parent="stretchOffset")
        mc.addAttr(dataNode, longName="stretchOffsetY", attributeType="float", parent="stretchOffset")
        mc.addAttr(dataNode, longName="stretchOffsetZ", attributeType="float", parent="stretchOffset")
        # assign attributes
        mc.setAttr(f"{dataNode}.name", self.muscleName, type="string")
        mc.setAttr(f"{dataNode}.type", "muscleJointGroup", type="string")
        mc.setAttr(f"{dataNode}.restLength", self.muscleLength)
        mc.setAttr(f"{dataNode}.compressionFactor", self.compressionFactor)
        mc.setAttr(f"{dataNode}.stretchFactor", self.stretchFactor)
        if self.compressionOffset is None:
            compressionOffset = [0, 0, 0]
        else:
            compressionOffset = self.compressionOffset
        mc.setAttr(f"{dataNode}.compressionOffset", *compressionOffset)

        if self.stretchOffset is None:
            stretchOffset = [0, 0, 0]
        else:
            stretchOffset = self.stretchOffset

        mc.setAttr(f"{dataNode}.stretchOffset", *stretchOffset)
        # muscle attach obj
        mc.addAttr(dataNode, longName="originAttachObj", niceName="Origin Attach Obj", attributeType="message")
        # muscle insertion obj
        mc.addAttr(dataNode, longName="insertionAttachObj", niceName="Insertion Attach Obj", attributeType="message")

        # muscle origin
        mc.addAttr(dataNode, longName="muscleOrigin", niceName="Muscle Origin", attributeType="message")
        # muscle insertion
        mc.addAttr(dataNode, longName="muscleInsertion", niceName="Muscle Insertion", attributeType="message")
        # muscle driver
        mc.addAttr(dataNode, longName="muscleDriver", niceName="Muscle Insertion", attributeType="message")
        # muscle base
        mc.addAttr(dataNode, longName="muscleBase", niceName="Muscle Base", attributeType="message")
        # muscle tip
        mc.addAttr(dataNode, longName="muscleTip", niceName="Muscle Tip", attributeType="message")
        # JO muscle
        mc.addAttr(dataNode, longName="JOMuscle", niceName="JOMuscle", attributeType="message")
        # main point constraint
        mc.addAttr(dataNode, longName="mainPtConst", niceName="Main PointConstraint", attributeType="message")
        # main aim constraint
        mc.addAttr(dataNode, longName="mainAimConst", niceName="Main AimConstraint", attributeType="message")

        dataParentAttr = f"{self.muscleName}_dataParent"
        # connect
        if not mc.attributeQuery(dataParentAttr, node=self.insertionAttachObj, exists=True):
            mc.addAttr(self.insertionAttachObj, longName=dataParentAttr, niceName=dataParentAttr,
                       attributeType="message")
        mc.connectAttr(f"{dataNode}.insertionAttachObj", f"{self.insertionAttachObj}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.originAttachObj, exists=True):
            mc.addAttr(self.originAttachObj, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.originAttachObj", f"{self.originAttachObj}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.muscleOrigin, exists=True):
            mc.addAttr(self.muscleOrigin, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.muscleOrigin", f"{self.muscleOrigin}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.muscleInsertion, exists=True):
            mc.addAttr(self.muscleInsertion, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.muscleInsertion", f"{self.muscleInsertion}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.muscleDriver, exists=True):
            mc.addAttr(self.muscleDriver, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.muscleDriver", f"{self.muscleDriver}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.muscleBase, exists=True):
            mc.addAttr(self.muscleBase, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.muscleBase", f"{self.muscleBase}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.muscleTip, exists=True):
            mc.addAttr(self.muscleTip, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.muscleTip", f"{self.muscleTip}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.JOmuscle, exists=True):
            mc.addAttr(self.JOmuscle, longName=dataParentAttr, niceName=dataParentAttr, attributeType="message")
        mc.connectAttr(f"{dataNode}.JOMuscle", f"{self.JOmuscle}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.mainPointConstraint, exists=True):
            mc.addAttr(self.mainPointConstraint, longName=dataParentAttr, niceName=dataParentAttr,
                       attributeType="message")
        mc.connectAttr(f"{dataNode}.mainPtConst", f"{self.mainPointConstraint}.{dataParentAttr}")

        if not mc.attributeQuery(dataParentAttr, node=self.mainAimConstraint, exists=True):
            mc.addAttr(self.mainAimConstraint, longName=dataParentAttr, niceName=dataParentAttr,
                       attributeType="message")
        mc.connectAttr(f"{dataNode}.mainAimConst", f"{self.mainAimConstraint}.{dataParentAttr}")

    @classmethod
    def getMuscleObjFromDataNode(cls, dataNode):
        muscleName = mc.getAttr(f"{dataNode}.name")
        muscleLength = mc.getAttr(f"{dataNode}.restLength")
        compressionFactor = mc.getAttr(f"{dataNode}.compressionFactor")
        stretchFactor = mc.getAttr(f"{dataNode}.stretchFactor")
        compressionOffset = mc.getAttr(f"{dataNode}.compressionOffset")[0]
        stretchOffset = mc.getAttr(f"{dataNode}.stretchOffset")[0]
        muscleOrigin = mc.listConnections(f"{dataNode}.muscleOrigin", destination=True, source=False)[0]
        muscleInsertion = mc.listConnections(f"{dataNode}.muscleInsertion", destination=True, source=False)[0]
        muscleDriver = mc.listConnections(f"{dataNode}.muscleDriver", destination=True, source=False)[0]
        muscleBase = mc.listConnections(f"{dataNode}.muscleBase", destination=True, source=False)[0]
        muscleTip = mc.listConnections(f"{dataNode}.muscleTip", destination=True, source=False)[0]
        JOmuscle = mc.listConnections(f"{dataNode}.JOMuscle", destination=True, source=False)[0]

        originAttachObj = mc.listConnections(f"{dataNode}.originAttachObj", destination=True, source=False)[0]
        insertionAttachObj = mc.listConnections(f"{dataNode}.insertionAttachObj", destination=True, source=False)[0]

        mainPtConst = mc.listConnections(f"{dataNode}.mainPtConst", destination=True, source=False)[0]
        mainAimConst = mc.listConnections(f"{dataNode}.mainAimConst", destination=True, source=False)[0]

        muscleObj = cls(muscleName, muscleLength, compressionFactor, stretchFactor, compressionOffset, stretchOffset)
        muscleObj.muscleOrigin = muscleOrigin
        muscleObj.muscleInsertion = muscleInsertion
        muscleObj.originAttachObj = originAttachObj
        muscleObj.insertionAttachObj = insertionAttachObj
        muscleObj.muscleDriver = muscleDriver
        muscleObj.muscleBase = muscleBase
        muscleObj.muscleTip = muscleTip
        muscleObj.JOmuscle = JOmuscle

        muscleObj.mainAimConstraint = mainAimConst
        muscleObj.mainPointConstraint = mainPtConst
        return muscleObj

    @classmethod
    def createFromAttachObjs(cls, muscleName, originAttachObj, insertionAttachObj, compressionFactor=0.5,
                             stretchFactor=1.5, compressionOffset=None, stretchOffset=None):

        originAttachPos = om.MVector(mc.xform(originAttachObj, translation=True, worldSpace=True, query=True))
        insertionAttachPos = om.MVector(mc.xform(insertionAttachObj, translation=True, worldSpace=True, query=True))
        muscleLength = om.MVector((insertionAttachPos - originAttachPos)).length()
        muscleJointGroup = cls(muscleName, muscleLength, compressionFactor, stretchFactor, compressionOffset,
                               stretchOffset)
        muscleJointGroup.originAttachObj = originAttachObj
        muscleJointGroup.insertionAttachObj = insertionAttachObj

        mc.matchTransform(muscleJointGroup.originLoc, originAttachObj)
        mc.matchTransform(muscleJointGroup.insertionLoc, insertionAttachObj)

        mc.parent(muscleJointGroup.muscleOrigin, originAttachObj)
        mc.parent(muscleJointGroup.muscleInsertion, insertionAttachObj)
        mc.parent(muscleJointGroup.originLoc, originAttachObj)
        mc.parent(muscleJointGroup.insertionLoc, insertionAttachObj)
        return muscleJointGroup



    def delete(self):
        self.update()
        if mc.objExists(self.muscleOrigin):
            mc.delete(self.muscleOrigin)

        if mc.objExists(self.muscleInsertion):
            mc.delete(self.muscleInsertion)

    def serialize(self):
        pass


def mirror(muscleJointGroup, muscleOriginAttachObj, muscleInsertionAttachObj, mirrorAxis="x"):

    if not isinstance(muscleJointGroup, MuscleJoint):
       return

    originPos = om.MVector(mc.xform(muscleJointGroup.muscleOrigin, translation=True, worldSpace=True, query=True))
    insertionPos = om.MVector(mc.xform(muscleJointGroup.muscleInsertion, translation=True, worldSpace=True, query=True))
    centerPos = om.MVector(mc.xform(muscleJointGroup.muscleDriver, translation=True, worldSpace=True, query=True))

    if mirrorAxis == "x":
        mirrorOriginPos = om.MVector(-originPos.x, originPos.y, originPos.z)
        mirrorInsertionPos = om.MVector(-insertionPos.x, insertionPos.y, insertionPos.z)
        mirrorCenterPos = om.MVector(-centerPos.x, centerPos.y, centerPos.z)
    elif mirrorAxis == "y":
        mirrorOriginPos = om.MVector(originPos.x, -originPos.y, originPos.z)
        mirrorInsertionPos = om.MVector(insertionPos.x, -insertionPos.y, insertionPos.z)
        mirrorCenterPos = om.MVector(centerPos.x, -centerPos.y, centerPos.z)
    elif mirrorAxis == "z":
        mirrorOriginPos = om.MVector(originPos.x, originPos.y, -originPos.z)
        mirrorInsertionPos = om.MVector(insertionPos.x, insertionPos.y, -insertionPos.z)
        mirrorCenterPos = om.MVector(centerPos.x, centerPos.y, -centerPos.z)
    else:
        raise RuntimeError("Invalid mirrorAxis, should be either x, y or z")

    muscleLength = om.MVector(insertionPos - originPos).length()

    if "Left" in muscleJointGroup.muscleName:
        newMuscleName = muscleJointGroup.muscleName.replace("Left", "Right")
    elif "Right" in muscleJointGroup.muscleName:
        newMuscleName = muscleJointGroup.muscleName.replace("Right", "Left")
    else:
        raise RuntimeError("Invalid muscleName, no side indication")

    mirrorMuscleJointGrp = MuscleJoint(newMuscleName, muscleLength,
                                       muscleJointGroup.compressionFactor, muscleJointGroup.stretchFactor,
                                       muscleJointGroup.stretchOffset, muscleJointGroup.compressionOffset)


    mc.xform(mirrorMuscleJointGrp.originLoc, translation=mirrorOriginPos, worldSpace=True)
    mc.xform(mirrorMuscleJointGrp.insertionLoc, translation=mirrorInsertionPos, worldSpace=True)
    mc.xform(mirrorMuscleJointGrp.centerLoc, translation=mirrorCenterPos, worldSpace=True)

    mc.parent(mirrorMuscleJointGrp.muscleOrigin, muscleOriginAttachObj)
    mc.parent(mirrorMuscleJointGrp.originLoc, muscleOriginAttachObj)
    mc.parent(mirrorMuscleJointGrp.muscleInsertion, muscleInsertionAttachObj)
    mc.parent(mirrorMuscleJointGrp.insertionLoc, muscleInsertionAttachObj)

    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleOrigin}.jo", 0, 0, 0)
    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleInsertion}.jo", 0, 0, 0)

    return mirrorMuscleJointGrp



def mirrorWoReference(muscleOrigin, muscleInsertion, muscleDriver, muscleOriginAttachObj, muscleInsertionAttachObj,
                      compressionFactor=0.5, stretchFactor=1.5, stretchOffset=None, compressionOffset=None, mirrorAxis="x"):


    originPos = om.MVector(mc.xform(muscleOrigin, translation=True, worldSpace=True, query=True))
    insertionPos = om.MVector(mc.xform(muscleInsertion, translation=True, worldSpace=True, query=True))
    centerPos = om.MVector(mc.xform(muscleDriver, translation=True, worldSpace=True, query=True))

    if mirrorAxis == "x":
        mirrorOriginPos = om.MVector(-originPos.x, originPos.y, originPos.z)
        mirrorInsertionPos = om.MVector(-insertionPos.x, insertionPos.y, insertionPos.z)
        mirrorCenterPos = om.MVector(-centerPos.x, centerPos.y, centerPos.z)
    elif mirrorAxis == "y":
        mirrorOriginPos = om.MVector(originPos.x, -originPos.y, originPos.z)
        mirrorInsertionPos = om.MVector(insertionPos.x, -insertionPos.y, insertionPos.z)
        mirrorCenterPos = om.MVector(centerPos.x, -centerPos.y, centerPos.z)
    elif mirrorAxis == "z":
        mirrorOriginPos = om.MVector(originPos.x, originPos.y, -originPos.z)
        mirrorInsertionPos = om.MVector(insertionPos.x, insertionPos.y, -insertionPos.z)
        mirrorCenterPos = om.MVector(centerPos.x, centerPos.y, -centerPos.z)
    else:
        raise RuntimeError("Invalid mirrorAxis, should be either x, y or z")

    muscleLength = om.MVector(insertionPos - originPos).length()

    muscleName = muscleOrigin.split("_")[0]

    if "Left" in muscleName:
        newMuscleName = muscleName.replace("Left", "Right")
    elif "Right" in muscleName:
        newMuscleName = muscleName.replace("Right", "Left")
    else:
        raise RuntimeError("Invalid muscleName, no side indication")

    mirrorMuscleJointGrp = MuscleJoint(newMuscleName, muscleLength,
                                       compressionFactor, stretchFactor,
                                       stretchOffset, compressionOffset)

    mc.xform(mirrorMuscleJointGrp.originLoc, translation=mirrorOriginPos, worldSpace=True)
    mc.xform(mirrorMuscleJointGrp.insertionLoc, translation=mirrorInsertionPos, worldSpace=True)
    mc.xform(mirrorMuscleJointGrp.centerLoc, translation=mirrorCenterPos, worldSpace=True)

    mc.parent(mirrorMuscleJointGrp.muscleOrigin, muscleOriginAttachObj)
    mc.parent(mirrorMuscleJointGrp.originLoc, muscleOriginAttachObj)
    mc.parent(mirrorMuscleJointGrp.muscleInsertion, muscleInsertionAttachObj)
    mc.parent(mirrorMuscleJointGrp.insertionLoc, muscleInsertionAttachObj)

    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleOrigin}.jo", 0, 0, 0)
    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleInsertion}.jo", 0, 0, 0)

    return mirrorMuscleJointGrp



def resetMuscleJoints(muscleOrigin, muscleInsertion, muscleDriver, muscleOriginAttachObj, muscleInsertionAttachObj,
                      compressionFactor=0.5, stretchFactor=1.5, stretchOffset=None, compressionOffset=None):


    originPos = om.MVector(mc.xform(muscleOrigin, translation=True, worldSpace=True, query=True))
    insertionPos = om.MVector(mc.xform(muscleInsertion, translation=True, worldSpace=True, query=True))
    centerPos = om.MVector(mc.xform(muscleDriver, translation=True, worldSpace=True, query=True))

    muscleLength = om.MVector(insertionPos - originPos).length()

    muscleName = muscleOrigin.split("_")[0]

    if mc.objExists(muscleOrigin):
        mc.delete(muscleOrigin)

    if mc.objExists(muscleInsertion):
        mc.delete(muscleInsertion)

    resetMuscleJointGrp = MuscleJoint(muscleName, muscleLength,
                                       compressionFactor, stretchFactor,
                                       stretchOffset, compressionOffset)

    mc.xform(resetMuscleJointGrp.originLoc, translation=originPos, worldSpace=True)
    mc.xform(resetMuscleJointGrp.insertionLoc, translation=insertionPos, worldSpace=True)
    mc.xform(resetMuscleJointGrp.centerLoc, translation=centerPos, worldSpace=True)

    mc.parent(resetMuscleJointGrp.muscleOrigin, muscleOriginAttachObj)
    mc.parent(resetMuscleJointGrp.originLoc, muscleOriginAttachObj)
    mc.parent(resetMuscleJointGrp.muscleInsertion, muscleInsertionAttachObj)
    mc.parent(resetMuscleJointGrp.insertionLoc, muscleInsertionAttachObj)

    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleOrigin}.jo", 0, 0, 0)
    #mc.setAttr(f"{mirrorMuscleJointGrp.muscleInsertion}.jo", 0, 0, 0)

    return resetMuscleJointGrp
