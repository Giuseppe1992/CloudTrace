import json

REGION_NAME_MAPPING = {'us-east-1':"N. Virginia",
                       'eu-west-1':"Ireland",
                       'eu-west-3':"Paris",
                       'ap-southeast-1':"Singapore",
                       'us-east-2':"Ohio",
                       'ap-east-1':"Hong Kong",
                       'cn-northwest-1':"Ningxia",
                       'eu-central-1':"Frankfurt",
                       'GLOBAL':"",
                       'sa-east-1':"Sao Paulo",
                       'me-south-1':"Bahrain",
                       'cn-north-1':"Beijing",
                       'eu-north-1':"Stockholm",
                       'us-west-2':"Oregon",
                       'ap-northeast-1':"Tokyo",
                       'us-gov-west-1':"US-West",
                       'ap-northeast-3':"Osaka-Local",
                       'eu-west-2':"London",
                       'ap-southeast-2':"Sydney",
                       'ap-south-1':"Mumbai",
                       'us-gov-east-1':"US-East",
                       'af-south-1':"Cape Town",
                       'us-west-1':"N. California",
                       'ap-northeast-2':"Seoul",
                       'ca-central-1':"Central"
                       }

COORD_MAPPING = {'us-east-1': (37.541290, -77.434769),
                 'eu-west-1': (53.350140, -6.266155),
                 'eu-west-3': (48.864716, 2.349014),
                 'ap-southeast-1': (1.290270, 103.851959),
                 'us-east-2': (40.367474, -82.996216),
                 'ap-east-1': (22.302711, 114.177216),
                 'cn-northwest-1': (36.015854,106.242607),
                 'eu-central-1': (50.110924, 8.682127),
                 'GLOBAL': (0.0),
                 'sa-east-1': (-23.5475, -46.63611),
                 'me-south-1': (26.21536, 50.5832),
                 'cn-north-1': (39.916668, 116.383331),
                 'eu-north-1': (59.334591, 18.063240),
                 'us-west-2': (45.523064, -122.676483),
                 'ap-northeast-1': (35.652832, 139.839478),
                 'us-gov-west-1': (46.203611, -119.159167),
                 'ap-northeast-3': (34.6937400,135.5021800),
                 'eu-west-2': (51.509865, -0.118092),
                 'ap-southeast-2': (-33.865143, 151.209900),
                 'ap-south-1': (19.076090, 72.877426),
                 'us-gov-east-1': (41.505493, -81.681290),
                 'af-south-1': (-33.918861, 18.423300),
                 'us-west-1': (37.733795, -122.446747),
                 'ap-northeast-2': (37.532600, 127.024612),
                 'ca-central-1': (43.651070, -79.347015)
                 }


class AwsIp(object):
    def __init__(self):
        self.aws_ip = None
        self.aws_coord = COORD_MAPPING
        self.aws_region_name = REGION_NAME_MAPPING

    def read_file(self, ip_range_json_file):
        with open(ip_range_json_file, "r") as json_f:
            dict_ips = dict(json.load(json_f))
        self.aws_ip = dict_ips
        return self.aws_ip

    def get_aws_ip(self):
        return self.aws_ip

    def get_ipv4_data(self):
        return self.aws_ip["prefixes"]

    def get_ipv6_data(self):
        return self.aws_ip["ipv6_prefixes"]

    def get_region_service_pair(self):
        ipv4_data = self.get_ipv4_data()
        ipv6_data = self.get_ipv6_data()
        pair = set()
        for data in ipv4_data + ipv6_data:
            region, service = data["region"], data["service"]
            pair.add((region, service))
        return pair

    def group_ip_networks_per_region_and_service(self):
        """
        Group the ip network using the pair (region, service) as a key
        :return: dictionary key=(region, service), values=list of IPNetworks.
        """
        keys = self.get_region_service_pair()
        group = {key: [] for key in keys}
        ipv4_data = self.get_ipv4_data()
        ipv6_data = self.get_ipv6_data()
        for data in ipv4_data:
            ipv4_str, region, service = data["ip_prefix"], data["region"], data["service"]
            group[(region, service)].append(ipv4_str)

        for data in ipv6_data:
            ipv6_str, region, service = data["ipv6_prefix"], data["region"], data["service"]
            group[(region, service)].append(ipv6_str)

        return group

    def group_region_and_service_per_ip_networks(self):
        """
        Group the pair (region, service) using ip_network as key
        :return: dictionary values=(region, service), key=ipNetwork.
        """
        ipv4_data = self.get_ipv4_data()
        ipv6_data = self.get_ipv6_data()
        group = {ip_prefix["ip_prefix"]:[] for ip_prefix in ipv4_data}
        for ip_prefix in ipv6_data:
            group[ip_prefix["ipv6_prefix"]] = []

        for data in ipv4_data:
            ipv4_str, region, service = data["ip_prefix"], data["region"], data["service"]
            group[ipv4_str].append((region, service))

        for data in ipv6_data:
            ipv6_str, region, service = data["ipv6_prefix"], data["region"], data["service"]
            group[ipv6_str].append((region, service))
        return group

    def get_aws_services(self):
        ipv4_data = self.get_ipv4_data()
        ipv6_data = self.get_ipv6_data()
        services = set([data["service"]for data in ipv4_data +ipv6_data])
        return services

    def get_aws_regions(self):
        ipv4_data = self.get_ipv4_data()
        ipv6_data = self.get_ipv6_data()
        regions = set([data["region"] for data in ipv4_data + ipv6_data])
        return regions

    def get_aws_ipv4_networks(self):
        ipv4_data = self.get_ipv4_data()
        ips = set([data["ip_prefix"] for data in ipv4_data])
        return ips

    def get_aws_ipv6_networks(self):
        ipv6_data = self.get_ipv6_data()
        ips = set([data["ipv6_prefix"] for data in ipv6_data])
        return ips


if __name__ == '__main__':
    aws =AwsIp()
    aws.read_file("data/ip-ranges.json")
    test=aws.group_ip_networks_per_region_and_service()
    for i in test:
        print(i, test[i])

    print(aws.get_aws_regions())
