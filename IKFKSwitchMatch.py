import maya.cmds as mc
import maya.api.OpenMaya as om
import limb_data_node as ldn

def fk_matching(joint_chain, fk_controls, ikfk_switch_attr):
    set_transform_to_fk_controls(joint_chain, fk_controls)
    mc.setAttr(ikfk_switch_attr, 0)

def set_transform_to_fk_controls(joint_chain, fk_controls):
    #joint_chain= ut.get_joint_chain(start_joint, end_joint)
    for index, fk_control in enumerate(fk_controls):
        mc.matchTransform(fk_control, joint_chain[index])


#==========IKMatching=================================================#
def set_transform_to_ik_controls(end_joint, ik_control):
    worldMatrix = mc.xform(end_joint, matrix=True, worldSpace=True, query=True)
    mc.xform(ik_control, matrix=worldMatrix, worldSpace=True)


def set_transform_to_pv_controls(joint_chain, pv_control, pv_marker, type = "Leg", side = "Left"):
    #joint_chain = ut.get_joint_chain(start_joint, end_joint)
    root_jnt_pos = om.MPoint(mc.xform(joint_chain[0], translation=True, worldSpace=True, query=True))
    mid_jnt_pos = om.MPoint(mc.xform(joint_chain[1], translation=True, worldSpace=True, query=True))
    end_jnt_pos = om.MPoint(mc.xform(joint_chain[2], translation=True, worldSpace=True, query=True))

    if type == "Leg":
        # ========set the position with mid point and hardcoded factor========#
        mid_point_pos = root_jnt_pos + (end_jnt_pos - root_jnt_pos) / 2
        pole_vector_dir = mid_jnt_pos - mid_point_pos
        pv_pos = mid_jnt_pos + pole_vector_dir.normalize() * 5  # hardcoded factor
        mc.xform(pv_control, translation=(pv_pos.x, pv_pos.y, pv_pos.z), worldSpace=True)

        #=======set the position same with matrix========#
        #localVec = om.MVector(offset[0], offset[1], offset[2])
        #worldMatrix = om.MMatrix(mc.xform(joint_chain[1], worldSpace=True, matrix=True, query=True))
        #elbowWorldPos = om.MVector(mc.xform(joint_chain[1], worldSpace=True, translation=True, query=True))
        #worldPos = elbowWorldPos + localVec * worldMatrix
        #mc.xform(pv_control, translation=worldPos, worldSpace=True)

        '''
        #adjust pv control orientation  （optional）
        mc.delete(mc.aimConstraint(joint_chain[1], pv_control,
                               aimVector=(0,0,-1),
                               upVector=(0,1,0),
                               worldUpObject=joint_chain[1],
                               worldUpType="objectrotation",
                               worldUpVector=(0,-1,0)))
        '''
        mc.matchTransform(pv_control, pv_marker)

    else:
        worldupVector = (mid_jnt_pos - end_jnt_pos) ^ (root_jnt_pos - end_jnt_pos)
        if side == "Left":
            aimVector = (0, 1, 0)
        else:
            aimVector = (0, -1, 0)
        mc.delete(mc.aimConstraint(joint_chain[1], pv_marker, aimVector=aimVector,
                                   upVector=(1, 0, 0), worldUpVector=worldupVector))
        mc.matchTransform(pv_control, pv_marker)

    #========set the position with mid point and hardcoded factor========#
    #mid_point_pos = root_jnt_pos + (end_jnt_pos - root_jnt_pos) / 2.0
    #pole_vector_dir = mid_jnt_pos - mid_point_pos
    #pv_pos = mid_jnt_pos + pole_vector_dir * 10.0  # hardcoded factor
    #mc.xform(pv_control, translation=(pv_pos.x, pv_pos.y, pv_pos.z), worldSpace=True)

    #========set the position same with parenting=======#
    #old_parent = mc.lisRelatives(pv_control, parent=True)
    #mc.parent(pv_control, joint_chain[1])
    #mc.setAttr(f"{pv_control}.tx", offset_x)
    #mc.setAttr(f"{pv_control}.ty", offset_y)
    #mc.setAttr(f"{pv_control}.tz", offset_z)
    #mc.parent(pv_control, old_parent)


class IKFKMatching:
    '''
    joint_chain: joints which involved in the ikfk matching process
    fk_controls: fk controls which involved in the ikfk matching process
    ik_controls: ik controls which involved in the ikfk matching process
    pv_control: pv controls which involved in the ikfk matching process
    ikfk_switch_attr: ik_switch attribute that need to be change to finish the process
    '''

    def __init__(self, node_type=None, side="Left", joint_chain=None, fk_controls=None, ik_controls=None,
                 ikfk_switch_attr=None, pv_marker=None, end_marker=None):
        self.node_type = node_type
        self.side = side
        self.joint_chain = joint_chain
        self.fk_controls = fk_controls
        self.ik_control = ik_controls[0]
        self.pv_control = ik_controls[1]
        self.toe_control = ik_controls[-1]
        self.ikfk_switch_attr = ikfk_switch_attr
        self.end_marker = end_marker
        self.pv_marker = pv_marker


    @classmethod
    def create(cls, data_node=None):
        if not data_node:
            selected_nodes = mc.ls(sl=True)
            if not selected_nodes:
                return None
            for node in selected_nodes:
                if mc.attributeQuery("dataParent", node=node, exists=True):
                    if mc.listConnections(f"{node}.dataParent", source=True, destination=False, type="network"):
                        data_node = mc.listConnections(f"{node}.dataParent",
                                                        source=True,
                                                        destination=False,
                                                        type="network")[0]
                        break

            if not data_node:
                print("Failed to find the data node connected to any selected items")
                return

        else:
            limb_data_nodes = ldn.get_limb_nodes()
            if data_node not in limb_data_nodes:
                print("Failed to find the data node connected to any selected items")
                return

        node_type = mc.getAttr(f"{data_node}.node_type")
        fk_controls = mc.listConnections(f"{data_node}.fk_controls", source=False, destination=True)
        ik_controls = mc.listConnections(f"{data_node}.ik_controls", source=False, destination=True)
        joint_chain = mc.listConnections(f"{data_node}.driven_joints", source=False, destination=True)
        ikfk_switch_control = mc.listConnections(f"{data_node}.switch_control", source=False, destination=True)[0]
        end_marker = mc.listConnections(f"{data_node}.end_marker", source=False, destination=True)
        pv_marker = mc.listConnections(f"{data_node}.pv_marker", source=False, destination=True)
        side = mc.getAttr(f"{data_node}.side")
        return cls(node_type, side, joint_chain, fk_controls, ik_controls,
                   ikfk_switch_attr=f"{ikfk_switch_control}.IKSwitch", pv_marker=pv_marker, end_marker=end_marker)

    def to_fk(self):
        set_transform_to_fk_controls(self.joint_chain, self.fk_controls)
        mc.setAttr(self.ikfk_switch_attr, 0)

    def to_ik(self):
        set_transform_to_ik_controls(self.end_marker, self.ik_control)
        set_transform_to_pv_controls(self.joint_chain, self.pv_control, self.pv_marker, self.node_type, self.side)
        mc.setAttr(self.ikfk_switch_attr, 1)

    def get_ik_state(self):
        #return true if we are in IK state already, false if we are in FK state
        return mc.getAttr(self.ikfk_switch_attr)


