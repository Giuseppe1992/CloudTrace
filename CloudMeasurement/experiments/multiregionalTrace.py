class MultiregionalTrace(object):
    def __init__(self, list_of_regions, az_mapping=None, machine_type_mapping=None):
        """
        :param list_of_regions: list of regions
        :param az_mapping: dict
        :param machine_type_mapping: dict
        """
        self.list_of_regions = list_of_regions
        self.az_mapping = az_mapping
        self.machine_type_mapping = machine_type_mapping
