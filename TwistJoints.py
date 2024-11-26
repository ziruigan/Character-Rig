import maya.cmds as mc
import maya.api.OpenMaya as om


def create_twist_joints(start_joint, end_joint, aim_vector=om.MVector.kYaxisVector,
                        up_vector=om.MVector.kXaxisVector, twist_joint_num=3):
    """

        Args:
            start_joint (str): parent joint name of the joint chain
            end_joint (str): child joint name of the joint chain
            aim_vector (MVector, optional): twist axis of the driving joint
            up_vector (MVector, optional): up axis
            twist_joint_num (int, optional): number of helper joints distributed along the chain

        Returns:
            Return all newly created joints
        """
    mc.select(clear=True)

    #create joints to orient constraint twist joints
    twist_basis_joint1 = mc.joint(name=start_joint.lstrip('JO') + "TwistBasis1")
    mc.parent(twist_basis_joint1, start_joint)
    mc.matchTransform(twist_basis_joint1, start_joint)

    twist_value_joint1 = mc.joint(name=start_joint.lstrip('JO') + "TwistValue1")
    mc.matchTransform(twist_value_joint1, twist_basis_joint1)
    #mc.parent(twist_value_joint1, twist_basis_joint1)

    basis_offset_joint1 = mc.joint(name=start_joint.lstrip('JO') + "BasisOffset1")
    mc.matchTransform(basis_offset_joint1, twist_basis_joint1)
    mc.parent(basis_offset_joint1, twist_basis_joint1)

    #aim constraint the value twist joint by the end twisting joint
    mc.aimConstraint(end_joint, twist_value_joint1,
                     aimVector=aim_vector,
                     upVector=up_vector,
                     worldUpObject=end_joint,
                     worldUpType="objectrotation",
                     worldUpVector=up_vector)

    twist_joints = []
    #create the joints in between
    for i in range(twist_joint_num):

        chain_length = (om.MVector(mc.xform(end_joint, translation=True, query=True, worldSpace=True)) -
                        om.MVector(mc.xform(start_joint, translation=True, query=True, worldSpace=True))).length()

        distributionDistance = chain_length / twist_joint_num

        twist_joint = mc.joint(name=start_joint.lstrip('JO') + f"Twist{i}")
        mc.parent(twist_joint, start_joint)

        translation = distributionDistance * aim_vector * (i + 1)
        mc.setAttr(f'{twist_joint}.t', *translation)

        # Apply the orient constraint with the two objects as targets
        constraint = mc.orientConstraint(twist_value_joint1, basis_offset_joint1, twist_joint)[0]

        weight_0 = 1 / twist_joint_num * (i + 1)
        weight_1 = 1 - weight_0

        # Set the weights of the constraint
        mc.setAttr(f"{constraint}.{twist_value_joint1}W0", weight_0)
        mc.setAttr(f"{constraint}.{basis_offset_joint1}W1", weight_1)
        mc.setAttr(f"{constraint}.interpType", 2)

        twist_joints.append(twist_joint)

    return twist_joints


def create_counter_twist_joints(start_joint, end_joint, aim_vector=om.MVector.kYaxisVector,
                        up_vector=om.MVector.kXaxisVector, twist_joint_num=3):
    """

        Args:
            start_joint (str): parent joint name of the joint chain
            end_joint (str): child joint name of the joint chain
            aim_vector (MVector, optional): twist axis of the driving joint
            up_vector (MVector, optional): up axis
            twist_joint_num (int, optional): number of helper joints distributed along the chain


        Returns:
            Return all the newly created joints
        """
    mc.select(clear=True)

    # create joints to orient constraint twist joints
    twist_basis_joint1 = mc.joint(name=start_joint.lstrip('JO') + "TwistBasis1")
    mc.parent(twist_basis_joint1, start_joint)
    mc.matchTransform(twist_basis_joint1, start_joint)

    twist_value_joint1 = mc.joint(name=start_joint.lstrip('JO') + "TwistValue1")
    mc.matchTransform(twist_value_joint1, twist_basis_joint1)
    # mc.parent(twist_value_joint1, twist_basis_joint1)

    basis_offset_joint1 = mc.joint(name=start_joint.lstrip('JO') + "BasisOffset1")
    mc.matchTransform(basis_offset_joint1, twist_basis_joint1)
    mc.parent(basis_offset_joint1, twist_basis_joint1)

    # aim constraint the value twist joint by the end twisting joint
    mc.aimConstraint(end_joint, twist_value_joint1,
                     aimVector=aim_vector,
                     upVector=up_vector,
                     worldUpObject=start_joint,
                     worldUpType="objectrotation",
                     worldUpVector=up_vector)

    mc.select(clear=True)
    twist_up_joint1 = mc.joint(name=start_joint.lstrip('JO') + "TwistUp1")
    mc.matchTransform(twist_up_joint1, start_joint)
    mc.parent(twist_up_joint1, start_joint)
    mc.setAttr(f"{twist_up_joint1}.t", *(up_vector * 5))
    start_parent = mc.listRelatives(start_joint, parent=True)[0]
    mc.parent(twist_up_joint1, start_parent)

    mc.aimConstraint(end_joint, twist_basis_joint1,
                    aimVector=aim_vector,
                    upVector=up_vector,
                    worldUpObject=twist_up_joint1,
                    worldUpType="object")

    twist_joints = []
    # create the joints in between
    for i in range(twist_joint_num):

        chain_length = (om.MVector(mc.xform(end_joint, translation=True, query=True, worldSpace=True)) -
                        om.MVector(mc.xform(start_joint, translation=True, query=True, worldSpace=True))).length()

        distributionDistance = chain_length / twist_joint_num

        twist_joint = mc.joint(name=start_joint.lstrip('JO') + f"Twist{i}")
        mc.parent(twist_joint, start_joint)

        translation = distributionDistance * aim_vector * i
        mc.setAttr(f'{twist_joint}.t', *translation)

        # Apply the orient constraint with the two objects as targets
        constraint = mc.orientConstraint(twist_value_joint1, basis_offset_joint1, twist_joint)[0]

        if i == 0:
            weight_0 = 0.1
        else:
            weight_0 = 1 / twist_joint_num * i
        weight_1 = 1 - weight_0

        # Set the weights of the constraint
        mc.setAttr(f"{constraint}.{twist_value_joint1}W0", weight_0)
        mc.setAttr(f"{constraint}.{basis_offset_joint1}W1", weight_1)
        mc.setAttr(f"{constraint}.interpType", 2)

        twist_joints.append(twist_joint)

    return twist_joints


def setup_nonflip_twist(start_joint, end_joint, up_joint, limbcontrol, up_vector=om.MVector.kXaxisVector,
                        offset=5):
    """
        Args:
            start_joint (str): parent joint name of the joint chain
            end_joint (str): child joint name of the joint chain
            up_joint (str): joint that was created for start_joint as up object
            limbcontrol (str): control which help the limb to rotate
            up_vector (MVector, optional): up vector used for set up the counter twist joints
            rot_axis (MVector, optional): rotation axis for the limb to get driven key set
            offset(int, optional): offset that the nonflip marker would be placed

            """

    mc.select(start_joint)

    twist_marker = mc.joint(name=start_joint.lstrip('JO') + "twist_marker")
    translation = -up_vector * offset
    aim_vector = om.MVector(mc.xform(end_joint, translation=True, query=True)).normalize()
    rot_axis = (aim_vector ^ up_vector).normalize()
    mc.setAttr(f"{twist_marker}.t", *translation)
    start_parent = mc.listRelatives(start_joint, parent=True)[0]
    mc.parent(twist_marker, start_parent)

    multi_matrix_node = mc.createNode("multMatrix", name="multiMatrixNode")

    mc.connectAttr(f"{twist_marker}.worldMatrix[0]", f"{multi_matrix_node}.matrixIn[0]")
    mc.connectAttr(f"{start_joint}.worldInverseMatrix[0]", f"{multi_matrix_node}.matrixIn[1]")

    decompose_node = mc.createNode("decomposeMatrix", name="decomposeMatrixNode")
    mc.connectAttr(f"{multi_matrix_node}.matrixSum", f"{decompose_node}.inputMatrix")

    vector_product_node = mc.createNode("vectorProduct", name="vectorProductNode")

    mc.setAttr(f"{vector_product_node}.operation", 1)  # 1 is for dot product
    mc.setAttr(f"{vector_product_node}.normalizeOutput", True)

    mc.connectAttr(f"{decompose_node}.outputTranslate", f"{vector_product_node}.input1")
    mc.connectAttr(f"{end_joint}.translate", f"{vector_product_node}.input2")

    up_joint_locator = mc.spaceLocator(name=start_joint.lstrip('JO') + "up_locator1")[0]
    mc.matchTransform(up_joint_locator, up_joint)
    mc.parent(up_joint_locator, start_joint)

    sphere = mc.sphere(radius=10, name=start_joint.lstrip('JO')+"sphere1")[0]
    mc.matchTransform(sphere, start_joint)
    mc.parent(sphere, start_joint)
    mc.connectAttr(f"{vector_product_node}.outputX", f"{sphere}.translateX")

    driver_attr = f"{vector_product_node}.outputX"
    driven_attr_x = f"{up_joint}.translateX"
    driven_attr_y = f"{up_joint}.translateY"
    driven_attr_z = f"{up_joint}.translateZ"

    #set driven key at neutral pose
    mc.setDrivenKeyframe(driven_attr_x, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_y, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_z, currentDriver=driver_attr)

    #set driven key at 90 degree
    rotation = 90 * rot_axis
    mc.select(limbcontrol)
    mc.rotate(*rotation, relative=True, objectSpace=True)
    mc.matchTransform(up_joint, up_joint_locator)
    print(mc.getAttr(f"{start_joint}.rotateZ"))
    print(mc.getAttr(driver_attr))
    mc.setDrivenKeyframe(driven_attr_x, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_y, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_z, currentDriver=driver_attr)

    # set driven key at -90 degree
    rotation = -180 * rot_axis
    mc.select(limbcontrol)
    mc.rotate(*rotation, relative=True, objectSpace=True)
    mc.matchTransform(up_joint, up_joint_locator)
    print(mc.getAttr(f"{start_joint}.rotateZ"))
    print(mc.getAttr(driver_attr))
    mc.setDrivenKeyframe(driven_attr_x, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_y, currentDriver=driver_attr)
    mc.setDrivenKeyframe(driven_attr_z, currentDriver=driver_attr)

    rotation = 90 * rot_axis
    mc.select(limbcontrol)
    mc.rotate(*rotation, relative=True, objectSpace=True)
    print(mc.getAttr(f"{start_joint}.rotateZ"))





def setup_elbow_correction_joints(upper_joint, elbow_joint, offset):
    """
           Args:
               upper_joint (str): parent joint name of the elbow joint
               elbow_joint (str): elbow joint name which intended to correct
               offset(int list): offset that the elbow corrective joint would be placed

               """

    mc.select(clear=True)

    elbow_driver = mc.joint(name=elbow_joint.lstrip('JO') + "elbowDriver1")
    mc.parent(elbow_driver, elbow_joint)
    mc.matchTransform(elbow_driver, elbow_joint)

    constraint = mc.orientConstraint(upper_joint, elbow_joint, elbow_driver)[0]

    elbow_offset = mc.joint(name=elbow_joint.lstrip('JO') + "elbowOffset1")
    mc.matchTransform(elbow_offset, elbow_driver)

    elbow_end = mc.joint(name=elbow_joint.lstrip('JO') + "elbowEnd1")
    mc.matchTransform(elbow_end, elbow_offset)
    mc.setAttr(f"{elbow_end}.t", offset)

