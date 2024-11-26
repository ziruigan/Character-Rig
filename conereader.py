import logging
import maya.api.OpenMaya as om
import maya.cmds as mc

"""
function helps to create cone reader at origin

Args: 
    name(str) : prefix of the respective cone readers and node
    joint(str): name of the joint that this cone reader works on
    min_angle(float): angle that the minimum cone accept
    max_angle(float): angle that the maximum cone accept
"""


def setup_conereader(name, joint, min_angle, max_angle):

    cone_locators = create_conereader(name, min_angle, max_angle)

    conereader_datanode = create_conereader_node(name, "coneReader", joint)

    connect_data_node(conereader_datanode, cone_locators)

    draw_and_connect_cone(cone_locators[0])

    create_HUD(conereader_datanode)
    group_node = mc.listConnections(f"{conereader_datanode}.group", source=True, destination=True)[0]
    registerNodeDirtyPlugCallback(group_node)

    return conereader_datanode

def create_conereader(name, min_angle, max_angle):


    temp_min_loc = mc.spaceLocator(name="temp_min")[0]
    temp_max_loc = mc.spaceLocator(name="temp_max")[0]
    center_loc = mc.spaceLocator(name=name + "_center")[0]
    temp_live_loc = mc.spaceLocator(name="temp_live")[0]

    mc.xform(center_loc, worldSpace=True, translation=[0, 2, 0])

    mc.xform(temp_min_loc, worldSpace=True, translation=[0, 2, 0])
    mc.rotate(0, 0, min_angle, temp_min_loc, relative=True, objectSpace=True, pivot=(0, 0, 0))
    min_loc = mc.spaceLocator(name=name + "_min")[0]
    mc.delete(mc.parentConstraint(temp_min_loc, min_loc, skipRotate=["x", "y", "z"]))
    mc.delete(temp_min_loc)

    mc.xform(temp_max_loc, worldSpace=True, translation=[0, 2, 0])
    mc.rotate(0, 0, max_angle, temp_max_loc, relative=True, objectSpace=True, pivot=(0, 0, 0))
    max_loc = mc.spaceLocator(name=name + "_max")[0]
    mc.delete(mc.parentConstraint(temp_max_loc, max_loc, skipRotate=["x", "y", "z"]))
    mc.delete(temp_max_loc)

    mc.xform(temp_live_loc, worldSpace=True, translation=[0, 2, 0])
    mc.rotate(0, 0, (max_angle + min_angle) / 2, temp_live_loc, relative=True, objectSpace=True, pivot=(0, 0, 0))
    live_loc = mc.spaceLocator(name=name + "_live")[0]
    mc.delete(mc.parentConstraint(temp_live_loc, live_loc, skipRotate=["x", "y", "z"]))
    mc.delete(temp_live_loc)

    locators = [center_loc, min_loc, max_loc, live_loc]

    cone_group = mc.group(empty=True, name=name + "_coneReader", world=True)
    for locator in locators:
        mc.parent(locator, cone_group)


    # get the angles between each vector formed by the locator with the origin
    angle_between_live_node = mc.createNode('angleBetween', name=name + 'angleBetween_live')

    mc.connectAttr(f"{live_loc}.translate", f"{angle_between_live_node}.vector1")
    mc.connectAttr(f"{center_loc}.translate", f"{angle_between_live_node}.vector2")

    angle_between_min_node = mc.createNode('angleBetween', name=name + 'angleBetween_min')

    mc.connectAttr(f"{min_loc}.translate", f"{angle_between_min_node}.vector1")
    mc.connectAttr(f"{center_loc}.translate", f"{angle_between_min_node}.vector2")

    angle_between_max_node = mc.createNode('angleBetween', name=name + 'angleBetween_max')

    mc.connectAttr(f"{max_loc}.translate", f"{angle_between_max_node}.vector1")
    mc.connectAttr(f"{center_loc}.translate", f"{angle_between_max_node}.vector2")

    # calculate the angle difference between live and min; max and min

    live_min_diff_pma_node = mc.createNode('plusMinusAverage', name=name + "live_min_diff_pma")
    max_min_diff_pma_node = mc.createNode('plusMinusAverage', name=name + "max_min_diff_pma")

    mc.setAttr(f"{live_min_diff_pma_node}.operation", 2)
    mc.setAttr(f"{max_min_diff_pma_node}.operation", 2)

    mc.connectAttr(f"{angle_between_live_node}.angle", f"{live_min_diff_pma_node}.input1D[0]")
    mc.connectAttr(f"{angle_between_min_node}.angle", f"{live_min_diff_pma_node}.input1D[1]")
    mc.connectAttr(f"{angle_between_max_node}.angle", f"{max_min_diff_pma_node}.input1D[0]")
    mc.connectAttr(f"{angle_between_min_node}.angle", f"{max_min_diff_pma_node}.input1D[1]")

    # calculate the weight of how far live comes between max and min
    weight_node = mc.createNode('multiplyDivide', name=name + 'weight')

    #divide
    mc.setAttr(f"{weight_node}.operation", 2)

    mc.connectAttr(f"{live_min_diff_pma_node}.output1D", f"{weight_node}.input1X")
    mc.connectAttr(f"{max_min_diff_pma_node}.output1D", f"{weight_node}.input2X")






    # first situation : locator angle is smaller than min angle              output:  the flag for whether live angle is smaller than min angle

    less_than_min_condition_node = mc.createNode('condition', name=name + 'condition_less_than_min')

    mc.connectAttr(f"{angle_between_live_node}.angle", f"{less_than_min_condition_node}.firstTerm")

    mc.connectAttr(f"{angle_between_min_node}.angle", f"{less_than_min_condition_node}.secondTerm")

    # smaller
    mc.setAttr(f"{less_than_min_condition_node}.operation", 4)

    # if live angle is smaller than min angle output 1; or else output live angle for further examination
    mc.connectAttr(f"{angle_between_live_node}.angle", f"{less_than_min_condition_node}.colorIfFalseR")
    mc.setAttr(f"{less_than_min_condition_node}.colorIfTrueR", 1)

    #create a flag for the situation when live angle is smaller than min angle
    less_than_min_flag_node = mc.createNode('condition', name=name + 'if_less_than_min')

    mc.connectAttr(f"{less_than_min_condition_node}.outColorR", f"{less_than_min_flag_node}.firstTerm")

    mc.setAttr( f"{less_than_min_flag_node}.secondTerm", 1)

    # equal
    mc.setAttr(f"{less_than_min_flag_node}.operation", 0)

    # if the input is 1 which means the live angle is smaller than min angle output 0; elsewise output 1 to give the other situation full control
    mc.setAttr(f"{less_than_min_flag_node}.colorIfFalseR", 1)
    mc.setAttr(f"{less_than_min_flag_node}.colorIfTrueR", 0)





    # second situation: the live angle is bigger than the max angle
    # third situation: when live angle is inbetween
    # output: the weight of the progression or a flag for exceeding

    more_than_max_condition_node = mc.createNode('condition', name=name + 'condition_more_than_max')

    mc.connectAttr(f"{angle_between_live_node}.angle", f"{more_than_max_condition_node}.firstTerm")

    mc.connectAttr(f"{angle_between_max_node}.angle", f"{more_than_max_condition_node}.secondTerm")

    # smaller or equal
    mc.setAttr(f"{more_than_max_condition_node}.operation", 5)

    # if live angle is greater than max angle output 1; or else output weight for further examination
    mc.connectAttr(f"{weight_node}.outputX", f"{more_than_max_condition_node}.colorIfTrueR")
    mc.setAttr(f"{more_than_max_condition_node}.colorIfFalseR", 1)


    # combining the cases

    combine_condition_node = mc.createNode('multiplyDivide', name=name + 'combine_condition')

    # multiply
    mc.setAttr(f"{combine_condition_node}.operation", 1)

    mc.connectAttr(f"{more_than_max_condition_node}.outColorR", f"{combine_condition_node}.input1X")
    mc.connectAttr(f"{less_than_min_flag_node}.outColorR", f"{combine_condition_node}.input2X")





    # reverse the output for correct answer

    reverse_node = mc.createNode('plusMinusAverage', name=name + "reverse")

    #minus
    mc.setAttr(f"{reverse_node}.operation", 2)

    mc.setAttr(f"{reverse_node}.input1D[0]", 1)
    mc.connectAttr(f"{combine_condition_node}.outputX", f"{reverse_node}.input1D[1]")



    # check the case if min angle is greater than max angle, if so invalidate the answer

    max_min_diff_conditional_node = mc.createNode('condition', name=name + 'max_min_diff_conditional')

    mc.connectAttr(f"{max_min_diff_pma_node}.output1D", f"{max_min_diff_conditional_node}.firstTerm")

    mc.setAttr(f"{max_min_diff_conditional_node}.secondTerm", 0)

    # smaller or equal
    mc.setAttr(f"{max_min_diff_conditional_node}.operation", 5)

    # if live angle is greater than max angle output 1; or else output weight for further examination
    mc.setAttr(f"{max_min_diff_conditional_node}.colorIfTrueR", 0)
    mc.setAttr(f"{max_min_diff_conditional_node}.colorIfFalseR", 1)

    # using the output as mask
    final_condition_node = mc.createNode('multiplyDivide', name=name + 'final_condition')

    #multiply
    mc.setAttr(f"{final_condition_node}.operation", 1)

    mc.connectAttr(f"{reverse_node}.output1D", f"{final_condition_node}.input1X")
    mc.connectAttr(f"{max_min_diff_conditional_node}.outColorR", f"{final_condition_node}.input2X")

    #add and connect attribute to the group object
    mc.addAttr(cone_group, longName="coneReading", attributeType="float", defaultValue=.0, k = True)
    mc.addAttr(cone_group, longName="minAngleReading", attributeType="float", defaultValue=.0, k=True)
    mc.addAttr(cone_group, longName="maxAngleReading", attributeType="float", defaultValue=.0, k=True)

    mc.connectAttr(f"{final_condition_node}.outputX", f"{cone_group}.coneReading")
    mc.connectAttr(f"{angle_between_min_node}.angle", f"{cone_group}.minAngleReading")
    mc.connectAttr(f"{angle_between_max_node}.angle", f"{cone_group}.maxAngleReading")

    return locators



"""
function draws the actual cones and connect them to data node for further operation

Args: 
    selected_nodes(str) : any node; ideally are the nodes associated with a cone reader
"""

def draw_and_connect_cone(selected_nodes):
    if type(selected_nodes) is not list:
        selected_nodes = [selected_nodes]

    for node in selected_nodes:
        if node is not None:
            if mc.attributeQuery("dataParent", node=node, exists=True):
                if mc.listConnections(f"{node}.dataParent", source=True, destination=False, type="network"):
                    data_node = mc.listConnections(f"{node}.dataParent",
                                                   source=True,
                                                   destination=False,
                                                   type="network")[0]

                    if data_node in get_conereader_nodes():

                        # if there were cones drew before
                        if (mc.listConnections(f"{data_node}.min_cone", source=False, destination=True) and
                        mc.listConnections(f"{data_node}.max_cone", source=False, destination=True)):

                            old_min_cone = mc.listConnections(f"{data_node}.min_cone", source=False, destination=True)[0]
                            old_max_cone = mc.listConnections(f"{data_node}.max_cone", source=False, destination=True)[0]

                            mc.delete(old_min_cone)
                            mc.delete(old_max_cone)

                        name = mc.getAttr(f"{data_node}.name")

                        min_loc_node = mc.listConnections(f"{data_node}.min_loc", source=False, destination=True)[0]
                        max_loc_node = mc.listConnections(f"{data_node}.max_loc", source=False, destination=True)[0]


                        min_additional_rot = 1
                        max_additional_rot = 1
                        min_translate_flag = 1
                        max_translate_flag = 1

                        if mc.getAttr(f"{min_loc_node}.translateY") < 0:
                            min_additional_rot = -1
                            min_translate_flag = -1

                        if mc.getAttr(f"{max_loc_node}.translateY") < 0:
                            max_additional_rot = -1
                            max_translate_flag = -1

                        min_cone_radius = abs(mc.getAttr(f"{min_loc_node}.translateX")) * min_additional_rot
                        min_cone_height = abs(mc.getAttr(f"{min_loc_node}.translateY"))

                        max_cone_radius = abs(mc.getAttr(f"{max_loc_node}.translateX")) * max_additional_rot
                        max_cone_height = abs(mc.getAttr(f"{max_loc_node}.translateY"))

                        min_cone_hr = abs(min_cone_height / min_cone_radius)
                        max_cone_hr = abs(max_cone_height / max_cone_radius)

                        min_cone = mc.cone(name=name + "_min_cone", radius=min_cone_radius, heightRatio=min_cone_hr)
                        max_cone = mc.cone(name=name + "_max_cone", radius=max_cone_radius, heightRatio=max_cone_hr)

                        mc.rotate(0, 0, -90 , min_cone, relative=True, objectSpace=True)
                        mc.rotate(0, 0, -90 , max_cone, relative=True, objectSpace=True)

                        if not mc.attributeQuery("dataParent", node=min_cone[0], exists=True):
                            mc.addAttr(min_cone, longName="dataParent", niceName="dataParent", attributeType="message")
                        mc.connectAttr(f"{data_node}.min_cone", f"{min_cone[0]}.dataParent", force=True)

                        if not mc.attributeQuery("dataParent", node=max_cone[0], exists=True):
                            mc.addAttr(max_cone, longName="dataParent", niceName="dataParent", attributeType="message")
                        mc.connectAttr(f"{data_node}.max_cone", f"{max_cone[0]}.dataParent", force=True)

                        if mc.listConnections(f"{data_node}.group", source=False, destination=True):
                            group_node = mc.listConnections(f"{data_node}.group", source=False, destination=True)[0]

                            mc.parent(min_cone, group_node)
                            mc.parent(max_cone, group_node)
                            mc.setAttr(f"{min_cone[0]}.translateY", min_translate_flag * min_cone_height * 0.5)
                            mc.setAttr(f"{max_cone[0]}.translateY", max_translate_flag * max_cone_height * 0.5)





# Create meta data node for limbs
def create_conereader_node(node_name, node_type, node_joint):
    # create data node
    data_node = mc.createNode("network", name=node_name)
    # create attribute
    mc.addAttr(data_node, longName="name", niceName="Name", dataType='string')
    mc.addAttr(data_node, longName="node_type", niceName="Node Type", dataType='string')
    mc.addAttr(data_node, longName="joint", niceName="Joint", dataType='string')
    # assign attributes
    mc.setAttr(f"{data_node}.name", node_name, type="string")
    mc.setAttr(f"{data_node}.node_type", node_type, type="string")
    mc.setAttr(f"{data_node}.joint", node_joint, type="string")

    mc.addAttr(data_node, longName="cen_loc", niceName="Central Locator")

    mc.addAttr(data_node, longName="min_loc", niceName="Minimum Locator")

    mc.addAttr(data_node, longName="max_loc", niceName="Maximum Locator")

    mc.addAttr(data_node, longName="live_loc", niceName="Live Locator")

    mc.addAttr(data_node, longName="min_cone", niceName="Min Cone")

    mc.addAttr(data_node, longName="max_cone", niceName="Max Cone")

    mc.addAttr(data_node, longName="group", niceName="Group")

    return data_node


def connect_data_node(data_node, cone_locators):

    cen_loc = cone_locators[0]
    min_loc = cone_locators[1]
    max_loc = cone_locators[2]
    live_loc = cone_locators[3]

    group = mc.listRelatives(cen_loc, parent=True)[0]

    if not mc.attributeQuery("dataParent", node=cen_loc, exists=True):
        mc.addAttr(cen_loc, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.cen_loc", f"{cen_loc}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=min_loc, exists=True):
        mc.addAttr(min_loc, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.min_loc", f"{min_loc}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=max_loc, exists=True):
        mc.addAttr(max_loc, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.max_loc", f"{max_loc}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=live_loc, exists=True):
        mc.addAttr(live_loc, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.live_loc", f"{live_loc}.dataParent", force=True)

    if not mc.attributeQuery("dataParent", node=group, exists=True):
        mc.addAttr(group, longName="dataParent", niceName="dataParent", attributeType="message")
    mc.connectAttr(f"{data_node}.group", f"{group}.dataParent", force=True)


def get_conereader_nodes():
    conereader_nodes = []
    data_nodes = mc.ls(type="network")
    for dn in data_nodes:
        if mc.getAttr(f"{dn}.node_type") == "coneReader":
            conereader_nodes.append(dn)

    return conereader_nodes


def getConeReading():

    try:
        selectedNodes = mc.selectedNodes()
        mainObj = selectedNodes[-1]
        if mc.attributeQuery("coneReading", node=mainObj, exists=True):
            coneReading = mc.getAttr(f"{mainObj}.coneReading")
            return coneReading
        else:
            if mc.listConnections(f"{mainObj}.dataParent", source=True, destination=False):
                data_node = mc.listConnections(f"{mainObj}.dataParent", source=True, destination=True)[0]
                if mc.listConnections(f"{data_node}.group", source=False, destination=True):
                    group = mc.listConnections(f"{data_node}.group", source=False, destination=True)[0]
                    coneReading = mc.getAttr(f"{group}.coneReading")
                    return coneReading
    except:
        return -1

def getMinAngleReading():

    try:
        selectedNodes = mc.selectedNodes()
        mainObj = selectedNodes[-1]
        if mc.attributeQuery("minAngleReading", node=mainObj, exists=True):
            coneReading = mc.getAttr(f"{mainObj}.minAngleReading")
            return coneReading
        else:
            if mc.listConnections(f"{mainObj}.dataParent", source=True, destination=False):
                data_node = mc.listConnections(f"{mainObj}.dataParent", source=True, destination=True)[0]
                if mc.listConnections(f"{data_node}.group", source=False, destination=True):
                    group = mc.listConnections(f"{data_node}.group", source=False, destination=True)[0]
                    coneReading = mc.getAttr(f"{group}.minAngleReading")
                    return coneReading
    except:
        return -1


def getMaxAngleReading():

    try:
        selectedNodes = mc.selectedNodes()
        mainObj = selectedNodes[-1]
        if mc.attributeQuery("maxAngleReading", node=mainObj, exists=True):
            coneReading = mc.getAttr(f"{mainObj}.maxAngleReading")
            return coneReading
        else:
            if mc.listConnections(f"{mainObj}.dataParent", source=True, destination=False):
                data_node = mc.listConnections(f"{mainObj}.dataParent", source=True, destination=True)[0]
                if mc.listConnections(f"{data_node}.group", source=False, destination=True):
                    group = mc.listConnections(f"{data_node}.group", source=False, destination=True)[0]
                    coneReading = mc.getAttr(f"{group}.maxAngleReading")
                    return coneReading
    except:
        return -1


def create_HUD(data_node):
    data_node_name = mc.getAttr(f"{data_node}.name")

    coneReading_HUD = data_node_name + 'coneReading'
    min_reading_HUD = data_node_name + 'min_reading'
    max_reading_HUD = data_node_name + 'max_reading'

    if not mc.headsUpDisplay(coneReading_HUD, exists=True):
        mc.headsUpDisplay( coneReading_HUD, section=1, block=0, blockSize='medium', label='ConeReading',
                           labelFontSize='large', command=getConeReading, attachToRefresh=True)

    if not mc.headsUpDisplay(min_reading_HUD, exists=True):
        mc.headsUpDisplay( min_reading_HUD, section=1, block=1, blockSize='medium', label='MinAngleReading',
                           labelFontSize='large', command=getMinAngleReading, attachToRefresh=True)

    if not mc.headsUpDisplay(max_reading_HUD, exists=True):
        mc.headsUpDisplay( max_reading_HUD, section=1, block=2, blockSize='medium', label='MaxAngleReading',
                           labelFontSize='large', command=getMaxAngleReading, attachToRefresh=True)



def delete_HUD(data_node):

    data_node_name = mc.getAttr(f"{data_node}.name")

    coneReading_HUD = data_node_name + 'coneReading'
    min_reading_HUD = data_node_name + 'min_reading'
    max_reading_HUD = data_node_name + 'max_reading'

    HUD_names = [coneReading_HUD, min_reading_HUD, max_reading_HUD]

    for name in HUD_names:
        if mc.headsUpDisplay(name, exists=True):
            mc.headsUpDisplay(name, remove=True)
        else:
            mc.warning(f"HUD element '{name}' does not exist.")





def ModifyConeShapeCallback(msg, plug, clientData):
    attrName = plug.partialName(useLongNames=True)
    #check the plug data type is Float
    if plug.attribute().apiType() == om.MFn.kNumericAttribute:
        #check the changed attribute name is correct
        if attrName in ["minAngleReading","maxAngleReading"]:
            ModifyConeShape()



def ModifyConeShape():

    selectedNodes = mc.ls(selection=True)

    for node in selectedNodes:
        if mc.listConnections(f"{node}.dataParent", source=True, destination=False):
            data_node = mc.listConnections(f"{node}.dataParent", source=True, destination=True)[0]
            if (mc.listConnections(f"{data_node}.min_cone", source=False, destination=True) and
            mc.listConnections(f"{data_node}.max_cone", source=False, destination=True)):
                min_cone = mc.listConnections(f"{data_node}.min_cone", source=False, destination=True)[0]
                max_cone = mc.listConnections(f"{data_node}.max_cone", source=False, destination=True)[0]

                min_history = mc.listHistory(min_cone)
                max_history = mc.listHistory(max_cone)
                min_cone_node = next(node for node in min_history if mc.nodeType(node) == "makeNurbCone")
                max_cone_node = next(node for node in max_history if mc.nodeType(node) == "makeNurbCone")

                min_loc_node = mc.listConnections(f"{data_node}.min_loc", source=False, destination=True)[0]
                max_loc_node = mc.listConnections(f"{data_node}.max_loc", source=False, destination=True)[0]

                min_translate_flag = 1
                max_translate_flag = 1

                if mc.getAttr(f"{min_loc_node}.translateY") < 0:
                    min_translate_flag = -1

                if mc.getAttr(f"{max_loc_node}.translateY") < 0:
                    max_translate_flag = -1

                min_cone_radius = abs(mc.getAttr(f"{min_loc_node}.translateX"))
                min_cone_height = abs(mc.getAttr(f"{min_loc_node}.translateY"))
                max_cone_radius = abs(mc.getAttr(f"{max_loc_node}.translateX"))
                max_cone_height = abs(mc.getAttr(f"{max_loc_node}.translateY"))

                min_cone_hr = abs(min_cone_height / min_cone_radius)
                max_cone_hr = abs(max_cone_height / max_cone_radius)

                min_cone_radius = (4 / (min_cone_hr**2 + 1)) ** 0.5 * min_translate_flag
                max_cone_radius = (4 / (max_cone_hr**2 + 1)) ** 0.5 * max_translate_flag
                #r**2 + r**2 * min_cone_hr**2 = 4

                mc.setAttr(f"{min_cone_node}.radius", min_cone_radius)
                mc.setAttr(f"{max_cone_node}.radius", max_cone_radius)

                mc.setAttr(f"{min_cone_node}.heightRatio", min_cone_hr)
                mc.setAttr(f"{max_cone_node}.heightRatio", max_cone_hr)

                min_new_height = abs(min_cone_radius) * min_cone_hr
                max_new_height = abs(max_cone_radius) * max_cone_hr

                mc.setAttr(f"{min_cone}.translateY", min_translate_flag * min_new_height * 0.5)
                mc.setAttr(f"{max_cone}.translateY", max_translate_flag * max_new_height * 0.5)


def registerNodeDirtyPlugCallback(nodeName: str):

    # add the node to selectionlist and get the Mobject
    selectionList = om.MSelectionList()
    selectionList.add(nodeName)
    nodeMObject = selectionList.getDependNode(0)

    #bind the callback function and return the id as reference
    id = om.MNodeMessage.addNodeDirtyPlugCallback(nodeMObject, ModifyConeShapeCallback)
    return id

def removeCallback(identifier):
    om.MMessage.removeCallback(identifier)
    logger.info(f"Callback with ID {identifier} has been removed")

def getCallbacks(nodeName):
    selectionList = om.MSelectionList()
    selectionList.add(nodeName)
    nodeMObject = selectionList.getDependNode(0)
    #collect all callback identifiers on that node (cast to list not callback array)
    identifiers = list(om.MMessage.nodeCallbacks(nodeMObject))
    return identifiers

def removeCallbacksOnNode(nodeName):
    identifiers = getCallbacks(nodeName)
    for identifier in identifiers:
        removeCallback(identifier)


