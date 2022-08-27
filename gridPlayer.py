import platform
import os
import sys
import random

from PySide6 import QtWidgets, QtGui, QtCore
import vlc

class FileRandomizer:
    def __init__(self, path):
        self.videos_list = self.getVideoList(path)
        self.buffer = []

    def getVideoList(self, path):
        video_list = []
        for root, subFolder, files in os.walk(path):
            for file in files:
                if file.endswith('.mp4') or file.endswith('.avi'):
                    video_list.append(root + '\\' + file)
        return video_list

    def getRandomVideo(self):
        if self.videos_list != []:
            temp = self.videos_list.pop(random.randrange(len(self.videos_list)))
            self.buffer.append(temp)
            return temp
        else:
            self.videos_list = self.buffer.copy()
            self.buffer.clear()
            self.getRandomVideo()

class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt
    """

    def __init__(self, player_quantity=4, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.setWindowTitle("Media Player")

        self.player_quantity = player_quantity
        self.selected = 1
        self.volume = 60
        self.isFull = False
        self.auto_rand = True
        self.one_fullscreen = False

        # Get files
        # self.path = r'C:\Users\inglp\Downloads'
        # self.videos_list = FileRandomizer(self.path)

        # Create a basic vlc instance
        self.instance = []
        self.media = []
        self.media_event = []
        # self.is_paused = []
        self.timer_is_paused = []
        self.mediaplayer = []

        for i in range(self.player_quantity):
            self.instance.append( vlc.Instance() )
            self.media.append( None )

            # Create an empty vlc media player
            self.mediaplayer.append( self.instance[i].media_player_new() )
            self.media_event.append( self.mediaplayer[i].event_manager() )
            self.media_event[i].event_attach(vlc.EventType.MediaPlayerEndReached, self.video_end, i)
            # self.is_paused.append( False )
            self.timer_is_paused.append( None )

        self.create_ui()

    @vlc.callbackmethod 
    def video_end(self,*args):
        print(f'ended video {args[1]}')
        # self.open_random_file(args[1])

    def create_ui(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        self.videoframe = []
        self.fullscreen_frame = QtWidgets.QFrame()
        # In this widget, the video will be drawn
        if platform.system() == "Darwin": # for MacOS
            # self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
            pass
        else:
            for i in range(self.player_quantity):
                self.videoframe.append( QtWidgets.QFrame() )

        self.palette = []
        self.timer = []
        for i in range(self.player_quantity):
            self.palette.append( self.videoframe[i].palette() )
            self.palette[i].setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
            self.videoframe[i].setPalette(self.palette[i])
            self.videoframe[i].setAutoFillBackground(True)
            
            # Timer set up
            self.timer.append( QtCore.QTimer(self) )

        self.videoframe_fullscreen = QtWidgets.QFrame()
        palette_full = self.videoframe_fullscreen.palette()
        palette_full.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe_fullscreen.setPalette(palette_full)
        self.videoframe_fullscreen.setAutoFillBackground(True)

        self.timer[0].timeout.connect(self.timer0_reload)
        self.timer[1].timeout.connect(self.timer1_reload)
        self.timer[2].timeout.connect(self.timer2_reload)
        self.timer[3].timeout.connect(self.timer3_reload)

        self.grid_widget = QtWidgets.QWidget()
        self.fullscreen_widget = QtWidgets.QWidget()

        self.stack_layout = QtWidgets.QStackedLayout()
        self.stack_layout.setContentsMargins(0,0,0,0)
        self.gridlayout = QtWidgets.QGridLayout()
        self.fullscreen_layout = QtWidgets.QGridLayout()
        self.fullscreen_layout.addWidget(self.fullscreen_frame)
        self.fullscreen_layout.setContentsMargins(1, 1, 1, 1)
        k = 0
        for i in range(2):
            for j in range(2):
                self.gridlayout.addWidget(self.videoframe[k], i, j)
                k = k+1
        
        self.fullscreen_layout.addWidget(self.videoframe_fullscreen, 0, 0)

        self.gridlayout.setHorizontalSpacing(1)
        self.gridlayout.setVerticalSpacing(1)
        self.gridlayout.setContentsMargins(1, 1, 1, 1)

        self.fullscreen_widget.setLayout(self.fullscreen_layout)
        self.grid_widget.setLayout(self.gridlayout)

        self.stack_layout.addWidget(self.grid_widget)
        self.stack_layout.addWidget(self.fullscreen_widget)

        self.widget.setLayout(self.stack_layout)
        # self.widget.setLayout(self.gridlayout)

        # Set Qpainter pen to set rectangle color
        # self.p = QtGui.QPainter()
        # self.p.setPen(QtGui.QPen(QtGui.QColor(0,255,0), 2, QtCore.Qt.SolidLine))

        # Menu bar        
        self.menu_bar = self.menuBar()
        self.menu_is_visible = True

        # File menu
        file_menu = self.menu_bar.addMenu("File")
        edit_menu = self.menu_bar.addMenu("Edit")
        view_menu = self.menu_bar.addMenu("View")

        # Add actions to file menu
        open_path_action = QtGui.QAction("Open Path (P)", self)
        close_action = QtGui.QAction("Close App", self)
        hide_menu_action = QtGui.QAction("Hide Menu (H)", self)
        fullscreen_action = QtGui.QAction("Full screen (F)", self)
        self.auto_action = QtGui.QAction("Auto (G)", self, checkable=True, checked=True)
        file_menu.addAction(open_path_action)
        file_menu.addAction(close_action)
        view_menu.addAction(hide_menu_action)
        view_menu.addAction(fullscreen_action)
        edit_menu.addAction(self.auto_action)

        open_path_action.triggered.connect(self.open_path)
        close_action.triggered.connect(sys.exit)
        hide_menu_action.triggered.connect(self.toggleHide)
        fullscreen_action.triggered.connect(self.fullscreen)
        self.auto_action.triggered.connect(self.toggleTimers)
        
        # Creating a rectangle arountd default videoframe
        self.p = QtGui.QPainter()
        self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x()-1,self.videoframe[self.selected].y()-1,self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
        self.update()

    def play_pause_timer(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        if self.timer_is_paused[player_window]:
            self.play_timer(player_window)
        else:
            self.stop_timer(player_window)
        self.update()
    
    def play_timer(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        print(self.timer[player_window].remainingTime())
        self.timer[player_window].start()
        self.timer_is_paused[player_window] = False

    def stop_timer(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        print(self.timer[player_window].remainingTime())
        self.timer[player_window].stop()
        self.timer_is_paused[player_window] = True

    def play_pause(self, player_window=None):
        """Toggle play/pause status
        """
        if player_window is None:
            player_window = self.selected

        if self.mediaplayer[player_window].is_playing():
            self.pause(player_window)
        else:
            self.play(player_window)
        self.update()

            # self.playbutton.setText("Pause")
            # self.timer.start()
            # self.is_paused = False
    
    def play(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        if self.mediaplayer[player_window].play() == -1:
            self.open_file()
            return

        self.mediaplayer[player_window].play()
        self.play_timer(player_window)

    def pause(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        self.mediaplayer[player_window].set_pause(1)
        self.stop_timer(player_window)

    def stop(self, player_window=None):
        """Stop player
        """
        if player_window is None:
            player_window = self.selected
        self.mediaplayer[player_window].stop()
        # self.playbutton.setText("Play")
    
    def open_path(self):
        dialog_text = 'Choose Media Directory'
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, dialog_text, os.path.expanduser('~'))
        if not os.path.isdir(folderpath):
            print('Path selected is not a directory')
            return
        self.videos_list = FileRandomizer(folderpath)

        for i in range(4):
            self.open_random_file(i)
            if i == self.selected:
                self.set_volume(self.volume)
            else:
                self.set_volume(0, i)

        # for i in range(self.player_quantity):
        #     self.timer[i].setInterval(random.randint(25000,45000))
        # self.timer[0].timeout.connect(self.timer0_reload)
        # self.timer[1].timeout.connect(self.timer1_reload)
        # self.timer[2].timeout.connect(self.timer2_reload)
        # self.timer[3].timeout.connect(self.timer3_reload)
        # for i in range(self.player_quantity):
        #     self.timer[i].start()
        #     self.timer_is_paused[i] = False

    def timer0_reload(self):
        self.open_random_file(0)

    def timer1_reload(self):
        self.open_random_file(1)

    def timer2_reload(self):
        self.open_random_file(2)

    def timer3_reload(self):
        self.open_random_file(3)

    # def video_end0(self, event):
    #     if event.type == vlc.EventType.MediaPlayerEndReached:
    #         self.open_random_file(0)

    # def video_end1(self, event):
    #     if event.type == vlc.EventType.MediaPlayerEndReached:
    #         self.open_random_file(1)

    # def video_end2(self, event):
    #     if event.type == vlc.EventType.MediaPlayerEndReached:
    #         self.open_random_file(2)

    # def video_end3(self, event):
    #     if event.type == vlc.EventType.MediaPlayerEndReached:
    #         self.open_random_file(3)
    def toggleHide(self):
        if self.menu_is_visible:
            self.menu_bar.hide()
            self.menu_is_visible = False
        else:
            self.menu_bar.setVisible(True)
            self.menu_is_visible = True

    def toggleTimers(self):
        if self.auto_rand:
            self.auto_rand = False
            for i in range(self.player_quantity):
                if not self.timer_is_paused[i]:
                    self.timer[i].stop()
                    self.timer_is_paused[i] = True
        else:
            self.auto_rand = True
            for i in range(self.player_quantity):
                if self.timer_is_paused[i]:
                    self.timer[i].start()
                    self.timer_is_paused[i] = False
        self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
        self.update()

    def fullscreen(self):
            if self.isFull:
                self.showNormal()
                print('Normal screen')
                self.isFull = False
            else:
                self.showFullScreen()
                print('FullScreen')
                self.isFull = True
            self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
            self.update()

    def open_file(self, open_in=None, ran=False ):
        """Open a media file in a MediaPlayer
        """
        if open_in is None:
            open_in = self.selected

        dialog_txt = "Choose Media File"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename:
            return

        # getOpenFileName returns a tuple, so use only the actual file name
        self.media[open_in] = self.instance[open_in].media_new(filename[0])

        # Put the media in the media player
        self.mediaplayer[open_in].set_media(self.media[open_in])

        # Parse the metadata of the file
        self.media[open_in].parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media[open_in].get_meta(0))

        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux": # for Linux using the X Server
            self.mediaplayer[open_in].set_xwindow(int(self.videoframe[open_in].winId()))
        elif platform.system() == "Windows": # for Windows
            self.mediaplayer[open_in].set_hwnd(int(self.videoframe[open_in].winId()))
        elif platform.system() == "Darwin": # for MacOS
            self.mediaplayer[open_in].set_nsobject(int(self.videoframe[open_in].winId()))

        self.play_pause()

    def open_random_file(self, player_window=None):
        if player_window is None:
            i = self.selected
        else:
            i = player_window
        # self.mediaplayer[i].release()
        # getOpenFileName returns a tuple, so use only the actual file name
        filename = self.videos_list.getRandomVideo()
        self.media[i] = self.instance[i].media_new(filename)
        # self.media[i].add_option('start-time=0')
        # self.media[i].add_option('stop-time=30')

        print(f'trace 1 {i}')
        # Put the media in the media player
        self.mediaplayer[i].set_media(self.media[i])

        print(f'trace 2 {i}')
        # Parse the metadata of the file
        self.media[i].parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media[i].get_meta(0))

        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux": # for Linux using the X Server
            self.mediaplayer[i].set_xwindow(int(self.videoframe[i].winId()))
        elif platform.system() == "Windows": # for Windows
            self.mediaplayer[i].set_hwnd(int(self.videoframe[i].winId()))
        elif platform.system() == "Darwin": # for MacOS
            self.mediaplayer[i].set_nsobject(int(self.videoframe[i].winId()))

        print('trace 3')
        # Set random position
        self.play(i)
        self.set_random_position(i)

        # Set timer interval
        self.timer[i].setInterval(random.randint(25000,45000))
        if self.auto_rand:
            self.timer[i].start()
            self.timer_is_paused[i] = False
        else:
            self.timer[i].stop()
            self.timer_is_paused[i] = True
        self.update()


    def set_volume(self, volume, player_window=None):
        """Set the volume
        """
        if player_window == None:
            self.mediaplayer[self.selected].audio_set_volume(volume)
        else:
            self.mediaplayer[player_window].audio_set_volume(volume)

    # def set_position(self):
    #     """Set the movie position according to the position slider.
    #     """

    #     # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
    #     # integer variables, so you need a factor; the higher the factor, the
    #     # more precise are the results (1000 should suffice).

    #     # Set the media position to where the slider was dragged
    #     # self.timer.stop()
    #     pos = self.positionslider.value()
    #     self.mediaplayer.set_position(pos / 1000.0)
    #     # self.timer.start()

    def set_random_position(self, player_window=None):
        if player_window is None:
            player_window = self.selected
        # Sets the position of the player at most at 30 secs before ending of the media
        self.mediaplayer[player_window].set_position(random.uniform(0, 1 - 30000/self.media[player_window].get_duration()))


    def update_ui(self):
        """Updates the user interface"""

        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.
        media_pos = int(self.mediaplayer.get_position() * 1000)
        self.positionslider.setValue(media_pos)

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            # self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.stop()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_1 and not self.one_fullscreen:
            if self.selected == 0:
                self.set_random_position(0)
                if not self.timer_is_paused[0]:
                    self.timer[0].start()
            else:
                self.set_volume(0)
                self.selected = 0
                self.set_volume(self.volume)
                self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
                self.update()
                print('Top Left Selected')
        elif e.key() == QtCore.Qt.Key_2 and not self.one_fullscreen:
            if self.selected == 1:
                self.set_random_position(1)
                if not self.timer_is_paused[1]:
                    self.timer[1].start()
            else:
                self.set_volume(0)
                self.selected = 1
                self.set_volume(self.volume)
                # QtGui.QPainter.eraseRect(self.p)
                self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
                self.update()
                print('Top Right Selected')
        elif e.key() == QtCore.Qt.Key_3 and not self.one_fullscreen:
            if self.selected == 2:
                self.set_random_position(2)
                if not self.timer_is_paused[2]:
                    self.timer[2].start()
            # self.videoframe[self.selected].setStyleSheet("")
            else:
                self.set_volume(0)
                self.selected = 2
                self.set_volume(self.volume)
                # self.videoframe[self.selected].setStyleSheet("border: 1px solid red;background: black;")
                self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
                self.update()
                print('Bottom Right Selected')
        elif e.key() == QtCore.Qt.Key_4 and not self.one_fullscreen:
            if self.selected == 3:
                self.set_random_position(3)
                if not self.timer_is_paused[3]:
                    self.timer[3].start()
            else:
                self.set_volume(0)
                self.selected = 3
                self.set_volume(self.volume)
                # Creating a rectangle arountd default videoframe
                self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
                self.update()
                print('Bottom Left Selected')
        elif e.key() == QtCore.Qt.Key_R:
            self.open_random_file()
        elif e.key() == QtCore.Qt.Key_Space:
            self.open_random_file()
        elif e.key() == QtCore.Qt.Key_T:
            self.set_random_position()
            if not self.timer_is_paused[self.selected]:
                self.timer[self.selected].start()
        # Go forward/ for 5000 miliseconds
        elif e.key() == QtCore.Qt.Key_Q:
            self.play_pause_timer()
        elif e.key() == QtCore.Qt.Key_E:
            if self.mediaplayer[self.selected].get_time() <= self.media[self.selected].get_duration() - 5000:
                self.mediaplayer[self.selected].set_time(self.mediaplayer[self.selected].get_time() + 5000)
                print('5 sec +')
        # Go backward for 5000 miliseconds
        elif e.key() == QtCore.Qt.Key_W:
            # if self.mediaplayer[self.selected].get_position() >= 5000/self.media[self.selected].get_duration():
            #     self.mediaplayer[self.selected].set_position(self.mediaplayer[self.selected].get_position() - 5000/self.media[self.selected].get_duration())
            if self.mediaplayer[self.selected].get_time() >=  5000:
                self.mediaplayer[self.selected].set_time(self.mediaplayer[self.selected].get_time() - 5000)
                print('5 sec -')
        # Increase volume 5 %
        elif e.key() == QtCore.Qt.Key_D:
            if self.volume <= 95:
                self.volume = self.volume + 5
                self.set_volume(self.volume)
                print('Volume +')
        # Decrese volume 5 %
        elif e.key() == QtCore.Qt.Key_S:
            if self.volume >= 5:
                self.volume = self.volume - 5
                self.set_volume(self.volume)
                print('Volume -')
        # elif e.key() == QtCore.Qt.Key_R:
        #     self.palette[self.selected].setColor(QtGui.QPalette.Window, QtGui.QColor(100, 0, 0))
        #     self.videoframe[self.selected].setPalette(self.palette[self.selected])
        #     print('Rojo')
        elif e.key() == QtCore.Qt.Key_F:
            self.fullscreen()
        elif e.key() == QtCore.Qt.Key_G:
            self.toggleTimers()
        # elif e.key() == QtCore.Qt.Key_V:
        #     if self.one_fullscreen:
        #         for i in range(self.selected):
        #             if i != self.selected:
        #                 self.play(i)
        #         self.one_fullscreen = False
        #     else:
        #         for i in range(self.selected):
        #             if i != self.selected:
        #                 self.pause(i)
        #         self.one_fullscreen = True
        #     self.widget.setLayout(self.fullscreen_layout)
        #     print('layout changed')
        #     # self.mediaplayer[self.selected].set_hwnd(0)
        #     # self.mediaplayer[self.selected].toggle_fullscreen()
        #     self.gridlayout.removeWidget(self.videoframe[2])
        #     self.gridlayout.removeWidget(self.videoframe[3])
        #     self.gridlayout.removeWidget(self.videoframe[1])
        #     self.update()
        elif e.key() == QtCore.Qt.Key_Escape:
            self.showNormal()
            print('Normal screen')
            self.isFull = False
        elif e.key() == QtCore.Qt.Key_X:
            if self.mediaplayer[self.selected].get_state() == vlc.State.Ended:
                self.mediaplayer[self.selected].set_media(self.media[self.selected])
                self.mediaplayer[self.selected].play()
                print('video ended')
            else:
                self.mediaplayer[self.selected].set_position(0)
                print('video not ended yet')
        elif e.key() == QtCore.Qt.Key_A:
            self.play_pause()
        elif e.key() == QtCore.Qt.Key_Z:
            self.stop()
        elif e.key() == QtCore.Qt.Key_P:
            self.open_path()
        elif e.key() == QtCore.Qt.Key_O:
            self.open_file()
        elif e.key() == QtCore.Qt.Key_H:
            self.toggleHide()
        elif e.key() == QtCore.Qt.Key_B:
            self.stack_layout.setCurrentIndex(self.stack_layout.currentIndex()*-1 + 1)
            for i in range(self.player_quantity):
                if i != self.selected:
                    self.play_pause(i)
            stashed = self.mediaplayer[self.selected].get_time()
            if self.one_fullscreen:
                self.mediaplayer[self.selected].release()
                self.mediaplayer[self.selected] = self.instance[self.selected].media_player_new()
                self.mediaplayer[self.selected].set_hwnd(int(self.videoframe[self.selected].winId()))
                self.mediaplayer[self.selected].set_media(self.media[self.selected])
                self.mediaplayer[self.selected].play()
                self.mediaplayer[self.selected].set_time(stashed)
                # self.gridlayout.removeWidget(self.videoframe[2])
                # self.gridlayout.removeWidget(self.videoframe[3])
                # self.gridlayout.removeWidget(self.videoframe[1])
                self.one_fullscreen = False
                self.myRectangle = QtCore.QRect(self.videoframe[self.selected].x(),self.videoframe[self.selected].y(),self.videoframe[self.selected].width(),self.videoframe[self.selected].height())
                print(f'hi1 {stashed}')
            else:
                self.mediaplayer[self.selected].release()
                self.mediaplayer[self.selected] = self.instance[self.selected].media_player_new()
                self.mediaplayer[self.selected].set_hwnd(int(self.videoframe_fullscreen.winId()))
                self.mediaplayer[self.selected].set_media(self.media[self.selected])
                self.mediaplayer[self.selected].play()
                self.mediaplayer[self.selected].set_time(stashed)
                # self.gridlayout.removeWidget(self.videoframe[2])
                # self.gridlayout.removeWidget(self.videoframe[3])
                # self.gridlayout.removeWidget(self.videoframe[1])
                self.one_fullscreen = True
                self.myRectangle = QtCore.QRect(self.videoframe_fullscreen.x(),self.videoframe_fullscreen.y(),self.videoframe_fullscreen.width(),self.videoframe_fullscreen.height())
                print(f'hi2 {stashed}')
            self.update()
        elif e.key() == QtCore.Qt.Key_N:
            self.mediaplayer[self.selected].release()
            # self.mediaplayer[1].release()
            # self.mediaplayer[2].release()
            # self.mediaplayer[3].release()
            self.mplyr = self.instance[self.selected].media_player_new()
            self.mplyr.set_media(self.media[self.selected])
            self.mplyr.play()
            self.mplyr.toggle_fullscreen()
            print('hi')
            self.update()
        elif e.key() == QtCore.Qt.Key_M:
            self.mplyr.pause()
        

    def paintEvent(self,e):
        if self.timer_is_paused[self.selected]:
            color = QtCore.Qt.red
        else:
            color = QtCore.Qt.green
        self.p.begin(self)
        # self.p.setPen(QtGui.QPen(QtGui.QColor(255,0,0), 2, QtCore.Qt.SolidLine))
        self.p.setPen(QtGui.QPen(color, 2, QtCore.Qt.SolidLine))
        self.p.drawRect(self.myRectangle)
        self.p.end()

def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)
    player = Player()
    player.show()
    player.resize(640, 480)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
