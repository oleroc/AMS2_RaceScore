
class ConfigManager:
    _instance = None  # Singleton instance for global access
    def __init__(self, task_queue):
        self.config_file = 'config.ini'
        self.__version__ = "1.5.9"
        self.__author__ = "RockyTM"
        self.__email__ = "post@drs.no"
        self.__date__ = "2025-03-28"
        self.__description__ = "Script for getting Race Data from AMS2"
        self.config = configparser.ConfigParser()
        self.task_queue = task_queue
        if ConfigManager._instance is None:
            ConfigManager._instance = self
 
class DatabaseThread(QThread):
    race_data_loaded_signal = pyqtSignal(object, object, object)
    load_race_on_start_signal = pyqtSignal(object, object)
    score_data_signal = pyqtSignal(object, object, object)
    write_cp_all_signal = pyqtSignal(object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    write_cp_signal = pyqtSignal(object, object)
    load_highscores_on_start_signal = pyqtSignal(object)
    highscore_data_loaded_signal = pyqtSignal(object)
    drivers_signal = pyqtSignal(object)


    def __init__(self, task_queue, config_manager):
        super().__init__()
        self.task_queue = task_queue
        self.running = True
        self.config_manager = config_manager
        self.db_name = 'RaceDB.db'
        self.conn = None

    def run(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        #self.cursor.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
        self.create_database()
        #self.migrate_laps_table()
        while self.running:
            try:
                operation, args = self.task_queue.get()
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Operation: {operation} Args: {args}")
                print(f"DB Line {inspect.currentframe().f_lineno}  Queue Called: {operation} ")
                if operation == 'stop':
                    self.running = False
                    self.conn.close()  # Close the connection after the race ends
                    self.conn = None
                    break
                else: self.process_queue(operation, *args)
            except Exception as e: logging.error(f"DB Unpack failed: Operation: {operation} Message: {e}")
            finally: 
                self.task_queue.task_done()

  

    def stop(self):
        self.running = False
        self.task_queue.put(('stop', None))
        if hasattr(self, 'session') and self.session:
            self.session.close()  # Safely close the session
        self.quit()  # Stop the event loop if it's running
        self.wait()  # Wait until the thread has fully exited        
        
class ControlPanel(QObject):
    driver_sims_updated = pyqtSignal(dict)  # Signal to update driver sims

    def __init__(self, db_thread, config_manager, gui_main_app, race_app=None):
        super().__init__()
        self.running = True
        self.config_manager = config_manager
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.file_path = self.config['config']['path_to_cp_scores'] + 'score.txt'
        self.best_lap_file_path = self.config['config']['path_to_cp_scores'] + 'bestlap.txt'
        self.driver_file_path = self.config['config']['path_to_cp_scores'] + 'drivers.txt'
        self.db_thread = db_thread
        self.gui_main_app = gui_main_app
        self.race_app = race_app

        # Signalling
        self.db_thread.write_cp_signal.connect(self.process_signal)
        self.db_thread.write_cp_all_signal.connect(self.process_all_signal)
        
    def connect_signals(self, race_app):
        self.race_app = race_app
        #self.race_app.get_request_for_sim_signal.connect(self.process_sim_signal)

   
    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()        
        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal(object, object)
    qualify_finished = pyqtSignal()
    practice_finished = pyqtSignal()
    flags_updated = pyqtSignal(dict)
    initialize = pyqtSignal()

    api_signal_status_updated = pyqtSignal(bool, str)  # Signal to update API status
    ip_address_updated = pyqtSignal(str) # Signal to update IP address
    race_message_updated = pyqtSignal(str) # Signal to update label text
  
    session_type_updated = pyqtSignal(str)  # Signal to indicate time trial detection

    
    def __init__(self, gui_main_app, tab_widget, task_queue, config_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = config_manager
        self.ip_address = self.config_manager.read_ip_address()
        self.gui_main_app = gui_main_app
        self.task_queue = task_queue
        self.tab_widget = tab_widget

        # Variabler
        self.previous_game_state = None
        self.previous_race_state = None
        self.previous_session_state = None
        self.running = True
        self.first_time_run = True
        self.race_id = 0
        self.race_may_not_be_finished = False
        self.session_id = 0
        self.session = None
        self.pit_stops_dict = {}
        self.previous_ipaddress = None
        self.connecton_restored_message_shown = False

        self.init_signals()
    def connect_race_app(self, race_app):
        self.race_app = race_app
        self.race_app.pit_stops_updated.connect(self.update_pit_stops)        
    def init_signals(self):
        self.gui_main_app.session_id_updated.connect(self.set_session_id)
        self.race_app.pit_stops_updated.connect(self.update_pit_stops)

    def run(self):
        # Start the asyncio event loop in this thread
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_main_loop())  # Run your async method
        loop.close()
        
 
                
    async def stop(self):
        if self.session:
            await self.session.close()  # Close the session when stopping
            self.session = None
        self.running = False
        print(f"MT Line {inspect.currentframe().f_lineno} Starting pending all tasks")
        pending = asyncio.all_tasks(loop=asyncio.get_event_loop())
        for task in pending: task.cancel()
        print(f"MT Line {inspect.currentframe().f_lineno} all tasks cancelled")
        self.quit()
        self.wait()

class GuiMainApp(QMainWindow):
    session_id_updated = pyqtSignal(int)
    
    tab_changed = pyqtSignal(int)
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance or cls()

    def __init__(self):
        if GuiMainApp._instance is not None:
            raise RuntimeError("GuiMainApp er allerede opprettet! Bruk get_instance().")
        super().__init__()
        GuiMainApp._instance = self
        self.available_ips = [ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '').strip() for i in range(1, 21) if ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '')]
        self.initUI()
        self.init_threads_and_managers()
        self.init_components()
        self.connect_signals()
        self.init_state_variables()
        self.on_tab_changed(1)  # Set the initial tab to Live view

        print(f"RMA Line {inspect.currentframe().f_lineno} Get latest session ID from DB.")
        self.task_queue.put(('get_latest_session_id', (self.set_session_id,)))
        #self.race_app.get_request_for_sim_signal.emit()

    def init_threads_and_managers(self):
        self.task_queue = queue.Queue()
        self.config_manager = ConfigManager(self.task_queue)
        self.update_config_file = self.config_manager.update_config_file(self)
        self.db_thread = DatabaseThread(self.task_queue, self.config_manager)
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.task_queue, self.config_manager)

    def init_components(self):
        self.control_panel = ControlPanel(self.db_thread, self.config_manager, self)
        self.race_app = RaceApp(
            self.monitor_thread, self.task_queue, self.config_manager,
            self.db_thread, self.control_panel, self, self.tab_widget, self
        )
        self.race_app.get_request_for_sim_signal.connect(self.control_panel.process_sim_signal)
        self.monitor_thread.connect_race_app(self.race_app)
        self.monitor_thread.start()
        self.db_thread.start()

    def connect_signals(self):
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.qualify_finished.connect(self.qualify_finished)
        self.monitor_thread.practice_finished.connect(self.practice_finished)
        self.monitor_thread.initialize.connect(self.initialize_dropdown)
        self.db_thread.load_race_on_start_signal.connect(self.handle_race_data_on_start)
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data)
        self.db_thread.load_highscores_on_start_signal.connect(self.handle_high_scores_data_on_start)
        self.db_thread.race_data_loaded_signal.connect(self.on_race_loaded)
        self.db_thread.highscore_data_loaded_signal.connect(self.on_highscore_loaded)
        self.db_thread.drivers_signal.connect(self.handle_driver_statistics_on_start)
        self.db_thread.score_data_signal.connect(self.calculate_score)
        self.monitor_thread.ip_address_updated.connect(self.update_ip_address)
        self.monitor_thread.race_message_updated.connect(self.update_race_message)
        self.monitor_thread.api_signal_status_updated.connect(self.update_api_status)
        self.monitor_thread.session_type_updated.connect(self.handle_session_type)
        #self.monitor_thread.radio_button_update.connect(self.handle_radio_button_update)
        self.race_app.gui_needle_update.connect(self.needle_rotation)
        self.race_app.participant_update.connect(self.handle_participant_update)
        self.race_app.gui_update.connect(self.apply_gui_updates)
        self.race_app.hide_buttons.connect(self.set_hide_button_flag)
        self.control_panel.driver_sims_updated.connect(self.update_driver_names)  # Connect the signal to the slot that updates the driver names
        self.race_app.radio_button_update.connect(self.handle_radio_button_update)  # IP of computers in the race passed

    def init_state_variables(self):
        self.response_time_log = {}
        self.last_flush = time.time()
        self.live_first_time_run = True
        self.session_id_dropdown = None
        self.latest_session_id = None
        self.hidebuttons = False
        self.time_trial = False
        self.active_computers = []
        self.do_not_reset_index = False
        self.selected_race_id = 0
        self.all_driver_dropdown_items = []
        self.speedo_max = 320
        self.speedo_sweep = (0, 225)
        self.tacho_max = 14000
        self.tacho_sweep = (0, 245)


    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def stop(self):
        print(f"RMA Line {inspect.currentframe().f_lineno} Closing the application...")
        app.quit() # Quit the application immediately.
        if hasattr(self, 'db_thread') and self.db_thread.isRunning(): # Stop the database thread if it exists and is running
            logging.info("Stopping DatabaseThread...")
            self.db_thread.stop()
            self.db_thread.wait()  # Wait for the thread to finish
            print(f"RMA Line {inspect.currentframe().f_lineno} Database thread stopped.")
        logging.info("Stopping MonitorThread...")
        print(f"RMA Line {inspect.currentframe().f_lineno} Stopping MonitorThread...")
        if hasattr(self, 'monitor_thread'):
            try:
                self.monitor_thread.data_updated.disconnect()
                self.monitor_thread.race_finished.disconnect()
            except TypeError:
                pass  # Signals might already be disconnected or not connected
        if hasattr(self, 'monitor_thread') and self.monitor_thread.isRunning(): # Stop the monitor thread if it exists and is running
                self.monitor_thread.running = False
                print(f"RMA Line {inspect.currentframe().f_lineno} Running self monitor thread stop")
                self.monitor_thread.wait()  # Wait for the thread to finish
                print(f"RMA Line {inspect.currentframe().f_lineno} Monitor thread stopped.")
                pass  # Signals might already be disconnected or not connected
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RaceMonitorApp stopped successfully.") # Log completion of stopping sequence

class RaceApp(QThread):
    gui_needle_update = pyqtSignal(object)
    session_id_updated = pyqtSignal(int)
    participant_update = pyqtSignal(int, str)
    gui_update = pyqtSignal(list)
    hide_buttons = pyqtSignal()
    get_request_for_sim_signal = pyqtSignal()
    radio_button_update = pyqtSignal(list)  # Signal to update radio button text
    pit_stops_updated = pyqtSignal(dict)

    def __init__(self, monitor_thread, task_queue, config_manager, db_thread, control_panel, parent=None, tab_widget=None, race_monitor_app=None):
        super().__init__(parent)
        self.task_queue = task_queue
        self.monitor_thread = monitor_thread
        self.config_manager = config_manager
        self.db_thread = db_thread
        self.control_panel = control_panel
        self.tab_widget = tab_widget
        self.race_monitor_app = race_monitor_app or GuiMainApp.get_instance()

        logging.info(f"GMA Line{inspect.currentframe().f_lineno} RaceApp __init__ called")
        print(f"GMA Line{inspect.currentframe().f_lineno} RaceApp __init__ called")
        self.connect_signals()
        self.init_state_variables()


    def connect_signals(self):
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.data_updated.connect(self.update_driver_view)
        self.db_thread.highscore_data_loaded_signal.connect(self.on_highscore_loaded)
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data)
        self.race_monitor_app.session_id_updated.connect(self.handle_latest_session_id)
        self.monitor_thread.session_type_updated.connect(self.handle_session_type)
        self.monitor_thread.ip_address_updated.connect(self.update_ip_address)
        self.race_monitor_app.tab_changed.connect(self.tab_changed)
        self.control_panel.driver_sims_updated.connect(self.update_driver_names)

    def init_state_variables(self):
        self.running = True
        self.speedo_max = 320
        self.speedo_sweep = (0, 225)
        self.tacho_max = 14000
        self.tacho_sweep = (0, 245)
        self.active_tab = 0
        self.live_first_time_run = True
        self.gui = GuiMainApp.get_instance()
    
   

    def run(self):
        
        while self.running:
            if not self.task_queue.empty():
                task, args = self.task_queue.get()
                if hasattr(self, task):
                    getattr(self, task)(*args)

    def stop(self):
        self.running = False

def main():
    global app
    app = QApplication(sys.argv)
    ex = GuiMainApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address