#!/usr/bin/env python

"""
Cloud Measurement Runner

author: Giuseppe Di Lena (giuseppedilena92@gmail.com)
"""

import sys
from json import load
from os import system
from optparse import OptionParser
from pathlib import Path
import termtables as tt


from CloudMeasurement.experiments.multiregionalTrace import MultiregionalTrace
from CloudMeasurement.liteSQLdb import CloudMeasurementDB
from CloudMeasurement.experiments.ansibleConfiguration import InventoryConfiguration
from CloudMeasurement.experiments.awsUtils.awsUtils import AWSUtils
from sqlite3 import OperationalError
from datetime import datetime


EXPERIMENTS = {"multiregionalTrace": MultiregionalTrace}
CLOUDUTILS = {"aws": AWSUtils }

home = Path.home()
UTILS_PATH = home / ".CloudMeasurement"
ANSIBLE_PATH = UTILS_PATH / "ansible"
DB_PATH = UTILS_PATH / "CloudMeasurementDB.db"
PRIVATE_KEY_PATH = home / ".ssh" / "id_rsa"

class CloudMeasurementRunner(object):
    def __init__(self):
        """Init."""
        self.options = None
        self.args = None  # May be used someday for more CLI scripts
        self.validate = None

        self.parseArgs()
        self.begin()

    def parseArgs( self ):

        desc = ( "The utility creates experiments  from the\n"
                 "command line. It can create experiments,\n"
                 "list them, and manage." )

        usage = ( '%prog [options]\n'
                  '(type %prog -h for details)' )

        opts = OptionParser(description=desc, usage=usage )
        opts.add_option('--create_experiment', type='string', default=None,
                        help="possible experiments: \n" + "|".join(EXPERIMENTS.keys()))

        opts.add_option('--init', action='store_true', default=None, help='initialize the environment')

        opts.add_option('--configuration', action='store_true', default=None, help='initialize the environment')

        opts.add_option('--purge', action='store_true', default=None, help='purge all the active experiments')

        opts.add_option('--experiments_list', '-e', action='store_true', default=None, help='list the experiments')

        opts.add_option('--regions_list', '-r', action='store_true', default=None, help='list the regions')

        opts.add_option('--instances_list', '-i', action='store_true', default=None, help='list the instances')

        opts.add_option('--delete_experiment', '-d', type='string', default=None, help='delete experiment')

        opts.add_option('--retrieve_data', type='string', default=None, help='retrieve data')

        opts.add_option('--list_of_regions', type='string', default="eu-central-1", help='list of region to use')

        opts.add_option('--az_mapping', type='string', default=None, help='optional Json, describing the az_mapping')

        opts.add_option('--machine_type_mapping', type='string', default=None, help='optional Json, describing'
                                                                                    ' the machine type mapping')

        opts.add_option('--cloud_util', type='string', default="aws", help='retrieve data')

        opts.add_option('--key_pair_id', type='string', default="id_rsa", help='public key id')

        opts.add_option('--verbose', '-v', default=None, action='store_true', help='Shows more details')


        self.options, self.args = opts.parse_args()

        # We don't accept extra arguments after the options
        if self.args:
            opts.print_help()
            exit()

    def begin( self ):
        """Run the CLI"""
        opts = self.options

        # dict_opts without the optional values
        dict_opts = dict(vars(opts))
        dict_opts.pop("list_of_regions")
        dict_opts.pop("cloud_util")
        dict_opts.pop("az_mapping")
        dict_opts.pop("machine_type_mapping")
        dict_opts.pop("key_pair_id")
        dict_opts.pop("verbose")

        if len(list(filter(lambda x: x is not None and x is not False, dict_opts.values()))) > 1:
            raise ValueError("you have to pass just one of this options: {}".format(dict_opts.values()))

        if opts.init:
            system("aws configure")

            private_key_path = str(input("Insert the default private key [default: {}] : "
                                         "".format(PRIVATE_KEY_PATH)) or str(PRIVATE_KEY_PATH))
            if not Path(private_key_path).is_file():
                raise ValueError('{} is not a valid file'.format(private_key_path))

            try:
                CloudMeasurementDB.purge(db_path=DB_PATH)
            except OperationalError:
                print("ERROR:",
                      "Make sure that the directory {} exists and it has the correct permissions".format(UTILS_PATH))
                exit(1)

            CloudMeasurementDB.add_configuration(db_path=DB_PATH, utils_path=UTILS_PATH,
                                                 private_key_path=private_key_path)
            exit(0)

        if opts.configuration:
            try:
                rows = CloudMeasurementDB.get_configuration(db_path=DB_PATH)
            except OperationalError:
                print("Configuration not found, make sure to run 'cm --init' before starting your experiments ")
                exit(1)

            if len(rows) == 0:
                print("Configuration not found, make sure to run 'cm --init' before starting your experiments ")
                exit(1)
            else:
                row = rows[0]
                headers_up = ['DB_PATH', 'UTILS_PATH', 'PRIVATE_KEY_PATH']
                table = tt.to_string([row], header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.purge:
            # TODO: purge all the experiment
            # CloudMeasurementDB.purge()
            # InventoryConfiguration.purge()
            exit(0)

        if opts.experiments_list:
            headers_up = ["EXPERIMENT_ID", "CLOUD", "EXPERIMENT", "PEERED", "NETWORK_OPTIMIZED",
                          "STARTING_DATE", "ENDING_DATE", "STATUS", "ANSIBLE_FILE", "CIDR_BLOCK"]

            rows = CloudMeasurementDB.get_experiments(db_path=DB_PATH)
            if len(rows) == 0:
                print("NO EXPERIMENTS CREATED")
            else:
                table = tt.to_string(rows, header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.regions_list:
            headers_up = ["EXPERIMENT_ID", "REGION", "VPC_ID", "STATUS"]
            rows = CloudMeasurementDB.get_regions(db_path=DB_PATH)
            if len(rows) == 0:
                print("NO REGIONS CREATED")
            else:
                table = tt.to_string(rows, header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.instances_list:
            headers_up = ["INSTANCE_ID", "MACHINE_TYPE", "EXPERIMENT_ID", "REGION", "AVAILABILITY_ZONE",
                          "VPC_ID", "STATUS", "PUBLIC_IP", "PRIVATE_IP", "KEYPAIR_ID"]
            rows = CloudMeasurementDB.get_instances(db_path=DB_PATH)
            if len(rows) == 0:
                print("NO INSTANCES CREATED")
            else:
                table = tt.to_string(rows, header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.create_experiment:
            list_of_regions = opts.list_of_regions
            list_of_regions = list_of_regions.split(",")
            experiments_class = EXPERIMENTS[opts.create_experiment]
            az_mapping = convert_json_to_dict(json_path=opts.az_mapping)
            machine_type_mapping = convert_json_to_dict(json_path=opts.machine_type_mapping)
            experiment = experiments_class(list_of_regions=list_of_regions, az_mapping=az_mapping,
                                           machine_type_mapping=machine_type_mapping,
                                           cloud_util=CLOUDUTILS[opts.cloud_util])

            print("* CREATING THE VPCS IN {}".format(list_of_regions))
            experiment_data = experiment.create_multiregional_vpcs()

            print(experiment_data)

            experiment_id = experiment_data["experiment_id"]
            ansible_file = str(ANSIBLE_PATH / (experiment_id + ".yml"))
            cidr_block = experiment_data["cidr_block"]
            starting_date = str(datetime.now())
            self.save_experiment(db_path=DB_PATH, experiment_id=experiment_id, cloud_util=opts.cloud_util,
                                 experiment_type=opts.create_experiment, peered=0, network_optimized=0,
                                 starting_date=starting_date, ending_date="None", status="VPCS CONFIGURED", ansible_file=ansible_file,
                                 cidr_block=cidr_block)

            self.save_regions(db_path=DB_PATH, experiment_data=experiment_data)

            print("* CREATING THE INSTANCES".format(list_of_regions))
            experiment_data = experiment.create_instances(key_pair_id=opts.key_pair_id)
            self.save_instances(db_path=DB_PATH, experiment_data=experiment_data)
            exit(0)

        # if opts.start_experiment:
        #    experiment.create_instances(key_pair=opts.key_id)
        #    self.save_instances(experiment_data=experiment_data)

        if opts.retrieve_data:
            # TODO: retrieve data from the instances
            exit(0)

        if opts.delete_experiment:
            experiment_id = opts.delete_experiment
            row = CloudMeasurementDB.get_experiment(experiment_id, db_path=DB_PATH,)
            if row is None:
                raise ValueError("{} does not exists".format(opts.delete_experiment))

            cloud_util = row[1]
            create_experiment = row[2]
            experiments_class = EXPERIMENTS[create_experiment]
            dict_region_vpc = CloudMeasurementDB.get_regions_dict(experiment_id,db_path=DB_PATH)
            if dict_region_vpc is None:
                raise ValueError("No region assigned for experiment {}".format(opts.delete_experiment))

            print("* DELETING THE EXPERIMENT {} - Please DO NOT close this terminal before it is completed"
                  ", you may have inconsistent data otherwise".format(experiment_id))
            experiments_class.purge_experiment(dict_region_vpc=dict_region_vpc, cloud_utils=CLOUDUTILS[cloud_util])
            CloudMeasurementDB.delete_experiment(experiment_id, db_path=DB_PATH)
            exit(0)

        print("No operation")
        exit(0)

    @staticmethod
    def save_experiment(**kwargs):
        headers_dict = {"EXPERIMENT_ID": "experiment_id", "CLOUD": "cloud_util", "EXPERIMENT": "experiment_type",
                        "PEERED": "peered", "NETWORK_OPTIMIZED": "network_optimized", "STARTING_DATE": "starting_date",
                        "ENDING_DATE": "ending_date", "STATUS": "status", "ANSIBLE_FILE": "ansible_file",
                        "CIDR_BLOCK": "cidr_block"}
        CloudMeasurementDB.add_experiment(**kwargs)

    @staticmethod
    def save_regions(db_path, experiment_data):
        list_of_regions = list(experiment_data.keys())
        list_of_regions.remove("cidr_block")
        list_of_regions.remove("experiment_id")

        experiment_id = experiment_data["experiment_id"]

        for region in list_of_regions:
            vpc_id = experiment_data[region]["vpc_id"]
            status = "VPC UP"
            CloudMeasurementDB.add_region(db_path=db_path, experiment_id=experiment_id, region=region,
                                          vpc_id=vpc_id, status=status)

    def save_instances(self, db_path, experiment_data):
        list_of_regions = list(experiment_data.keys())
        list_of_regions.remove("cidr_block")
        list_of_regions.remove("experiment_id")
        experiment_id = experiment_data["experiment_id"]

        for region in list_of_regions:
            instance_id = experiment_data[region]["instance_id"]
            machine_type = experiment_data[region]["machine_type"]
            public_address = experiment_data[region]["public_address"]
            private_address = experiment_data[region]["private_address"]
            availability_zone = experiment_data[region]["availability_zone"]
            vpc_id = experiment_data[region]["vpc_id"]
            status = "RUNNING"
            key_pair_id = experiment_data[region]["key_pair_id"]
            CloudMeasurementDB.add_instance(db_path=db_path, instance_id=instance_id, machine_type=machine_type,
                                            experiment_id=experiment_id, region=region,
                                            availability_zone=availability_zone, vpc_id=vpc_id, status=status,
                                            public_address=public_address, private_address=private_address,
                                            key_pair_id=key_pair_id)

def convert_json_to_dict(json_path):
    if json_path is None:
        return None
    with open(Path(json_path), "r") as json_file:
        dictionary = eval(load(json_file))
    return dictionary


def cleanup():
    pass

def main():
    try:
        CloudMeasurementRunner()
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt. Shutting down and cleaning up...\n\n")
        cleanup()


if __name__ == '__main__':
    main()
