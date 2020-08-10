from pathlib import Path

class InventoryConfiguration(object):
    def __init__(self, experiment_id, dir_path):
        if type(experiment_id) is not str:
            raise TypeError(f"type of experiment_id is not str, got type {type(experiment_id)}")
        self.experiment_id = experiment_id
        self.dir_path = Path(dir_path)
        self.file_path = self.dir_path / (experiment_id + ".yml")
        if self.file_path.is_file():
            raise FileExistsError(f"file {self.file_path} already exists")

    def add_host(self, host_id, region, public_ip):
        pass
