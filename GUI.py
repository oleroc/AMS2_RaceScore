
class GuiMainApp(QMainWindow):
   
    
    def initUI(self):
        self.labels = {}
        self.session_id = None
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        # Load assets
        self.window_icon = QIcon(self.base64_to_qicon(rockytm_icon_base64))
        self.setWindowIcon(self.window_icon)
        self.live_background_image = self.base64_to_pixmap(liverace_liveview_img_base64)
        self.result_background_image = self.base64_to_pixmap(race_results_background_img_base64)
        self.final_background_image = self.base64_to_pixmap(race_scores_background_img_base64)
        self.live_status_image = self.base64_to_pixmap(liverace_status_img_base64)
        self.highscore_background_image = self.base64_to_pixmap(high_scores_background_img_base64)
        self.driver_statistics_background_image = self.base64_to_pixmap(driver_statistics_background_img_base64)
        self.speedometer_image = self.base64_to_pixmap(speedometer_bg_img_base64)
        self.tachometer_image = self.base64_to_pixmap(tachometer_bg_img_base64)
        self.needle_image = self.base64_to_pixmap(needle_bg_img_base64)
        self.lap_image = self.base64_to_pixmap(lap_bg_img_base64)
        self.bestlaptime_image = self.base64_to_pixmap(bestlap_bg_img_base64)
        self.wheel_image = self.base64_to_pixmap(wheel_bg_img_base64)
        self.pedals_image = self.base64_to_pixmap(pedal_bg_img_base64)
        self.pedals_raw_image = self.base64_to_pixmap(pedal_raw_bg_img_base64)
        self.pos_image = self.base64_to_pixmap(pos_bg_img_base64)
        self.laptime_image = self.base64_to_pixmap(laptime_bg_img_base64)
        self.delta_local_record_image = self.base64_to_pixmap(delta_local_record_bg_img_base64)
        self.delta_world_record_image = self.base64_to_pixmap(delta_world_record_bg_img_base64)
        self.font_family = self.base64_to_font(sui_generis_rg_font_base64)
        self.font_family_digits = self.base64_to_font(ds_digib_font_base64)

        # Colors
        self.color_values = '#FFD700'
        self.color_labels = '#FFFFFF'
        self.color_dnf = '#00FF00'
        self.color_falsestart = '#FF0000'
        self.color_pitstop = '#0000ff'
        self.color_gold = '#e9c20c'
        self.color_silver = '#C0C0C0'
        self.color_bronze = '#CD7F32'
        self.color_scores = '#000000'
        self.color_lastpos = '#00FF00'

        # Main window setup
        if not self.config.get('config', 'titlebar', fallback='False').strip().lower() == 'true':
            self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Live Race Data")
        self.setGeometry(0, 0, int(self.config['config']['width']), int(self.config['config']['height']))
        self.setFixedSize(int(self.config['config']['width']), int(self.config['config']['height']))
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)

        monitor_index = int(self.config.get('config', 'monitor', fallback='0'))
        screens = QGuiApplication.screens()
        if 0 <= monitor_index < len(screens):
            self.move(screens[monitor_index].geometry().x(), screens[monitor_index].geometry().y())
        else:
            self.move(0, 0)

        # Tab widget and layout
        self.tab_widget = QTabWidget(self.central_widget)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { background: rgba(0, 0, 0, 0); border: 0px; }
            QTabBar::tab { background: rgba(255, 255, 255, 100); color: black; padding: 5px; }
            QTabBar::tab:selected { background: rgba(255, 255, 255, 150); }
        """)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Create widgets for each tab
        self.live_view_widget = QWidget()
        self.results_view_widget = QWidget()
        self.final_view_widget = QWidget()
        self.highscore_view_widget = QWidget()
        self.driver_statistics_widget = QWidget()
        self.driver_info_tab = QWidget()

        self.tab_widget.addTab(self.live_view_widget, "Live Race Data")
        self.tab_widget.addTab(self.results_view_widget, "Previous Races")
        self.tab_widget.addTab(self.final_view_widget, "Accumulated Score")
        self.tab_widget.addTab(self.highscore_view_widget, "High Scores")
        self.tab_widget.addTab(self.driver_statistics_widget, "Driver Statistics")
        self.tab_widget.addTab(self.driver_info_tab, "Driver Info")

        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.live_status_image)
        self.background_label.setGeometry(0, 0, int(self.config['config']['width']), int(self.config['config']['height']))
        self.background_label.setScaledContents(True)
        self.background_label.lower()

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Setup per-tab layouts
        self.setup_live_view()
        self.setup_result_view()
        self.setup_final_view()
        self.setup_highscore_view()
        self.setup_driver_statistics_view()
        self.setup_driver_info_view()

        # Setup radio container
        self.radio_container = QWidget(self.driver_info_tab)
        self.radio_container.setGeometry(640, 820, 600, 100)
        self.radio_container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 120);
            border-radius: 10px;
        """)

        self.radio_layout = QGridLayout(self.radio_container)
        self.radio_layout.setContentsMargins(5, 5, 5, 5)
        self.radio_layout.setSpacing(5)

        self.sim_radio_group = QButtonGroup(self.radio_container)
        for i, ip in enumerate(self.available_ips):
            btn = QRadioButton(str(i + 1))
            btn.setToolTip(ip)
            btn.setStyleSheet("""
                QRadioButton:enabled {
                    color: white;
                }
                QRadioButton:disabled {
                    color: gray;
                }
            """)
            self.sim_radio_group.addButton(btn, i)
            self.radio_layout.addWidget(btn, i // 5, i % 5)

        self.sim_radio_group.buttonClicked.connect(
            lambda button: self.set_monitored_ip(self.sim_radio_group.id(button))
        )

        default_ip = ConfigManager.get_config_value('ip_address', 'config', '127.0.0.1').strip()
        default_index = self.available_ips.index(default_ip) if default_ip in self.available_ips else 0
        self.sim_radio_group.button(default_index).setChecked(True)

        self.tab_widget_mapping = {
            0: [],
            1: ['dropdown_races', 'delete_button', 'delete_all_races_button', 'calendar_widget'],
            2: ['Enable_CP','new_session_button', 'dropdown_sessionid', 'previous_session_button'],
            3: ['car_dropdown', 'track_dropdown', 'load_high_scores_button'],
            4: ['driver_dropdown', 'delete_driver_button'],
            5: ['find_computers_button', 'Enable_CP', 'radio_buttons']
        }
    
   
    def on_tab_changed(self, index):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        #print(f"RMA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        for widget_list in self.tab_widget_mapping.values(): # Hide all widgets first
            for widget_name in widget_list:
                if widget_name in self.labels:  # Check if the widget exists in the labels dictionary
                     self.labels[widget_name].hide()
        for widget_name in self.tab_widget_mapping.get(index, []): # Show only the widgets associated with the active tab
            if widget_name in self.labels:
                if self.hidebuttons != True:
                    self.labels[widget_name].show()
                else:
                    if (widget_name != 'new_session_button') and (widget_name != 'previous_session_button'):
                        self.labels[widget_name].show()
                
        if index == 0: self.update_background('live') # Handle other tab-specific logic, like background updates
        elif index == 1 or index ==2 or index == 3: self.update_background('status')
        elif index == 4:
            self.update_background('status')
            if self.all_driver_dropdown_items: # Check if the driver dropdown items have been loaded 
                for item in self.all_driver_dropdown_items:
                    self.driver_dropdown.addItem(item)
                self.driver_dropdown.setItemText(0, "Select a driver or type a driver name...")
                self.driver_dropdown.setCurrentIndex(0)
        #self.radio_container.setVisible(index == 5)
        '''        
        elif index == 5:
            self.toggle_sim_radio_buttons(True)
        else:
            self.toggle_sim_radio_buttons(False)'''

        print(f"RMA Line {inspect.currentframe().f_lineno} Sending signal Tab: {index}")
        self.tab_changed.emit(index)  # Emit the signal with the new index
        #self.tab_widget.currentChanged.connect(lambda: self.tab_changed.emit(self.tab_widget.currentIndex()))
    
    def toggle_sim_radio_buttons(self, visible: bool):
        """Viser eller skjuler alle radio-knappene i sim_radio_group."""
        if hasattr(self, 'sim_radio_group'):
            for button in self.sim_radio_group.buttons():
                button.setVisible(visible)

    def update_background(self, view):

        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def update_background entered")
        if view == 'status': self.background_label.setPixmap(self.live_status_image)
        elif view == 'live': self.background_label.setPixmap(self.live_background_image)
    
 

    def setup_result_view(self): # Content label for displaying loaded results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_result_view entered")
        #Create the Previous Races graphics
        self.result_background_label = QLabel(self.results_view_widget)
        pixmap = QPixmap(self.result_background_image)
        self.result_background_label.setPixmap(pixmap)
        font_name = self.font_family

        # Resize the QLabel to the new size
        self.results_view_layout.addWidget(self.result_background_label)
        self.result_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.results_heading = QLabel("\n Select a race to view previous races", self.results_view_widget)
        self.results_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.results_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_heading.move(30, 15)

        # Add the content label for displaying the loaded results
        self.results_places = QLabel("#", self.results_view_widget)
        self.results_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.results_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.results_name = QLabel("Name", self.results_view_widget)
        self.results_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.results_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_name.move(100, 165)

        self.results_flags = QLabel("Flags", self.results_view_widget)
        self.results_flags.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_flags.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_flags.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_flags.move(490, 165)

        self.results_pitstops = QLabel("Pits", self.results_view_widget)
        self.results_pitstops.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_pitstops.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.results_pitstops.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.results_pitstops.move(620, 165)

        self.results_bestlap = QLabel("Lap", self.results_view_widget)
        self.results_bestlap.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_bestlap.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_bestlap.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_bestlap.move(720, 165)

        self.results_total = QLabel("Total", self.results_view_widget)
        self.results_total.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_total.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_total.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_total.move(845, 165)

        self.results_points = QLabel("#", self.results_view_widget)
        self.results_points.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_points.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.results_points.setAlignment(Qt.AlignHCenter| Qt.AlignTop)
        self.results_points.move(965, 165) 
        
        #Status Label
        self.results_message_label = QLabel(f"", self.results_view_widget)
        self.results_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.results_view_layout.addWidget(self.results_message_label)
        self.results_view_layout.addStretch(1)

    def setup_final_view(self): # Content label for displaying Final results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_final_view entered")
        font_name = self.font_family
        self.final_background_label = QLabel(self.final_view_widget)
        pixmap = QPixmap(self.final_background_image)
        self.final_background_label.setPixmap(pixmap)
        self.final_view_layout.addWidget(self.final_background_label)
        self.final_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.final_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
  
        #self.final_content = QLabel("No race data available", self.final_view_widget)
        #self.final_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        #self.final_view_layout.addWidget(self.final_content)
        #self.final_view_layout.addStretch(1)

        # Add the content label for displaying the Header Data
        self.final_heading = QLabel("Select a session to view scores", self.final_view_widget)
        self.final_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.final_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_heading.move(30, 15)

        # Add the content label for displaying the loaded results
        self.final_places = QLabel("#", self.final_view_widget)
        self.final_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.final_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.final_name = QLabel("Name", self.final_view_widget)
        self.final_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.final_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_name.move(100, 165)
 
        self.final_lastpos = QLabel("LastPos", self.final_view_widget)
        self.final_lastpos.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_lastpos.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.final_lastpos.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_lastpos.move(490, 165)

        self.final_points = QLabel("#", self.final_view_widget)
        self.final_points.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_points.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_points.setAlignment(Qt.AlignHCenter| Qt.AlignTop)
        self.final_points.move(620, 165)  

        self.final_gold = QLabel("Gold", self.final_view_widget)
        self.final_gold.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_gold.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_gold.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_gold.move(720, 165)

        self.final_silver = QLabel("Silver", self.final_view_widget)
        self.final_silver.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_silver.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_silver.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_silver.move(820, 165)

        self.final_bronze = QLabel("Bronze", self.final_view_widget)
        self.final_bronze.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_bronze.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_bronze.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_bronze.move(920, 165)

        self.final_message_label = QLabel("", self.final_view_widget)
        self.final_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.final_view_layout.addWidget(self.final_message_label)
        self.final_view_layout.addStretch(1)

    def setup_highscore_view(self): # Content label for displaying Final results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_higscore_view entered")
        font_name = self.font_family
        self.highscore_background_label = QLabel(self.highscore_view_widget)
        pixmap = QPixmap(self.highscore_background_image)
        self.highscore_background_label.setPixmap(pixmap)
        self.highscore_view_layout.addWidget(self.highscore_background_label)
        self.highscore_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.highscore_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.highscore_heading = QLabel("\n Select a track and car to view high Scores", self.highscore_view_widget)
        self.highscore_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.highscore_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_heading.move(30, 15)
        
        # Add the content label for displaying places
        self.highscore_places = QLabel("#", self.highscore_view_widget)
        self.highscore_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.highscore_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.highscore_name = QLabel("Name", self.highscore_view_widget)
        self.highscore_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.highscore_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_name.move(100, 165)
 
        self.highscore_laptime = QLabel("Laptime", self.highscore_view_widget)
        self.highscore_laptime.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_laptime.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.highscore_laptime.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_laptime.move(490, 165)
    
    def setup_driver_statistics_view(self): # Content label for displaying Final results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_higscore_view entered")
        font_name = self.font_family
        self.driver_statistics_background_label = QLabel(self.driver_statistics_widget)
        pixmap = QPixmap(self.driver_statistics_background_image)
        self.driver_statistics_background_label.setPixmap(pixmap)
        self.driver_statistics_layout.addWidget(self.driver_statistics_background_label)
        self.driver_statistics_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.driver_statistics_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.driver_statistics_heading = QLabel("Select a driver to view statistics", self.driver_statistics_widget)
        self.driver_statistics_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.driver_statistics_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.driver_statistics_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_heading.move(30, 15)
        

        # Add the content label for displaying the loaded results
        self.driver_statistics_track = QLabel("Track", self.driver_statistics_widget)
        self.driver_statistics_track.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_track.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_track.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_track.move(45, 165)

        # Add the content label for displaying the loaded results
        self.driver_statistics_car = QLabel("Car", self.driver_statistics_widget)
        self.driver_statistics_car.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_car.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_car.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_car.move(520, 165)
        

        self.driver_statistics_laptime = QLabel("Laptime", self.driver_statistics_widget)
        self.driver_statistics_laptime.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_laptime.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_laptime.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_laptime.move(900, 165)

        self.driver_statistics_lap = QLabel("Lap", self.driver_statistics_widget)
        self.driver_statistics_lap.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_lap.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_lap.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_lap.move(1015, 165)

    def setup_live_view(self): # Setup your live view widgets here
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_live_view entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def setup_live_view entered {self.session_id}")
        self.live_heading = QLabel(f"Waiting for a new race to start...Current Session: {self.session_id}", self.live_view_widget)
        self.live_heading.setStyleSheet("font-size: 18px;font-weight:bold; color: black;")
        self.live_view_layout.addWidget(self.live_heading, alignment=Qt.AlignTop)
        self.live_heading.setMinimumSize(1000, 120)  # Set this to a size that you believe should fit your text
        
        # Add Race Status label for live updates
        #self.live_status_label = QLabel("Race Messages here: ", self.live_view_widget)
        self.live_status_label = QLabel("Race Messages...", self.live_view_widget)
        self.live_status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.live_status_label.setMinimumSize(325, 60)  # Set this to a size that you believe should fit your text
        self.live_status_label.move(10, -5)

        # Add top times/speed label for live updates
        self.live_best_label = QLabel("Top Speed and Time:", self.live_view_widget)
        self.live_best_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.live_best_label.setMinimumSize(600, 60)  # Set this to a size that you believe should fit your text
        self.live_best_label.move(350, -5)
        
        # Add world record information label for live updates
        self.world_record_label = QLabel("Records", self.live_view_widget)
        self.world_record_label.setStyleSheet("font-size: 14px; color: red; font-weight: bold; background-color: rgba(0, 0, 0, 0);")
        self.world_record_label.setMinimumSize(450, 50)  # Set this to a size that you believe should fit your text
        self.world_record_label.move(650, -20)  # Adjust the position as needed
        self.world_record_label.raise_()
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(lambda: self.world_record_label.setVisible(not self.world_record_label.isVisible()))
        self.main_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Add participant labels for live updates
        self.participant_labels = {}
        for i in range(20):  # Assuming 20 participants max
            self.participant_labels[i] = QLabel("", self.live_view_widget)
            self.live_view_layout.addWidget(self.participant_labels[i])
            self.participant_labels[i].hide()  # Hide labels initially
        # You can add other live view specific components here as per the original design.

    def setup_driver_info_view(self): # Setup your driver info view widgets here
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
        font_name = self.font_family
        scaled_speedo = self.speedometer_image.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        scaled_tacho = self.tachometer_image.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.speedometer_label = QLabel(self.driver_info_tab)
        self.speedometer_label.setPixmap(scaled_speedo)
        self.speedometer_label.setFixedSize(scaled_speedo.size())
        self.speedometer_label.setStyleSheet("background: transparent;")
        self.speedometer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.speedometer_label.move(25, 25)

        self.tachometer_label = QLabel(self.driver_info_tab)
        self.tachometer_label.setPixmap(scaled_tacho)
        self.tachometer_label.setFixedSize(scaled_tacho.size())
        self.tachometer_label.setStyleSheet("background: transparent;")
        self.tachometer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.tachometer_label.move(210, 25)

        self.scaled_needle_image = self.needle_image.scaled(183, 183, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.speed_needle_label = QLabel(self.speedometer_label)
        self.speed_needle_label.setPixmap(self.scaled_needle_image)
        self.speed_needle_label.setAttribute(Qt.WA_TranslucentBackground)
        self.speed_needle_label.setStyleSheet("background: transparent;")
        self.speed_needle_label.setFixedSize(self.scaled_needle_image.size())

        self.tacho_needle_label = QLabel(self.tachometer_label)
        self.tacho_needle_label.setPixmap(self.scaled_needle_image)
        self.tacho_needle_label.setAttribute(Qt.WA_TranslucentBackground)
        self.tacho_needle_label.setStyleSheet("background: transparent;")
        self.tacho_needle_label.setFixedSize(self.scaled_needle_image.size())

        speedo_center = QPoint(self.speedometer_label.width() // 2, self.speedometer_label.height() // 2)
        needle_center = self.scaled_needle_image.rect().center()
        self.speed_needle_label.move(speedo_center.x() - needle_center.x(), speedo_center.y() - needle_center.y())
        self.speed_needle_label.raise_()

        tacho_center = QPoint(self.tachometer_label.width() // 2, self.tachometer_label.height() // 2)
        self.tacho_needle_label.move(tacho_center.x() - needle_center.x(), tacho_center.y() - needle_center.y())
        self.tacho_needle_label.raise_()

        self.speed_display = QLabel(self.speedometer_label)
        self.speed_display.setFont(QFont(self.font_family_digits, 25))
        self.speed_display.setStyleSheet("color: red; background-color: black;")
        self.speed_display.setAttribute(Qt.WA_TranslucentBackground)
        self.speed_display.setAlignment(Qt.AlignCenter)
        self.speed_display.setFixedSize(50, 30)
        self.speed_display.move(int(self.speedometer_label.width() * 0.55), int(self.speedometer_label.height() * 0.67))

        self.gear_display = QLabel(self.tachometer_label)
        self.gear_display.setFont(QFont(self.font_family_digits, 32))
        self.gear_display.setStyleSheet("color: red; background-color: black;")
        self.gear_display.setAttribute(Qt.WA_TranslucentBackground)
        self.gear_display.setAlignment(Qt.AlignCenter)
        self.gear_display.setFixedSize(50, 30)
        self.gear_display.move(int(self.tachometer_label.width() * 0.55), int(self.tachometer_label.height() * 0.67))

        pedal_x = self.tachometer_label.x() + self.tachometer_label.width() + 30
        base_y = self.tachometer_label.y()

        self.car_heading_text = QLabel("Car:", self.driver_info_tab)
        self.car_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.car_heading_text.setMinimumSize(100, 50)
        self.car_heading_text.move(25, 300)
        self.track_heading_text = QLabel("Track:", self.driver_info_tab)
        self.track_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.track_heading_text.setMinimumSize(100, 50)
        self.track_heading_text.move(25, 350)
        self.driver_heading_text = QLabel("Driver:", self.driver_info_tab)
        self.driver_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.driver_heading_text.setMinimumSize(100, 50)
        self.driver_heading_text.move(25, 400)
        self.collison_heading_text = QLabel("Crash:", self.driver_info_tab)
        self.collison_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.collison_heading_text.setMinimumSize(100, 50)
        self.collison_heading_text.move(25, 450)
        self.worldrecord_heading_text = QLabel("World Record:", self.driver_info_tab)
        self.worldrecord_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.worldrecord_heading_text.setMinimumSize(200, 50)
        self.worldrecord_heading_text.move(25, 500)
        self.localrecord_heading_text = QLabel("Local Record:", self.driver_info_tab)
        self.localrecord_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.localrecord_heading_text.setMinimumSize(200, 50)
        self.localrecord_heading_text.move(25, 550)

        self.car_txt = QLabel("Car", self.driver_info_tab)
        self.car_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.car_txt.setMinimumSize(500, 50)
        self.car_txt.move(90, 300)
        self.track_txt = QLabel("Track", self.driver_info_tab)
        self.track_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.track_txt.setMinimumSize(500, 50)
        self.track_txt.move(110, 350)
        self.driver_txt = QLabel("Driver", self.driver_info_tab)
        self.driver_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.driver_txt.setMinimumSize(300, 50)
        self.driver_txt.move(115, 400)
        self.collison_txt = QLabel("Crash", self.driver_info_tab)
        self.collison_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.collison_txt.setMinimumSize(300, 50)
        self.collison_txt.move(115, 450)
        self.worldrecord_txt = QLabel("World Record", self.driver_info_tab)
        self.worldrecord_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.worldrecord_txt.setMinimumSize(300, 50)
        self.worldrecord_txt.move(200, 500)
        self.localrecord_txt = QLabel("Local Record", self.driver_info_tab)
        self.localrecord_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.localrecord_txt.setMinimumSize(400, 50)
        self.localrecord_txt.move(200, 550)

        self.pedals_bg = QLabel(self.driver_info_tab)
        self.pedals_bg.setPixmap(self.pedals_image)
        self.pedals_bg.setScaledContents(True)
        self.pedals_bg.setFixedSize(100, 110)
        self.pedals_bg.move(pedal_x - 10, base_y)
        self.pedals_bg.lower()

        self.clutch_bar = QProgressBar(self.pedals_bg)
        self.brake_bar = QProgressBar(self.pedals_bg)
        self.throttle_bar = QProgressBar(self.pedals_bg)

        for bar, color, offset in zip([self.clutch_bar, self.brake_bar, self.throttle_bar], ['blue', 'red', 'green'], [0, 30, 60]):
            bar.setOrientation(Qt.Vertical)
            bar.setRange(0, 100)
            bar.setGeometry(offset + 10, 8, 20, 70)  # Leave 10px padding at top
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background: transparent;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            bar.setTextVisible(False)
            bar.raise_()


        self.pedals_raw_bg = QLabel(self.driver_info_tab)
        self.pedals_raw_bg.setPixmap(self.pedals_raw_image)
        self.pedals_raw_bg.setScaledContents(True)
        self.pedals_raw_bg.setFixedSize(100, 110)
        self.pedals_raw_bg.move(pedal_x - 10, self.pedals_bg.height()+30)
        self.pedals_bg.lower()
        self.clutch_raw_bar = QProgressBar(self.pedals_raw_bg)
        self.brake_raw_bar = QProgressBar(self.pedals_raw_bg)
        self.throttle_raw_bar = QProgressBar(self.pedals_raw_bg)

        for bar_raw, color, offset in zip([self.clutch_raw_bar, self.brake_raw_bar, self.throttle_raw_bar], ['blue', 'red', 'green'], [0, 30, 60]):
            bar_raw.setOrientation(Qt.Vertical)
            bar_raw.setRange(0, 100)
            bar_raw.setGeometry(offset + 10, 8, 20, 70)  # Leave 10px padding at top
            bar_raw.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background: transparent;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            bar_raw.setTextVisible(False)
            bar_raw.raise_()
        #Create Player race position labels and text            
        self.pos_bg = QLabel(self.driver_info_tab)
        self.pos_bg.setPixmap(self.pos_image)
        self.pos_bg.setFixedSize(self.pos_image.size())
        self.pos_bg.move(self.pedals_raw_bg.x() - int((self.pos_bg.width() - self.pedals_raw_bg.width())/2), self.pedals_raw_bg.y() + self.pedals_raw_bg.height() + 10)

        self.pos_text = QLabel("0", self.pos_bg)
        self.pos_text.setFont(QFont(self.font_family_digits, 62))
        self.pos_text.setStyleSheet("color: red; background: transparent;")
        self.pos_text.setAlignment(Qt.AlignCenter)
        self.pos_text.setGeometry(0, -15, self.pos_bg.width(), self.pos_bg.height())
        self.pos_text.raise_()

        #Create Player lap and laptime labels and text
        self.lap_bg = QLabel(self.driver_info_tab)
        self.lap_bg.setPixmap(self.lap_image)
        self.lap_bg.setFixedSize(self.lap_image.size())
        self.lap_bg.move(pedal_x + self.pedals_bg.width() + 30, 25)
        self.lap_text = QLabel("0/0", self.lap_bg)
        self.lap_text.setFont(QFont(self.font_family_digits, 42))
        self.lap_text.setStyleSheet("color: red; background: transparent;")
        self.lap_text.setAlignment(Qt.AlignCenter)
        self.lap_text.setGeometry(0, -15, self.lap_bg.width(), self.lap_bg.height())
        self.lap_text.raise_()

        self.laptime_bg = QLabel(self.driver_info_tab)
        self.laptime_bg.setPixmap(self.laptime_image)
        self.laptime_bg.setFixedSize(self.laptime_image.size())
        self.laptime_bg.move(self.lap_bg.x(), self.lap_bg.y() + self.lap_bg.height() + 10)
        self.laptime_text = QLabel("0:00.00", self.laptime_bg)
        self.laptime_text.setFont(QFont(self.font_family_digits, 42))
        self.laptime_text.setStyleSheet("color: red; background: transparent;")
        self.laptime_text.setAlignment(Qt.AlignLeft)
        self.laptime_text.setGeometry(25, 20, self.laptime_bg.width(), self.laptime_bg.height())
        self.laptime_text.raise_()

        self.bestlaptime_bg = QLabel(self.driver_info_tab)
        self.bestlaptime_bg.setPixmap(self.bestlaptime_image)
        self.bestlaptime_bg.setFixedSize(self.bestlaptime_image.size())
        self.bestlaptime_bg.move(self.laptime_bg.x(), self.laptime_bg.y() + self.laptime_bg.height() + 10)
        self.bestlaptime_text = QLabel("0:00.00", self.bestlaptime_bg)
        self.bestlaptime_text.setFont(QFont(self.font_family_digits, 42))
        self.bestlaptime_text.setStyleSheet("color: red; background: transparent;")
        self.bestlaptime_text.setAlignment(Qt.AlignCenter)
        self.bestlaptime_text.setGeometry(0, -5, self.bestlaptime_bg.width(), self.bestlaptime_bg.height())
        self.bestlaptime_text.raise_()

        self.deltaworldrecord_bg = QLabel(self.driver_info_tab)
        self.deltaworldrecord_bg.setPixmap(self.delta_world_record_image)
        self.deltaworldrecord_bg.setFixedSize(self.delta_world_record_image.size())
        self.deltaworldrecord_bg.move(self.bestlaptime_bg.x(), self.bestlaptime_bg.y() + self.bestlaptime_bg.height() + 10)
        self.deltaworldrecord_text = QLabel("0:00.00", self.deltaworldrecord_bg)
        self.deltaworldrecord_text.setFont(QFont(self.font_family_digits, 42))
        self.deltaworldrecord_text.setStyleSheet("color: red; background: transparent;")
        self.deltaworldrecord_text.setAlignment(Qt.AlignCenter)
        self.deltaworldrecord_text.setGeometry(0, -5, self.deltaworldrecord_bg.width(), self.deltaworldrecord_bg.height())
        self.deltaworldrecord_text.raise_()

        self.deltalocalrecord_bg = QLabel(self.driver_info_tab)
        self.deltalocalrecord_bg.setPixmap(self.delta_local_record_image)
        self.deltalocalrecord_bg.setFixedSize(self.delta_local_record_image.size())
        self.deltalocalrecord_bg.move(self.deltaworldrecord_bg.x(), self.deltaworldrecord_bg.y() + self.deltaworldrecord_bg.height() + 10)
        self.deltalocalrecord_text = QLabel("0:00.00", self.deltalocalrecord_bg)
        self.deltalocalrecord_text.setFont(QFont(self.font_family_digits, 42))
        self.deltalocalrecord_text.setStyleSheet("color: red; background: transparent;")
        self.deltalocalrecord_text.setAlignment(Qt.AlignCenter)
        self.deltalocalrecord_text.setGeometry(0, -5, self.deltalocalrecord_bg.width(), self.deltalocalrecord_bg.height())
        self.deltalocalrecord_text.raise_()

        # Create the wheel image and label
        self.wheel_label = QLabel(self.driver_info_tab)
        self.wheel_label.setPixmap(self.wheel_image)
        self.wheel_label.setFixedSize(self.wheel_image.size())
        self.wheel_label.move(pedal_x + 420, base_y)
     