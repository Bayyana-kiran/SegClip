import av
import cv2
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider, QLineEdit, QHBoxLayout, QTextEdit, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from fpdf import FPDF

class project(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Segmentation Tool")
        self.layout = QVBoxLayout()

        self.label = QLabel()
        self.layout.addWidget(self.label)

        self.slider_layout = QHBoxLayout()
        self.start_time_edit = QLineEdit()
        self.start_time_edit.setPlaceholderText("Start Time (seconds)")
        self.slider_layout.addWidget(self.start_time_edit)

        self.end_time_edit = QLineEdit()
        self.end_time_edit.setPlaceholderText("End Time (seconds)")
        self.slider_layout.addWidget(self.end_time_edit)

        self.layout.addLayout(self.slider_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.layout.addWidget(self.slider)

        self.split_button = QPushButton("Split at Current Time")
        self.split_button.clicked.connect(self.split_video)
        self.layout.addWidget(self.split_button)

        self.preview_button = QPushButton("Preview Segment")
        self.preview_button.clicked.connect(self.preview_segment)
        self.layout.addWidget(self.preview_button)

        self.save_button = QPushButton("Save Timestamps as PDF")
        self.save_button.clicked.connect(self.save_timestamps)
        self.layout.addWidget(self.save_button)

        self.open_button = QPushButton("Open Video File")
        self.open_button.clicked.connect(self.open_file)
        self.layout.addWidget(self.open_button)

        self.setLayout(self.layout)

        self.container = None
        self.video_stream = None
        self.video_duration = 0
        self.current_time = 0
        self.video_file = ""

     
    def open_file(self):
        self.video_file, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        if self.video_file:
            self.container = av.open(self.video_file)
            self.video_stream = next(s for s in self.container.streams if s.type == 'video')
            self.video_duration = self.container.duration / 1000000  # duration in seconds
            self.slider.setMaximum(int(self.video_duration))
            self.update_frame()


    def slider_value_changed(self, value):
        self.current_time = value
        self.update_frame()

    def update_frame(self):
        if self.container:
            self.container.seek(int(self.current_time * 1000000), backward=True, any_frame=False, stream=self.video_stream)
            packet = next(self.container.demux(self.video_stream))
            frame = packet.decode()[0]
            frame_rgb = cv2.cvtColor(frame.to_ndarray(format='bgr24'), cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape
            qimg = QImage(frame_rgb.data, w, h, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(qimg))

    def split_video(self):
        start_time = int(self.start_time_edit.text())
        end_time = int(self.end_time_edit.text())
        if start_time >= 0 and end_time <= self.video_duration and start_time < end_time:
            output_file = f"segment_{start_time}_{end_time}.mp4"
            output_container = av.open(output_file, 'w')
            output_stream = output_container.add_stream('h264')

            self.container.seek(int(start_time * 1000000), stream=self.video_stream)
            for packet in self.container.demux(self.video_stream):
                if packet.pts is not None and packet.pts < end_time * 1000000:
                    packet.stream = output_stream
                    output_container.mux(packet)
                else:
                    break
            
            output_container.close()
            print(f"Segment saved as {output_file}")
        else:
            print("Invalid start or end time.")



    def preview_segment(self):
        start_time = int(self.start_time_edit.text())
        end_time = int(self.end_time_edit.text())
        if start_time >= 0 and end_time <= self.video_duration and start_time < end_time:
            self.current_time = start_time
            self.slider.setValue(start_time)
            self.update_frame()

    def save_timestamps(self):
        start_time = int(self.start_time_edit.text())
        end_time = int(self.end_time_edit.text())
        if start_time >= 0 and end_time <= self.video_duration and start_time < end_time:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Segment Timestamps for {self.video_file}", ln=True, align="C")
            pdf.cell(200, 10, txt=f"Start Time: {start_time} seconds", ln=True, align="L")
            pdf.cell(200, 10, txt=f"End Time: {end_time} seconds", ln=True, align="L")
            pdf.output("segment_timestamps.pdf")
            print("Timestamps saved as segment_timestamps.pdf")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = project()
    tool.show()
    sys.exit(app.exec_())
