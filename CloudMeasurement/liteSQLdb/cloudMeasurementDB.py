import sqlite3
from sqlite3 import Error

from pathlib import Path, PosixPath


class CloudMeasurementDB(object):
    def __init__(self):
        pass

    @staticmethod
    def create_db(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        c.execute('''CREATE TABLE CONFIGURATIONS ([DB_PATH] TEXT,[UTILS_PATH] TEXT, [PRIVATE_KEY_PATH] TEXT,
         PRIMARY KEY (DB_PATH)) ''')

        # Create table - CLIENTS
        c.execute('''CREATE TABLE EXPERIMENTS ([EXPERIMENT_ID] TEXT PRIMARY KEY, [CLOUD] TEXT, [EXPERIMENT] TEXT,
         [PEERED] INTEGER,[NETWORK_OPTIMIZED] INTEGER, [STARTING_DATE] date, [ENDING_DATE] date, [STATUS] TEXT,
          [ANSIBLE_FILE] TEXT)''')

        c.execute('''CREATE TABLE REGIONS ([EXPERIMENT_ID] TEXT, [REGION] TEXT, [VPC_ID] TEXT, [STATUS] TEXT,
         PRIMARY KEY (REGION, EXPERIMENT_ID)) ''')

        c.execute('''CREATE TABLE INSTANCES ([INSTANCE_ID] TEXT, [MACHINE_TYPE] TEXT, [EXPERIMENT_ID] TEXT,
         [REGION] TEXT, [AVAILABILITY_ZONE] TEXT, [VPC_ID] TEXT, [STATUS] TEXT, [PUBLIC_IP], [PRIVATE_IP] TEXT,
          [KEYPAIR_ID] TEXT, PRIMARY KEY (INSTANCE_ID)) ''')

        conn.commit()

    @staticmethod
    def remove_db(db_path):
        if type(db_path) is not Path and type(db_path) is not PosixPath:
            raise TypeError("db_path should be a Path type, got {} ", format(type(db_path)))
        if db_path.is_file() and str(db_path.name).split(".")[-1] == "db":
            db_path.unlink()
        else:
            raise ValueError("{} is not a database".format(db_path))

    @staticmethod
    def purge(db_path):
        if db_path.is_file():
            CloudMeasurementDB.remove_db(db_path)
        CloudMeasurementDB.create_db(db_path)

    @staticmethod
    def get_experiments(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute()

    def get_instances(self):
        pass

    def get_regions(self):
        pass

    @staticmethod
    def get_configuration(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM CONFIGURATIONS''')

        rows = c.fetchall()
        return rows

    def remove_experiment(self, experiment_id):
        pass

    @staticmethod
    def add_experiment():
        pass

    @staticmethod
    def add_region():
        pass

    @staticmethod
    def add_instance():
        pass

    @staticmethod
    def add_configuration(db_path, utils_path, private_key_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''INSERT INTO CONFIGURATIONS VALUES ('{}', '{}', '{}')'''.format(db_path,
                                                                                    utils_path,
                                                                                    private_key_path))
        conn.commit()
        c.close()
