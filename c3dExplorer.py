from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from pyC3D import c3dFile


class C3DExplorer(QtWidgets.QMainWindow):
    """A class representing a C3D file explorer."""

    _WINDOW_NAME = "C3D Explorer"

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """
        Initialize the C3DExplorer.

        Args:
            parent: The parent object. Defaults to None.
        """
        super().__init__(parent=parent)
        self.setupUI()
        self.setWindowTitle(self._WINDOW_NAME)

    def setupUI(self) -> None:
        """
        Set up the user interface of the C3DExplorer.
        """
        splitter: QtWidgets.QSplitter = QtWidgets.QSplitter()

        self._treeView: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        self._infoPanel: QtWidgets.QTableWidget = QtWidgets.QTableWidget()

        splitter.addWidget(self._treeView)
        splitter.addWidget(self._infoPanel)

        self.setCentralWidget(splitter)

        self._treeView.currentItemChanged.connect(self._handleParamChange)

        self._createMenuBar()

    def _createMenuBar(self) -> None:
        """
        Create the menu bar of the C3DExplorer.
        """
        menuBar: QtWidgets.QMenuBar = self.menuBar()

        fileMenu: QtWidgets.QMenu = menuBar.addMenu("File")

        loadAction = fileMenu.addAction("Load C3D File")
        loadAction.triggered.connect(self._handleActionFileLoad)

    def _handleActionFileLoad(self) -> None:
        """
        Handle the action of loading a C3D file.
        """
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open C3D File", "", "C3D Files (*.c3d)")
        if fileName:
            self._loadFile(fileName)

    def _loadFile(self, filePath: str) -> None:
        """
        Load a C3D file.

        Args:
            filePath: The path to the C3D file.
        """
        data: c3dFile.C3DFile = c3dFile.C3DFile(filePath)
        self.setWindowTitle(f"{self._WINDOW_NAME} - {filePath}")
        self._populateTree(data)
        
    def _handleParamChange(self, oldNode, newNode):
        """
        Handle the change of selected parameter.

        Args:
            oldNode: The previously selected node.
            newNode: The newly selected node.
        """
        if newNode is None:
            return
        self._populateTable(self._treeView.currentItem())

    def _populateTable(self, node):
        """
        Populate the information panel table with data.

        Args:
            node: The selected node in the tree view.
        """
        self._infoPanel.clear()
        data = node.data(0, 32)
        if isinstance(data, dict):
            self._infoPanel.setRowCount(1)
            self._infoPanel.setColumnCount(2)
            nameLabelNode = QtWidgets.QTableWidgetItem('Name')
            nameNode = QtWidgets.QTableWidgetItem(node.text(0))
            self._infoPanel.setItem(0, 0, nameLabelNode)
            self._infoPanel.setItem(0, 1, nameNode)
        else:
            if not isinstance(data, list):
                data = [data]
            self._infoPanel.setRowCount(len(data))
            self._infoPanel.setColumnCount(1)
            for idx in range(len(data)):
                dataNode = QtWidgets.QTableWidgetItem(str(data[idx]))
                self._infoPanel.setItem(idx, 0, dataNode)

    def _populateTree(self, c3dFile):
        """
        Populate the tree view with parameter data.

        Args:
            c3dFile: The C3D file object.
        """
        self._treeView.clear()
        allParamData = c3dFile.getParameterDict()

        for key, value in allParamData.items():
            paramNode = QtWidgets.QTreeWidgetItem()
            paramNode.setText(0, key)
            paramNode.setData(0, 32, value)
            self._treeView.addTopLevelItem(paramNode)
            for prop in c3dFile.getParametersInGroup(key):
                propertyNode = QtWidgets.QTreeWidgetItem()
                propertyNode.setText(0, prop)
                propertyNode.setData(0, 32, c3dFile.getParameterValue(key, prop))
                paramNode.addChild(propertyNode)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = C3DExplorer()
    window.show()
    sys.exit(app.exec_())
