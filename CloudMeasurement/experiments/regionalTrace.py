from CloudMeasurement.experiments.awsUtils import AWSUtils
from .multiregionalTrace import MultiregionalTrace

import ipaddress

DEFAULT_MACHINE_TYPE = "t3.small"
IP_PERMISSION = [{"IpProtocol": "-1", "FromPort": 1, "ToPort": 65353, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
IMAGE_NAME = "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20190722.1"
REMOTE_USER = "ubuntu"


class RegionalTrace(MultiregionalTrace):
    def __init__(self, list_of_regions=("eu-central-1",), az_mapping=None, machine_type_mapping=None,
                 cloud_util=AWSUtils, network_optimized=False):
        """
        A regional Trace is a particular case fo the Multiregional,
        :param region: region
        :param list_of_az: dict
        :param machine_type_mapping: dict
        """
        if len(list_of_regions) > 1:
            raise ValueError("for Regional Trace you have to pass just one Region")
        super(RegionalTrace, self).__init__(list_of_regions=list_of_regions, az_mapping=az_mapping,
                                            machine_type_mapping=machine_type_mapping, cloud_util=cloud_util,
                                            network_optimized=network_optimized)

        # Overrides the previus az_mapping with the new function
        self.az_mapping = self.__get_az_mapping(az_mapping=az_mapping)
        # self.machine_type_mapping = self.__get_machine_type_mapping(machine_type_mapping=machine_type_mapping)
        self.network_optimized = network_optimized

    def __get_az_mapping(self, az_mapping):
        mapping = dict()
        region = self.list_of_regions[0]
        if az_mapping is None:
            az = self.cloud_utils.get_az_in_the_region(region=region)
            mapping[region] = az
            print(az)
        else:
            az_list = self.cloud_utils.get_az_in_the_region(region=region)
            map_value = az_mapping.get(region, None)
            if map_value is None:
                mapping[region] = az_list
                return mapping
            for val in map_value:
                if val not in az_list:
                    raise ValueError("Availability Zone '{}' is not valid for region {}".format(map_value, region))
        return mapping

    def create_experiment_environment(self):
        return self.create_regional_vpc()

    def create_regional_vpc(self, cidr_block="10.0.0.0/16"):
        if self.vpcs_data is not None:
            raise PermissionError("the experiment vpc is already created: {}".format(self.vpcs_data))
        region = self.list_of_regions[0]
        # check if the resource are available in all the regions before starting the experiment
        self.cloud_utils.check_if_it_is_possible_to_create_a_new_vpc_in_the_region(region=region, vpc_needed=1)
        self.cloud_utils.check_if_maximum_it_possible_to_run_instances_in_the_region(region=region,
                                                                                     instances_needed=1)
        subnetwork_pool_generator = ipaddress.ip_network(cidr_block).subnets(new_prefix=24)
        experiment_id = self.cloud_utils.generate_experiment_id()
        vpcs_data = {region: dict() for region in self.list_of_regions}
        vpcs_data["cidr_block"] = cidr_block
        vpcs_data["experiment_id"] = experiment_id

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

        public_subnet_ids = []
        print("MAPPING", self.az_mapping)
        for az in self.az_mapping[region]:
            subnet_pool = str(next(subnetwork_pool_generator))

            public_subnet_id = self.cloud_utils.create_subnet(vpc_id=vpc_id, region=region, az=az,
                                                              subnet_name="Subnet_{}".format(az),
                                                              cidr_block=subnet_pool,
                                                              route_table_id=public_route_table_id)
            public_subnet_ids.append(public_subnet_id)
            self.cloud_utils.modify_MapPublicIpOnLaunch(subnet_id=public_subnet_id, region=region, value=True)

        vpcs_data[region] = [{"vpc_id": vpc_id, "internet_gateway_id": internet_gateway_id,
                              "public_route_table_id": public_route_table_id,
                              "security_group_id": security_group_id,
                              "availability_zone": self.az_mapping[region],
                              "public_subnet": public_subnet_ids}]

        if self.network_optimized:
            self.enable_network_optimized()

        self.vpcs_data = vpcs_data

        return vpcs_data

    def create_peering_connection(self):
        pass

    def create_instances(self, key_pair_id="id_rsa"):
        # TODO check that key_pair exists in all the regions
        region = self.list_of_regions[0]
        refactored_data = []

        for az, subnet in zip(self.vpcs_data[region][0]["availability_zone"],
                              self.vpcs_data[region][0]["public_subnet"]):
            new_data = dict(self.vpcs_data[region][0])
            new_data["availability_zone"] = az
            new_data["public_subnet"] = subnet
            refactored_data.append(new_data)

        self.vpcs_data[region] = refactored_data

        for instance_dict in self.vpcs_data[region]:
            public_subnet_id = instance_dict["public_subnet"]
            image_ami = self.cloud_utils.get_image_AMI_from_region(region=region, image_name=IMAGE_NAME)
            regional_instances_ids = self.cloud_utils.run_instances(region=region, subnet_id=public_subnet_id,
                                                                    instance_type=self.machine_type_mapping[region],
                                                                    key_name=key_pair_id, image_id=image_ami,
                                                                    number_of_instances=1)
            instance_dict["instance_id"] = regional_instances_ids[0]

        for instance_dict in self.vpcs_data[region]:
            instance_id = instance_dict["instance_id"]
            security_group = instance_dict["security_group_id"]
            self.cloud_utils.wait_instances_running(region=region, instances_id_list=[instance_id])
            self.cloud_utils.modify_security_group(region=region, instance_ids=[instance_id],
                                                   groups=[security_group])
            instance_dict["public_address"] = self.cloud_utils.get_instance_public_ip(
                region=region,
                instance_id=instance_id)
            instance_dict["private_address"] = self.cloud_utils.get_instance_private_ip(
                region=region,
                instance_id=instance_id)
            instance_dict["machine_type"] = self.machine_type_mapping[region]
            instance_dict["key_pair_id"] = key_pair_id

        return self.vpcs_data
