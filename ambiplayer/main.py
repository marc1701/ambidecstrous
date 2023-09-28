import os
import sys
import decoders
import soundfile as sf
import sounddevice as sd

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QPushButton,
    QMainWindow, 
    QApplication, 
    QLabel, 
    QFileDialog, 
    QFormLayout,
    QDial,
    QComboBox,
    QWidget, 
    QGridLayout
)

from audio_processing import AudioPlayer

from pathlib import Path
root_path = str(Path(__file__).parent.parent)

# TODO: Support for files with channels > 2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.player = None
        self.setFixedSize(QSize(500,300))

        layout = QGridLayout()
        self.setWindowTitle('Ambisonic Audio Player')

        # label shown in main part of window
        self.label = QLabel('')
        layout.addWidget(self.label, 1, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)

        # find default output device
        device_list = list(sd.query_devices())
        # list devices with output channels available
        output_device_names = \
            [device['name'] for device in device_list
             if device['max_output_channels'] > 0]
        self.output_device_indices = \
            [device['index'] for device in device_list
             if device['max_output_channels'] > 0]

        # create dropdown menu for device selection
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(output_device_names)
        self.device_dropdown.setCurrentIndex(
            self.output_device_indices.index(sd.default.device[1]))
        self.device_dropdown.currentIndexChanged.connect(self.device_changed)
        self.device_index = sd.default.device[1]

        self.decoder_dropdown = QComboBox()
        self.decoder_dropdown.addItems(['Raw', 'Stereo UHJ', 'Ambisonics'])
        self.decoder_dropdown.currentIndexChanged.connect(self.decoder_changed)
        
        self.channel_format_dropdown = QComboBox()
        self.channel_format_dropdown.addItems(['ACN', 'FuMa'])

        form = QFormLayout()
        form.addRow('Output Device:', self.device_dropdown)
        form.addRow('Decoder:', self.decoder_dropdown)
        form.addRow('Channel Format:', self.channel_format_dropdown)
        layout.addLayout(form, 0, 0, 1, 4, Qt.AlignmentFlag.AlignJustify)
        
        # play button
        self.play_button = QPushButton(
            QIcon(root_path + '/icons/play.png'), 'Play', self)
        self.play_button.clicked.connect(self.playButtonClicked)
        self.play_button.setMinimumWidth(100)
        self.play_button.setMaximumWidth(100)
        self.play_button.setMinimumHeight(100)
        self.play_button.setCheckable(True)
        self.play_button.setDisabled(True)
        layout.addWidget(self.play_button, 2, 0)

        # pause button
        self.pause_button = QPushButton(
            QIcon(root_path + '/icons/pause.png'), 'Pause', self)
        self.pause_button.clicked.connect(self.pauseButtonClicked)
        self.pause_button.setMinimumWidth(100)
        self.pause_button.setMaximumWidth(100)
        self.pause_button.setMinimumHeight(100)
        self.pause_button.setCheckable(True)
        self.pause_button.setDisabled(True)
        layout.addWidget(self.pause_button, 2, 1)

        # stop button
        self.stop_button = QPushButton(
            QIcon(root_path + '/icons/stop.png'), 'Stop', self)
        self.stop_button.clicked.connect(self.stopButtonClicked)
        self.stop_button.setMinimumWidth(100)
        self.stop_button.setMaximumWidth(100)
        self.stop_button.setMinimumHeight(100)
        self.stop_button.setCheckable(True)
        self.stop_button.setDisabled(True)
        layout.addWidget(self.stop_button, 2, 2)

        # open button
        self.open_button = QPushButton(
            QIcon(root_path + '/icons/open-folder.png'), 'Open', self)
        # self.open_button.setStatusTip('Open File')
        self.open_button.clicked.connect(self.openButtonClicked)
        self.open_button.setMinimumWidth(100)
        self.open_button.setMaximumWidth(100)
        self.open_button.setMinimumHeight(100)
        layout.addWidget(self.open_button, 2, 3)
        
        # layout.addWidget(QDial(), 4, 0)
        # layout.addWidget(QDial(), 4, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def playButtonClicked(self):
        self.stop_button.setChecked(False)
        self.pause_button.setDisabled(False)
        self.pause_button.setChecked(False)
        self.play_button.setChecked(True)
        self.player.play()
        self.device_dropdown.setDisabled(True)
        self.decoder_dropdown.setDisabled(True)
        self.channel_format_dropdown.setDisabled(True)
    
    def pauseButtonClicked(self):
        self.play_button.setChecked(False)
        self.pause_button.setChecked(True)
        self.player.pause()
        self.device_dropdown.setDisabled(False)
        self.decoder_dropdown.setDisabled(False)
        self.channel_format_dropdown.setDisabled(False)

    def stopButtonClicked(self):
        self.stop_button.setChecked(True)
        self.play_button.setChecked(False)
        self.pause_button.setChecked(False)
        self.player.stop()
        self.pause_button.setDisabled(True)
        self.device_dropdown.setDisabled(False)
        self.decoder_dropdown.setDisabled(False)
        self.channel_format_dropdown.setDisabled(False)

    def openButtonClicked(self, _):
        # set up dialog box
        dialog = QFileDialog()
        # single file only
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        # accepted audio formats
        dialog.setNameFilter('Audio (*.wav *.flac)')
        # run the dialog
        dialog.exec()
        # retrieve filepath
        filepath = dialog.selectedFiles()
        
        if not filepath: return False
        self.filepath = filepath[0]
        self.label.setText(os.path.basename(self.filepath))

        self.file, self.fs = sf.read(self.filepath)

        print(self.decoder_dropdown.currentIndex())
        match self.decoder_dropdown.currentIndex():
            case 0: decoder = decoders.raw
            case 1: decoder = decoders.stereo_uhj
            case 2: pass # Ambisonics
        # TODO: MIGHT NEED TO STORE CURRENT DECODER
        self.player = AudioPlayer(
            self.file, 
            self.fs, 
            self.device_index, 
            decoder
        )

        self.play_button.setDisabled(False)
        self.stop_button.setDisabled(False)
        self.stop_button.setChecked(True)

    def device_changed(self, index):
        self.device_index = self.output_device_indices[index]
        if not self.player: return False
        self.player = AudioPlayer(self.file, 
                                  self.fs, 
                                  self.device_index,
                                  current_frame=self.player.current_frame
        )
    
    def decoder_changed(self, index):
        print(index)
        if not self.player: return False
        match index:
            case 0: self.player.decoder = decoders.raw
            case 1: self.player.decoder = decoders.stereo_uhj
            case 2: pass # Ambisonics

app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()
