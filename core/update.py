import re
import os
import time
import shutil
import _thread
import urllib.request, urllib.error, urllib.parse
import subprocess

from gui import settings
from gui import update_ui
from PyQt5 import QtCore, QtGui, QtWidgets

class update_class(QtWidgets.QDialog,update_ui.Ui_Dialog):
    file_downloaded = QtCore.pyqtSignal()
    finished_downloading = QtCore.pyqtSignal()
    restart_application_signal = QtCore.pyqtSignal()
    download_failed = QtCore.pyqtSignal()
    new_update_available = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.retranslateUi(self)

        self.current_version = 1.64

        self.new_version = float()
        self.svn_failure_message = str()
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)

        self.upgrade_button.clicked.connect(self.update_installer)
        self.download_failed.connect(self.update_timeout_message)
        self.finished_downloading.connect(self.finished_download)
        self.file_downloaded.connect(self.downloading)
        self.restart_application_signal.connect(self.restart_application)


    def display_update_version(self):
        self.update_display_label.setText("<font color=blue>Version %s Available</font>"%(self.new_version))


    def percentage(self,current,total):
        float_point = float(current)/float(total)
        calculation = int(float_point * 100)
        percent = str(calculation) + '%'
        return(percent)


    def restart_application(self):
        self.label_2.setText('<font color=red>Please restart_Application</font>')


    def finished_download(self):
        self.label_2.setText('<font color=green>finished_Downloading</font>')


    def downloading(self):
        self.label_2.setText('<font color=green>%s Complete</font>'%(self.percentage(self.files_downloaded,self.file_total)))


    def update_timeout_message(self):
        self.label_2.setText("<font color=red>Network timeout</font>")


    def update_error(self):
        svn_failure = self.svn_access.stderr
        self.svn_failure_message = svn_failure.read()
        if self.svn_failure_message:
            self.label_2.setText("<font color=red>Update Failed:" + self.svn_failure_message + "</font>")


    def update_installer(self):
        self.label_2.setText('<font color=green>Downloading...</font>')
        _thread.start_new_thread(self.update_launcher,())


    def update_launcher(self):
        ''' Downloads and installs update files
        '''
        self.file_total = int()
        self.files_downloaded = int()

        ghost_directory = os.getcwd()
        forbidden_files = ['Settings','Ghost-Phisher-Database']

        update_directory = '/tmp/Ghost-Phisher/'

        svn_path = 'https://github.com/savio-code/ghost-phisher/trunk/Ghost-Phisher/'

        try:
            online_response_check = urllib.request.urlopen('https://raw.githubusercontent.com/savio-code/ghost-phisher/master/Ghost-Phisher/UPDATE')
            online_response = online_response_check.read()

            online_files = re.compile('total_files = \d+',re.IGNORECASE)

            for online_file_total in online_response.splitlines():
                if re.match(online_files,online_file_total):
                    self.file_total = int(online_file_total.split()[2])

            if os.path.exists(update_directory):
                shutil.rmtree(update_directory)

            self.svn_access = subprocess.Popen('cd /tmp/ \n svn checkout ' + svn_path,\
                    shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE)
            svn_update = self.svn_access.stdout
            _thread.start_new_thread(self.update_error,())

            while True:
                response = svn_update.readline()
                if len(response) > 0:
                    self.files_downloaded += 1
                    self.file_downloaded.emit()

                if str('revision') in str(response):
                    self.finished_downloading.emit()

                    for old_file in os.listdir(os.getcwd()):
                        if os.path.isfile(os.getcwd() + os.sep + old_file) and old_file not in  forbidden_files:
                            os.remove(os.getcwd() + os.sep + old_file)

                    for old_directory in os.listdir(os.getcwd()):
                        if os.path.isdir(os.getcwd() + os.sep + old_directory) and old_directory not in  forbidden_files:
                            shutil.rmtree(os.getcwd() + os.sep + old_directory)

                    for update_file in os.listdir(update_directory):        
                    # Copy new_update_files to working directory
                       filepath = os.getcwd() + os.sep + update_file
                       if os.path.isfile(update_directory + update_file):
                          shutil.copyfile(update_directory + update_file,filepath)
                       else:
                          shutil.copytree(update_directory + update_file,filepath)

                       os.chmod(filepath,0o777)

                    time.sleep(5)

                    whats_new = settings.Ghost_settings()
                    whats_new.create_settings("disable whats new window","True")
                    whats_new.close_setting_file()

                    self.restart_application.emit()
                    break
                if len(self.svn_failure_message) > 2:
                    self.download_failed.emit()
                    break

        except(urllib.error.URLError,urllib.error.HTTPError):
            self.download_failed.emit()


    #
    # Update checker Thread
    #
    def update_initializtion_check(self):
        while True:
            try:
                online_response_thread = urllib.request.urlopen('https://raw.githubusercontent.com/savio-code/ghost-phisher/master/Ghost-Phisher/UPDATE')
                online_response = online_response_thread.read()

                online_version = re.compile('version\s+=\s+(\d*?\.\d*)',re.IGNORECASE)

                update_version_number = float(online_version.findall(online_response)[0])

                if float(self.current_version) != update_version_number:
                    self.new_version = update_version_number
                    self.new_update_available.emit()
                    break

                if float(self.current_version) == update_version_number:
                    break

            except Exception:
                time.sleep(9)








