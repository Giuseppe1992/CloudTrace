#!/usr/bin/env python

"""
Cloud Measurement Runner

author: Giuseppe Di Lena (giuseppedilena92@gmail.com)
"""

import sys
from optparse import OptionParser
from CloudMeasurement.experiments.multiregionalTrace import MultiregionalTrace

EXPERIMENTS = {"multiregionalTrace": MultiregionalTrace}


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

        opts.add_option('--experiments_list', '-e', action='store_true', default=None, help='list the experiments')

        opts.add_option('--instances_list', '-i', action='store_true', default=None, help='list the instances')

        opts.add_option('--region_list', '-r', action='store_true', default=None, help='list the region')

        opts.add_option('--delete_experiment', '-d', type='string', default=None, help='delete experiment')

        opts.add_option('--retrieve_data', type='string', default=None, help='retrieve data')

        self.options, self.args = opts.parse_args()

        # We don't accept extra arguments after the options
        if self.args:
            opts.print_help()
            exit()

    def begin( self ):
        """Run the CLI"""
        opts = self.options
        dict_opts = vars(opts)
        if not any(dict_opts.values()):
            dict_opts["experiments_list"]=True
            opts.experiments_list = True

        if len(list(filter(lambda x: x is not None and x is not False, dict_opts.values()))) > 1:
            raise ValueError("you have to pass just one option")

        if opts.init:
            # TODO: initialize the environment
            exit(0)

        if opts.purge:
            # TODO: purge all the experiment
            exit(0)

        if opts.experiments_list:
            # TODO: list all the experiments
            exit(0)

        if opts.region_list:
            # TODO: list all the experiments
            exit(0)

        if opts.instances_list:
            # TODO: list all the experiments
            exit(0)

        if opts.create_experiment:
            # TODO: create new experiment
            exit(0)

        if opts.retrieve_data:
            # TODO: retrieve data from the instances
            exit(0)

        if opts.delete_experiment:
            # TODO: delete experiment
            exit(0)


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
