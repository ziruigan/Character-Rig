import maya.cmds as mc

#Create meta data node for limbs
def create_limb_node(node_name, node_type, node_side):
    #create data node
    data_node = mc.createNode("network", name=node_name)
    #create attribute
    mc.addAttr(data_node, longName="name", niceName="Name", dataType='string')
    mc.addAttr(data_node, longName="node_type", niceName="Node Type", dataType='string')
    mc.addAttr(data_node, longName="side", niceName="Side", dataType='string')
    #assign attributes
    mc.setAttr(f"{data_node}.name", node_name, type="string")
    mc.setAttr(f"{data_node}.node_type", node_type, type="string")
    mc.setAttr(f"{data_node}.side", node_side, type="string")

    #create fk_controls connection
    mc.addAttr(data_node, longName="fk_controls", niceName="FK Controls", multi=True, indexMatters=True)

    #create ik_controls connection
    mc.addAttr(data_node, longName="ik_controls", niceName="IK Controls", multi=True, indexMatters=True)

    #switch control
    mc.addAttr(data_node, longName="switch_control", niceName="Switch Control")

    # end marker
    mc.addAttr(data_node, longName="end_marker", niceName="End Marker")

    # pv marker
    mc.addAttr(data_node, longName="pv_marker", niceName="PV Marker")

    #driven joints
    mc.addAttr(data_node, longName="driven_joints", niceName="Driven Joints", multi=True, indexMatters=True)

    return data_node


def connect_limb_node(data_node, driven_joints, fk_controls, ik_controls, switch_control, pv_marker, end_marker):
    for index, driven_joint in enumerate(driven_joints):
        if not mc.attributeQuery("dataParent", node=driven_joint, exists=True):
            mc.addAttr(driven_joint, longName="dataParent", niceName="dataParent", attributeType="message")
        mc.connectAttr(f"{data_node}.driven_joints[{index}]", f"{driven_joint}.dataParent", force=True)

    for index, fk_control in enumerate(fk_controls):
        if not mc.attributeQuery("dataParent", node=fk_control, exists=True):
            mc.addAttr(fk_control, longName="dataParent", niceName="dataParent", attributeType="message")
        mc.connectAttr(f"{data_node}.fk_controls[{index}]", f"{fk_control}.dataParent", force=True)

    for index, ik_control in enumerate(ik_controls):
        if not mc.attributeQuery("dataParent", node=ik_control, exists=True):
            mc.addAttr(ik_control, longName="dataParent", niceName="dataParent", attributeType="message")
        mc.connectAttr(f"{data_node}.ik_controls[{index}]", f"{ik_control}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=switch_control, exists=True):
        mc.addAttr(switch_control, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.switch_control", f"{switch_control}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=pv_marker, exists=True):
        mc.addAttr(pv_marker, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.pv_marker", f"{pv_marker}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=end_marker, exists=True):
        mc.addAttr(end_marker, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.end_marker", f"{end_marker}.dataParent", force=True)

def get_limb_nodes():
    limb_nodes = []
    data_nodes = mc.ls(type="network")
    for dn in data_nodes:
        if mc.attributeQuery("node_type", node=dn, exists=True):
            if mc.getAttr(f"{dn}.node_type") in ["Arm", "Leg"]:
                limb_nodes.append(dn)

    return limb_nodes

"""
import limb_data_node as ldn
import importlib
importlib.reload(ldn)

data_node = ldn.create_limb_node("LeftArmDataNode", "Arm", "Left")
ldn.connect_limb_node(data_node,
                     driven_joints=["JOLeftUpperArm1", "JOLeftLowerArm1","JOLeftWrist1"],
                     fk_controls=["LeftShoulderFKControl1", "LeftElbowFKControl1", "LeftHandFKControl1"],
                     ik_controls=["LeftHandIKControl1", "LeftElbowIKControl1"],
                     switch_control="LeftHandIKFKSwitchControl1",
                     end_marker="LeftHandEndMarker1",
                     pv_marker="LeftElbowControlMarker1")

data_node = ldn.create_limb_node("RightArmDataNode", "Arm", "Right")
ldn.connect_limb_node(data_node,
                      driven_joints=["JORightUpperArm1", "JORightLowerArm1", "JORightWrist1"],
                      fk_controls=["RightShoulderFKControl1", "RightElbowFKControl1", "RightHandFKControl1"],
                      ik_controls=["RightHandIKControl1", "RightElbowIKControl1"],
                      switch_control="RightHandIKFKSwitchControl1",
                      end_marker="RightHandEndMarker1",
                      pv_marker="RightElbowControlMarker1")

data_node = ldn.create_limb_node("LeftLegDataNode", "Leg", "Left")
ldn.connect_limb_node(data_node,
                      driven_joints=["JOLeftUpperLeg1", "JOLeftLowerLeg1", "JOLeftAnkle1","JOLeftToe1"],
                      fk_controls=["LeftHipFKControl1", "LeftKneeFkControl1", "LeftFootFKControl1", "LeftToeFKControl1"],
                      ik_controls=["LeftFootControl1", "LeftKneePoleVectorControl1", "LeftToeIKControl1"],
                      switch_control="LeftFootIKFKSwitchControl1",
                      end_marker="LeftFootEndMarker1",
                      pv_marker="LeftKneeControlMarker1")

data_node = ldn.create_limb_node("RightLegDataNode", "Leg", "Right")
ldn.connect_limb_node(data_node,
                      driven_joints=["JORightUpperLeg1","JORightLowerLeg1", "JORightAnkle1", "JORightToe1"],
                      fk_controls=["RightUpperLControl1", "RightLowerLControl1", "RightAnkControl1", "RightToeFKControl1"],
                      ik_controls=["RightFootControl1", "RightKneePoleVectorControl1","RightToeIKControl1"],
                      switch_control="RightFootIKFKSwitchControl1",
                      end_marker="RightFootEndMarker1",
                      pv_marker="RightKneeControlMarker1")

"""