from PyQt5.QtWidgets import QFileDialog

class FolderSelector(QFileDialog):
    def __init__(self):
        super().__init__()

    def get_folder_path(self, init_path):
        file_path = self.getExistingDirectory(self, "选择角色卡", init_path, QFileDialog.ShowDirsOnly)
        return file_path