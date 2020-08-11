import sqlite3

DB_PATH = ""
DB_NAME = ""

class CloudMeasurementDB(object):
    def __init__(self):
        pass

    def create_db(self):
        pass

    def remove_db(self):
        pass

    def purge(self):
        self.remove_db()
        self.create_db()

    def get_experiments(self):
        pass

    def get_instances(self):
        pass

    def get_regions(self):
        pass

    def remove_experiment(self, experiment_id):
        pass

    def add_experiment(self,):
        pass
