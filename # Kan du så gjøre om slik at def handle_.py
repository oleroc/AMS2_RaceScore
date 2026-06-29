#  Kan du så gjøre om slik at def handle_radio_button_update er hybrid, 
# slik at får den en liste med bare IP, så fungerer den som før,
# men er det en liste med Ip {navn, in_race] så setter den navn på alle knappene, setter all som er i race enabled og de andre disabled.


def handle_radio_button_update(self, active_computers):
    if active_computers is None:
        print(f"RMA Line {inspect.currentframe().f_lineno} No active computers provided, using stored value.")
        active_computers = getattr(self, 'active_computers', None)
        if active_computers is None:
            print(f"RMA Line {inspect.currentframe().f_lineno} Still no active computers, skipping.")
            return
    else:
        self.active_computers = active_computers
    for i, ip in enumerate(self.available_ips):
        button = self.sim_radio_group.button(i)
        if button:  # Safety check
            button.setEnabled(ip in active_computers)
            if ip in active_computers:
                print(f"RMA Line {inspect.currentframe().f_lineno} Computer {i+1} is active: {ip}")

def update_driver_names(self, driver_sims):
    """Update button labels in sim_radio_group with driver names and sim numbers."""

    if not driver_sims:
        print(f"RMA Line {inspect.currentframe().f_lineno} No driver sims provided, skipping update.")
        return

    self.driver_sims = driver_sims
    print(f"RMA Line {inspect.currentframe().f_lineno} Driver sims updated: {self.driver_sims}")

    for sim_index_str in driver_sims.values():
        sim_index = int(sim_index_str) - 1  # Adjust from 1-based to 0-based index
        driver_name = [name for name, idx in driver_sims.items() if idx == sim_index_str][0]
        button = self.sim_radio_group.button(sim_index)
        if button:
            button.setText(f"{driver_name} [{sim_index_str}]")
            print(f"RMA Line {inspect.currentframe().f_lineno} Set button {sim_index + 1} to: {driver_name} [{sim_index_str}]")
        else:
            print(f"⚠️ Fant ingen knapp med ID {sim_index_str} for navn {driver_name}")