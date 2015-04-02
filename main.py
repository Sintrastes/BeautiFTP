#!/usr/bin/env python3
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from ftplib import FTP
import ftplib
import threading
import os
from socket import gaierror
from os.path import expanduser
import wave, sys, pyaudio

### Utiliy functions ###

def getFile(x):
    e = ""
    while(x[len(x)-1] != '/'):
       e = x[len(x)-1] + e
       x = x[:len(x)-1]
    return e

def getPath(x):
    while(x[len(x)-1] != "/"):
        x = x[:len(x)-1]
    return x

def getPathFile(x):
    return (getPath(x),getFile(x))

def getMode(x):
    for item in x:
        if item[0:9] == "UNIX.mode":
            print(item[10:])
            return item[10:]

def boolListToBin(x):
    n = 0
    i = 0
    while x != []:
        value = x.pop()
        if value == True:
            n += 2**i
        i += 1
    return n

class UploadThread(threading.Thread):
  def __init__(self,ref,filename):
        threading.Thread.__init__(self)
        self.ref = ref
        self.filename = filename
  def run(self):
    ext = os.path.splitext(self.filename)[1]
    (path,name) = getPathFile(self.filename)
    if ext in (".txt", ".htm", ".html"):
        os.chdir(path)
        myfile = open(name,"r")
        self.ref.server.storlines("STOR " + name, myfile)
        os.chdir(self.ref.main_directory)
    else:
        os.chdir(path)
        myfile = open(name, "rb")
        self.ref.server.storbinary("STOR " + name, myfile, 1024)
        os.chdir(self.ref.main_directory)
    self.ref.UL_done = True
    self.ref.loading_status.set_text("Done!")

    # Play sound!
    try:
        wf = wave.open('Tutturuu.wav', 'rb')
        sound = wave.open('Tutturuu.wav')
        p = pyaudio.PyAudio()
        chunk = 1024
        stream = p.open(format =
            p.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True)
        data = wf.readframes(chunk)
        while data != '':
            stream.write(data)
            data = wf.readframes(chunk)
    except:
        pass

class DownloadThread(threading.Thread):
  def __init__(self,ref):
        threading.Thread.__init__(self)
        self.ref = ref
  
  def run(self):
    # fetch a binary file

    #ftp.retrbinary("RETR " + filename, outfile.write)
    if(self.ref.selected[len(self.ref.selected)-1] != "/"):
           os.chdir(expanduser("~")+"/Downloads")
           self.ref.server.retrbinary('RETR '+self.ref.selected,open(self.ref.selected, 'wb').write)    
           os.chdir(self.ref.main_directory)
    self.ref.DL_done = True
    self.ref.loading_status.set_text("Done!")
    
# Play sound!
    try:
        wf = wave.open('Tutturuu.wav', 'rb')
        sound = wave.open('Tutturuu.wav')
        p = pyaudio.PyAudio()
        chunk = 1024
        stream = p.open(format =
            p.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True)
        data = wf.readframes(chunk)
        while data != '':
            stream.write(data)
            data = wf.readframes(chunk)
    except:
        pass    

class ConnectionThread(threading.Thread):
    def __init__(self,ref):
        threading.Thread.__init__(self)
        self.ref = ref

    def run(self):
        try:
            if(self.ref.username_entry.get_text() == ""):
                self.ref.connectioninfo.set_text("Please enter a username.")
            elif(self.ref.password_entry.get_text() == ""):
                self.ref.connectioninfo.set_text("Please enter a password.")
            elif(self.ref.address_entry.get_text() == ""):
                self.ref.connectioninfo.set_text("Please enter an address.")
            else:
                if(self.ref.connected):
                    self.ref.directory_model.clear()
                self.ref.connectioninfo.set_text("Connecting...")
                self.ref.server = FTP(self.ref.address_entry.get_text())
                self.ref.server.login(self.ref.username_entry.get_text(), self.ref.password_entry.get_text())
                self.ref.connectioninfo.set_text("Connected")
                self.ref.connected = True 
                
                # Populate Tree
                self.ref.pop_tree()

                # Sets the selected variable to the currently selected item
                # in the tree view.
                def on_tree_selection_changed(selection):
                    model, treeiter = selection.get_selected()
                    if treeiter != None:
                        self.ref.selected = model[treeiter][0]
                # Select Folder/File
                select = self.ref.directory_display.get_selection()
                select.connect("changed", on_tree_selection_changed)
                
        except ftplib.all_errors as err: 
            self.ref.connectioninfo.set_text("Could not connect: "+str(err))
        except gaierror:
            self.connectioninfo.set_text("Address not found.")
        except ConnectionRefusedError:
            self.connectioninfo.set_text("Connection refused.")
        except Exception as err:
            self.ref.connectioninfo.set_text("Error: "+str(err))


class Application:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("Beautiftp.glade")
        self.builder.connect_signals(self)
        
        #### Application Windows

        self.mainWindow         = self.builder.get_object("Main Window")
        self.loadingScreen      = self.builder.get_object("Loading Screen")
        self.permissionChange   = self.builder.get_object("Permission Change")
        self.filechooserdialog1 = self.builder.get_object("filechooserdialog1")
        self.openingWindow      = self.builder.get_object("Opening Window")

        #### Application Objects
        ## Connect Tab
        self.connectioninfo = self.builder.get_object("Connection Info")
        self.username_entry = self.builder.get_object("Username Entry")
        self.password_entry = self.builder.get_object("Password Entry")
        self.address_entry  = self.builder.get_object("Address Entry")

        ## Browse Tab
        self.directory_entry = self.builder.get_object("Directory Entry")
        self.directory_display = self.builder.get_object("Directory Display")
        self.browse_tab        = self.builder.get_object("Browse Tab")

        ## Permission Change Window
        self.owner_write    = self.builder.get_object("Owner Write")
        self.owner_read     = self.builder.get_object("Owner Read")
        self.owner_execute  = self.builder.get_object("Owner Execute")

        self.group_write    = self.builder.get_object("Group Write")
        self.group_read     = self.builder.get_object("Group Read")
        self.group_execute  = self.builder.get_object("Group Execute")

        self.public_write   = self.builder.get_object("Public Write")
        self.public_read    = self.builder.get_object("Public Read")
        self.public_execute = self.builder.get_object("Public Execute")

        self.recurse_subdirectories = self.builder.get_object("recurse subdirectories")

        ## Loading Window
        self.canvas = self.builder.get_object("Canvas")
        self.loader=GdkPixbuf.PixbufAnimation.new_from_file("nyan2.gif")
        self.canvas.set_from_animation(self.loader)
        self.loading_status   = self.builder.get_object("Loading Status")

        self.apply_all        = self.builder.get_object("Apply All")
        self.files_only       = self.builder.get_object("Files Only")
        self.directories_only = self.builder.get_object("Directories Only")
        self.null_select      = self.builder.get_object("Null Select")
        self.recurse_buttons  = [self.apply_all, self.files_only, self.directories_only, self.null_select]
        
        #### Application State
        ## Connection data
        self.server       = None
        self.connected    = False
        self.connected_to = ""
        self.UL_done      = False
        self.DL_done      = False

        ## Browse Data
        self.selected = ""
        self.main_directory = os.getcwd()
        ## FTP directory data
        self.directory_model = self.builder.get_object("Directory Model")

        # Open the welcome window
        self.openingWindow.show_all()

        # Run every 500 ms
        GObject.timeout_add(10,self.clock_event)


#### Opening Window Handler
    def openApp(self,widget):
        self.openingWindow.hide()
        self.mainWindow.show_all()

        # Set Up the treeview
        self.displayTree()

#### Main window handlers
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

## Connect Tab
    def CN_connectHandler(self, button):
        # Connect to the server
        if(not self.connected):
            thread = ConnectionThread(self)
            thread.daemon = True
            thread.start()

    # Quits the current session
    def CN_disconnectHandler(self,x):
        if( (self.server != None) and self.connected):
            self.server.quit()
            self.directory_model.clear()
            self.connected = False
            self.connectioninfo.set_text("Disconnected")
        else:
            self.connectioninfo.set_text("Disconnected")
        #self.openLoading(x)

## Browse tab
    def displayTree(self):
        self.directory_display.show_all()
        column0 = Gtk.TreeViewColumn("Files",Gtk.CellRendererText(),text=0)
        column1 = Gtk.TreeViewColumn("Permissions",Gtk.CellRendererText(),text=1)
        self.directory_display.append_column(column0)
        self.directory_display.append_column(column1)
        self.directory_model.clear()

    def pop_tree(self):
        self.directory_model.clear()
        ls = []
        self.server.retrlines('MLSD', ls.append)
        for item in ls:
            name = item.split(';').pop()
            if 'type=dir' in item.split(';'):
                self.directory_model.append([name.lstrip(' ')+"/",getMode(item.split(";"))])
            elif 'type=pdir' not in item.split(';'):
                if(name.lstrip(' ') != '.'):
                    self.directory_model.append([name.lstrip(' '),getMode(item.split(";"))])

        if(self.server.pwd() != "/"):
            self.directory_model.prepend(["../",""])

    def item_select(self,treeview,row,treeview_col):
        # Activated when a row of the tree view is double-clicked
        listiter = treeview.get_model().get_iter(Gtk.TreePath(row))
        try:
            self.server.cwd(treeview.get_model().get_value(listiter,0)[:-1])
            self.pop_tree()
        except Exception as e:
            print(e)
            if(treeview.get_model().get_value(listiter,0) == "../"):
                self.server.cwd("..")
                pop_tree(self)
            else:
                print(e)        
    
    def BR_deleteHandler(self,x):
        if(self.selected != ""):
            if self.selected[len(self.selected)-1] != "/":
                self.server.delete(self.selected)
            else:
                self.server.rmd(self.selected[:-1])
            self.pop_tree()

    def BR_downloadHandler(self,x):
        self.openLoading(None)
        self.loading_status.set_text("Loading...")
        self.loader=GdkPixbuf.PixbufAnimation.new_from_file("nyan2.gif")
        self.canvas.set_from_animation(self.loader)
        downthread = DownloadThread(self)
        downthread.start()
        #TODO: Can only download individual files, not whole directories
        
    def BR_uploadHandler(self,x):
        self.filechooserdialog1.connect('delete-event', lambda w, e: w.hide() or True)
        self.filechooserdialog1.show_all()
        self.loading_status.set_text("Loading...")
        self.loader=GdkPixbuf.PixbufAnimation.new_from_file("nyan2.gif")
        self.canvas.set_from_animation(self.loader)

    def BR_permissionsHandler(self,x):
        self.permissionChange.connect('delete-event', lambda w, e: w.hide() or True)
        self.permissionChange.show_all()

    def BR_directoryHandler(self,x):
        try:
            new_directory = self.server.mkd(self.directory_entry.get_text())
            print('Directory "%s" added.' % new_directory)
            self.pop_tree()

        except:
            print("Failed to create directory")

    def LD_CancelHandler(self,x):
        self.loadingScreen.hide()


    def LD_OkHandler(self,x):
        self.loadingScreen.hide()

    def FC_CancelHandler(self,x):
        self.filechooserdialog1.hide()

    def FC_OkHandler(self,x):
        filename = self.filechooserdialog1.get_filename()
        thread = UploadThread(self,filename)
        thread.daemon = True
        thread.start()
        self.filechooserdialog1.hide()
        self.openLoading(None)
        
    def fileActivated(self,x):
        # Activates when a file is double-clicked on.
        filename = self.filechooserdialog1.get_filename()
        thread = UploadThread(self,filename)
        thread.daemon = True
        thread.start()
        self.filechooserdialog1.hide()
        self.openLoading(None)

#### Permission Change Window Handlers

    def PC_Cancel_Handler(self,x):
        self.permissionChange.hide()

    def PC_OKHandler(self,x):
        o_mode = [self.owner_read.get_active(), self.owner_write.get_active(), self.owner_execute.get_active()]
        g_mode = [self.group_read.get_active(), self.group_write.get_active(), self.group_execute.get_active()]
        p_mode = [self.public_read.get_active(), self.public_write.get_active(), self.public_execute.get_active()]
        mode = str(boolListToBin(o_mode)) + str(boolListToBin(g_mode)) + str(boolListToBin(p_mode))
        self.server.sendcmd('SITE CHMOD ' + mode + ' ' + self.selected)
        self.permissionChange.hide()
        self.pop_tree()

    def PC_RecurseSubdirectoriesToggle(self,widget):
        if(self.recurse_subdirectories.get_active()):
            for x in self.recurse_buttons:
                x.set_sensitive(True)
        else:
            for x in self.recurse_buttons:
                x.set_sensitive(False)

    def PC_onDestroy(self,x):
        self.permissionChange.hide()

    def clock_event(self):
        if self.UL_done:
            self.pop_tree()
            self.loading_status.set_text("Done!")
 

            # Stop Nyan Cat Animation
            loader=GdkPixbuf.PixbufAnimation.new_from_file("tmp-0.gif")
            self.canvas.set_from_animation(loader)
            
            self.UL_done = False

        if self.DL_done:
            self.pop_tree()

            # Stop Nyan Cat Animation
            loader=GdkPixbuf.PixbufAnimation.new_from_file("tmp-0.gif")
            self.canvas.set_from_animation(loader)
            
            self.DL_done = False

        if self.connected:
            self.browse_tab.set_sensitive(True)
        if not self.connected:
            self.browse_tab.set_sensitive(False)
        return True

#### Misc. Methods
    def openLoading(self, button):
        self.loadingScreen.connect('delete-event', lambda w, e: w.hide() or True)
        self.loadingScreen.show_all()

def main():
    # Initalize and run the application
    applicaton = Application()
    Gtk.main()

if __name__ == "__main__":
    main()
