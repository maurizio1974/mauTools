"""Attribute selection for inserting a Utility node into an existing wire."""
from .qt import QtCore, QtWidgets


class SocketDialog(QtWidgets.QDialog):
    def __init__(self, type_name, source, destination, inputs, outputs, parent=None):
        super(SocketDialog, self).__init__(parent)
        self.setWindowTitle('Inbetween - ' + type_name)
        self.setMinimumWidth(420)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel('%s\n  -> %s ->\n%s' % (source, type_name, destination))
        label.setTextFormat(QtCore.Qt.PlainText)
        label.setWordWrap(True)
        layout.addWidget(label)
        form = QtWidgets.QFormLayout()
        self.input = QtWidgets.QComboBox()
        self.output = QtWidgets.QComboBox()
        for combo, options in ((self.input, inputs), (self.output, outputs)):
            for name, cls in options:
                combo.addItem('%s (%s)' % (name, cls), name)
        form.addRow('Input attribute', self.input)
        form.addRow('Output attribute', self.output)
        layout.addLayout(form)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Insert')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def attributes(self):
        return self.input.currentData(), self.output.currentData()
