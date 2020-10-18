import pickle

from pathlib import Path
from os import system
from re import match
from datetime import datetime, timedelta
from json import load
from numpy import mean
from statistics import stdev
import plotly.graph_objects as go

from CloudMeasurement.cmplotter.extract_data import OneWayTraceroute

class Plotter(object):
    def __init__(self, path):
        self.path = path
        if type(path) is str:
            self.path = Path(path)
        self.check_plot_data(self.path)
        self.all_ips = self.get_all_ips(path)
        self.private_ip_mapping = self.get_private_ip_mapping(path)
        self.traceroutes = self.build_traceroutes()
        self.filtered_data = None
        self.coord = {"eu-central-1a": (50.110924, 8.682127), "eu-central-1b": (50.120924, 8.692127),
                      "eu-central-1c": (50.100924, 8.672127),
                      "eu-west-1a": (51.509865, -0.118092), "eu-west-1b": (51.519865, -0.108092),
                      "eu-west-1c": (51.499865, -0.128092),
                      "eu-west-2a": (53.350140, -6.266155), "eu-west-2b": (53.360140, -6.256155),
                      "eu-west-2c": (53.340140, -6.276155)}

    def get_all_ips(self, path):
        return self.get_ip_dir(path)

    def get_private_ip_mapping(self, path):
        mapping = {}
        description = self.read_experiment_json(path)
        for instance in description["instances"]:
            instance_data = list(instance.values())[0]
            mapping[instance_data["private_ip"]] = instance_data["public_ip"]
        return mapping

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
                    if self.private_ip_mapping[dst_ip] not in dsts:
                        raise ValueError("filename: {} not good for the destinations: {}".format(file_name, dsts))

                if dst_ip not in traceroutes[src].keys():
                    traceroutes[src][dst_ip] = []
                tr = OneWayTraceroute(src, dst_ip, file)
                tr.build_traceroute()
                # TODO: CHECK CORRECTNESS
                if tr.delay is None:
                    continue
                traceroutes[src][dst_ip].append(tr.to_dict())

        return traceroutes

    def plot(self, starting_date, ending_date, starting_time, ending_time, delta=timedelta(hours=1),
             description=None, ylim=None, **kwargs):
        self.check_dates_format(starting_date, ending_date)
        self.check_time_format(starting_time, ending_time)

        day, month, year = [int(x) for x in starting_date.split("/")]
        hour, minute, second = [int(x) for x in starting_time.split(":")]
        starting_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

        day, month, year = [int(x) for x in ending_date.split("/")]
        hour, minute, second = [int(x) for x in ending_time.split(":")]
        ending_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        print(starting_datetime, " -- ", ending_datetime, " -- TOTAL EXP: ", ending_datetime-starting_datetime)

        experiment_delta = ending_datetime - starting_datetime
        if experiment_delta.total_seconds() <= 300:
            raise ValueError("Please provide an experiment with more than 5 minutes data")

        r_experiment_delta = experiment_delta % delta
        print(r_experiment_delta)
        if bool(r_experiment_delta):
            raise ValueError("Your delta is not consistent with the starting and ending time,"
                             " r_experiment_delta={}".format(r_experiment_delta))

        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                self.traceroutes[src][dst] = \
                    list(filter(lambda x: starting_datetime <= self.datetime_convertion(x) <= ending_datetime,
                                self.traceroutes[src][dst]))

        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                max_datetime = self.datetime_convertion(
                    max(self.traceroutes[src][dst], key=lambda x: self.datetime_convertion(x))
                )
                min_datetime = self.datetime_convertion(
                    min(self.traceroutes[src][dst], key=lambda x: self.datetime_convertion(x))
                )
                if min_datetime != starting_datetime:
                    raise ValueError("Not enough data, datetime starts at {}, you asked for {}".format(
                        min_datetime, starting_datetime
                    ))
                if max_datetime != ending_datetime:
                    raise ValueError("Not enough data, datetime ends at {}, you asked for {}".format(
                        max_datetime, ending_datetime
                    ))

        abs_ylim_min_dl, abs_ylim_max_dl, abs_ylim_min_hop, abs_ylim_max_hop = 1000, 0, 1000, 0

        if ylim is None:
            for src in self.traceroutes.keys():
                for dst in self.traceroutes[src].keys():
                    ylim_min_dl = min(self.traceroutes[src][dst], key=lambda x: x["delay"])
                    ylim_min_dl = ylim_min_dl["delay"]
                    if abs_ylim_min_dl > ylim_min_dl:
                        abs_ylim_min_dl = ylim_min_dl

                    ylim_max_dl = max(self.traceroutes[src][dst], key=lambda x: x["delay"])
                    ylim_max_dl = ylim_max_dl["delay"]
                    if abs_ylim_max_dl < ylim_max_dl:
                        abs_ylim_max_dl = ylim_max_dl

                    ylim_min_hop = min(self.traceroutes[src][dst], key=lambda x: x["hops"])
                    ylim_min_hop = ylim_min_hop["hops"]
                    if abs_ylim_min_hop > ylim_min_hop:
                        abs_ylim_min_hop = ylim_min_hop

                    ylim_max_hop = max(self.traceroutes[src][dst], key=lambda x: x["hops"])
                    ylim_max_hop = ylim_max_hop["hops"]
                    if abs_ylim_max_hop < ylim_max_hop:
                        abs_ylim_max_hop = ylim_max_hop
        else:
            abs_ylim_min_dl, abs_ylim_max_hop = 0, int(ylim)

        self.filter_data(starting_datetime, ending_datetime, delta)
        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                print("* plotting {} -> {}".format(src, dst))
                self.plot_experiment_hops(src, dst, starting_datetime, ending_datetime, delta, description,
                                          (abs_ylim_min_hop, abs_ylim_max_hop), **kwargs)
                self.plot_experiment_delay(src, dst, starting_datetime, ending_datetime, delta, description,
                                           (abs_ylim_min_dl, abs_ylim_max_dl), **kwargs)

        self.create_confidence_interval_table(starting_datetime, ending_datetime, delta, measure="delay")
        self.create_confidence_interval_table(starting_datetime, ending_datetime, delta, measure="hops")
        self.create_interactive_map(measure="hops")
        self.create_interactive_map(measure="delay")

    def plot_experiment_hops(self, src, dst, starting_datetime, ending_datetime, delta, description, ylim, **kwargs):
        # if the time of the experiment is less than one day, print only the hours
        import matplotlib.pyplot as plt
        number_of_box = int((ending_datetime-starting_datetime) / delta)

        # Fixing random state for reproducibility
        experiment_metadata = self.read_experiment_json(self.path)
        for instance_desc in experiment_metadata["instances"]:
            desc = list(instance_desc.values())[0]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == src or ip_priv == src:
                src_az = desc["availability_zone"]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == dst or ip_priv == dst:
                dst_az = desc["availability_zone"]

        data = self.filtered_data[src][dst]
        data_hop = [[x["hops"] for x in d] for d in data]
        # print([len(x) for x in data])
        # print(data_delay, data_hop)
        fig, ax = plt.subplots()
        ax.boxplot(data_hop)
        ax.tick_params(axis='x', labelrotation=90)
        plt.xticks(list(range(1, number_of_box + 1)),
                   [str(starting_datetime + (delta * i)) for i in range(0, number_of_box)])
        plt.title("HOPS {} -> {}".format(src_az, dst_az))
        plt.ylim(ylim[0] - 1, ylim[1] + 1)
        plt.tight_layout()
        plt.savefig(self.path / "HOPS_{}->{}.pdf".format(src_az, dst_az), bbox_inches="tight")

    def plot_experiment_delay(self, src, dst, starting_datetime, ending_datetime, delta, description, ylim, **kwargs):
        # if the time of the experiment is less than one day, print only the hours
        import matplotlib.pyplot as plt
        number_of_box = int((ending_datetime-starting_datetime) / delta)

        # Fixing random state for reproducibility
        experiment_metadata = self.read_experiment_json(self.path)
        for instance_desc in experiment_metadata["instances"]:
            desc = list(instance_desc.values())[0]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == src or ip_priv == src:
                src_az = desc["availability_zone"]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == dst or ip_priv == dst:
                dst_az = desc["availability_zone"]

        data = self.filtered_data[src][dst]

        data_delay = [[x["delay"] for x in d] for d in data]
        # print([len(x) for x in data])
        # print(data_delay, data_delay)
        fig, ax = plt.subplots()
        ax.boxplot(data_delay)
        ax.tick_params(axis='x', labelrotation=90)
        plt.xticks(list(range(1, number_of_box + 1)),
                   [str(starting_datetime + (delta * i)) for i in range(0, number_of_box)])
        plt.title("DELAY {} -> {}".format(src_az, dst_az))
        plt.ylim(ylim[0], ylim[1])
        plt.tight_layout()
        plt.savefig(self.path / "DELAY_{}-{}.pdf".format(src_az, dst_az), bbox_inches="tight")

    def create_confidence_interval_table(self, starting_datetime, ending_datetime, delta, measure="delay"):
        import matplotlib.pyplot as plt

        confidence_interval = dict()
        for src in self.filtered_data.keys():
            for dst in self.filtered_data[src].keys():
                data = self.filtered_data[src][dst]
                for interval in data:
                    # confidence interval formula
                    delays = [x[measure] for x in interval]
                    ci = (mean(delays), stdev(delays))
                    s, d = self.get_az(src, dst)
                    if s not in confidence_interval.keys():
                        confidence_interval[s] = dict()
                    if d not in confidence_interval[s].keys():
                        confidence_interval[s][d] = []

                    confidence_interval[s][d].append(ci)

        fig, ax = plt.subplots()

        # hide axes
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        row = [str(starting_datetime + (delta*x)) for x in range(int((ending_datetime-starting_datetime)/delta))]
        columns_unsorted = [(s, d) for s in confidence_interval.keys() for d in confidence_interval[s].keys()]
        columns = []
        for s, d in columns_unsorted:
            if (s, d) not in columns:
                columns.append((s, d))
                columns.append((d, s))

        values = [[(round(confidence_interval[s][d][i][0], 2), "+-", round(confidence_interval[s][d][i][1], 2))
                   for s, d in columns] for i in range(len(row))]

        ax.table(rowLabels=row, cellText=values, colLabels=columns, loc='center')
        fig.tight_layout()
        plt.text(10, 80, ax.table, size=50)
        plt.savefig(self.path / "{}_standard_deviation.pdf".format(measure))
        return values

    def create_interactive_map(self, measure="delay"):
        colors = ["red", "blue", "black", "orange", "yellow", "green"]
        confidence_interval = dict()
        for src in self.filtered_data.keys():
            for dst in self.filtered_data[src].keys():
                data = self.filtered_data[src][dst]
                united_measure = [x[measure] for li in data for x in li]
                ci = (mean(united_measure), stdev(united_measure))
                s, d = self.get_az(src, dst)
                if s not in confidence_interval.keys():
                    confidence_interval[s] = dict()
                if d not in confidence_interval[s].keys():
                    confidence_interval[s][d] = None

                confidence_interval[s][d] = ci

        fig = go.Figure()
        src_dst_list = [(s, d) for s in confidence_interval.keys() for d in confidence_interval[s].keys()]

        first_group = []
        second_group = []
        for s, d in src_dst_list:
            if (s, d) not in first_group and (s, d) not in second_group:
                first_group.append((s, d))
                second_group.append((d, s))

        for e, (s, d) in enumerate(first_group):
            slat, slon = self.get_az_coord(s)
            dlat, dlon = self.get_az_coord(d)
            fig.add_trace(go.Scattergeo(
                lat=[slat, dlat],
                lon=[slon, dlon],
                mode='lines+markers',
                line=dict(width=2, color=colors[e % len(colors)]),
                name="{}->{} {}".format(s, d, confidence_interval[s][d])

            ))

            fig.update_layout(title_text='MAP',
                              height=700, width=900,
                              margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
                              showlegend=True, geo_scope="world")

        pickle.dump(fig, open(str(self.path / "{}1.pickle".format(measure)), "wb"))
        fig.write_image(str(self.path / "{}1.pdf".format(measure)))

        fig = go.Figure()
        for e, (s, d) in enumerate(second_group):
            slat, slon = self.get_az_coord(s)
            dlat, dlon = self.get_az_coord(d)
            fig.add_trace(go.Scattergeo(
                lat=[slat, dlat],
                lon=[slon, dlon],
                mode='lines+markers',
                line=dict(width=2, color=colors[e % len(colors)]),
                name="{}->{} {}".format(s, d, confidence_interval[s][d])

            ))

            fig.update_layout(title_text='MAP',
                              height=700, width=900,
                              margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
                              showlegend=True, geo_scope="world")

        pickle.dump(fig, open(str(self.path / "{}2.pickle".format(measure)), "wb"))
        fig.write_image(str(self.path / "{}2.pdf".format(measure)))

        fig = go.Figure()
        for e, (s, d) in enumerate(src_dst_list):
            slat, slon = self.get_az_coord(s)
            dlat, dlon = self.get_az_coord(d)
            fig.add_trace(go.Scattergeo(
                lat=[slat, dlat],
                lon=[slon, dlon],
                mode='lines+markers',
                line=dict(width=2, color=colors[e % len(colors)]),
                name="{}->{} {}".format(s, d, confidence_interval[s][d])

            ))

            fig.update_layout(title_text='MAP',
                              height=700, width=900,
                              margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
                              showlegend=True, geo_scope="world")

        pickle.dump(fig, open(str(self.path / "{}_total.pickle".format(measure)), "wb"))
        fig.write_image(str(self.path / "{}_total.pdf".format(measure)))

    @staticmethod
    def show_interactive(file):
        import dash
        import dash_core_components as dcc
        import dash_html_components as html

        fig = pickle.load(open(file, "rb"))

        app = dash.Dash()
        app.layout = html.Div([
            dcc.Graph(figure=fig)
        ])

        app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter

    def get_az_coord(self, az):
        return self.coord[az]

    def filter_data(self, starting_datetime, ending_datetime, delta):
        # if the time of the experiment is less than one day, print only the hours
        self.filtered_data = {x: dict() for x in self.traceroutes.keys()}

        for src in self.traceroutes.keys():
            for dst in self.traceroutes[src].keys():
                traces = self.traceroutes[src][dst]
                number_of_box = int((ending_datetime-starting_datetime) / delta)
                # Fixing random state for reproducibility
                data = [
                    list(
                        filter(
                            lambda x:
                            starting_datetime + (delta * i) <= self.datetime_convertion(x)
                            < starting_datetime + (delta * (i + 1)), traces
                        )
                    )
                    for i in range(0, number_of_box)
                ]
                self.filtered_data[src][dst] = data
        return self.filtered_data

    def get_az(self, src, dst):
        experiment_metadata = self.read_experiment_json(self.path)
        for instance_desc in experiment_metadata["instances"]:
            desc = list(instance_desc.values())[0]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == src or ip_priv == src:
                src_az = desc["availability_zone"]
            ip_pub, ip_priv = desc["public_ip"], desc["private_ip"]
            if ip_pub == dst or ip_priv == dst:
                dst_az = desc["availability_zone"]

        return src_az, dst_az

    @staticmethod
    def datetime_convertion(trace):
        trace_date = trace["date"]
        trace_time = trace["time"]
        trace_datetime = datetime(year=int(trace_date["year"]), month=int(trace_date["month"]),
                                  day=int(trace_date["day"]), hour=int(trace_time["hour"]),
                                  minute=int(trace_time["minute"]), second=int(trace_time["second"]))

        return trace_datetime

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

    @staticmethod
    def read_experiment_json(path):
        if type(path) is str:
            path = Path(path)
        json_path = path / "experiment.json"
        if not json_path.exists():
            ValueError("experiments.json do not exists here")
        with open(Path(json_path), "r") as json_file:
            dictionary = eval(str(load(json_file)))
        return dictionary


if __name__ == '__main__':
    p = Plotter(path="/Users/giuseppedilena/Desktop/BE49F7F3/")
    p.build_traceroutes()
    # print(p.traceroutes)
    p.plot("13/10/2020", "14/10/2020", "8:30:00", "8:30:00", delta=timedelta(hours=1))
    p.show_interactive("delay_total.pickle")
