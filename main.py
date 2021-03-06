import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QThread

import win32
from config import Config
from mainWindow import Ui_MainWindow
from captureWorker import CaptureWorker

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setFixedSize(880, 650)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    self.setWindowTitle("NESTrisOCR for CTWC Japan Lite v0.1.0")

    self.currentHandle = 0
    self.captureWorker = None

    self.graphicsScene = QGraphicsScene(self)
    self.gridItem = QGraphicsPixmapItem(QPixmap.fromImage(QImage("assets/grid.png")))
    self.gridItem.setZValue(1)
    self.stencilItem = QGraphicsPixmapItem(QPixmap.fromImage(QImage("assets/stencil.png")))
    self.stencilItem.setZValue(2)
    self.lastCapItem = None
    self.graphicsScene.addItem(self.gridItem)
    self.graphicsScene.addItem(self.stencilItem)
    self.ui.graphicsView.setScene(self.graphicsScene)

    # timer = QTimer(self)
    # timer.timeout.connect(self.update)
    # timer.start(16)

    self.config = Config()
    self.config.load()
    self.ui.preview.setChecked(self.config.preview)
    self.ui.enableSettings.setChecked(self.config.enableSettings)
    self.ui.captureWindowName.setText(self.config.captureWindowName)
    self.ui.showGrid.setChecked(self.config.showGrid)
    self.ui.showStencil.setChecked(self.config.showStencil)
    self.ui.xCoord.setValue(self.config.xCoord)
    self.ui.yCoord.setValue(self.config.yCoord)
    self.ui.width.setValue(self.config.width)
    self.ui.height.setValue(self.config.height)
    self.ui.enableSettingsExpert.setChecked(self.config.enableSettingsExpert)
    self.ui.captureFPS.setValue(self.config.captureFPS)
    self.ui.sendFPS.setValue(self.config.sendFPS)
    self.ui.windowHandle.setValue(self.config.windowHandle)
    self.ui.blackThreshold.setValue(self.config.blackThreshold)
    self.ui.inGameThreshold.setValue(self.config.inGameThreshold)

    self.ui.preview.stateChanged.connect(lambda checked: self.updatePreview(checked == Qt.Checked))
    self.ui.enableSettings.stateChanged.connect(lambda _: self.updateEnableSettings())
    self.ui.enableSettingsExpert.stateChanged.connect(lambda _: self.updateEnableSettings())
    self.ui.captureWindowName.textChanged.connect(self.updateCaptureWindowName)
    self.ui.showGrid.stateChanged.connect(lambda checked: self.updateShowGrid(checked == Qt.Checked))
    self.ui.showStencil.stateChanged.connect(lambda checked: self.updateShowStencil(checked == Qt.Checked))
    self.ui.xCoord.valueChanged.connect(lambda _: self.updateCaptureRect())
    self.ui.yCoord.valueChanged.connect(lambda _: self.updateCaptureRect())
    self.ui.width.valueChanged.connect(lambda _: self.updateCaptureRect())
    self.ui.height.valueChanged.connect(lambda _: self.updateCaptureRect())
    self.ui.captureFPS.valueChanged.connect(self.updateCaptureFPS)
    self.ui.sendFPS.valueChanged.connect(self.updateSendFPS)
    self.ui.windowHandle.valueChanged.connect(self.updateWindowHandle)
    self.ui.blackThreshold.valueChanged.connect(lambda _: self.updateExpertOCRSettings())
    self.ui.inGameThreshold.valueChanged.connect(lambda _: self.updateExpertOCRSettings())

    self.updatePreview(self.config.preview)
    self.updateEnableSettings()
    self.updateCaptureWindowName(self.config.captureWindowName)
    self.updateShowGrid(self.config.showGrid)
    self.updateShowStencil(self.config.showStencil)
    self.updateCaptureRect()
    self.updateCaptureFPS(self.config.captureFPS)
    self.updateSendFPS(self.config.sendFPS)
    self.updateWindowHandle(self.config.windowHandle)
    self.updateExpertOCRSettings()

    self.show()

  def updateEnableSettings(self):
    enable = False
    enableExpert = False
    if self.ui.enableSettings.checkState() == Qt.Checked:
      enable = True
    if self.ui.enableSettingsExpert.checkState() == Qt.Checked:
      enableExpert = True

    widgets = [
      self.ui.captureWindowName,
      self.ui.captureWindowNameLabel,
      self.ui.showGrid,
      self.ui.showStencil,
      self.ui.xCoord,
      self.ui.xCoordLabel,
      self.ui.yCoord,
      self.ui.yCoordLabel,
      self.ui.width,
      self.ui.widthLabel,
      self.ui.height,
      self.ui.heightLabel,
      self.ui.enableSettingsExpert
    ]

    widgetsExpert = [
      self.ui.captureFPS,
      self.ui.captureFPSLabel,
      self.ui.sendFPS,
      self.ui.sendFPSLabel,
      self.ui.windowHandle,
      self.ui.windowHandleLabel,
      self.ui.blackThreshold,
      self.ui.blackThresholdLabel,
      self.ui.inGameThreshold,
      self.ui.inGameThresholdLabel
    ]

    for w in widgets:
      w.setEnabled(enable)
    for w in widgetsExpert:
      w.setEnabled(enable and enableExpert)

    self.config.enableSettings = enable
    self.config.enableSettingsExpert = enableExpert
    self.updateCaptureWorkerRunning()

  def updatePreview(self, enable):
    self.config.preview = enable

  def updateCaptureWindowName(self, name):
    self.config.captureWindowName = name
    self.updateTargetHandle()

  def updateShowGrid(self, show):
    if show:
      self.gridItem.show()
    else:
      self.gridItem.hide()
    self.config.showGrid = show

  def updateShowStencil(self, show):
    if show:
      self.stencilItem.show()
    else:
      self.stencilItem.hide()
    self.config.showStencil = show

  def updateCaptureRect(self):
    self.config.xCoord = self.ui.xCoord.value()
    self.config.yCoord = self.ui.yCoord.value()
    self.config.width = self.ui.width.value()
    self.config.height = self.ui.height.value()

  def updateCaptureFPS(self, fps):
    self.config.captureFPS = fps

  def updateSendFPS(self, fps):
    self.config.sendFPS = fps

  def updateWindowHandle(self, handle):
    self.config.windowHandle = handle
    self.updateTargetHandle()

  def updateExpertOCRSettings(self):
    self.config.blackThreshold = self.ui.blackThreshold.value()
    self.config.inGameThreshold = self.ui.inGameThreshold.value()

  def updateCaptureWorkerRunning(self):
    running = self.config.enableSettings
    if self.captureWorker and not running:
      self.stopCaptureWorker()
    elif not self.captureWorker and running:
      self.startCaptureWorker()

  def updateTargetHandle(self):
    windows = win32.getWindows()
    if self.config.windowHandle != 0:
      self.currentHandle = self.config.windowHandle
    else:
      self.currentHandle = 0
      for handle, name in windows:
        if name.startswith(self.config.captureWindowName):
          self.currentHandle = handle
          break

  def startCaptureWorker(self):
    if self.captureWorker:
      self.stopCaptureWorker()

    self.updateTargetHandle()

    self.captureWorker = CaptureWorker(self)
    self.captureWorker.done.connect(self.updateCapture)
    self.captureWorker.start(QThread.HighPriority)

  def stopCaptureWorker(self):
    if self.captureWorker:
      self.captureWorker.exiting = True
      self.captureWorker.wait()
      self.captureWorker.quit()
      self.captureWorker = None
    self.ui.status.setText("Capture stopped")

  def updateCapture(self, result):
    if result["success"]:
      fps = result["fps"]
      if result["inGame"]:
        score = result["score"]
        lines = result["lines"]
        level = result["level"]
        next_ = result["next"]
        stats = formatStats(result["stats"])
        field = formatField(result["field"])
        self.ui.status.setText(
          f"FPS: {fps}\n" +
          f"Score: {score}\n" +
          f"Lines: {lines}\n" +
          f"Level: {level}\n" +
          f"Field:\n{field}" +
          f"Next: {next_}\n" +
          f"Stats:\n{stats}")
      else:
        self.ui.status.setText(
          f"FPS: {fps}\n" +
          "Not in game")
      if self.config.preview:
        image = result["image"]
        qim = QImage(image.tobytes("raw", "RGB"), image.size[0], image.size[1], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qim)
        item = QGraphicsPixmapItem(pixmap)
        if self.lastCapItem:
          self.graphicsScene.removeItem(self.lastCapItem)
        self.graphicsScene.addItem(item)
        self.lastCapItem = item
    else:
      self.ui.status.setText("Capture failed")

  def closeEvent(self, event):
    self.stopCaptureWorker()
    self.config.save()

def formatField(field):
  result = ""
  for iy in range(20):
    for ix in range(10):
      result += str(field[iy][ix])
    result += "\n"
  return result

STATS_PIECES = ["T", "J", "Z", "O", "S", "L", "I"]
def formatStats(stats):
  result = ""
  for i in range(7):
    result += f"{STATS_PIECES[i]}: {stats[i]}\n"
  return result

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = MainWindow()
  sys.exit(app.exec_())