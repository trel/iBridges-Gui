from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5 import QtGui

import sys

class irodsBrowser(QMainWindow):
    def __init__(self, widget, ic):
        super(irodsBrowser, self).__init__()
        loadUi("irodsBrowserMain.ui", self)
        self.ic = ic
        self.widget = widget

        #some placeholder variables to catch information
        self.currentBrowserRow = 0

        #Main widget --> browser
        self.irodsRoot = self.ic.session.collections.get("/"+ic.session.zone+"/home")
        self.collTable.setColumnWidth(1,399)
        self.collTable.setColumnWidth(2,199)
        self.collTable.setColumnWidth(3,399)
        self.collTable.setColumnWidth(0,20)
        self.collTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.collTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.collTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.collTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.resetPath() 

        #Home button
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("home.png"))
        self.homeButton.setIcon(icon)

        #Metadata table
        self.metadataTable.setColumnWidth(0,199)
        self.metadataTable.setColumnWidth(1,199)
        self.metadataTable.setColumnWidth(2,199)
        self.metadataTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.metadataTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.metadataTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.metadataTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        #ACL table
        self.aclTable.setColumnWidth(0,299)
        self.aclTable.setColumnWidth(1,299)
        self.aclTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.aclTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.aclTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.metadataTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        #Resource table
        self.resourceTable.setColumnWidth(0,500)
        self.resourceTable.setColumnWidth(1,90)
        self.resourceTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.resourceTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.resourceTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.actionExit.triggered.connect(self.programExit)
        self.actionCloseSession.triggered.connect(self.newSession)
        self.browse()

    #Frame start

    def browse(self):
        #update main table when iRODS paht is changed upon 'Enter'
        self.inputPath.returnPressed.connect(self.loadTable)
        self.homeButton.clicked.connect(self.resetPath)
        #quick dataa upload
        self.UploadButton.clicked.connect(self.fileUpload)
        #functionality to lower tabs for metadata, acls and resources
        self.collTable.doubleClicked.connect(self.updatePath)
        self.collTable.clicked.connect(self.fillInfo)
        self.metadataTable.clicked.connect(self.editMetadata)
        self.aclTable.clicked.connect(self.editACL)
        #actions to update iCat entries of metadata and acls
        self.metaAddButton.clicked.connect(self.addIcatMeta)
        self.metaUpdateButton.clicked.connect(self.updateIcatMeta)
        self.metaDeleteButton.clicked.connect(self.deleteIcatMeta)
        self.aclAddButton.clicked.connect(self.updateIcatAcl)


    #connect functions
    def programExit(self):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ic.session.cleanup()
            sys.exit()
        else:
            pass


    def newSession(self):
        quit_msg = "Are you sure you want to disconnect?"
        reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ic.session.cleanup()
            currentWidget = self.widget.currentWidget()
            self.widget.setCurrentIndex(self.widget.currentIndex()-1)
            self.widget.removeWidget(currentWidget)
            self.loadTable()

        else:
            pass


    def resetPath(self):
        self.inputPath.setText(self.irodsRoot.path)
        self.loadTable()


    def fileUpload(self):
        from irodsUtils import getSize
        dialog = QFileDialog(self)
        resources = self.ic.listResources()
        resourceSize = []
        for resource in resources:
            try:
                resourceSize.append(str(round(int(self.ic.resourceSize(resource)/1024**3))+" GB"))
            except:
                resourceSize.append("0 GB")
        print([name+" "+size for name, size in zip(resources, resourceSize)])
        fileSelect = QFileDialog.getOpenFileName(self,"Open File", "","All Files (*);;Python Files (*.py)")
        size = getSize(fileSelect[0])
        buttonReply = QMessageBox.question(self, 'Message Box', "Upload " + fileSelect[0], 
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            parentColl = self.ic.session.collections.get("/"+self.inputPath.text().strip("/"))
            print("Upload "+fileSelect[0]+" to "+parentColl.path+" on resource "+self.ic.defaultResc)
            self.ic.uploadData(fileSelect[0], parentColl, 
                    self.ic.defaultResc, size)
            self.loadTable()

        else:
            pass


    def updateIcatAcl(self):
        self.aclError.clear()
        user = self.aclUserField.text()
        rights = self.aclBox.currentText()
        recursive = self.recurseBox.currentText() == 'True'
        parent = self.inputPath.text()
        cell = self.collTable.item(self.currentBrowserRow, 1).text()
        zone = self.aclZoneField.text()
        try:
            self.ic.setPermissions(rights, user, "/"+parent.strip("/")+"/"+cell.strip("/"), zone, recursive)
            self.__fillACLs(cell)
        except:
            self.aclError.setText("ERROR: please check user name.")
            raise


    def updateIcatMeta(self):
        newKey = self.metaKeyField.text()
        newVal = self.metaValueField.text()
        newUnits = self.metaUnitsField.text()
        if not (newKey is "" or newVal is ""):
            parent = self.inputPath.text()
            cell = self.collTable.item(self.currentBrowserRow, 1).text()
            if cell.endswith("/"):
                item = self.ic.session.collections.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            else:
                item = self.ic.session.data_objects.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            self.ic.updateMetadata([item], newKey, newVal, newUnits)
            self.__fillMetadata(cell)


    def addIcatMeta(self):
        newKey = self.metaKeyField.text()
        newVal = self.metaValueField.text()
        newUnits = self.metaUnitsField.text()
        if not (newKey is "" or newVal is ""):
            parent = self.inputPath.text()
            cell = self.collTable.item(self.currentBrowserRow, 1).text()
            if cell.endswith("/"):
                item = self.ic.session.collections.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            else:
                item = self.ic.session.data_objects.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            self.ic.addMetadata([item], newKey, newVal, newUnits)
            self.__fillMetadata(cell)


    def deleteIcatMeta(self):
        key = self.metaKeyField.text()
        val = self.metaValueField.text()
        units = self.metaUnitsField.text()
        if not (key is "" or val is ""):
            parent = self.inputPath.text()
            cell = self.collTable.item(self.currentBrowserRow, 1).text()
            if cell.endswith("/"):
                item = self.ic.session.collections.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            else:
                item = self.ic.session.data_objects.get("/"+parent.strip("/")+"/"+cell.strip("/"))
            self.ic.deleteMetadata([item], key, val, units)
            self.__fillMetadata(cell)


    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def updatePath(self, index):
        col = index.column()
        row = index.row()
        parent = self.inputPath.text()
        value = self.collTable.item(row, 1).text()
        if value.endswith("/"): #collection
            self.inputPath.setText("/"+parent.strip("/")+"/"+value.strip("/"))
            self.loadTable()


    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def fillInfo(self, index):
        self.previewBrowser.clear()

        self.metadataTable.setRowCount(0);
        self.aclTable.setRowCount(0);

        self.resourceTable.setRowCount(0);
        col = index.column()
        row = index.row()
        self.currentBrowserRow = row
        value = self.collTable.item(row, col).text()
        self.__fillPreview(value)
        self.__fillMetadata(value)
        self.__fillACLs(value)
        self.__fillResc(value)


    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def editMetadata(self, index):
        self.metaKeyField.clear()
        self.metaValueField.clear()
        self.metaUnitsField.clear()
        row = index.row()
        key = self.metadataTable.item(row, 0).text()
        value = self.metadataTable.item(row, 1).text() 
        units = self.metadataTable.item(row, 2).text()
        self.metaKeyField.setText(key)
        self.metaValueField.setText(value)
        self.metaUnitsField.setText(units)
        self.currentMetadata = (key, value, units)


    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def editACL(self, index):
        self.aclUserField.clear()
        self.aclZoneField.clear()
        self.aclBox.setCurrentText("----")
        row = index.row()
        user = self.aclTable.item(row, 0).text()
        zone = self.aclTable.item(row, 1).text()
        acl = self.aclTable.item(row, 2).text()
        self.aclUserField.setText(user)
        self.aclZoneField.setText(zone)
        self.aclBox.setCurrentText(acl)
        self.currentAcl = (user, acl)


    # Util functions
    def loadTable(self):
        newPath = "/"+self.inputPath.text().strip("/")
        if self.ic.session.collections.exists(newPath):
            coll = self.ic.session.collections.get(newPath)
            self.collTable.setRowCount(len(coll.data_objects)+len(coll.subcollections))
            row = 0
            for subcoll in coll.subcollections:
                self.collTable.setItem(row, 1, QtWidgets.QTableWidgetItem(subcoll.name+"/"))
                self.collTable.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
                self.collTable.setItem(row, 3, QtWidgets.QTableWidgetItem(""))
                self.collTable.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
                row = row+1
            for obj in coll.data_objects:
                self.collTable.setItem(row, 1, QtWidgets.QTableWidgetItem(obj.name))
                self.collTable.setItem(row, 2, QtWidgets.QTableWidgetItem(str(obj.size)))
                self.collTable.setItem(row, 3, QtWidgets.QTableWidgetItem(str(obj.checksum)))
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.Unchecked)
                #self.collTable.itemClicked.connect(self.__gatherClicked)
                self.collTable.setItem(row, 0, item)
                row = row+1
            self.collTable.resizeColumnsToContents()


    def __fillResc(self, value):
        newPath = "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
        if not value.endswith("/") and self.ic.session.data_objects.exists(newPath):
            resources = self.ic.listResources()
            self.resourceTable.setRowCount(len(resources))
            obj = self.ic.session.data_objects.get(
                    "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                    )
            replicas = [resc.resource_name for resc in obj.replicas]
            for i in range(len(resources)):
                self.resourceTable.setItem(i, 0, 
                        QtWidgets.QTableWidgetItem(resources[i]))
                if resources[i] in replicas:
                    item = QtWidgets.QTableWidgetItem()
                    item.setCheckState(QtCore.Qt.Checked)
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.resourceTable.setItem(i, 1, item)
        self.resourceTable.resizeColumnsToContents()


    def __fillACLs(self, value):
        self.aclTable.setRowCount(0);
        self.aclUserField.clear()
        self.aclZoneField.clear()
        self.aclBox.setCurrentText("----")

        newPath = "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
        acls = []
        if value.endswith("/") and self.ic.session.collections.exists(newPath):
            item = self.ic.session.collections.get(
                        "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                        )
            acls = self.ic.session.permissions.get(item)
        elif self.ic.session.data_objects.exists(newPath):
            item = self.ic.session.data_objects.get(
                    "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                    )
            acls = self.ic.session.permissions.get(item)
        
        self.aclTable.setRowCount(len(acls))
        row = 0
        for acl in acls:
            self.aclTable.setItem(row, 0, QtWidgets.QTableWidgetItem(acl.user_name))
            self.aclTable.setItem(row, 1,QtWidgets.QTableWidgetItem(acl.user_zone))
            self.aclTable.setItem(row, 2,
                        QtWidgets.QTableWidgetItem(acl.access_name.split(' ')[0].replace('modify', 'write')))
            row = row+1

        self.aclTable.resizeColumnsToContents()


    def __fillMetadata(self, value):
        self.metaKeyField.clear()
        self.metaValueField.clear()
        self.metaUnitsField.clear()

        newPath = "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
        metadata = []
        if value.endswith("/") and self.ic.session.collections.exists(newPath):
            coll = self.ic.session.collections.get(
                        "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                        )
            metadata = coll.metadata.items()
        elif self.ic.session.data_objects.exists(newPath):
            obj = self.ic.session.data_objects.get(
                    "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                    )
            metadata = obj.metadata.items()
        self.metadataTable.setRowCount(len(metadata))
        row = 0
        for item in metadata:
            self.metadataTable.setItem(row, 0,
                    QtWidgets.QTableWidgetItem(item.name))
            self.metadataTable.setItem(row, 1,
                    QtWidgets.QTableWidgetItem(item.value))
            self.metadataTable.setItem(row, 2,
                    QtWidgets.QTableWidgetItem(item.units))
            row = row+1
        self.metadataTable.resizeColumnsToContents()


    def __fillPreview(self, value):
        newPath = "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
        if value.endswith("/") and self.ic.session.collections.exists(newPath): # collection
            coll = self.ic.session.collections.get(
                        "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                        )
            content = [c.name+'/' for c in coll.subcollections] + \
                      [o.name for o in coll.data_objects]

            previewString = '\n'.join(content)
            #self.previewBrowser.append(previewString)
            self.previewBrowser.setText(previewString)
        elif self.ic.session.data_objects.exists(newPath): # object
            # get mimetype
            mimetype = value.split(".")[len(value.split("."))-1]
            obj = self.ic.session.data_objects.get(
                    "/"+self.inputPath.text().strip("/")+"/"+value.strip("/")
                    )
            if mimetype in ['txt', 'json', 'csv']:
                try:
                    out = []
                    with obj.open('r') as readObj:
                        for i in range(20):
                            out.append(readObj.readline())
                    previewString = ''.join([line.decode('utf-8') for line in out])
                    #self.previewBrowser.append(previewString)
                    self.previewBrowser.setText(previewString)
                except:
                    self.previewBrowser.append(
			"No Preview for: " + "/"+self.inputPath.text().strip("/")+"/"+value.strip("/"))



    def __gatherClicked(self):
        print('Click')
