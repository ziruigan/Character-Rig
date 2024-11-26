from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as mc
import muscle_rig as mr

import importlib
importlib.reload(mr)


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__(parent=maya_main_window())
        self.setWindowTitle('Muscle Joints Group Setup UI')
        self.initData()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.namelabel = QLabel('Please enter the muscle name')
        layout.addWidget(self.namelabel)

        self.nameEdit = QLineEdit()
        layout.addWidget(self.nameEdit)

        self.originattachlabel = QLabel('Please enter the origin attach object name')
        layout.addWidget(self.originattachlabel)

        self.originattachEdit = QLineEdit()
        layout.addWidget(self.originattachEdit)

        self.insertionattachlabel = QLabel('Please enter the insertion attach object name')
        layout.addWidget(self.insertionattachlabel)

        self.insertionattachEdit = QLineEdit()
        layout.addWidget(self.insertionattachEdit)

        self.strechfactorlabel = QLabel('Please enter the stretch factor')
        layout.addWidget(self.strechfactorlabel)

        self.stretchfactorEdit = QLineEdit()
        layout.addWidget(self.stretchfactorEdit)

        self.compressfactorlabel = QLabel('Please enter the compress factor')
        layout.addWidget(self.compressfactorlabel)

        self.compressfactorEdit = QLineEdit()
        layout.addWidget(self.compressfactorEdit)

        createMuscleBtn = QPushButton('Create Muscle Joints')
        editBtn = QPushButton('Edit the Muscle Joints')
        updateBtn = QPushButton('Update the Muscle Joints')
        mirrorBtn = QPushButton('Mirror the Muscle Joints')
        resetBtn = QPushButton('Reset the Muscle Joints')
        deleteBtn = QPushButton('Delete the Muscle Joints')

        layout.addWidget(createMuscleBtn)
        layout.addWidget(editBtn)
        layout.addWidget(updateBtn)
        layout.addWidget(mirrorBtn)
        layout.addWidget(resetBtn)
        layout.addWidget(deleteBtn)

        createMuscleBtn.clicked.connect(self.createMuscleJoints)
        editBtn.clicked.connect(self.editMuscleJoints)
        updateBtn.clicked.connect(self.updateMuscleJoints)
        mirrorBtn.clicked.connect(self.mirrorMuscleJoints)
        resetBtn.clicked.connect(self.resetMuscleJoints)
        deleteBtn.clicked.connect(self.deleteMuscleJoints)

        self.bind_selectioncallbacks()


    def initData(self):
        self.muscleOrigin = None
        self.muscleInsertion = None
        self.muscleStretchFactor = None
        self.muscleJointGroup = None



    def createMuscleJoints(self):

        muscleJointsName = self.nameEdit.text()
        originAttachName = self.originattachEdit.text()
        insertionAttachName = self.insertionattachEdit.text()
        stretchFactor = float(self.stretchfactorEdit.text())
        compressFactor = float(self.compressfactorEdit.text())

        muscleJointGrp = mr.MuscleJoint.createFromAttachObjs(muscleJointsName, originAttachName, insertionAttachName,
                                                             stretchFactor, compressFactor)


        self.muscleOrigin = muscleJointGrp.muscleOrigin
        self.muscleInsertion = muscleJointGrp.muscleInsertion
        self.muscleDriver = muscleJointGrp.muscleDriver
        self.muscleJointGroup=muscleJointGrp


    def editMuscleJoints(self):
        if self.muscleJointGroup:
            self.muscleJointGroup.edit()
        else:
            raise RuntimeError("please select element on the muscle Joints group to refresh reference")


    def updateMuscleJoints(self):
        if self.muscleJointGroup:
            self.muscleJointGroup.update()
        else:
            raise RuntimeError("please select element on the muscle Joints group to refresh reference")

    def mirrorMuscleJoints(self):

        attachmentNames = self.showAttachmentNameDialog()
        if not attachmentNames:
            raise RuntimeError("please enter attachment objs for mirroring")

        muscleOriginAttachObj = attachmentNames[0]
        muscleInsertionAttachObj = attachmentNames[1]
        if self.muscleJointGroup:
            muscleJointsGrp = mr.mirror(self.muscleJointGroup, muscleOriginAttachObj, muscleInsertionAttachObj)

            self.muscleJointGroup = muscleJointsGrp

        else:
            if self.muscleOrigin and self.muscleInsertion and self.muscleDriver:
                muscleJointsGrp = mr.mirrorWoReference(self.muscleOrigin, self.muscleInsertion, self.muscleDriver,
                                                       muscleOriginAttachObj,
                                                       muscleInsertionAttachObj)

                self.muscleJointGroup = muscleJointsGrp

            else:
                raise RuntimeError("please select element on the muscle Joints group to refresh reference")



    def resetMuscleJoints(self):

        stretchFactor = float(self.stretchfactorEdit.text())
        compressFactor = float(self.compressfactorEdit.text())
        muscleOriginAttachObj = self.originattachEdit.text()
        muscleInsertionAttachObj = self.insertionattachEdit.text()

        if self.muscleOrigin and self.muscleInsertion and self.muscleDriver:
            muscleJointsGrp = mr.resetMuscleJoints(self.muscleOrigin, self.muscleInsertion, self.muscleDriver, muscleOriginAttachObj,
                                                   muscleInsertionAttachObj,compressionFactor=compressFactor, stretchFactor=stretchFactor,
                                                   stretchOffset=None, compressionOffset=None)
        else:
            raise RuntimeError("please select element on the muscle Joints group to refresh reference")

        self.muscleJointGroup = muscleJointsGrp



    def deleteMuscleJoints(self):
        if self.muscleJointGroup:
            self.muscleJointGroup.delete()
        else:
            raise RuntimeError("please select element on the muscle Joints group to refresh reference")


    def selection_check(self, widgets):
        try:
            for node in mc.ls(sl=True):
                muscleName = node.split("_")[0]
                Origin = muscleName + "_muscleOrigin"
                Insertion = muscleName + "_muscleInsertion"
                Driver = muscleName + "_muscleDriver"
                if mc.objExists(Origin) and mc.objExists(Insertion) and mc.objExists(Driver):
                    self.muscleOrigin = Origin
                    self.muscleInsertion = Insertion
                    self.muscleDriver = Driver
                    widgets[0].setText(muscleName)
                    widgets[1].setText(mc.listRelatives(self.muscleOrigin, p=True)[0])
                    widgets[2].setText(mc.listRelatives(self.muscleInsertion, p=True)[0])

                    break

        except:
            raise RuntimeError("Selection check failed")





    def showAttachmentNameDialog(self):
        dialog = MirrorAttachDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            originAttachName = dialog.mirrorOriginAttachEdit.text()
            insertionAttachName = dialog.mirrorInsertionAttachEdit.text()
            return (originAttachName, insertionAttachName)

        return ""



    def bind_selectioncallbacks(self):
        self.callback_id = om.MEventMessage.addEventCallback("SelectionChanged", self.selection_check,
                                                             [self.nameEdit, self.originattachEdit, self.insertionattachEdit])

    def unbind_callbacks(self):
        if self.callback_id:
            om.MMessage.removeCallback(self.callback_id)
            self.callback_id = None

    def closeEvent(self, event):
        super(MyWindow, self).closeEvent(event)
        self.unbind_callbacks()
        print("Closing window")


class MirrorAttachDialog(QDialog):
    def __init__(self, parent=None):
        super(MirrorAttachDialog, self).__init__(parent)

        self.setWindowTitle('Enter the attachment for mirroring')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.originLabel = QLabel('Please enter the Origin Attach Obj name for mirroring')
        self.layout.addWidget(self.originLabel)

        self.mirrorOriginAttachEdit = QLineEdit()
        self.layout.addWidget(self.mirrorOriginAttachEdit)

        self.insertionLabel = QLabel('Please enter the Insertion Attach Obj name for mirroring')
        self.layout.addWidget(self.insertionLabel)

        self.mirrorInsertionAttachEdit = QLineEdit()
        self.layout.addWidget(self.mirrorInsertionAttachEdit)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)





def openUI():
    global win
    try:
        win.close()
    except Exception:
        pass

    win = MyWindow()
    win.show()
    return win



