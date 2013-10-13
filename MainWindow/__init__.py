# -*- coding: utf-8 -*-
__author__ = 'jershell'
from PyQt4 import QtCore, QtGui, QtNetwork, uic
import threading
from PyQt4.QtGui import QSystemTrayIcon, QPixmap, QMatrix, QPen, QGraphicsItem, QAction, QBrush, QColor

import InfoWindow

import time
import rpclib
import socket
import sys
import subprocess
import os
#import resources
#pyrcc4 resources.qrc -py3 -o resources.py

class ClockThread(threading.Thread):
    def __init__(self, interval, callback=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interval = interval
        self.call_back = None
        if callback:
            self.call_back = callback

    def run(self):
        while True:
            print("The time is %s" % time.ctime())
            time.sleep(self.interval)
            if self.call_back:
                execute = self.call_back
                execute('simple text')


class ThreadScanIp(threading.Thread):
    def __init__(self, ip, timeout, count_treads, form):
        threading.Thread.__init__(self)
        self.setName("scanIp " + str(ip))
        #print("Create new thread", self.getName())
        self.timeout = timeout
        self.ip = ip
        self.count = count_treads
        self.form = form

    def __del__(self):
        self.count.remove_thread()
        #print(self.getName(), "CLOSE THREAD")

    def run(self):
        self.count.add_thread()
        port = rpclib.getPort(self.ip, 100005, self.timeout)  # 100005 - MOUNT
        if port:
            exportList = rpclib.getExportList(self.ip, port, self.timeout)
            self.form.add_host(exportList)

class ThreadCheckHost(threading.Thread):
    def __init__(self, hosts, form, interval=10):
        threading.Thread.__init__(self)
        self.interval = interval
        self.enable = True
        self.form = form
        self.hosts = hosts
        self.setDaemon(True)

    def run(self):

        while self.enable:
            for host in self.hosts:
                if rpclib.check_host(host["host"]):
                    self.form.updateItem()
                else:
                    self.form.removeItem()
                print("FOR##")
            print("WHILE##", self.enable)
            time.sleep(self.interval)

    def set_state(self, state):
        self.enable = state

    def stop_check(self):
        self.enable = False



class ThreadScanNetwork(threading.Thread):
    def __init__(self, interval, net, cidr, form, scan_ip_timeout=1, num_tread=10):
        threading.Thread.__init__(self)
        self.interval = interval
        self.net = net
        self.cidr = cidr
        self.total_ip_count = (2 ** (32 - self.cidr)) - 2
        self.setDaemon(True)
        self.enable = True
        self.scan_ip_timeout = scan_ip_timeout
        self.count_threads = 0
        self.num_threads = num_tread
        self.form = form

    def add_thread(self):
        self.count_threads += 1

    def remove_thread(self):
        self.count_threads -= 1

    def run(self):
    # self.total_ip_count = 15
        while self.enable:
            for j in range(self.total_ip_count):
                ip = rpclib.int2ip(rpclib.ip2int(self.net) + (j + 1))
                if self.count_threads < self.num_threads:
                    #print(self.count_threads)
                    ThreadScanIp(ip, self.scan_ip_timeout, self, self.form).start()
                else:
                    time.sleep(self.scan_ip_timeout)
                    #print("threads count:", self.count_threads)
            time.sleep(self.interval)


    def setState(self, state):
        self.enable = state


class ListItem(QtGui.QListWidgetItem):
    def __init__(self, icon, text, parent=None):
        super(ListItem, self).__init__(parent)
        self.setText(text)
        self.setIcon(icon)
        self.state = "unmount"
        self.info = {
            "host": "n/a",
            "hostname": "n/a",
            "port": "n/a",
            "group": [],
            "path": [],
        }


class MainForm(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        uic.loadUi("./MainWindow/form.ui", self)
        self.setWindowTitle("NFS-List")
        self.setLayout(self.gridLayout)
        self.setGeometry(100, 100, 640, 480)
        self.listWidget.setViewMode(QtGui.QListView.IconMode)
        self.listWidget.setMovement(QtGui.QListWidget.Static)
        self.ipv6_enable = True  # False
        self.addr_ipv4 = None
        self.addr_ipv6 = None
        self.addr_ipv4_array = []
        self.addr_ipv6_array = []
        self.time = 1

        self.hosts = []
        self.icon = QtGui.QIcon("./MainWindow/NAS-icon.png")
        self.setWindowIcon(self.icon)

        #Tray
        tray_menu = QtGui.QMenu(self)

        show_hide_action = QAction("Show/Hide", self)
        quitAction = QAction("Quit", self)

        tray_menu.addAction(show_hide_action)
        tray_menu.addAction(quitAction)

        tray = QSystemTrayIcon(self)
        tray.setIcon(self.icon)
        tray.setContextMenu(tray_menu)
        tray.setToolTip(self.windowTitle())
        tray.show()
        #
        show_hide_action.triggered.connect(self.showHideWindow)
        quitAction.triggered.connect(QtGui.qApp.quit)

        #end tray

        # self.ico.addPixmap(self.pixmap)
        ifaces = QtNetwork.QNetworkInterface.allInterfaces()
        for iface in ifaces:
            for addr_iface in iface.addressEntries():
                if addr_iface.ip() != QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost) and \
                                addr_iface.ip() != QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHostIPv6):
                    if addr_iface.ip().toIPv4Address():
                        self.addr_ipv4_array.append(addr_iface)
                    if self.ipv6_enable:
                        if addr_iface.ip().toIPv6Address():
                            self.addr_ipv6_array.append(addr_iface)

        if len(self.addr_ipv4_array) >= 1:
            self.addr_ipv4 = self.addr_ipv4_array[0].ip().toString()

        #ip data#

        addr_mask = self.addr_ipv4_array[0].netmask().toString()
        #addr_mask = '255.255.255.192'

        __list_aprefix = addr_mask.split('.')
        cidr_ipv4 = 0
        bn = '0b'
        baddr = '0b'
        for i in __list_aprefix:
            cidr_ipv4 += rpclib.bit_count(int(i))
            bn += bin(int(i))[2:]

        print("cidr:", cidr_ipv4)
        print(bn)
        #
        total_ip_count = (2 ** (32 - cidr_ipv4)) - 2
        print('total_ip_count:', total_ip_count)
        print(self.addr_ipv4)
        int_net_ipv4 = rpclib.ip2int(self.addr_ipv4) & rpclib.ip2int(addr_mask)
        net_ipv4 = rpclib.int2ip(int_net_ipv4)


        #abc = ClockThread(self.time, self.add_new_item)
        #abc.start()
        #self.add_new_item('t34', 't32')

        self.scan_network = ThreadScanNetwork(10, net_ipv4, cidr_ipv4, self, 1.2)
        self.scan_network.start()

        self.check_host = ThreadCheckHost(self.hosts, self)
        self.check_host.start()

        #self.add_host({"host":"100.64.0.1","structures":[{'groups': [b'*'], 'dir': b'/srv/NFS'}]})
        """
        self.listWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.actionInfo = QAction("Info", self.listWidget)
        self.actionMount = QAction("Mount", self.listWidget)
        self.listWidget.addAction(self.actionMount)
        self.listWidget.addAction(self.actionInfo)

        self.actionInfo.triggered.connect(self.showInfo)
        self.actionMount.triggered.connect(self.my_method)
        """
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.showRightMenu)

    def showRightMenu(self, pos, arga=1, argb=2):
        item = self.listWidget.itemAt(pos)

        if item:
            #print(item.info)
            self.actionInfo = QAction("Info", self.listWidget)
            self.actionMount = QAction("Mount", self.listWidget)
            self.listWidget.addAction(self.actionMount)
            self.listWidget.addAction(self.actionInfo)
            contextMenu = QtGui.QMenu("Context menu", self.listWidget)

            contextMenu.addAction(self.actionInfo)
            contextMenu.addAction(self.actionMount)

            action = contextMenu.exec(self.listWidget.viewport().mapToGlobal(pos))
            if action == self.actionInfo:
                self.showInfo(item.info)
            if action == self.actionMount:
                self.mount(item.info["hostname"], item.info["host"], item.info["path"][0])

    def my_method(self, arg1=1, arg2=2, arg3=3):
        print(arg1, arg2, arg3)

    def showInfo(self, data):
        information = InfoWindow.InfoDialog(data)
        information.exec()

    def add_host(self, export_list):
        host_addr = export_list["host"]
        try:
            hostname = socket.gethostbyaddr(host_addr)[0]
        except:
            hostname = host_addr

        if len(self.hosts) != 0:
            found = False
            for item in self.hosts:
                if item["host"] == export_list["host"]:
                    found = True

            if found == False:
                self.hosts.append(export_list)
                self.add_new_item(hostname, host_addr, export_list)
        else:
            self.hosts.append(export_list)
            self.add_new_item(hostname, host_addr, export_list)

    def add_new_item(self, name, host, export_list, icon=None):
        #print("name", type(name))
        #print("host", host)
        if icon is None:
            item = ListItem(self.icon, name)
        else:
            item = ListItem(icon, name)
        item.info["host"] = host
        item.info["hostname"] = name
        item.info["port"] = export_list["port"]
        for j in export_list["structures"]:
            item.info["path"].append(j["dir"])
            for n in j["groups"]:
                item.info["group"].append(n)
        self.listWidget.addItem(item)

    def removeItem(self):
        print("removeItem")

    def updateItem(self):
        print("updateItem")

    def stateOff(self):
        self.scan_network.setState(False)
        self.check_host.set_state(False)
        self.check_host.stop_check()
        print("del")

    def __del__(self):
        self.scan_network.setState(False)
        self.check_host.set_state(False)
        self.check_host.enable = False
        self.check_host.stop_check()
        print("del")

    def showHideWindow(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()
    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def mount(self, m_dir, host, remove_path):
        #mount -t nfs  server_IP_addr:/share_name /local_mount_point
        print(m_dir, host, remove_path)
        host_path = host+":"+remove_path.decode("utf-8")
        if sys.platform == 'linux2':
            path = os.path.expanduser("~")
            mount_root = path+"/mnt/"
            if not os.path.isdir(mount_root):
                os.makedirs(mount_root)
            mount_dir = mount_root + m_dir

            if not os.path.isdir(mount_dir):
                os.makedirs(mount_dir)
            proc = subprocess.Popen(["gksu", "mount", "-t nfs", host_path, mount_dir], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            print("Success!", out.decode("utf-8"), err.decode("utf-8"))
        elif sys.platform == 'win32':
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            drives = ['{0}:'.format(d) for d in letters if not os.path.exists('{0}:'.format(d))]
            drv = drives[-1]
            proc = subprocess.Popen(["mount", host_path, drv], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            print("Success!", out, err)
        else:
            pass