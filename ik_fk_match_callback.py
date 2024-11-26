import logging
import maya.api.OpenMaya as om
import IKFKSwitchMatch as ifm

#initiate logging with module name
logger = logging.getLogger(__name__)

def ikfkMatchingCallback(msg, plug, otherPlug, clientData):
    # using bit mask to check if the action is an AttributeSet change
    if msg & om.MNodeMessage.kAttributeSet:
        '''
        #using plug to grab the node changing in MObject & the dependency node
        nodeMObject = plug.node()
        mfnNode = om.MFnDependencyNode(nodeMObject)
        '''

        # get the changed attribute name from plug
        attrName = plug.partialName(useLongNames=True)
        #check the plug data type is Enum
        if plug.attribute().apiType() == om.MFn.kEnumAttribute:
            #check the changed attribute name is correct
            if attrName == "IKFK_Matching":
                # convert to Enum index
                value = plug.asInt()
                if value == 0:
                    logger.info("Set to FK")
                    ikfk_match = ifm.IKFKMatching.create()
                    ikfk_match.to_fk()
                elif value == 1:
                    logger.info("Set to IK")
                    ikfk_match = ifm.IKFKMatching.create()
                    ikfk_match.to_ik()
                else:
                    logger.error("IKFK Switch Match failed")

def registerAttributeChangeCallback(nodeName: str):

    # add the node to selectionlist and get the Mobject
    selectionList = om.MSelectionList()
    selectionList.add(nodeName)
    nodeMObject = selectionList.getDependNode(0)

    #bind the callback function and return the id as reference
    id = om.MNodeMessage.addAttributeChangedCallback(nodeMObject, ikfkMatchingCallback)
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