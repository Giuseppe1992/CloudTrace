from CloudMeasurement.experiments.awsUtils import AWSUtils
from multiprocessing import Process
import ipaddress

DEFAULT_MACHINE_TYPE = "t3.small"
IP_PERMISSION = [{"IpProtocol": "-1", "FromPort": 1, "ToPort": 65353, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
IMAGE_NAME = "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20190722.1"
REMOTE_USER = "ubuntu"

class MultiregionalTrace(object):
    def __init__(self, list_of_regions=("eu-central-1",), az_mapping=None,
                 machine_type_mapping=None, cloud_util=AWSUtils):
        """
        :param list_of_regions: list of regions
        :param az_mapping: dict
        :param machine_type_mapping: dict
        :param cloud_util: cloud utils class
        """
        self.list_of_regions = list_of_regions
        self.cloud_utils = cloud_util()
        available_regions = self.cloud_utils.get_all_regions()
        self.vpcs_data = None

        if set(list_of_regions) - set(available_regions):
            raise ValueError("there is a region in the list_of_region that is not valid. \n"
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

    def create_multiregional_vpcs(self, cidr_block="10.0.0.0/16"):
        if self.vpcs_data is not None:
            raise PermissionError("the Multiregional vpc is already created: {}".format(self.vpcs_data))
        for region in self.list_of_regions:
            # check if the resource are available in all the regions before starting the experiment
            self.cloud_utils.check_if_it_is_possible_to_create_a_new_vpc_in_the_region(region=region, vpc_needed=1)
            self.cloud_utils.check_if_maximum_it_possible_to_run_instances_in_the_region(region=region,
                                                                                         instances_needed=1)
        subnetwork_pool_generator = ipaddress.ip_network(cidr_block).subnets(new_prefix=24)
        experiment_id = self.cloud_utils.generate_experiment_id()
        vpcs_data = {region: dict() for region in self.list_of_regions}
        vpcs_data["cidr_block"] = cidr_block
        vpcs_data["experiment_id"] = experiment_id
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
            subnet_pool = str(next(subnetwork_pool_generator))
            public_subnet_id = self.cloud_utils.create_subnet(vpc_id=vpc_id, region=region, az=az,
                                                              subnet_name="Public Subnet",
                                                              cidr_block=subnet_pool,
                                                              route_table_id=public_route_table_id)
            self.cloud_utils.modify_MapPublicIpOnLaunch(subnet_id=public_subnet_id, region=region, value=True)
            vpcs_data[region] = {"vpc_id": vpc_id, "internet_gateway_id": internet_gateway_id,
                                 "public_route_table_id": public_route_table_id, "security_group_id": security_group_id,
                                 "availability_zone": az, "public_subnet": public_subnet_id}
        self.cloud_utils.finalize(vpcs_data)
        self.vpcs_data = vpcs_data
        return vpcs_data

    def create_instances(self, key_pair_id="id_rsa"):
        # TODO check that key_pair exists in all the regions
        for region in self.list_of_regions:
            public_subnet_id = self.vpcs_data[region]["public_subnet"]
            image_ami = self.cloud_utils.get_image_AMI_from_region(region=region, image_name=IMAGE_NAME)
            regional_instances_ids = self.cloud_utils.run_instances(region=region, subnet_id=public_subnet_id,
                                                                    instance_type=self.machine_type_mapping[region],
                                                                    key_name=key_pair_id, image_id=image_ami,
                                                                    number_of_instances=1)
            self.vpcs_data[region]["instance_id"] = regional_instances_ids[0]


        for region in self.list_of_regions:
            instance_id = self.vpcs_data[region]["instance_id"]
            security_group = self.vpcs_data[region]["security_group_id"]
            self.cloud_utils.wait_instances_running(region=region, instances_id_list=[instance_id])
            self.cloud_utils.modify_security_group(region=region, instance_ids=[instance_id], groups=[security_group])
            self.vpcs_data[region]["public_address"] = self.cloud_utils.get_instance_public_ip(region=region,
                                                                                               instance_id=instance_id)
            self.vpcs_data[region]["private_address"] = self.cloud_utils.get_instance_private_ip(region=region,
                                                                                                 instance_id=instance_id
                                                                                                 )
            self.vpcs_data[region]["availability_zone"] = self.az_mapping[region]
            self.vpcs_data[region]["machine_type"] = self.machine_type_mapping[region]
            self.vpcs_data[region]["key_pair_id"] = key_pair_id


        print(self.vpcs_data)
        return self.vpcs_data

    def purge(self):
        proc = []
        for region in self.list_of_regions:
            # enable parallel removal
            vpc_id = self.vpcs_data[region]["vpc_id"]
            p = Process(target=self.cloud_utils.remove_vpc, args=(region, vpc_id))
            p.start()
            proc.append(p)

        for p in proc:
            p.join()

    @staticmethod
    def purge_experiment(dict_region_vpc, cloud_utils=AWSUtils):
        proc = []
        for region in dict_region_vpc.keys():
            # enable parallel removal
            vpc_id = dict_region_vpc[region]
            p = Process(target=cloud_utils.remove_vpc, args=(region, vpc_id))
            p.start()
            proc.append(p)

        for p in proc:
            p.join()


if __name__ == '__main__':
    a = MultiregionalTrace(list_of_regions=["eu-central-1"])
    a.create_multiregional_vpcs()
    a.create_instances(key_pair="id_rsa")
    a.purge()
