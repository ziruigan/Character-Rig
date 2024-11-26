from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as mc
import IKFKSwitchMatch as ifm
import limb_data_node as ldn
import ik_fk_match_callback as ifmc


import importlib
importlib.reload(ifm)
importlib.reload(ldn)
importlib.reload(ifmc)


#### doing UI in maya.cmds
def to_ik_callback(*args):
    ikfk_match = ifm.IKFKMatching.create()
    #in fk mode switch to ik
    if not ikfk_match.get_ik_state():
        ikfk_match.to_ik()
    else:
        print("The system is already in ik mode")

def to_fk_callback(*args):
    ikfk_match = ifm.IKFKMatching.create()
    # in ik mode switch to fk
    if ikfk_match.get_ik_state():
        ikfk_match.to_fk()
    else:
        print("The system is already in fk mode")

def create_window():
    # check if the window exists already, delete it if yes
    if mc.window("myWindow", exists=True):
        mc.deleteUI("myWindow")

    # create the window
    window = mc.window("myWindow", title="IKFKSwitchMatch", widthHeight=(200, 100))

    # create layout
    mc.columnLayout(adjustableColumn=True)
    # create separator
    mc.separator(height=5, style="none")
    # create label
    mc.text("Select a single IK or FK control of the limb you wan to switch and match." 
            "\nThis can be either an arm or leg Control", font="boldLabelFont")
    # create separator
    mc.separator(height=10, style="in")
    #create buttons for matching
    mc.button(label="Match IK to FK", command=to_fk_callback)
    mc.button(label="Match FK to IK", command=to_ik_callback)

    #show the window
    mc.showWindow(window)

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__(parent=maya_main_window())
        self.setWindowTitle('IKFK Matching Tool')
        self.initData()
        self.initUI()


    def initUI(self):
        # create central widget
        centralWidget = QWidget()
        # set central widget
        self.setCentralWidget(centralWidget)

        # create layout
        layout = QVBoxLayout()
        # set layour to central widget
        centralWidget.setLayout(layout)
        # set alignment for layout
        layout.setAlignment(Qt.AlignTop)
        # set content margins on four sides
        layout.setContentsMargins(10, 10, 10, 10)
        # set spacing for content in the layout
        layout.setSpacing(5)

        # create the font variable
        font = QFont("Comic Sans MS", 10, QFont.Bold)

        # create UI layout for dropdown selection
        m1_layout = QHBoxLayout()
        m1_layout.setAlignment(Qt.AlignLeft)
        m1_layout.setSpacing(20)
        self.m1_checkbox = QCheckBox()
        # create label
        self.m1_label = QLabel("Select an IKFK system in the dropdown")
        # set the font for label
        self.m1_label.setFont(font)
        m1_layout.addWidget(self.m1_checkbox)
        m1_layout.addWidget(self.m1_label)

        # create UI layout for the direct control selection
        m2_layout = QHBoxLayout()
        m2_layout.setAlignment(Qt.AlignLeft)
        m2_layout.setSpacing(20)
        self.m2_checkbox = QCheckBox()
        # create label
        self.m2_label = QLabel("Select a control that is part of the IKFK system")
        # set the font for label
        self.m2_label.setFont(font)
        m2_layout.addWidget(self.m2_checkbox)
        m2_layout.addWidget(self.m2_label)


        # create the dropbox for limb selection
        self.dropDownList = QComboBox()
        self.populateDropDownList()

        # create the buttons
        ik2FKBtn = QPushButton('Match IK to FK')
        fk2IKBtn = QPushButton('Match FK to IK')

        # bond the callback function to the button clicked
        ik2FKBtn.clicked.connect(self.btnCmdToFK)
        fk2IKBtn.clicked.connect(self.btnCmdToIK)

        # create button group to make checkboxes exclucive to each other
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.m1_checkbox, id=0)
        self.button_group.addButton(self.m2_checkbox, id=1)
        self.button_group.buttonClicked.connect(self.checkBoxClicked)
        # set the default selection to the first checkbox
        self.m1_checkbox.setChecked(True)
        self.m1_label.setEnabled(True)
        self.m2_label.setEnabled(False)

        self.callbackRegsiterBtn = QPushButton('Register Callbacks')
        self.callbackRegsiterBtn.setCheckable(True)
        self.callbackRegsiterBtn.clicked.connect(self.btnCmdRegisterCallbacks)

        if self.callback_registered:
            self.callbackRegsiterBtn.setText('Deregister Callbacks')
            self.callbackRegsiterBtn.setChecked(True)

        self.selection_display = QLabel("No control being selected")
        self.selection_display.setFont(font)
        self.bind_selectioncallbacks()


        # add widget from top to bottom
        layout.addLayout(m1_layout)
        layout.addWidget(self.dropDownList)
        layout.addWidget(self.createSepartorLine())
        layout.addLayout(m2_layout)
        layout.addWidget(self.selection_display)
        layout.addWidget(self.createSepartorLine())
        layout.addWidget(ik2FKBtn)
        layout.addWidget(fk2IKBtn)
        layout.addWidget(self.createSepartorLine())
        layout.addWidget(self.callbackRegsiterBtn)



    def initData(self):
        # inirialize all the limb nodes for IKFK Matching
        self.limb_nodes = ldn.get_limb_nodes()
        # initialize all the switch control for binding callbacks
        self.switch_controls = []
        # try to find the callbacks that already been registered
        self.callback_registered = []
        for data_node in self.limb_nodes:
            switch_control = mc.listConnections(f"{data_node}.switch_control", destination=True, source=False)
            if switch_control:
                self.switch_controls.append(switch_control[0])
                self.callback_registered.extend(switch_control[0])


    def selection_check(self, widget):
        selectionList = mc.ls(sl=True)
        selected_valid = None
        print("callback called")
        for selected in selectionList:
            if mc.attributeQuery("dataParent", node=selected, exists=True):
                if mc.listConnections(f"{selected}.dataParent", source=True, destination=False, type="network"):
                    widget.setText(f"{selected} is being selected")
                    widget.setStyleSheet("QLable {color : #3cb371;}")
                    selected_valid = selected
                    break

        if selected_valid is None:
            widget.setText("No valid control being selected")
            widget.setStyleSheet("QLable {color : #ff6347;}")

    def bind_selectioncallbacks(self):
        self.callback_id = om.MEventMessage.addEventCallback("SelectionChanged", self.selection_check, self.selection_display)

    def unbind_callbacks(self):
        if self.callback_id:
            om.MMessage.removeCallback(self.callback_id)
            self.callback_id = None

    def closeEvent(self, event):
        super(MyWindow, self).closeEvent(event)
        self.unbind_callbacks()
        print("Closing window")


    def populateDropDownList(self):
        displaynames = []
        for limb_node in self.limb_nodes:
            limb_type = mc.getAttr(f"{limb_node}.node_type")
            limb_side = mc.getAttr(f"{limb_node}.side")
            displaynames.append(f"{limb_side} {limb_type}")
        self.dropDownList.addItems(displaynames)

    def createSepartorLine(self):
        # create a line for seperation
        separateLine = QFrame()
        # set the style of the seperating line
        separateLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        # set the size of the seperating line
        separateLine.setLineWidth(1.0)
        separateLine.setFixedHeight(10)
        return separateLine

    # callback function for checkbox clicked     checkbox: the checkbox clieced
    def checkBoxClicked(self, checkbox):
        if checkbox == self.m1_checkbox:
            print("You are using dropdown to choose which system to match")
            self.m1_label.setEnabled(True)
            self.m2_label.setEnabled(False)
            # self.dropDownList.setVisible(True)
        elif checkbox == self.m2_checkbox:
            print("You are using direct selection to choose which system to match")
            self.m1_label.setEnabled(False)
            self.m2_label.setEnabled(True)
            # self.dropDownList.setVisible(False)
        else:
            return


    # ToFK callback function

    def btnCmdToFK(self):
        # check to see which method the matching is using
        # if we are using dropdown, find the index and pass the data node
        if self.button_group.checkedId() == 0:
            data_node = self.limb_nodes[self.dropDownList.currentIndex()]
        else:
            data_node = None

        ikfk_match = ifm.IKFKMatching.create(data_node=data_node)
        if not ikfk_match:
            return

        if ikfk_match.get_ik_state():
            ikfk_match.to_fk()
        else:
            print("The limb system is already in FK mode.")

    # To IK callback function
    def btnCmdToIK(self):

        if self.button_group.checkedId() == 0:
            data_node = self.limb_nodes[self.dropDownList.currentIndex()]
        else:
            data_node = None

        ikfk_match = ifm.IKFKMatching.create(data_node=data_node)
        if not ikfk_match:
            return

        if not ikfk_match.get_ik_state():
            ikfk_match.to_ik()
        else:
            print("The limb system is already in IK mode.")


    def btnCmdRegisterCallbacks(self, state):
        if state:
            self.callbackRegsiterBtn.setText("Deregister Callbacks")
            # bind callbacks for every switch control
            for switch_control in self.switch_controls:
                ifmc.registerAttributeChangeCallback(switch_control)
        else:
            self.callbackRegsiterBtn.setText("Register Callbacks")
            # unbind callbacks for every switch control
            for switch_control in self.switch_controls:
                ifmc.removeCallbacksOnNode(switch_control)


def openUI():
    global win
    try:
        win.close()
    except Exception:
        pass

    win = MyWindow()
    win.show()
    return win
