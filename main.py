#!/usr/bin/python3
from gi.repository import Gtk, Gdk, GdkPixbuf
from ftplib import FTP
import ftplib
import threading
from socket import gaierror 

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
                self.ref.connectioninfo.set_text("Connecting...")
                self.ref.server = FTP(self.ref.address_entry.get_text())
                self.ref.server.login(self.ref.username_entry.get_text(), self.ref.password_entry.get_text())
                self.ref.connectioninfo.set_text("Connected")
                self.ref.connected = True 
        # TODO: Need to make sure this catches all errors and displays an appropriate message for each error.
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

        ## FTP directory data
        self.directory_model = self.builder.get_object("Directory Model")
        def getFiles(self):
            self.directory_model = Gtk.ListStore(str)
            parents = {}
            for (path,dirs,files) in os.walk("home/"):
                for subdir in dirs:
                    parents[os.path.join(path,subdir)] = self.directory_model.append(parents.get(path,None),[subdir])
                for item in files:
                    tree = self.directory_model.append(parents.get(path,None),[item])
            self.directory_display = Gtk.TreeView(self.directory_model)
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn("Title",renderer,text=0)
            self.directory_display.append_column(column)

        # Open the welcome window
        self.openingWindow.show_all()

#### Opening Window Handler
    def openApp(self,widget):
        self.openingWindow.hide()
        self.mainWindow.show_all()

#### Main window handlers
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

## Connect Tab
    def CN_connectHandler(self, button):
        # Connect to the server
        thread = ConnectionThread(self)
        thread.daemon = True
        thread.start()


    # Quits the current session
    def CN_disconnectHandler(self,x):
        if( (self.server != None) and self.connected):
            self.server.quit()
            self.connected = False
            self.connectioninfo.set_text("Disconnected")
            print("Disconnected")
        else:
            self.connectioninfo.set_text("Disconnected")
            print("Not connected")
        #self.openLoading(x)

## TO DO: Do these all need to have multiprocessing implemented?
## Browse tab
    
    #TO DO: need to know which directory/file selected after 
    def BR_deleteHandler(self,x):
        pass
        #if file:
            #self.server.delete("file_name")
        #elif directory:
            #self.server.rmd("directory_name")

    #TO DO: need to know selected file name
    def BR_downloadHandler(self,x):
        pass
        #Can only download individual files, not whole directories
        #self.server.retrbinary('RETR filename')

    #TO DO: figure out how to get selected file name/path to command
    def BR_uploadHandler(self,x):
        self.filechooserdialog1.connect('delete-event', lambda w, e: w.hide() or True)
        self.filechooserdialog1.show_all()
        
        #upload selected file to current working directory on server
        #self.server.storbinary("STOR filename")


    def BR_permissionsHandler(self,x):
        self.permissionChange.connect('delete-event', lambda w, e: w.hide() or True)
        self.permissionChange.show_all()

    #TO DO: Does this need to be a separate thread?
    #       Implement different error handling?
    def BR_directoryHandler(self,x):
        try:
            new_directory = self.server.mkd(self.directory_entry.get_text())
            print('Directory "%s" added.' % new_directory)

        except:
            print("Failed to create directory")

#### TO DO
#### Loading Window Handlers
    def LD_CancelHandler(self,x):
        print("test")

    def LD_OkHandler(self,x):
        pass

#### TO DO
#### File Chooser Window Handlers
    def FC_CancelHandler(self,x):
        pass
    def FC_OkHandler(self,x):
        pass
    def fileActivated(self,x):
        # Activates when a file is double-clicked on.
        pass


#### Permission Change Window Handlers
    def PC_Cancel_Handler(self,x):
        self.permissionChange.hide()

    def PC_OKHandler(self,x):
        print(self.public_read.get_active())

    def PC_RecurseSubdirectoriesToggle(self,widget):
        if(self.recurse_subdirectories.get_active()):
            for x in self.recurse_buttons:
                x.set_sensitive(True)
        else:
            for x in self.recurse_buttons:
                x.set_sensitive(False)

    def PC_onDestroy(self,x):
        self.permissionChange.hide()

#### Misc. Methods
    def openLoading(self, button):
        self.loadingScreen.connect('delete-event', lambda w, e: w.hide() or True)
        self.loadingScreen.show_all()

def main():
    applicaton = Application()
    Gtk.main()

if __name__ == "__main__":
    main()
