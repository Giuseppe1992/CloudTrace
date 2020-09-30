#!/usr/bin/env python

"""
Cloud Measurement Runner

author: Giuseppe Di Lena (giuseppedilena92@gmail.com)
"""

import sys
from json import load, dump
from os import system, makedirs, umask, getcwd
from optparse import OptionParser
from pathlib import Path
import termtables as tt


from CloudMeasurement.experiments.multiregionalTrace import MultiregionalTrace
from CloudMeasurement.experiments.regionalTrace import RegionalTrace
from CloudMeasurement.liteSQLdb import CloudMeasurementDB
from CloudMeasurement.experiments.ansibleConfiguration import InventoryConfiguration
from CloudMeasurement.experiments.awsUtils.awsUtils import AWSUtils
from sqlite3 import OperationalError
from datetime import datetime


EXPERIMENTS = {"multiregional": MultiregionalTrace, "regional": RegionalTrace}
CLOUDUTILS = {"aws": AWSUtils }

home = Path.home()
UTILS_PATH = home / ".CloudMeasurement"
ANSIBLE_PATH = UTILS_PATH / "ansible"
EXPERIMENTS_PATH = UTILS_PATH / "experiments"
DB_PATH = UTILS_PATH / "CloudMeasurementDB.db"
PRIVATE_KEY_PATH = home / ".ssh" / "id_rsa"

CRONTAB_CFG_PATH = Path("/home/ubuntu/crontab.cfg")
TRACEROUTE_SCRIPT_PATH = Path("/home/ubuntu/traceroute.sh")
EXPERIMENT_REMOTE_DIR = Path("/home/ubuntu/experiments/")
EXPERIMENT_BK_REMOTE_DIR = Path("/home/ubuntu/experiments_bk/")

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
        opts.add_option('--create_experiment', '-c', type='string', default=None,
                        help="possible experiments: \n" + "|".join(EXPERIMENTS.keys()))

        opts.add_option('--init', action='store_true', default=None, help='initialize the environment')

        opts.add_option('--configuration', action='store_true', default=None, help='get the configurations')

        opts.add_option('--purge', action='store_true', default=None, help='purge all the active experiments')

        opts.add_option('--ls_experiments', '-e', action='store_true', default=None, help='list the experiments')

        opts.add_option('--ls_regions', '-r', action='store_true', default=None, help='list the regions')

        opts.add_option('--ls_instances', '-i', action='store_true', default=None, help='list the instances')

        opts.add_option('--start_experiment', '-s', type='string', default=None, help='start experiment')

        opts.add_option('--delete_experiment', '-d', type='string', default=None, help='delete experiment')

        opts.add_option('--retrieve_data', type='string', default=None, help='retrieve data')

        opts.add_option('--save_data', type='string', default=None, help='save data, EXP_ID,[PATH]')

        opts.add_option('--plot_data', type='string', default=None, help='plot the data in the path')

        ######## OPTIONAL ARGS ########

        opts.add_option('--regions', type='string', default="eu-central-1", help='list of region to use')

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
        dict_opts.pop("regions")
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

        if opts.ls_experiments:
            headers_up = ["EXPERIMENT_ID", "CLOUD", "EXPERIMENT", "PEERED", "NETWORK_OPTIMIZED",
                          "CREATION_DATE", "STARTING_DATE", "STATUS", "ANSIBLE_FILE", "CIDR_BLOCK"]

            rows = CloudMeasurementDB.get_experiments(db_path=DB_PATH)
            if len(rows) == 0:
                print("NO EXPERIMENTS CREATED")
            else:
                table = tt.to_string(rows, header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.ls_regions:
            headers_up = ["EXPERIMENT_ID", "REGION", "VPC_ID", "STATUS"]
            rows = CloudMeasurementDB.get_regions(db_path=DB_PATH)
            if len(rows) == 0:
                print("NO REGIONS CREATED")
            else:
                table = tt.to_string(rows, header=headers_up, style=tt.styles.ascii_thin_double)
                print(table)
            exit(0)

        if opts.ls_instances:
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
            list_of_regions = opts.regions
            list_of_regions = list_of_regions.split(",")
            experiments_class = EXPERIMENTS[opts.create_experiment]
            az_mapping = convert_json_to_dict(json_path=opts.az_mapping)
            machine_type_mapping = convert_json_to_dict(json_path=opts.machine_type_mapping)
            experiment = experiments_class(list_of_regions=list_of_regions, az_mapping=az_mapping,
                                           machine_type_mapping=machine_type_mapping,
                                           cloud_util=CLOUDUTILS[opts.cloud_util])

            print("* CREATING THE VPCS IN {}".format(list_of_regions))
            experiment_data = experiment.create_experiment_environment()

            print(experiment_data)

            experiment_id = experiment_data["experiment_id"]
            ansible_file = ANSIBLE_PATH / (experiment_id + ".cfg")
            cidr_block = experiment_data["cidr_block"]
            creation_date = str(datetime.now())
            self.save_experiment(db_path=DB_PATH, experiment_id=experiment_id, cloud_util=opts.cloud_util,
                                 experiment_type=opts.create_experiment, peered=0, network_optimized=0,
                                 creation_date=creation_date, starting_date="None", status="VPCS CONFIGURED",
                                 ansible_file=str(ansible_file), cidr_block=cidr_block)

            self.save_regions(db_path=DB_PATH, experiment_data=experiment_data)

            print("* CREATING THE INSTANCES {}".format(list_of_regions))
            experiment_data = experiment.create_instances(key_pair_id=opts.key_pair_id)
            self.save_instances(db_path=DB_PATH, experiment_data=experiment_data)
            self.save_inventory(ansible_path=ansible_file, experiment_data=experiment_data)
            print("* EXPERIMENT CORRECTLY CREATED! \n "
                  " you can start the experiment with: cm -s {}".format(experiment_id))
            exit(0)

        if opts.start_experiment:
            experiment_id = opts.start_experiment

            rows = CloudMeasurementDB.get_instances_experiment(db_path=DB_PATH, experiment_id=experiment_id)
            if len(rows) == 0:
                print("NO INSTANCES CREATED FOR THE EXPERIMENT {}".format(experiment_id))
                exit(1)

            ansible_file = CloudMeasurementDB.get_ansible_file(db_path=DB_PATH, experiment_id=experiment_id)
            if ansible_file is None:
                raise ValueError("Ansible File not configured in the DB")

            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="apt",
                                                       module_args="update_cache=yes name=traceroute",
                                                       forks=10, cmdline="--become")
            print(run)
            # experiment_class = EXPERIMENTS[CloudMeasurementDB.get_experiment_type(db_path=DB_PATH,
            # experiment_id=experiment_id)]
            data = ["INSTANCE_ID", "MACHINE_TYPE", "REGION", "AVAILABILITY_ZONE", "PUBLIC_IP", "PRIVATE_IP"]
            instances_data = CloudMeasurementDB.get_instances_data(db_path=DB_PATH, experiment_id=experiment_id,
                                                                   db_columns=data)

            crontab_path = "/tmp/crontab.cfg"
            self.make_crontab_file(crontab_path)
            copy_args = "src={} dest={} mode=777".format(crontab_path, CRONTAB_CFG_PATH)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="copy",
                                                       module_args=copy_args, forks=10, cmdline="--become")
            print(run)

            mkdir_args = "mkdir -p {} && mkdir -p {}".format(EXPERIMENT_REMOTE_DIR, EXPERIMENT_BK_REMOTE_DIR)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="raw",
                                                       module_args=mkdir_args, forks=10, cmdline="--become")

            print(run)

            instances_data_dict = {row[0]: {key.lower(): val for key, val in zip(data, row)} for row in instances_data}
            for instance in instances_data_dict:
                ip = instances_data_dict[instance]["public_ip"]
                list_of_destinations = [instances_data_dict[i]["public_ip"] for i in instances_data_dict]
                list_of_destinations.remove(ip)
                traceroute_path = "/tmp/traceroute.sh"
                self.make_traceroute(path=traceroute_path, list_of_destinations=list_of_destinations)
                copy_args = "src={} dest={} mode=777".format(traceroute_path, TRACEROUTE_SCRIPT_PATH)
                run = InventoryConfiguration.run_inventory(ansible_file, host_pattern=ip, module="copy",
                                                           module_args=copy_args, forks=1, cmdline="--become")
                print(run)

            crontab_cmd = "crontab {}".format(CRONTAB_CFG_PATH)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="raw",
                                                       module_args=crontab_cmd, forks=10, cmdline="--become")
            print(run)

            starting_date = str(datetime.now())
            CloudMeasurementDB.update_experiment_starting_time(experiment_id=experiment_id,
                                                               db_path=DB_PATH,
                                                               date=starting_date)

            exit(0)

        if opts.retrieve_data:
            experiment_id = opts.retrieve_data
            data_path = EXPERIMENTS_PATH / experiment_id

            if CloudMeasurementDB.get_experiment(experiment_id=experiment_id, db_path=DB_PATH) is None:
                print("Experiment: {} not in the DB".format(experiment_id))
                exit(1)

            ansible_file = CloudMeasurementDB.get_ansible_file(db_path=DB_PATH, experiment_id=experiment_id)
            if ansible_file is None:
                raise ValueError("Ansible File not configured in the DB")

            oringinal_mask = umask(0)
            try:
                makedirs(data_path, exist_ok=True, mode=0o777)
            finally:
                umask(oringinal_mask)

            zip_path = EXPERIMENT_REMOTE_DIR.parent / "experiment.zip"
            archive_args = "path={} dest={} format=zip".format(EXPERIMENT_REMOTE_DIR, zip_path)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="archive",
                                                       module_args=archive_args, forks=10, cmdline="--become")
            print(run)

            fetch_args = "src={} dest={} mode=666".format(zip_path, data_path)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="all", module="fetch",
                                                       module_args=fetch_args, forks=10, cmdline="--become")
            print(run)
            instances_data = CloudMeasurementDB.get_instances_data(db_path=DB_PATH, experiment_id=experiment_id,
                                                                   db_columns=["PUBLIC_IP"])
            instances_ips = [d[0] for d in instances_data]

            for ip in instances_ips:
                copy_args = "src={} dest={} mode=666".format(
                    EXPERIMENTS_PATH / experiment_id / ip / "home/ubuntu/experiment.zip",
                    EXPERIMENTS_PATH / experiment_id / ip / "experiment.zip")

                run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="localhost", module="copy",
                                                           module_args=copy_args, forks=1, cmdline="")
                print(run)
                raw_args = "rm -rf {}".format(EXPERIMENTS_PATH / experiment_id / ip / "home")
                run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="localhost", module="raw",
                                                           module_args=raw_args, forks=1, cmdline="")
                print(run)

            exit(0)

        if opts.save_data:
            experiment_id, destination_path = self.check_save_data_arg(args=opts.save_data)

            ansible_file = CloudMeasurementDB.get_ansible_file(db_path=DB_PATH, experiment_id=experiment_id)
            if ansible_file is None:
                raise ValueError("Ansible File not configured in the DB")

            raw_args = "cp -R {} {}".format(EXPERIMENTS_PATH / experiment_id, destination_path)
            run = InventoryConfiguration.run_inventory(ansible_file, host_pattern="localhost", module="raw",
                                                       module_args=raw_args, forks=1, cmdline="")

            print(run)
            experiment_keys = CloudMeasurementDB.get_experiment_columns(db_path=DB_PATH)
            instance_keys = CloudMeasurementDB.get_instance_columns(db_path=DB_PATH)
            experiment = CloudMeasurementDB.get_experiment(experiment_id=experiment_id, db_path=DB_PATH)
            instances = CloudMeasurementDB.get_instances_experiment(experiment_id=experiment_id, db_path=DB_PATH)
            data_dict = {"experiment": {k.lower(): v for k, v in zip(experiment_keys, experiment)},
                         "instances": [
                             {instance[0]: {k.lower(): v for k, v in zip(instance_keys, instance)}} for
                             instance in instances]}

            json_path = str(destination_path / experiment_id /"experiment.json")
            save_dict_to_json(json_path=json_path, data_dict=data_dict)
            exit(0)

        if opts.delete_experiment:
            experiment_id = opts.delete_experiment
            row = CloudMeasurementDB.get_experiment(experiment_id, db_path=DB_PATH,)
            if row is None:
                raise ValueError("{} does not exists".format(opts.delete_experiment))

            cloud_util = row[1]
            create_experiment = row[2]
            experiments_class = EXPERIMENTS[create_experiment]
            dict_region_vpc = CloudMeasurementDB.get_regions_dict(experiment_id=experiment_id, db_path=DB_PATH)
            if dict_region_vpc is None:
                raise ValueError("No region assigned for experiment {}".format(opts.delete_experiment))

            print("* DELETING THE EXPERIMENT {} - Please DO NOT close this terminal before it is completed"
                  ", you may have inconsistent data otherwise".format(experiment_id))
            experiments_class.purge_experiment(dict_region_vpc=dict_region_vpc, cloud_utils=CLOUDUTILS[cloud_util])
            CloudMeasurementDB.delete_experiment(experiment_id=experiment_id, db_path=DB_PATH)
            exit(0)

        if opts.plot_data:

            path = Path(opts.plot_data)
            self.check_plot_data(path)

            self.plot_data(path)
            exit(0)

        print("No operation")
        exit(0)


    def check_plot_data(self, path):
        None

    def plot_data(self, path):
        None

    def check_save_data_arg(self, args):
        arg = args.split(",")
        if len(arg) == 2:
            experiment_id, destination_path = arg[0], Path(arg[1])
        elif len(arg) == 1:
            experiment_id = arg[0]
            destination_path = Path(getcwd())
        else:
            print("Not a valid Argument")
            exit(1)

        if CloudMeasurementDB.get_experiment(experiment_id=experiment_id, db_path=DB_PATH) is None:
            print("Experiment {} does not exists".format(experiment_id))
            exit(1)

        if not destination_path.is_dir():
            print("Path {} is not a valid directory".format(destination_path))
            exit(1)

        return experiment_id, destination_path

    @staticmethod
    def save_experiment(**kwargs):
        CloudMeasurementDB.add_experiment(**kwargs)

    @staticmethod
    def save_regions(db_path, experiment_data):
        list_of_regions = list(experiment_data.keys())
        list_of_regions.remove("cidr_block")
        list_of_regions.remove("experiment_id")

        experiment_id = experiment_data["experiment_id"]
        for region in list_of_regions:
            for vpc in experiment_data[region]:
                vpc_id = vpc["vpc_id"]
                status = "VPC UP"
                CloudMeasurementDB.add_region(db_path=db_path, experiment_id=experiment_id, region=region,
                                              vpc_id=vpc_id, status=status)

    @staticmethod
    def save_instances(db_path, experiment_data):
        list_of_regions = list(experiment_data.keys())
        list_of_regions.remove("cidr_block")
        list_of_regions.remove("experiment_id")
        experiment_id = experiment_data["experiment_id"]

        for region in list_of_regions:
            for instance_dict in experiment_data[region]:
                instance_id = instance_dict["instance_id"]
                machine_type = instance_dict["machine_type"]
                public_address = instance_dict["public_address"]
                private_address = instance_dict["private_address"]
                availability_zone = instance_dict["availability_zone"]
                vpc_id = instance_dict["vpc_id"]
                status = "RUNNING"
                key_pair_id = instance_dict["key_pair_id"]
                CloudMeasurementDB.add_instance(db_path=db_path, instance_id=instance_id, machine_type=machine_type,
                                                experiment_id=experiment_id, region=region,
                                                availability_zone=availability_zone, vpc_id=vpc_id, status=status,
                                                public_address=public_address, private_address=private_address,
                                                key_pair_id=key_pair_id)

    @staticmethod
    def save_inventory(ansible_path, experiment_data):
        inventory_configuration = InventoryConfiguration(inventory_path=ansible_path)
        list_of_regions = list(experiment_data.keys())
        list_of_regions.remove("cidr_block")
        list_of_regions.remove("experiment_id")
        for region in list_of_regions:
            for instance_dict in experiment_data[region]:
                instance_id = instance_dict["instance_id"]
                public_address = instance_dict["public_address"]
                inventory_configuration.add_host(host_id=instance_id, region=region, public_ip=public_address,
                                                 user="ubuntu", password=None)

        inventory_configuration.make_inventory()

    @staticmethod
    def make_traceroute(path, list_of_destinations):
        tr_string = '''#!/bin/bash \n'''
        for ip in list_of_destinations:
            ip_name = "ip_" + ip + "date_"
            ip_name = ip_name.replace(".", "_")
            tr_string += 'traceroute -n -p 33434 {} -U -m 60 | tee {}$(date +"%M_%k_%d_%m_%Y").l' \
                         'og > {}$(date +"%M_%k_%d_%m_%Y").log \n'.format(ip, EXPERIMENT_REMOTE_DIR / ip_name,
                                                                          EXPERIMENT_BK_REMOTE_DIR / ip_name)

        with open(path, "w") as f:
            f.write(tr_string)

        return path

    @staticmethod
    def make_crontab_file(path):
        ct_string = '''*/1 * * * * {}\n\n'''.format(TRACEROUTE_SCRIPT_PATH)
        with open(path, "w") as f:
            f.write(ct_string)
        return path

def convert_json_to_dict(json_path):
    if json_path is None:
        return None
    with open(Path(json_path), "r") as json_file:
        dictionary = eval(load(json_file))
    return dictionary

def save_dict_to_json(json_path, data_dict):
    with open(Path(json_path), "w") as json_file:
        dump(obj=data_dict, fp=json_file)

def cleanup():
    pass

def main():
    try:
        CloudMeasurementRunner()
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt. Shutting down...\n\n")


if __name__ == '__main__':
    main()
