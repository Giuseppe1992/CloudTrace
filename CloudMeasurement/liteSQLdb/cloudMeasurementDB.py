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
        # Create tables

        c.execute('''CREATE TABLE CONFIGURATIONS ([DB_PATH] TEXT,[UTILS_PATH] TEXT, [PRIVATE_KEY_PATH] TEXT,
         PRIMARY KEY (DB_PATH)) ''')

        c.execute('''CREATE TABLE EXPERIMENTS ([EXPERIMENT_ID] TEXT PRIMARY KEY, [CLOUD] TEXT, [EXPERIMENT] TEXT,
         [PEERED] INTEGER,[NETWORK_OPTIMIZED] INTEGER, [CREATION_DATE] date, [STARTING_DATE] date, [STATUS] TEXT,
          [ANSIBLE_FILE] TEXT,[CIDR_BLOCK] TEXT) ''')

        c.execute('''CREATE TABLE REGIONS ([EXPERIMENT_ID] TEXT, [REGION] TEXT, [VPC_ID] TEXT, [STATUS] TEXT,
        PRIMARY KEY (REGION, EXPERIMENT_ID)) ''')

        c.execute('''CREATE TABLE INSTANCES ([INSTANCE_ID] TEXT, [MACHINE_TYPE] TEXT, [EXPERIMENT_ID] TEXT,
         [REGION] TEXT, [AVAILABILITY_ZONE] TEXT, [VPC_ID] TEXT, [STATUS] TEXT, [PUBLIC_IP] TEXT, [PRIVATE_IP] TEXT,
          [KEYPAIR_ID] TEXT, PRIMARY KEY (INSTANCE_ID)) ''')

        conn.commit()

    @staticmethod
    def remove_db(db_path):
        if type(db_path) is not Path and type(db_path) is not PosixPath:
            raise TypeError("db_path should be a Path or PosixPath type, got {} ", format(type(db_path)))
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
        c.execute('''SELECT * FROM EXPERIMENTS''')

        rows = c.fetchall()
        return rows

    @staticmethod
    def get_instances(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM INSTANCES''')
        rows = c.fetchall()
        return rows

    @staticmethod
    def get_instances_experiment(db_path, experiment_id):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM INSTANCES WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        rows = c.fetchall()
        return rows

    @staticmethod
    def get_instance_columns(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT NAME FROM pragma_table_info("INSTANCES") ''')
        rows = c.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def get_experiment_columns(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT NAME FROM pragma_table_info("EXPERIMENTS") ''')
        rows = c.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def get_regions(db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM REGIONS''')
        rows = c.fetchall()
        return rows

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
    def add_experiment(db_path, experiment_id, cloud_util, experiment_type, peered, network_optimized, creation_date,
                       starting_date, status, ansible_file, cidr_block):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''INSERT INTO EXPERIMENTS VALUES ('{}', '{}', '{}','{}', '{}', '{}','{}', '{}', '{}', '{}')'''.format(
            experiment_id, cloud_util, experiment_type, peered, network_optimized, creation_date, starting_date,
            status, ansible_file, cidr_block))

        conn.commit()
        c.close()

    @staticmethod
    def add_region(db_path, experiment_id, region, vpc_id, status):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''INSERT INTO REGIONS VALUES ('{}', '{}', '{}','{}')'''.format(experiment_id, region,
                                                                                  vpc_id, status))

        conn.commit()
        c.close()

    @staticmethod
    def add_instance(db_path, instance_id, machine_type, experiment_id, region, availability_zone,
                     vpc_id, status, public_address, private_address, key_pair_id):

        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        c.execute('''INSERT INTO INSTANCES VALUES ('{}', '{}', '{}','{}','{}', '{}', '{}','{}','{}', '{}')'''.format(
            instance_id, machine_type, experiment_id, region, availability_zone,
            vpc_id, status, public_address, private_address, key_pair_id))

        conn.commit()
        c.close()

    @staticmethod
    def add_configuration(db_path, utils_path, private_key_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''INSERT INTO CONFIGURATIONS VALUES ('{}', '{}', '{}')'''.format(db_path,
                                                                                    utils_path,
                                                                                    private_key_path))
        conn.commit()
        c.close()

    @staticmethod
    def get_experiment(experiment_id, db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM EXPERIMENTS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        rows = c.fetchall()
        if not rows:
            return None
        return rows[0]

    @staticmethod
    def get_regions_dict(experiment_id, db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT * FROM REGIONS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        rows = c.fetchall()
        if not rows:
            return None
        regions_vpc_dict = {r[1]: r[2]for r in rows}
        return regions_vpc_dict

    @staticmethod
    def stop_experiment(self):
        pass

    @staticmethod
    def delete_experiment(experiment_id, db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''DELETE FROM INSTANCES WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        c.execute('''DELETE FROM REGIONS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        c.execute('''DELETE FROM EXPERIMENTS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        conn.commit()
        c.close()

    @staticmethod
    def get_ansible_file(experiment_id, db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT ANSIBLE_FILE FROM EXPERIMENTS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        rows = c.fetchall()
        if not rows:
            return None
        return rows[0][0]

    @staticmethod
    def get_experiment_type(experiment_id, db_path):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT EXPERIMENT FROM EXPERIMENTS WHERE EXPERIMENT_ID='{}' '''.format(experiment_id))
        rows = c.fetchall()
        if not rows:
            return None
        return rows[0][0]

    @staticmethod
    def get_instances_data(experiment_id, db_path, db_columns):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''SELECT {} FROM INSTANCES WHERE EXPERIMENT_ID='{}' '''.format(",".join(db_columns), experiment_id))
        rows = c.fetchall()
        if not rows:
            return None
        return rows

    @staticmethod
    def update_experiment_starting_time(experiment_id, db_path, date):
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''UPDATE EXPERIMENTS SET STARTING_DATE='{}' WHERE EXPERIMENT_ID='{}'; '''.format(date,
                                                                                                    experiment_id))
        conn.commit()
        c.close()


if __name__ == '__main__':
    print(CloudMeasurementDB.get_experiment_columns(db_path="/Users/giuseppe/.CloudMeasurement/CloudMeasurementDB.db"))
    print(CloudMeasurementDB.get_instance_columns(db_path="/Users/giuseppe/.CloudMeasurement/CloudMeasurementDB.db"))
    print(CloudMeasurementDB.get_experiment(db_path="/Users/giuseppe/.CloudMeasurement/CloudMeasurementDB.db",

                                            experiment_id="86EF9987"))
