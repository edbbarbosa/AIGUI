import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QProgressBar, QLabel,
    QDialog, QTextEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate  
from langchain_google_genai import ChatGoogleGenerativeAI  

class LLMWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text, key):
        super().__init__()
        self.text = text 
        self.key = key

    def run(self):
        try:
            with open("api_key.config", "w", encoding="utf-8") as file_apikey:
                file_apikey.write(self.key)

            llm = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash", temperature=0.7, google_api_key=self.key
            )

            prompt_template = PromptTemplate.from_template(self.text)
            parser = StrOutputParser()
            chain = prompt_template | llm | parser

            response = chain.invoke({})

            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))

class AnswerDialog(QDialog):
    def __init__(self, response_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Answer")
        self.resize(550, 450)

        self.setWindowFlags(
            self.windowFlags() |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(response_text)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button) 

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI")
        self.resize(350, 200)

        layout = QVBoxLayout()

        self.entry_key = QLineEdit(self)
        api_key = ""
        try:
            with open("api_key.config", "r", encoding="utf-8") as file_apikey:
                    api_key = file_apikey.read().strip()
        except FileNotFoundError:
            pass
        self.entry_key.setPlaceholderText("Enter the API key here...")
        self.entry_key.setText(api_key)
        layout.addWidget(self.entry_key)

        self.entry_text = QTextEdit(self)        
        self.entry_text.setPlaceholderText("Enter the prompt here...")
        layout.addWidget(self.entry_text)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.click_ok)
        layout.addWidget(self.ok_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("", self)
        layout.addWidget(self.lbl_status)

        self.setLayout(layout)

    def click_ok(self):
        #text = self.entry_text.text().strip()
        text = self.entry_text.toPlainText().strip()    
        if not text:
            return 
        key = self.entry_key.text().strip()
        if not key:
            return

        self.ok_button.setEnabled(False)
        self.entry_text.setEnabled(False)
        self.progress_bar.show()
        self.lbl_status.setText("Please wait...")

        self.worker = LLMWorker(text, key)
        self.worker.finished.connect(self.show_answer)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def show_answer(self, response):
        self.restore_GUI()
        dialog = AnswerDialog(response, self)
        dialog.exec() 
        self.entry_text.clear()

    def show_error(self, error):
        self.restore_GUI()
        QMessageBox.critical(self, "Error", f"\n{error}")

    def restore_GUI(self):
        self.ok_button.setEnabled(True)
        self.entry_text.setEnabled(True)
        self.progress_bar.hide()
        self.lbl_status.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
