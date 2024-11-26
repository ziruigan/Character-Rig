import maya.cmds as mc
import json


def mirror_pose(controls, mirror_function="behavior", side="Left"):
    """
                  mirroring posing from one side to another, make sure the transformation info is restored back to the controls
                  call storeTransformationBackToControl(control) ahead
                  Args:
                      controls (list) : list of controls which would be contributing to a particular shape in FACS_HUB
                      mirror_function(string) : behavioral mirroring would have the controls converge or diverge from the
                                                mirroring plane
                      side (string) : the side where controls will be mirrored from
                  Returns:
                  """
    if side == "Left":
        other_side = "Right"
    elif side == "Right":
        other_side = "Left"
    else:
        mc.error(f"Invalid side name: {side}")
        return

    for control in controls:
        translate = mc.getAttr(f"{control}.translate")[0]
        rotate = mc.getAttr(f"{control}.rotate")[0]
        scale = mc.getAttr(f"{control}.scale")[0]
        mirrored_control = control.replace(side, other_side)
        if mirror_function == "behavior":
            mirrored_translate = (-translate[0], -translate[1], -translate[2])
            mirrored_rotate = rotate[:]
            mirrored_scale = scale[:]

            mc.setAttr(f"{mirrored_control}.translate", *mirrored_translate)
            mc.setAttr(f"{mirrored_control}.rotate", *mirrored_rotate)
            mc.setAttr(f"{mirrored_control}.scale", *mirrored_scale)

        elif mirror_function == "orientation":
            mirrored_translate = (-translate[0], translate[1], translate[2])
            mirrored_rotate = (rotate[0], -rotate[1], -rotate[2])
            mirrored_scale = scale[:]

            mc.setAttr(f"{mirrored_control}.translate", *mirrored_translate)
            mc.setAttr(f"{mirrored_control}.rotate", *mirrored_rotate)
            mc.setAttr(f"{mirrored_control}.scale", *mirrored_scale)

        else:
            raise RuntimeError(f"Invalid mirror function: {mirror_function}")


def flip_pose(controls):
    pass

def collect_pose_data(controls):
    poseData = {}
    for control in controls:
        controlWorldMatrix = mc.xform(control, matrix=True, query=True, worldSpace=True)
        localTranslation = mc.getAttr(f"{control}.translate")[0]
        localRotation = mc.getAttr(f"{control}.rotate")[0]
        localScale = mc.getAttr(f"{control}.scale")[0]

        poseData[control] = {"worldMatrix":controlWorldMatrix,
                             "localTrs":(localTranslation,localRotation,localScale)}

    return poseData

def apply_pose_data(poseData, space="local"):
    controls = list(poseData.keys())
    for control in controls:
        if space == "local":
            mc.setAttr(f"{control}.translate", *poseData.get(control).get("localTrs")[0])
            mc.setAttr(f"{control}.rotate", *poseData.get(control).get("localTrs")[1])
            mc.setAttr(f"{control}.scale", *poseData.get(control).get("localTrs")[2])
        elif space == "world":
            matrix = poseData.get(control).get("worldMatrix")
            mc.xform(control, matrix=matrix, worldSpace=True)



def export_pose(controls, filepath):
    poseData = collect_pose_data(controls)
    with open(filepath, "w") as fp:
        json.dump(poseData, fp, indent=4)

    print(f"Pose data exported to {filepath} successfully")



def import_pose(filepath, space="local"):
    with open(filepath, "r") as fp:
        poseData = json.load(fp)
    apply_pose_data(poseData, space=space)
    return poseData