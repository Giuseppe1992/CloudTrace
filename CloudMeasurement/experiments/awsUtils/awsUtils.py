import boto3


class AWSUtils(object):
    def __init__(self, region="eu-central-1"):
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.regions = None
        self.regions_az_dict = {}
        self.all_az = None

    def get_all_AWS_regions(self):
        if self.regions is None:
            response = self.ec2_client.describe_regions()
            list_region = []
            for region in response['Regions']:
                list_region.append(region['RegionName'])
            self.regions = sorted(list_region)
        return self.regions

    def get_az_in_the_region(self, region):
        if self.regions_az_dict.get(region, None) is None:
            temp_client = boto3.client('ec2', region_name=region)
            response = temp_client.describe_availability_zones()
            list_az = []
            for az in list(response['AvailabilityZones']):
                list_az.append(az['ZoneName'])
            self.regions_az_dict[region] = list_az

        return self.regions_az_dict[region]

    def get_all_az(self):
        if self.all_az is None:
            regions = self.get_all_AWS_regions()
            list_az = []
            for region in regions:
                list_az += self.get_az_in_the_region(region=region)
            self.all_az = list_az
        return self.all_az

    @staticmethod
    def create_vpc(vpc_name, region='eu-central-1', cidr_block='10.0.0.0/16',  **kwargs):
        ec2_resource = boto3.resource('ec2', region_name=region)
        vpc = ec2_resource.create_vpc(CidrBlock=cidr_block, **kwargs)
        vpc.create_tags(Tags=[{"Key": "Name", "Value": vpc_name}])
        vpc.wait_until_available()
        return vpc


    @staticmethod
    def modifyEnableDnsSupport(vpc_id, region, value=True):
        """
        Modify the parameter EnableDnsSupport in a given VPC with the new Value
        :param vpc_id: VpcId where to modify EnableDnsSupport
        :param region: region where the vpc is created
        :param value: new value of EnableDnsSupport
        :return: None
        """
        ec2Client = boto3.client('ec2', region_name=region)
        ec2Client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": value})

    @staticmethod
    def create_subnet(vpc_id, region, subnet_name, cidr_block, route_table, **kwargs):
        """
        Create a subnet inside a Vpc
        :param vpc_id: id of a Vpc already created; be careful, the Vpc should be ready, before creating a subnet
        :param region: region where the vpc is created
        :param subnet_name: Subnet Name tag associated to the subnet
        :param cidr_block: Network pool to be assigned, be sure that the subnet is contained in the vpc pool, and
         that the subnet pool is valid. You can check if it is a valid subnet at:
         https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
        :param route_table: Route table object associated to the subnet
        :param kwargs: Optional parameters that you can assign to the Subnet
        :return: subnet object from boto3.resource('ec2')
        """
        ec2_resource = boto3.resource('ec2', region_name=region)
        subnet = ec2_resource.create_subnet(CidrBlock=cidr_block, VpcId=vpc_id, **kwargs)
        subnet.create_tags(Tags=[{"Key": "Name", "Value": subnet_name}])
        route_table.associate_with_subnet(SubnetId=subnet.id)
        return subnet

    @staticmethod
    def create_internet_gateway(region, **kwargs):
        """
        Create an Internet Gateway
        :param region: region where to crate the Internet Gateway
        :param kwargs: Optional parameters that you can assign to the gateway
        :return: Internet Gateway object from boto3.resource('ec2'), you can access the Id by: InternetGatewayObject.id
        """
        ec2_resource = boto3.resource('ec2', region_name=region)
        IGW = ec2_resource.create_internet_gateway(**kwargs)
        return IGW

    @staticmethod
    def attach_internet_gateway_to_vpc(vpc_obj, internet_gateway_id, **kwargs):
        """
        Attach an Internet gateway already created to a vpc
        :param Vpc: vpc object
        :param InternetGatewayId: internet gateway id
        :param kwargs: Optional parameters that you can assign
        :return: None
        """
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
        :param instances_id_list: List of instances Ids
        :return: None
        """
        ec2_client = boto3.client('ec2', region_name=region)
        ec2_client.get_waiter('instance_running').wait(Filters=[{'Name': "instance-id", "Values": instances_id_list}])


    @staticmethod
    def create_security_group(region, vpc_id, security_group_name, description="", **kwargs):
        """
        Create a new Security in the Vpc
        :param region: region where the vpc is created
        :param vpc_id: Vpc Id where to create the new Security Group
        :param security_group_name: Name of the Security Group, it should be unique
        :param description: optional description of the new Security Group
        :param kwargs: Optional parameters that you can assign to the Security Group
        :return: SecurityGroup Id
        """
        ec2_client = boto3.client('ec2', region_name=region)
        sg = ec2_client.create_security_group(VpcId=vpc_id, GroupName=security_group_name,
                                              Description=description, **kwargs)
        return sg["GroupId"]


    @staticmethod
    def AuthorizeSecurityGroupTraffic(region, security_group_id, ip_permissions, directions=[]):
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
        >>> i, e = distrinetAWS.AuthorizeSecurityGroupTraffic("id-xxxx", {"RULES..."},directions=["egress"])
        >>> i
            None
        >>> e
            SOMEDATA....
        """
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
        responses = []
        ec2_client = boto3.client('ec2', region_name=region)
        for id_ in instances_id:
            responses.append(ec2_client.modify_instance_attribute(InstanceId=id_, Groups=security_groups, **kwargs))
        return responses



if __name__ == '__main__':
    t = AWSUtils()
    print(t.get_all_AWS_regions())
    print("2", t.get_all_AWS_regions())
    print(t.get_az_in_the_region(region="eu-central-1"))
    print("2", t.get_az_in_the_region(region="ca-central-1"))
    print(t.get_all_az())
    print("2", t.get_all_az())
