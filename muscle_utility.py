import maya.cmds as mc

def getTrapeziusMuscles():
    trapeziusData = {}
    for side in ['left', 'right']:
        trapeziusData[side] = {}

    for