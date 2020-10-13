import boto3
from botocore.exceptions import ClientError
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
    def check_if_subnet_id_exists_in_region(subnet_id, region):
        AWSUtils.check_if_region_exists(region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        list_of_subnets = ec2_resource.subnets.all()
        subnets_ids = [subnet.id for subnet in list_of_subnets]
        if subnet_id not in subnets_ids:
            raise ValueError("The Subnet id that you specified '{}' does not exists in region {},"
                             "possible Subnet in the region are: {}".format(subnet_id, region, subnets_ids))

    @staticmethod
    def get_route_table_ids_in_the_region(region):
        ec2_resource = boto3.resource('ec2', region_name=region)
        return [rt.id for rt in list(ec2_resource.route_tables.iterator())]

    @staticmethod
    def create_vpc_peering(region, vpc_id, peer_region, peer_vpc_id):
        AWSUtils.check_if_region_exists(region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        peer_request = ec2_resource.create_vpc_peering_connection(PeerVpcId=peer_vpc_id,
                                                                  PeerRegion=peer_region,
                                                                  VpcId=vpc_id)
        request_id = peer_request.id
        vpc_requester = ec2_resource.Vpc(id=vpc_id)
        AWSUtils.check_if_region_exists(region=peer_region)

        ec2_resource = boto3.resource('ec2', region_name=peer_region)
        vpc_accepter = ec2_resource.Vpc(id=peer_vpc_id)
        peer_request = None
        for t in range(10):
            try:
                peer_request = list(ec2_resource.vpc_peering_connections.filter(
                    VpcPeeringConnectionIds=[request_id]))
                break
            except ClientError:
                print("ClientError on try: {} {}".format(t, request_id))
                sleep(0.5)

        if not peer_request:
            raise IndexError("the peer request is empty: {}".format(request_id))
        peer_request = peer_request[0]
        if peer_request.status["Code"] != "pending-acceptance":
            raise ValueError("status code for peering request {} - {} is {}".format(region,
                                                                                    peer_region,
                                                                                    peer_request.status["Code"]))
        response = peer_request.accept()

        route_table_requester = list(vpc_requester.route_tables.all())[0].id
        route_table_accepter = list(vpc_accepter.route_tables.all())[0].id
        if vpc_requester != vpc_accepter:
            subnet_accepter = vpc_accepter.cidr_block
            subnet_requester = vpc_requester.cidr_block
            AWSUtils.add_peer_route(region=region, route_table_id=route_table_requester, peer_id=request_id,
                                    destination_cidr_block=subnet_accepter)
            AWSUtils.add_peer_route(region=peer_region, route_table_id=route_table_accepter, peer_id=request_id,
                                    destination_cidr_block=subnet_requester)
        return response

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
    def modify_MapPublicIpOnLaunch(subnet_id, region, value=True):
        """
        Modify the parameter EnableDnsHostnames in a given VPC with the new Value
        :param subnet_id: subnet_id where to modify EnableDnsHostnames
        :param region: region
        :param value: new value of MapPublicIpOnLaunch
        :return: None
        """
        AWSUtils.check_if_subnet_id_exists_in_region(subnet_id=subnet_id, region=region)
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.modify_subnet_attribute(MapPublicIpOnLaunch={'Value': value, }, SubnetId=subnet_id, )
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code != 200:
            raise ValueError("The request returned a wrong HTTPStatusCode: {}".format(status_code))

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
        return subnet.id

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
    def add_peer_route(region, route_table_id, peer_id, destination_cidr_block, **kwargs):
        """
        Add new route in the route table
        :param region: region
        :param route_table_id: RouteTable Object
        :param peer_id: VpcPeeringConnectionId to add in the route
        :param destination_cidr_block: Ip subnet to route. "0.0.0.0/0" for all the traffic
        :param kwargs: Optional parameters that you can assign to the route
        :return: Route Object
        """
        AWSUtils.check_if_route_table_id_exists_in_region(route_table_id=route_table_id, region=region)
        ec2_resource = boto3.resource('ec2', region_name=region)
        route_table = ec2_resource.RouteTable(route_table_id)
        route = route_table.create_route(VpcPeeringConnectionId=peer_id,
                                         DestinationCidrBlock=destination_cidr_block, **kwargs)
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
    def run_instances(region, subnet_id, instance_type, key_name, image_id, number_of_instances=1, **kwargs):
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

    @staticmethod
    def check_if_it_is_possible_to_create_a_new_vpc_in_the_region(region, vpc_needed=1):
        default_max_vpcs = 5
        ec2_client = boto3.client('ec2', region_name=region)
        usedVpc = len(ec2_client.describe_vpcs()["Vpcs"])
        if usedVpc + vpc_needed > default_max_vpcs:
            raise PermissionError(f"You dont have enough free Vpcs in {region}: Required={vpc_needed},"
                                  f" used={usedVpc}, limit={default_max_vpcs}")

    @staticmethod
    def check_if_maximum_it_possible_to_run_instances_in_the_region(region, instances_needed=1):
        default_total_max_instances = 20
        ec2_client = boto3.client('ec2', region_name=region)
        used_instances = {}
        for reservation in ec2_client.describe_instances()["Reservations"]:
            instances = reservation["Instances"]
            for instance in instances:
                instance_type = instance['InstanceType']
                if instance["State"]["Name"] == "running":
                    if instance_type in used_instances.keys():
                        used_instances[instance_type] += 1
                    else:
                        used_instances[instance_type] = 1

        if sum(used_instances.values()) + instances_needed > default_total_max_instances:
            raise PermissionError(f"You dont have enough free instances: Required={instances_needed},"
                                  f" used={sum(used_instances)}, limit={default_total_max_instances}")

    @staticmethod
    def get_image_AMI_from_region(region, image_name):
        """
        Return the imageId (ami-xxxxxxxx) for a given ImageName and a given region. Note that an imageId is different
        for the same image in a different region.
        :param region: regione name ex. eu-central-1 or us-west-1 etc.
        :param image_name: image Name provided by in the amazon description,
                ex. ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20190722.1 for Ubuntu bionic
        :return:  string containing the ImageId
        """
        ec2_client = boto3.client('ec2', region_name=region)
        images_response_with_filter = ec2_client.describe_images(ExecutableUsers=["all"],
                                                                 Filters=[{"Name": "name", "Values": [image_name]}])

        Images = images_response_with_filter["Images"]
        if len(Images) == 0:
            raise RuntimeError(f"Image with Name: {image_name} not found in region:{region}")
        image_description = Images[0]
        image_id = image_description["ImageId"]
        return image_id

    @staticmethod
    def get_instance_private_ip(region, instance_id):
        ec2_resource = boto3.resource('ec2', region_name=region)
        instance = ec2_resource.Instance(id=instance_id)
        return instance.private_ip_address

    @staticmethod
    def get_instance_public_ip(region, instance_id):
        ec2_resource = boto3.resource('ec2', region_name=region)
        instance = ec2_resource.Instance(id=instance_id)
        return instance.public_ip_address

    @staticmethod
    def modify_security_group(region, instance_ids, groups, **kwargs):
        """
        Change the Security Groups Assigned to an instance
        :param instance_ids: to modify the Security Groups
        :param region: region where to modify the Security Groups
        :param groups: List of Security groups Ids to set in the instance
        :param kwargs: Optional parameters that you can assign to the boto3.client("ec2").modify_instance_attribute
        method, you can find the correct documentation at:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.modify_instance_attribute
        :return: None
        """
        responses = []
        ec2_client = boto3.client('ec2', region_name=region)
        for id_ in instance_ids:
            responses.append(ec2_client.modify_instance_attribute(InstanceId=id_, Groups=groups, **kwargs))

    @staticmethod
    def remove_vpc(region, vpc_id):
        """
        Remove the vpc using boto3.resource('ec2')
        :param region: region where the vpc is located
        :param vpc_id: Id of the Vpc
        :return: client response
        Script adapted from https://gist.github.com/vernhart/c6a0fc94c0aeaebe84e5cd6f3dede4ce
        TODO: Make it cleaner and more modular, seems to work now, but the code is terrible
        """
        ec2_resource = boto3.resource('ec2', region_name=region)
        ec2 = ec2_resource
        vpc = ec2.Vpc(vpc_id)
        ec2client = ec2.meta.client

        # detach default dhcp_options if associated with the vpc
        dhcp_options_default = ec2.DhcpOptions('default')
        if dhcp_options_default:
            dhcp_options_default.associate_with_vpc(
                VpcId=vpc.id
            )

        # delete any instances
        public_ips = []
        for subnet in vpc.subnets.all():
            for instance in subnet.instances.all():
                if instance.public_ip_address:
                    public_ips.append(instance.public_ip_address)
                instance.terminate()

        # delete nat_gateways
        nat_gateways = ec2client.describe_nat_gateways(Filters=[{"Name": "vpc-id", "Values": [vpc.id]}])["NatGateways"]
        nat_ids = [nat['NatGatewayId']for nat in nat_gateways]

        for nat in nat_gateways:
            for address in nat["NatGatewayAddresses"]:
                if "PublicIp" in address.keys():
                    public_ips.append(address["PublicIp"])

        for nat in nat_ids:
            ec2client.delete_nat_gateway(NatGatewayId=nat)

        # wait that all the nat gateways are in deleted state
            nat_gateways = ec2client.describe_nat_gateways(Filters=[{"Name": "vpc-id", "Values": [vpc.id]}])[
                "NatGateways"]
            if nat_gateways == []:
                break
            status = tuple(set([nat["State"] for nat in nat_gateways]))
            if status == ("deleted",):
                break

            sleep(1)

        # wait that all the instances are deleted

        subnets = vpc.subnets.all()
        i = 0
        for subnet in subnets:
            i += len(list(subnet.instances.all()))

        completed_hosts = 0
        while True:
            subnets = vpc.subnets.all()
            instances = []
            for subnet in subnets:
                instances += subnet.instances.all()
                if i-len(instances) != completed_hosts:
                    completed_hosts = i-len(instances)
            if not instances:
                break
            sleep(1)

        # detach and delete all gateways associated with the vpc
        for gw in vpc.internet_gateways.all():
            # We need to remove the public address before removing the Internet GW
            vpc.detach_internet_gateway(InternetGatewayId=gw.id)
            gw.delete()
        # delete all route table associations
        route_tables = ec2client.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc.id]}])["RouteTables"]
        for rt in route_tables:
            associations = rt['Associations']
            if associations == []:
                ec2client.delete_route_table(RouteTableId=rt['RouteTableId'])
                continue

            for association in associations:
                if not association["Main"]:
                    association_id = association['RouteTableAssociationId']
                    ec2client.disassociate_route_table(AssociationId=association_id)
            sleep(1)
            if (False,) == tuple(set([association["Main"] for association in associations])):
                ec2client.delete_route_table(RouteTableId=rt["RouteTableId"])

        # delete our endpoints
        for ep in ec2client.describe_vpc_endpoints(
                Filters=[{
                    'Name': 'vpc-id',
                    'Values': [vpc.id]
                }])['VpcEndpoints']:
            ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
        # delete our security groups
        sleep(5)
        for sg in vpc.security_groups.all():
            if sg.group_name != 'default':
                sg.delete()
        # delete any vpc peering connections
        for vpcpeer in ec2client.describe_vpc_peering_connections(
                Filters=[{
                    'Name': 'requester-vpc-info.vpc-id',
                    'Values': [vpc.id]
                }])['VpcPeeringConnections']:
            ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
        # delete non-default network acls
        for netacl in vpc.network_acls.all():
            if not netacl.is_default:
                netacl.delete()
        # delete network interfaces
        for subnet in vpc.subnets.all():
            for interface in subnet.network_interfaces.all():
                interface.delete()
            subnet.delete()
        # finally, delete the vpc

        return ec2client.delete_vpc(VpcId=vpc.id)


if __name__ == '__main__':
    # t = AWSUtils()
    AWSUtils.create_vpc_peering(region="eu-west-1", peer_vpc_id="vpc-0233250a138d717e6",
                                peer_region="eu-west-2", vpc_id="vpc-0e5394562c0d218c5")
