from pathlib import Path
from os import system
from re import match
from datetime import datetime, timedelta

from CloudMeasurement.cmplotter.extract_data import OneWayTraceroute

class Plotter(object):
    def __init__(self, path):
        self.path = path
        if type(path) is str:
            self.path = Path(path)
        self.check_plot_data(self.path)
        self.all_ips = self.get_all_ips(path)
        self.traceroutes = self.build_traceroutes()

    def get_all_ips(self, path):
        return self.get_ip_dir(path)

    @staticmethod
    def unzip(zip_file):
        extracted_dir = zip_file.parent
        system("unzip -u -d {} {}".format(extracted_dir, zip_file))

    @staticmethod
    def check_plot_data(path):
        destination_path = Path(path)

        if not destination_path.is_dir():
            print("Path {} is not a valid directory".format(destination_path))
            exit(1)

        file_list = [file.name for file in destination_path.glob("*")]
        if "experiment.json" not in file_list:
            print("Not a valid directory, experiment.json is missing")
            exit(1)

    @staticmethod
    def get_ip_dir(path):
        destination_path = Path(path)
        file_list = [file.name for file in destination_path.glob("*")]
        ip_list = list(filter(lambda x: match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", x), file_list))
        return ip_list

    def build_traceroutes(self):
        path = self.path

        traceroutes = dict()
        for src in self.all_ips:
            traceroutes[src] = dict()
            dsts = set(self.all_ips) - {src}
            exp_path = path / src / "experiments"
            for file in exp_path.glob("*"):
                file_name = file.name
                dst_ip = file_name.split("date_")[0].replace("_", ".")[3:]
                if dst_ip not in dsts:
                    raise ValueError("filename: {} not good for the destinations: {}".format(file_name, dsts))

                if dst_ip not in traceroutes[src].keys():
                    traceroutes[src][dst_ip] = []
                tr = OneWayTraceroute(src, dst_ip, file)
                tr.build_traceroute()
                traceroutes[src][dst_ip].append(tr.to_dict())

        return traceroutes

    def plot(self, starting_date, ending_date, starting_time, ending_time, description=None, **kwargs):
        self.check_dates_format(starting_date, ending_date)
        self.check_time_format(starting_time, ending_time)

        day, month, year = [int(x) for x in starting_date.split("/")]
        hour, minute, second = [int(x) for x in starting_time.split(":")]
        starting_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

        day, month, year = [int(x) for x in ending_date.split("/")]
        hour, minute, second = [int(x) for x in ending_time.split(":")]
        ending_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        print(starting_datetime, ending_datetime, ending_datetime-starting_datetime)

        def filter_datetime(trace):
            trace_date = trace["date"]
            trace_time = trace["time"]
            trace_datetime = datetime(year=int(trace_date["year"]), month=int(trace_date["month"]),
                                      day=int(trace_date["day"]), hour=int(trace_time["hour"]),
                                      minute=int(trace_time["minute"]), second=int(trace_time["second"]))

            return starting_datetime <= trace_datetime <= ending_datetime

        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                self.traceroutes[src][dst] = list(filter(filter_datetime, self.traceroutes[src][dst]))

        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                for trace in self.traceroutes[src][dst]:
                    print(trace)

        if ending_datetime-starting_datetime <= timedelta(hours=1):
            self.plot_hour()
        elif ending_datetime-starting_datetime <= timedelta(days=1):
            self.plot_day()
        elif ending_datetime-starting_datetime <= timedelta(days=7):
            self.plot_week()
        elif ending_datetime-starting_datetime <= timedelta(days=30):
            self.plot_month()
        else:
            raise ValueError("WTF are you trying to plot?")

    def plot_hour(self):
        pass

    def plot_day(self):
        pass

    def plot_week(self):
        pass

    def plot_month(self):
        pass

    @staticmethod
    def check_dates_format(starting_date, ending_date):
        regular_expression = r"^\d{1,2}\/\d{1,2}\/\d{4}$"
        if not match(regular_expression, starting_date):
            raise ValueError("{} does not match re: {}".format(starting_date, regular_expression))
        if not match(regular_expression, ending_date):
            raise ValueError("{} does not match re: {}".format(ending_date, regular_expression))

    @staticmethod
    def check_time_format(starting_time, ending_time):
        regular_expression = r"^\d{1,2}\:\d{1,2}\:\d{2}$"
        if not match(regular_expression, starting_time):
            raise ValueError("{} does not match re: {}".format(starting_time, regular_expression))
        if not match(regular_expression, ending_time):
            raise ValueError("{} does not match re: {}".format(ending_time, regular_expression))

    def plot_fig(self):
        pass


if __name__ == '__main__':
    p = Plotter(path="/Users/giuseppedilena/Desktop/ABEE5D71/")
    p.build_traceroutes()
    # print(p.traceroutes)
    p.plot("5/10/2020", "5/10/2020", "8:45:00", "8:50:00")
