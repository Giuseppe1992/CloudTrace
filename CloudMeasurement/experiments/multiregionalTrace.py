from CloudMeasurement.experiments.awsUtils import AWSUtils

DEFAULT_MACHINE_TYPE = "t3.small"
IP_PERMISSION = [{"IpProtocol": "-1", "FromPort": 1, "ToPort": 65353, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]

class MultiregionalTrace(object):
    def __init__(self, list_of_regions, az_mapping=None, machine_type_mapping=None, cloud_util=AWSUtils):
        """
        :param list_of_regions: list of regions
        :param az_mapping: dict
        :param machine_type_mapping: dict
        :param cloud_util: cloud utils class
        """
        self.list_of_regions = list_of_regions
        self.cloud_utils = cloud_util()
        available_regions = self.cloud_utils.get_all_regions()

        if set(list_of_regions) - set(available_regions) != set():
            raise ValueError("there is a region in the list_of_region parameter that is not valid. \n"
                             "Valid regions: {}".format(available_regions))

        if len(set(list_of_regions)) < len(list_of_regions):
            raise ValueError("One or more region are repeated multiple times")

        self.az_mapping = self.__get_az_mapping(az_mapping=az_mapping)
        self.machine_type_mapping = self.__get_machine_type_mapping(machine_type_mapping=machine_type_mapping)

    def __get_az_mapping(self, az_mapping):
        mapping = dict()
        if az_mapping is None:
            for region in self.list_of_regions:
                az = self.cloud_utils.get_az_in_the_region(region=region)[0]
                mapping[region] = az
        else:
            for region in self.list_of_regions:
                az_list = self.cloud_utils.get_az_in_the_region(region=region)
                map_value = az_mapping.get(region, None)
                if map_value is None:
                    mapping[region] = az_list[0]
                elif map_value in az_list:
                    mapping[region] = map_value
                else:
                    raise ValueError("Availability Zone '{}' is not valid for region {}".format(map_value, region))
        return mapping

    def __get_machine_type_mapping(self, machine_type_mapping):
        # TODO: check that all the machine type are valid.
        mapping = dict()
        if machine_type_mapping is None:
            mapping = {region: DEFAULT_MACHINE_TYPE for region in self.list_of_regions}
        elif type(machine_type_mapping) is str:
            mapping = {region: machine_type_mapping for region in self.list_of_regions}
        else:
            for region in self.list_of_regions:
                map_value = machine_type_mapping.get(region, None)
                if map_value is None:
                    mapping[region] = DEFAULT_MACHINE_TYPE
                else:
                    mapping[region] = map_value
        return mapping

    def create_multiregional_environment(self, cidr_block="10.0.0.0/16"):
        experiment_id = self.cloud_utils.generate_experiment_id()
        for region in self.list_of_regions:
            vpc_id = self.cloud_utils.create_vpc(vpc_name=experiment_id, region=region, cidr_block=cidr_block)
            self.cloud_utils.modify_EnableDnsSupport(vpc_id=vpc_id, region=region, value=True)
            self.cloud_utils.modify_EnableDnsHostnames(vpc_id=vpc_id, region=region, value=True)
            internet_gateway_id = self.cloud_utils.create_internet_gateway(region=region)
            self.cloud_utils.attach_internet_gateway_to_vpc(vpc_id=vpc_id, region=region,
                                                            internet_gateway_id=internet_gateway_id)

            public_route_table_id = self.cloud_utils.create_route_table(vpc_id=vpc_id, region=region,
                                                                     table_name=experiment_id)

            security_group_id = self.cloud_utils.create_security_group(vpc_id=vpc_id, region=region,
                                                                       security_group_name=experiment_id,
                                                                       description=experiment_id)

            self.cloud_utils.authorize_security_group_traffic(region=region, security_group_id=security_group_id,
                                                              ip_permissions=IP_PERMISSION, directions=["ingress"])

            self.cloud_utils.add_route(region=region, route_table_id=public_route_table_id,
                                       gateway_id=internet_gateway_id, destination_cidr_block='0.0.0.0/0')
            az = self.az_mapping[region]
            public_subnet = self.cloud_utils.create_subnet(vpc_id=vpc_id, region=region, az=az,
                                                           subnet_name="Public Subnet", cidr_block=cidr_block,
                                                           route_table_id=public_route_table_id)

if __name__ == '__main__':
    a = MultiregionalTrace(list_of_regions=["eu-central-1", "eu-west-1", "eu-west-2"],
                           az_mapping={"eu-west-1": "eu-west-1b"})
    a.create_multiregional_environment()