from gi.repository import Gtk

class Handler:
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def connectHandler(self, button):
        print("Hello World!")

    def openLoading(self, button):
        loadingScreen.show_all()

builder = Gtk.Builder()
builder.add_from_file("Beautiftp.glade")

mainWindow = builder.get_object("Main Window")
loadingScreen = builder.get_object("Loading Screen")

builder.connect_signals(Handler())
mainWindow.show_all()

Gtk.main()
