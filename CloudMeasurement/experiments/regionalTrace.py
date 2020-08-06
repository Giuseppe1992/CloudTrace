class RegionalTrace(object):
    def __init__(self, region, list_of_az=None, machine_type_mapping=None, placement_group=None):
        """
        :param regions: region
        :param list_of_az: dict
        :param machine_type_mapping: dict
        """
        self.region = region
        self.list_of_az = list_of_az
        self.machine_type_mapping = machine_type_mapping
