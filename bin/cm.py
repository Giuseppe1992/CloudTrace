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

from CloudMeasurement.experiments.multiregionalTrace import MultiregionalTrace
from CloudMeasurement.liteSQLdb import CloudMeasurementDB
from CloudMeasurement.experiments.ansibleConfiguration import InventoryConfiguration
from CloudMeasurement.experiments.awsUtils.awsUtils import AWSUtils



EXPERIMENTS = {"multiregionalTrace": MultiregionalTrace}
CLOUDUTILS = {"aws": AWSUtils }


class CloudMeasurementRunner(object):
    def __init__(self):
        "Init."
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

        opts.add_option('--purge', action='store_true', default=None, help='purge all the active experiments')

        opts.add_option('--experiments_list', '-l', action='store_true', default=None, help='list the experiments')

        opts.add_option('--instances_list', '-i', action='store_true', default=None, help='list the instances')

        opts.add_option('--delete_experiment', '-d', type='string', default=None, help='delete experiment')

        opts.add_option('--retrieve_data', type='string', default=None, help='retrieve data')

        opts.add_option('--list_of_regions', type='string', default="eu-central-1", help='list of region to use')

        opts.add_option('--az_mapping', type='string', default=None, help='optional Json, describing the az_mapping')

        opts.add_option('--machine_type_mapping', type='string', default=None, help='optional Json, describing'
                                                                                    ' the machine type mapping')

        opts.add_option('--cloud_util', type='string', default="aws", help='retrieve data')

        opts.add_option('--key_id', type='string', default="id_rsa", help='public key id')

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
        dict_opts.pop("key_id")

        if len(list(filter(lambda x: x is not None and x is not False, dict_opts.values()))) > 1:
            raise ValueError("you have to pass just one of this options: {}".format(dict_opts.values()))

        print(dict_opts)
        print(opts)

        if opts.init:
            # TODO: initialize the environment
            system("aws configure")
            # CloudMeasurementDB.purge()
            # InventoryConfiguration.purge()
            exit(0)

        if opts.purge:
            # TODO: purge all the experiment
            # CloudMeasurementDB.purge()
            # InventoryConfiguration.purge()
            exit(0)

        if opts.experiments_list:
            # TODO: list all the experiments
            # CloudMeasurementDB.get_experiments()

            exit(0)

        if opts.instances_list:
            # TODO: list all the experiments
            # CloudMeasurementDB.get_instances()
            exit(0)

        if opts.create_experiment:
            # TODO: create new experiment
            list_of_regions = opts.list_of_regions
            list_of_regions = list_of_regions.split(",")
            experiments_class = EXPERIMENTS[opts.create_experiment]
            az_mapping = convert_json_to_dict(json_path=opts.az_mapping)
            machine_type_mapping = convert_json_to_dict(json_path=opts.machine_type_mapping)
            experiment = experiments_class(list_of_regions=list_of_regions, az_mapping=az_mapping,
                                           machine_type_mapping=machine_type_mapping,
                                           cloud_util=CLOUDUTILS[opts.cloud_util])
            experiment_data = experiment.create_multiregional_vpcs()

            print(experiment_data)
            # CloudMeasurementDB.save(experiment_data)
            exit(0)
            experiment.create_instances(key_pair=opts.key_id)



        if opts.retrieve_data:
            # TODO: retrieve data from the instances
            exit(0)

        if opts.delete_experiment:
            # TODO: delete experiment
            cloud_util = "aws" # From the DB
            create_experiment = "multiregionalTrace" # From DB
            experiments_class = EXPERIMENTS[create_experiment]
            dict_region_vpc = {"eu-central-1": "vpc-01e07dc48feecda0c", "eu-west-2": "vpc-0b5fff0059f4eb176"} # From DB
            experiments_class.clean_experiment(dict_region_vpc=dict_region_vpc, cloud_utils=CLOUDUTILS[cloud_util])
            exit(0)

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
    except Exception:
        # Print exception
        type_, val_, trace_ = sys.exc_info()
        error_msg = ("-" * 80 + "\n" +
                    "Caught exception. Cleaning up...\n\n" +
                    "%s: %s\n" % (type_.__name__, val_) +
                    "-" * 80 + "\n")
        print(error_msg)
        # Print stack trace to debug log
        import traceback

        stack_trace = traceback.format_exc()
        print(stack_trace + "\n")
        cleanup()


if __name__ == '__main__':
    main()
