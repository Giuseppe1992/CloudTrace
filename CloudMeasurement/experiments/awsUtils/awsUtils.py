import boto3


class AWSUtils(object):
    def __init__(self, region="eu-central-1"):
        self.ec2Resource = boto3.resource('ec2', region_name=region)
        self.ec2Client = boto3.client('ec2', region_name=region)
        self.regions = None
        self.regions_az_dict = {}
        self.all_az = None

    def get_all_AWS_regions(self):
        if self.regions is None:
            response = self.ec2Client.describe_regions()
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

    def create_vpc(self,region, az):
        pass

    def create_instance(self,region,az,vpc):
        pass

    def create_route_table(self):
        pass


if __name__ == '__main__':
    t = AWSUtils()
    print(t.get_all_AWS_regions())
    print("2", t.get_all_AWS_regions())
    print(t.get_az_in_the_region(region="eu-central-1"))
    print("2", t.get_az_in_the_region(region="ca-central-1"))
    print(t.get_all_az())
    print("2", t.get_all_az())
