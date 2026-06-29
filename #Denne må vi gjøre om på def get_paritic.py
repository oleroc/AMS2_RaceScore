#Denne må vi gjøre om på def get_pariticipants_ips(self, participants): (Skriv all kode kommentarer, print etc på engelske!):
#Nå baserer den seg på drivers.txt fra et annet program, og jeg ønsker at det skal kunne handles internt.    
#    sjekk API ip in self.active_computers, find if participants are present, note name of viewed participant, and match with IP, set rest of buttons as s-1,s-2 etc.
    
# Under har jeg laget forslag til ny kode, men ufullstendig, sikkert mye feil, og ikke testet.    
    
 #old:  
    def get_pariticipants_ips(self, participants):
     
        sim_config = [ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '').strip() for i in range(1, 21) if ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '')]
        self.active_drivers = []

        for participant in participants:
            name = participant['mName']

            if name in self.driver_sims:
                sim_pos = int(self.driver_sims[name])  # f.eks. '3' -> int = 3
                ip = sim_config[sim_pos - 1]  # 1-basert til 0-basert indeks
                self.active_drivers.append(ip)

             self.radio_button_update.emit(self.active_drivers)  # Emit the signal to update the radio buttons with the active drivers.
  
#new: 
    def get_pariticipants_ips(self, participants):
        ip_name = {}
        for i, ip in self.active_computers:
            data = get_api_data(ip)
            if data != None
                participants = data.get('participants', {}).get('mParticipantInfo', []) # Fetch participants data
                if participants:
                    index = participants.get('mViewedParticipantIndex', -1)
                    ip_name[ip] = participants[index]['mName']
                else:
                    ip_name[ip] = #S-1 if last part of ip is 201, S-2 if last part is 202, etc."       
        self.radio_button_update.emit(ip_name)  # Emit the signal to update the radio buttons with the active drivers.
 
    def get_api_data(self, ip_address):
        if self.session is None: self.session = aiohttp.ClientSession()
        self.session.get(f"http://{ip_address}:8180/crest2/v1/api", timeout=3) as r:
        if r.status != 200:
            return None
        else:
            data = r.json()
            if data is None:
                return None
            else:
                return data
            
            Kan du så gjøre om slik at handle_radio_button_update er hybrid, slik at får den en liste med bare IP, så fungerer den som før, men er det en liste med Ip {navn] så setter den den navn på alle knappene, setter all