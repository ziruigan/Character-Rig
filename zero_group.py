import maya.cmds as mc

def create_zero_group(node, group_name = None, group_type = "transform"):
    
    if not group_name:
        group_name = node.replace("Control", "ControlGroup")

    if group_type == "transform":
        group = mc.group(em = True, w = True, name=group_name)

    if group_type == "joint":
        mc.select(cl=True)
        group = mc.joint(name = group_name)
        mc.setAttr("{0}.drawStyle".format(group), 2)

    mc.matchTransform(group, node)
    node_parent = mc.listRelatives(node, parent=True)
    if node_parent:
        mc.parent(group, node_parent)
    mc.parent(node, group)
    return group

def create_control(shape_name = "octagonPoint"):
    control = mel.eval('createControlShapes("' + shape_name +'")')
    zero_group = create_zero_group(control, group_name="FKControl1", group_type= "joint")
    control_shape = get_shape(control)
    mc.parent(control_shape, zero_group, r = True, s = True)
    mc.delete(control)
    mc.rename(control_shape, "FKControlShape1")
    mc.setAttr("{0}.drawStyle".format(zero_group), 2)


def get_shape(obj, shapeTypes = None, longNames = False):
    if shapeTypes is None:
        shapeTypes = ['mesh', 'nurbsCurve', 'nurbsSurface']
    
    ntype = mc.objectType(obj)
    if ntype in shapeTypes:
        return obj
    
    shapes = mc.listRelatives(obj, shapes=True, noIntermediate=True, f = longNames)
    if shapes and ntype == 'transform' and mc.objectType(shapes[0]) in shapeTypes:
        return shapes[0]
    
    return None


def set_up_IKSpineControls():
    jointLocations = []
    selectedJoints = mc.ls(sl=True)
    for node in selectedJoints:
        jointLoc = mc.xform(node, query = True, worldSpace = True, translation = True)
        jointLocations.append(jointLoc)
    scurve = mc.curve(degree = 1, p = jointLocations)
    BackIKHandle = mc.ikHandle(sj = selectedJoints[0], ee = selectedJoints[-1], c = scurve, roc = True, sol = "ikSplineSolver", ccv = False, pcv = False)

    BackSetupGrp = mc.group (empty =True, name = 'BackSetupGroup')
    mc.parent(BackIKHandle, BackSetupGrp)
    mc.parent(scurve, BackSetupGrp)

    curveDegree = mc.getAttr(scurve + '.degree')
    curveSpans = mc.getAttr(scurve + '.spans')
    cvTotal = curveDegree + curveSpans
    for i in range (0, cvTotal):
    
        #selects curve
        mc.ls(scurve)
        #creates variable for curve cv #i
        cvSelection = (scurve + '.cv [%s]' %i)
        #selects CV
        mc.ls (cvSelection)
        #creates cluster name variable
        clusterName = ('%s_Cluster%s_' %(scurve, i))
        #creates cluster
        cluster = mc.cluster(cvSelection, name = clusterName)
        #parents cluster under the macro cluster group
        #mc.parent(clusterName, BackSetupGrp)
   
        ikcontrol = create_control(shape_name = "octahedron", name = "IKControl1")
        mc.matchTransform(ikcontrol, cluster)
        mc.setAttr(ikcontrol + ".s", 100, 100, 100)  
    
        #mc.parentConstraint(ikcontrol, cluster)  //parent constraint control to cluster
        #mc.makeIdentity(ikcontrol, apply=True, t=True, r=True, s=True)      //freeze scale                                
        #ikcontrolgroup = create_zero_group(ikcontrol, group_name = None, group_type = "joint") //create zero group
        
        



