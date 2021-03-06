# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MergeCSV
                                 A QGIS plugin
 Merges data from a comma-separated-values file (.csv) to an existing layer with the same structure.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-06-27
        git sha              : $Format:%H$
        copyright            : (C) 2022 by labMGF
        email                : federica.gaspari@polimi.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from PyQt5.QtWidgets import QAction, QFileDialog
from pathlib import Path
from qgis.gui import QgsProjectionSelectionDialog


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .merge_csv_dialog import MergeCSVDialog
import os.path


class MergeCSV:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MergeCSV_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Merge CSV to existing layer')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MergeCSV', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/merge_csv/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Merge CSV to existing layer'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Merge CSV to existing layer'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_input_file(self):
        #qfd = QtWidgets.QFileDialog()
        #filt = self.plugin.tr("CSV files(*.csv)") # change the file type
        #title = self.plugin.tr("Select a .csv file")
        f, _ = QFileDialog.getOpenFileName(
            self.dlg, "Select input file","", '*.csv')
        self.dlg.lineEdit.setText(f)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = MergeCSVDialog()
            self.dlg.pushButton.clicked.connect(self.select_input_file)
            self.dlg.CRSButton.clicked.connect(self.selectCRS)
            self.dlg.ReadCSVButton.clicked.connect(self.readCSV)    
            self.dlg.CSVFieldButton.clicked.connect(self.defineCSV)


        # Fetch the currently loaded layers
        layers = QgsProject.instance().layerTreeRoot().children()
        #Clear the contents of the comboBox from previous runs
        self.dlg.comboBox.clear()
        # Populate the comboBox with names of all the loaded layers
        self.dlg.comboBox.addItems([layer.name() for layer in layers])

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.iface.messageBar().pushMessage("Success", "Input CSV data successfully written into chosen target layer.", level=Qgis.Success, duration=5)
            
            pass
    
    def selectCRS(self):
        """Let user select layer CRS"""
        dialog = QgsProjectionSelectionDialog()
        dialog.exec_()
        crs = dialog.crs().authid()
        self.dlg.lineEdit_2.setText(crs)

    def defineCSV(self):
        """Define fields and delimiter of CSV"""
        # Read csv selected with the file browser
        csv_filename = self.dlg.lineEdit.text()
        uri_00 = "file:///"+ csv_filename + "?encoding=%s&delimiter=%s"
        uri_01 = uri_00 % ("UTF-8",";")
        csv_layernoxy=QgsVectorLayer(uri_01,"read_layer","delimitedtext")
        fields = csv_layernoxy.fields()
        field_names = [field.name() for field in fields]
        # ----
        #Clear the contents of the comboBox_x from previous runs
        self.dlg.comboBox_x.clear()
        # Populate the comboBox_x with field names of input csv
        self.dlg.comboBox_x.addItems([field.name() for field in fields])
        # ----
        #Clear the contents of the comboBox_y from previous runs
        self.dlg.comboBox_y.clear()
        # Populate the comboBox_y with field names of input csv
        self.dlg.comboBox_y.addItems([field.name() for field in fields])

    def readCSV(self):
        """Read correctly the input CSV"""
        # Read csv selected with the file browser
        csv_filename = self.dlg.lineEdit.text()
        # Compute file path and encoding for opening the file
        uri_02 = "file:///"+ csv_filename + "?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s"
        uri = uri_02 % ("UTF-8",";", self.dlg.comboBox_x.currentText(), self.dlg.comboBox_y.currentText(),self.dlg.lineEdit_2.text())
        # Print in the Python console the name of the selected csv file
        print("The selected csv file is:", uri)
        # Get the name of target layer selected in the combobox widget
        target_layer = self.dlg.comboBox.currentText()
        # Print in the Python console the name of the selected target file
        print("Target layer: " + target_layer)
        # Read as csv the selected input file path
        csv_layer=QgsVectorLayer(uri,"csv_layer","delimitedtext")
        # Check validity of selected csv
        if not csv_layer.isValid():
            # Print in the Python console that the selected csv is not valid for upload
            print ("Layer not loaded")
        else:
            # Add CSV data
            QgsProject.instance().addMapLayer(csv_layer)
            # Select all the items included in the csv layer
            csv_layer.selectAll()
            # Copy all the selected items
            self.iface.copySelectionToClipboard(csv_layer)
            # Get target layer as active
            target = QgsProject.instance().mapLayersByName(target_layer)[0]
            # Enable editing mode in target layer
            target.startEditing()
            # Paste all the selected items in the target layer
            self.iface.pasteFromClipboard(target)
            # Save changes in the target layer
            target.commitChanges()
            QgsMessageLog.logMessage("File "+csv_filename+" successfully copied and pasted into " + target_layer, "CSV Processing", level=Qgis.Info )
            self.iface.messageBar().pushMessage("Success", "Input CSV data successfully written into chosen target layer.", level=Qgis.Success, duration=5)
            #self.iface.messageBar().pushMessage("Success", "Output file written at ", level=Qgis.Success, duration=5)
