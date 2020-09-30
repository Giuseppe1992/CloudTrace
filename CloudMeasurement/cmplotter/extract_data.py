from pathlib import Path


class OneWayTraceroute(object):
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.traceroute_list = []


    @staticmethod
    def read_traceroute(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
        if not lines[0].startswith("traceroute"):
            raise ValueError("This is not a Traceroute File")
        lines = lines[1:]
        lines = [tuple(line.split()) for line in lines]
        return lines

    @staticmethod
    def get_info_from_file(file_path):
        file_name = file_path.name

        ip, datetime = file_name.replace(".log", "").replace("ip_", "") .split("date_")
        ip = ip.replace("_", ".")
        minute, hour, day, month, year = datetime.split("_")
        date = {'month': month, 'day': day, 'year': year}
        time = {'hour': hour, 'minute': minute, 'second': "0"}
        return ip, date, time

    def build_tracertroute(self, path):

        src, date, time = self.get_info_from_file(file_path=path)
        tr = self.read_traceroute(file_path=path)
        data = {'date': date, 'time': time, 'src': src, 'traceroute': tr}
        self.traceroute_list.append(data)
        return self.traceroute_list


if __name__ == '__main__':
    src = "18.195.116.246"
    dst = "34.248.163.149"
    traceroute = OneWayTraceroute(source=src, destination=dst)
    traceroute.build_tracertroute(path=Path("/Users/giuseppedilena/Desktop/4FC48CC3/{}/experiments/ip_{}date_39_13_30_09_2020.log".format(src, dst.replace(".","_"))))
    print(traceroute.traceroute_list)
