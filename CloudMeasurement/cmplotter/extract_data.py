from pathlib import Path
from re import match


class OneWayTraceroute(object):
    def __init__(self, source, destination, path):
        self.source = source
        self.destination = destination
        self.path = path
        if type(path) is str:
            self.path = Path(path)
        self.traceroute = []
        self.date = None
        self.time = None
        self.delay = None
        self.hops = None

    def __str__(self):
        return str({"src": self.source, "dst": self.destination, "traceroute": self.traceroute, "date": self.date,
                    "time": self.time, "path": self.path, "delay": self.delay, "hops": self.hops})

    @staticmethod
    def read_traceroute(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
        if not lines[0].startswith("traceroute"):
            raise ValueError("This is not a Traceroute File")
        lines = lines[1:]
        lines = [tuple(line.split()) for line in lines]
        lines = list(filter(lambda x: bool(x), lines))
        return lines

    @staticmethod
    def get_info_from_file(file_path):
        file_name = file_path.name
        ip, datetime_ = file_name.replace(".log", "").replace("ip_", "").split("date_")
        ip = ip.replace("_", ".")
        minute, hour, day, month, year = datetime_.split("_")
        date_ = {'month': month, 'day': day, 'year': year}
        time_ = {'hour': hour, 'minute': minute, 'second': "0"}
        return ip, date_, time_

    def build_traceroute(self):
        _, date_, time_ = self.get_info_from_file(file_path=self.path)
        tr = self.read_traceroute(file_path=self.path)
        self.date = date_
        self.time = time_
        tr = [self.intervall_conversion(x) for x in tr]
        self.traceroute = tr
        self.delay = self.get_delay()
        self.hops = self.number_of_hops()

    @staticmethod
    def intervall_conversion(intervall):
        if len(intervall) == 4:
            return intervall[0], None, None, None, None
        if len(intervall) == 5:
            n, ip_, t1, t2, t3 = intervall
            new_t = []
            for t in (t1, t2, t3):
                m = match(r"(([0-9]+\.([0-9]{1,3}))ms)|[0-9]+ms", t)
                if m:
                    start, end = m.span()
                    # remove ms
                    new_t.append(float(t[start:end - 2]))
                elif t == "*":
                    new_t.append(None)
                else:
                    raise ValueError("Value {} not convertible".format(t))
            return tuple([n, ip_] + new_t)

        raise ValueError(intervall)

    def number_of_hops(self):
        return len(self.traceroute)

    def get_delay(self):
        last_hop_delays = self.traceroute[-1][2:]
        last_hop_delays = list(filter(lambda x: x is not None, last_hop_delays))
        return sum(last_hop_delays)/len(last_hop_delays)

    def to_dict(self):
        return self.__dict__


if __name__ == '__main__':
    src = "52.215.48.195"
    dst = "3.123.41.173"
    file = "/Users/giuseppedilena/Desktop/" \
           "ABEE5D71/{}/experiments/ip_{}date_41_8_05_10_2020.log".format(src, dst.replace(".", "_"))
    traceroute = OneWayTraceroute(source=src, destination=dst, path=file)
    traceroute.build_traceroute()
    print(traceroute.to_dict())
    print(traceroute.number_of_hops(), traceroute.get_delay())
