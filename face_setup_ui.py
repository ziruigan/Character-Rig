from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as mc
import os
import FACS_setup as fs
import pose_library as pl

import importlib
importlib.reload(fs)
importlib.reload(pl)

Preset_Dir = r"E:\Maya_Document\FacePresets"


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__(parent=maya_main_window())
        self.setWindowTitle('Face Setup UI')
        self.initData()
        self.initUI()


    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #create layout
        mainlayout = QVBoxLayout()
        central_widget.setLayout(mainlayout)
        mainlayout.setAlignment(Qt.AlignTop)
        mainlayout.setContentsMargins(10, 10, 10, 10)
        mainlayout.setSpacing(5)

        tabWidget = QTabWidget()
        tabFACS = QWidget()
        FACSLayout = QVBoxLayout()
        tabFACS.setLayout(FACSLayout)

        self.poseListWidget = QListWidget()
        newPoseBtn = QPushButton('Add New Pose')
        addCtrlToPoseBtn = QPushButton('Add Controls to Pose')
        updatePoseBtn = QPushButton('Update Pose')
        assumePoseBtn = QPushButton('Assume Pose')

        FACSLayout.setContentsMargins(5, 5, 5, 5)
        FACSLayout.addWidget(self.poseListWidget)
        FACSLayout.addWidget(newPoseBtn)
        FACSLayout.addWidget(addCtrlToPoseBtn)
        FACSLayout.addWidget(updatePoseBtn)
        FACSLayout.addWidget(assumePoseBtn)

        tabPreset = QTabWidget()
        presetLayout = QVBoxLayout()
        tabPreset.setLayout(presetLayout)
        self.presetListWidget = QListWidget()
        presetLayout.addWidget(self.presetListWidget)

        addPresetBtn = QPushButton('Add Preset')
        applyPresetBtn = QPushButton('Apply Preset')
        editPresetBtn = QPushButton('Edit Preset')
        deletePresetBtn = QPushButton('Delete Preset')
        presetLayout.addWidget(addPresetBtn)
        presetLayout.addWidget(applyPresetBtn)
        presetLayout.addWidget(editPresetBtn)
        presetLayout.addWidget(deletePresetBtn)

        addPresetBtn.clicked.connect(self.addPreset)
        applyPresetBtn.clicked.connect(self.applyPreset)
        editPresetBtn.clicked.connect(self.editPreset)
        deletePresetBtn.clicked.connect(self.deletePreset)

        tabWidget.addTab(tabFACS, 'FACS Shapes')
        tabWidget.addTab(tabPreset, 'Presets')

        mirrorLtoRBtn = QPushButton('Mirror Left To Right')
        mirrorRtoLBtn = QPushButton('Mirror Right To Left')

        mirrorLayout = QHBoxLayout()
        mirrorLayout.addWidget(mirrorLtoRBtn)
        mirrorLayout.addWidget(mirrorRtoLBtn)
        mirrorLtoRBtn.setStyleSheet('QPushButton {background-color: #426ff5}')
        mirrorRtoLBtn.setStyleSheet('QPushButton {background-color: #426ff5}')

        resetPoseBtn = QPushButton('Reset Pose')
        resetPoseBtn.setStyleSheet('QPushButton{background-color: #f5bf42; color: black}')
        mainlayout.addWidget(tabWidget)
        mainlayout.addLayout(mirrorLayout)
        mainlayout.addWidget(resetPoseBtn)

        newPoseBtn.clicked.connect(self.addPose)
        updatePoseBtn.clicked.connect(self.updatePose)
        addCtrlToPoseBtn.clicked.connect(self.addCtrlToPose)
        assumePoseBtn.clicked.connect(self.assumePose)
        resetPoseBtn.clicked.connect(self.resetPose)
        mirrorLtoRBtn.clicked.connect(lambda x: self.mirrorPose(side="Left"))
        mirrorRtoLBtn.clicked.connect(lambda x: self.mirrorPose(side="Right"))


        self.poseListWidget.doubleClicked.connect(self.onPoseDoubleClicked)
        self.presetListWidget.doubleClicked.connect(self.applyPreset)
        self.updatePresetList()
        self.updatePoseList()
        self.setSelectedPose(0)

    def initData(self):
        self.presetDir = Preset_Dir


    def updatePoseList(self):
        poseNames = mc.listAttr(f"{fs.FACS_HUB}", userDefined=True)
        poseNames = sorted(poseNames)
        self.poseListWidget.clear()
        self.poseListWidget.addItems(poseNames)

    def updatePresetList(self):
        self.presetListWidget.clear()
        presetFiles = [file for file in os.listdir(self.presetDir) if
                       file.startswith('preset') and file.endswith('.json')]

        presetNames = [os.path.splitext(file)[0].removeprefix('preset') for file in presetFiles]

        self.presetListWidget.addItems(presetNames)

    def addPreset(self):
        presetName = self.showNameDialog()
        if not presetName:
            return
        controls = fs.getFaceControls()
        fp = os.path.join(self.presetDir, f"preset{presetName.capitalize()}.json")
        for control in controls:
            fs.storeTransformationBackToControl(control)
        pl.export_pose(controls, fp)
        self.updatePresetList()

    def deletePreset(self):
        selectedItems = self.presetListWidget.selectedItems()
        if selectedItems:
            result = QMessageBox.question(self, 'Confirm Deletion',
                                          "Are you sure you want to delete the selected preset?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result == QMessageBox.Yes:
                for item in selectedItems:
                    self.presetListWidget.takeItem(self.presetListWidget.row(item))
                    filepath = os.path.join(self.presetDir, f"preset{item.text()}.json")
                    os.remove(filepath)
                    print(f"{filepath} has been deleted")

    def applyPreset(self):
        selectedItems = self.presetListWidget.selectedItems()
        if selectedItems:
            filepath = os.path.join(self.presetDir, f"preset{selectedItems[0].text()}.json")
            pl.import_pose(filepath, space="local")

    def editPreset(self):
        selectedPreset = self.presetListWidget.currentItem()
        if not selectedPreset:
            return
        presetName = selectedPreset.text()
        controls = fs.getFaceControls()
        fp = os.path.join(self.presetDir, f"preset{presetName.text()}.json")
        pl.export_pose(controls, fp)

    def addPose(self):
        poseName = self.showNameDialog()
        if not poseName:
            return
        #can be more delicate about exmaning the flags for actual controls
        controls = mc.ls(selection=True, type="transform")
        #[control for control in contrls if "isControl" in mc.listAttr("f{control}", userDefined=True)]
        fs.addControlsToShape(controls,poseName)
        self.updatePoseList()

    def setSelectedPose(self, index):
        selectedItem = self.poseListWidget.item(index)
        selectedItem.setSelected(True)

    def getSelectedPose(self):
        selectedItem = self.poseListWidget.currentItem()
        if not selectedItem:
            return
        selectedPoseName = selectedItem.text()
        return selectedPoseName

    def updatePose(self):
        selectedPoseName = self.getSelectedPose()
        if not selectedPoseName:
            return
        controls = mc.ls(selection=True, type="transform")
        fs.editShape(controls, selectedPoseName)

    def assumePose(self):
        selectedPoseName = self.getSelectedPose()
        if not selectedPoseName:
            return
        fs.assumePose(selectedPoseName)

    def resetPose(self):
        fs.resetAllControls()


    def mirrorPose(self, side="Left"):
        fs.mirrorPose(side=side)

    def onPoseDoubleClicked(self):
        selectedPoseName = self.getSelectedPose()
        if not selectedPoseName:
            return
        controls = fs.getControlsFromFACSAttr(f"{fs.FACS_HUB}.{selectedPoseName}")
        mc.select(controls)


    def showNameDialog(self):
        dialog = PoseNameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.nameEdit.text()
            return name

        return ""

    def addCtrlToPose(self):
        selectedPoseName = self.getSelectedPose()
        if not selectedPoseName:
            return
        controls = mc.ls(selection=True, type="transform")
        fs.addControlsToShape(controls, selectedPoseName)


class PoseNameDialog(QDialog):
    def __init__(self, parent=None):
        super(PoseNameDialog, self).__init__(parent)

        self.setWindowTitle('Enter Pose Name')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel('Please enter the pose name')
        self.layout.addWidget(self.label)

        self.nameEdit = QLineEdit()
        self.layout.addWidget(self.nameEdit)

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
