import boto3
import uuid
from time import sleep


class AWSUtils(object):
    def __init__(self, region="eu-central-1"):
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)

    @staticmethod
    def check_if_region_exists(region):
        regions = AWSUtils.get_all_regions()
        if region not in regions:
            raise ValueError("The region that you specified '{}' does not exists,"
                             " possible regions are: {}".format(region, regions))

    @staticmethod
    def check_if_az_exists_in_region(az, region):
        azs = AWSUtils.get_az_in_the_region(region=region)
        if az not in azs:
            raise ValueError("The Availability Zone that you specified '{}' does not exists in region {},"
                             "possible az in the region are: {}".format(az, region, azs))

    @staticmethod
    def check_if_route_table_id_exists_in_region(route_table_id, region):
        route_table_ids = AWSUtils.get_route_table_ids_in_the_region(region=region)
        if route_table_id not in route_table_ids:
            raise ValueError("The Route Table id that you specified '{}' does not exists in region {},"
                             "possible Route Tables in the region are: {}".format(route_table_id, region,
                                                                                  route_table_ids))

    @staticmethod
    def get_route_table_ids_in_the_region(region):
        ec2_resource = boto3.resource('ec2', region_name=region)
        return [rt.id for rt in list(ec2_resource.route_tables.iterator())]

    @staticmethod
    def get_all_regions(region="eu-central-1"):
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.describe_regions()
        list_region = []
        for region in response['Regions']:
            list_region.append(region['RegionName'])
        return sorted(list_region)

    @staticmethod
    def get_az_in_the_region(region="eu-central-1"):
        AWSUtils.check_if_region_exists(region=region)
        temp_client = boto3.client('ec2', region_name=region)
        response = temp_client.describe_availability_zones()
        list_az = []
        for az in list(response['AvailabilityZones']):
            list_az.append(az['ZoneName'])
        return sorted(list_az)

    @staticmethod
    def get_all_az(region="eu-central-1"):
        AWSUtils.check_if_region_exists(region=region)
        regions = AWSUtils.get_all_regions(region=region)
        list_az = []
        for region in regions:
            list_az += AWSUtils.get_az_in_the_region(region=region)
        return sorted(list_az)

    @staticmethod
    def create_vpc(vpc_name, region='eu-central-1', cidr_block='10.0.0.0/16', **kwargs):
        """
        create a vpc om the specigied region
        :param vpc_name:
        :param region:
        :param cidr_block:
        :param kwargs:
        :return: vpc id
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        vpc = ec2_resource.create_vpc(CidrBlock=cidr_block, **kwargs)
        vpc.create_tags(Tags=[{"Key": "Name", "Value": vpc_name}])
        vpc.wait_until_available()
        return vpc.id

    @staticmethod
    def modify_EnableDnsSupport(vpc_id, region, value=True):
        """
        Modify the parameter EnableDnsSupport in a given VPC with the new Value
        :param vpc_id: VpcId where to modify EnableDnsSupport
        :param region: region where the vpc is created
        :param value: new value of EnableDnsSupport
        :return: None
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": value})

    @staticmethod
    def modify_EnableDnsHostnames(vpc_id, region, value=True):
        """
        Modify the parameter EnableDnsHostnames in a given VPC with the new Value
        :param vpc_id: VpcId where to modify EnableDnsHostnames
        :param region: region
        :param value: new value of EnableDnsHostnames
        :return: None
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": value})

    @staticmethod
    def create_subnet(vpc_id, region, az, subnet_name, cidr_block, route_table_id, **kwargs):
        """
        Create a subnet inside a Vpc
        :param vpc_id: id of a Vpc already created; be careful, the Vpc should be ready, before creating a subnet
        :param region: region where the vpc is created
        :param az: availability zone
        :param subnet_name: Subnet Name tag associated to the subnet
        :param cidr_block: Network pool to be assigned, be sure that the subnet is contained in the vpc pool, and
         that the subnet pool is valid. You can check if it is a valid subnet at:
         https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
        :param route_table_id: Route table id associated to the subnet
        :param kwargs: Optional parameters that you can assign to the Subnet
        :return: subnet object from boto3.resource('ec2')
        """
        AWSUtils.check_if_region_exists(region=region)
        AWSUtils.check_if_az_exists_in_region(az=az, region=region)
        AWSUtils.check_if_route_table_id_exists_in_region(route_table_id=route_table_id, region=region)

        ec2_resource = boto3.resource('ec2', region_name=region)
        route_table = ec2_resource.RouteTable(route_table_id)
        subnet = ec2_resource.create_subnet(CidrBlock=cidr_block, VpcId=vpc_id, AvailabilityZone=az, **kwargs)
        subnet.create_tags(Tags=[{"Key": "Name", "Value": subnet_name}])
        route_table.associate_with_subnet(SubnetId=subnet.id)
        return subnet

    @staticmethod
    def create_internet_gateway(region, **kwargs):
        """
        Create an Internet Gateway
        :param region: region where to crate the Internet Gateway
        :param kwargs: Optional parameters that you can assign to the gateway
        :return: Internet Gateway id
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        IGW = ec2_resource.create_internet_gateway(**kwargs)
        return IGW.id

    @staticmethod
    def create_route_table(vpc_id, region, table_name, **kwargs):
        """
        Create a new route table inside a Vpc
        :param vpc_id: Vpc id where to create the table
        :param region: region
        :param table_name: Tag Name added to the new table
        :param kwargs: Optional parameters that you can assign to the RouteTable
        :return: Route Table id
        """
        AWSUtils.check_if_region_exists(region=region)
        vpc = AWSUtils.get_vpc_obj_from_vpc_id(vpc_id=vpc_id, region=region)
        route_table = vpc.create_route_table(**kwargs)
        sleep(1)
        route_table.create_tags(Tags=[{"Key": "Name", "Value": table_name}])
        return route_table.id

    @staticmethod
    def get_vpc_obj_from_vpc_id(vpc_id, region):
        ec2_resource = boto3.resource('ec2', region_name=region)
        list_of_vpc_ids = [vpc.id for vpc in list(ec2_resource.vpcs.all())]
        if vpc_id not in list_of_vpc_ids:
            raise ValueError("vpc_id: {}, do not exist in region {}.\n"
                             "available ids are: {}".format(vpc_id, region, list_of_vpc_ids))
        vpc = ec2_resource.Vpc(vpc_id)
        return vpc

    @staticmethod
    def add_route(region, route_table_id, gateway_id, destination_cidr_block, **kwargs):
        """
        Add new route in the route table
        :param region: region
        :param route_table_id: RouteTable Object
        :param gateway_id: Gateway Id to add in the route
        :param destination_cidr_block: Ip subnet to route. "0.0.0.0/0" for all the traffic
        :param kwargs: Optional parameters that you can assign to the route
        :return: Route Object
        """
        AWSUtils.check_if_route_table_id_exists_in_region(route_table_id=route_table_id, region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        route_table = ec2_resource.RouteTable(route_table_id)
        route = route_table.create_route(GatewayId=gateway_id, DestinationCidrBlock=destination_cidr_block, **kwargs)
        return route

    @staticmethod
    def attach_internet_gateway_to_vpc(vpc_id, region, internet_gateway_id, **kwargs):
        """
        Attach an Internet gateway already created to a vpc
        :param vpc_id: vpc id
        :param region:  region where to attach the Internet Gateway
        :param internet_gateway_id: internet gateway id
        :param kwargs: Optional parameters that you can assign
        :return: None
        """
        AWSUtils.check_if_region_exists(region=region)
        vpc_obj = AWSUtils.get_vpc_obj_from_vpc_id(vpc_id=vpc_id, region=region)
        vpc_obj.attach_internet_gateway(InternetGatewayId=internet_gateway_id, **kwargs)

    @staticmethod
    def runInstances(region, subnet_id, instance_type, key_name, image_id, number_of_instances=1, **kwargs):
        """
        Run multiple instances in the specified SubnetId, using the specified KeyName pair and The specified Id
        :param region:
        :param subnet_id:
        :param instance_type:
        :param key_name:
        :param image_id:
        :param number_of_instances:
        :param kwargs: Optional parameters to personalize your image, the correct documentation can be found at:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances
        :return: list of the instances ids
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.run_instances(SubnetId=subnet_id, ImageId=image_id, InstanceType=instance_type,
                                            KeyName=key_name, MaxCount=number_of_instances,
                                            MinCount=number_of_instances, **kwargs)
        hosts_id = []
        for host in response['Instances']:
            hosts_id.append(host['InstanceId'])

        return hosts_id

    @staticmethod
    def wait_instances_running(region, instances_id_list):
        """
        Wait until all the instance in input are in 'running state'
        :param region: region
        :param instances_id_list: List of instances Ids
        :return: None
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        ec2_client.get_waiter('instance_running').wait(Filters=[{'Name': "instance-id", "Values": instances_id_list}])

    @staticmethod
    def create_security_group(vpc_id, region, security_group_name, description="", **kwargs):
        """
        Create a new Security in the Vpc
        :param region: region where the vpc is created
        :param vpc_id: Vpc Id where to create the new Security Group
        :param security_group_name: Name of the Security Group, it should be unique
        :param description: optional description of the new Security Group
        :param kwargs: Optional parameters that you can assign to the Security Group
        :return: SecurityGroup Id
        """
        AWSUtils.check_if_region_exists(region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        sg = ec2_client.create_security_group(VpcId=vpc_id, GroupName=security_group_name,
                                              Description=description, **kwargs)
        return sg["GroupId"]

    @staticmethod
    def authorize_security_group_traffic(region, security_group_id, ip_permissions, directions=[]):
        """
        Add a Security Group Rule in the Security Group
        :param region: region where the Security Group is created
        :param security_group_id: Security Group Id
        :param ip_permissions: Description of the rule, Tuo can find the documentation at:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_egress
        or:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_ingress
        :param directions: list of the Direction of the rule, it can be :
        ['ingress','egress'] or ['egress'] or ['ingress']
        :return: tuple containing (ingressData, egressData), in case you dont specify one of the two,
        that part will be None.
        Example:
        >>> i, e = AWSUtils.authorize_security_group_traffic("id-xxxx", {"RULES..."},directions=["egress"])
        >>> i
            None
        >>> e
            SOMEDATA....
        """
        AWSUtils.check_if_region_exists(region=region)
        if ("ingress" not in directions) and ("egress" not in directions):
            raise ValueError("Directions not correct")

        ingress_data, egress_data = None, None

        ec2_client = boto3.client('ec2', region_name=region)
        if "ingress" in directions:
            ingress_data = ec2_client.authorize_security_group_ingress(GroupId=security_group_id,
                                                                       IpPermissions=ip_permissions)

        if "egress" in directions:
            egress_data = ec2_client.authorize_security_group_ingress(GroupId=security_group_id,
                                                                      IpPermissions=ip_permissions)

        return ingress_data, egress_data

    @staticmethod
    def modify_group_id(region, instances_id, security_groups, **kwargs):
        """
        Change the Security Groups Assigned to an instance
        :param region: region where the instance should be created
        :param instances_id: Instance where to modify the Security Groups
        :param security_groups: List of Security groups Ids to set in the instance
        :param kwargs: Optional parameters that you can assign to the boto3.client("ec2").modify_instance_attribute
        method, you can find the correct documentation at:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.modify_instance_attribute
        :return: boto3.client("ec2").modify_instance_attribute response
        """
        AWSUtils.check_if_region_exists(region=region)
        responses = []
        ec2_client = boto3.client('ec2', region_name=region)
        for id_ in instances_id:
            responses.append(ec2_client.modify_instance_attribute(InstanceId=id_, Groups=security_groups, **kwargs))
        return responses

    @staticmethod
    def generate_experiment_id():
        return str(uuid.uuid4()).split("-")[0].upper()


if __name__ == '__main__':
    t = AWSUtils()
