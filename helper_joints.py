import maya.cmds as mc

def addScapularJointsToBiped(acromionloc, scapulaloc, scapulatiploc, backaimvector, side='Left'):

    assert side in ['Left', 'Right'], "Invalid side, should be either 'Left' or 'Right'"

    # get the neck joint
    if mc.ls('JONeck1'):
        neckJoint = mc.ls('JONeck1')[0]
    else:
        raise RuntimeError("Failed to Find the Neck joint: JONeck1 in the scene")

    if mc.ls('JOBack3'):
        Back3Joint = mc.ls('JOBack3')[0]
    else:
        raise RuntimeError("Failed to Find the Back3 joint: JOBack3 in the scene")

    if mc.ls('JO{0}Clavicle1'.format(side)):
        clavicleJoint = mc.ls('JO{0}Clavicle1'.format(side))[0]
    else:
        raise RuntimeError("Failed to Find the clavicle joint at side: JO{0}Clavicle in the scene".format(side))

    scapulaDrive = createJoint("{0}Acromion1".format(side))
    mc.delete(mc.pointConstraint(acromionloc, scapulaDrive, maintainOffset=False))
    scapulaJoint = createJoint("{0}ScapularRoot1".format(side))
    mc.delete(mc.pointConstraint(scapulaloc, scapulaJoint, maintainOffset=False))
    scapulaTip = createJoint("{0}InferiorAngle1".format(side))
    mc.delete(mc.pointConstraint(scapulatiploc, scapulaTip, maintainOffset=False))

    orientJointChains([[scapulaDrive, scapulaJoint], [scapulaJoint, scapulaTip]])
    mc.parent(scapulaTip,scapulaJoint)
    mc.parent(scapulaJoint, scapulaDrive)
    mc.parent(scapulaDrive, clavicleJoint)
    mc.aimConstraint(neckJoint, scapulaDrive,
                     aimVector=(0, 1, 0),
                     upVector=(1, 0, 0),
                     worldUpType="objectrotation",
                     worldUpObject=Back3Joint,
                     worldUpVector=backaimvector,
                     maintainOffset=True)

    return [scapulaDrive, scapulaJoint, scapulaTip]


def createJoint(jointName, parent=None):
    mc.select(clear=True)
    jnt = mc.joint(name=jointName)
    if parent:
        mc.parent(jnt, parent)
        mc.setAttr(f"{jnt}.t", 0, 0, 0)
        mc.setAttr(f"{jnt}.r", 0, 0, 0)
        mc.setAttr(f"{jnt}.jo", 0, 0, 0)

    return jnt

def orientJointChains(jointChains):
    for jntChain in jointChains:
        mc.delete(mc.aimConstraint(jntChain[1], jntChain[0],
                     aimVector=(0,1,0),
                     upVector=(1,0,0),
                     worldUpType="scene"))
