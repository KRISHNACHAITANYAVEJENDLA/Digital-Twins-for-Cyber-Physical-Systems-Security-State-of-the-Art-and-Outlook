class DigitalTwin:
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.state = {}

    def update(self, new_data):
        self.state.update(new_data)

    def get_state(self):
        return self.state
