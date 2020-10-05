from CloudMeasurement.cmplotter.extract_data import OneWayTraceroute
from datetime import date, time, datetime, timedelta
from re import match
import ipaddress

def intervall_conversion(intervall):
    m = match(r"(([0-9]+\.([0-9]{1,3}))ms)|[0-9]+ms", intervall)
    if m:
        start, end = m.span()
        # remove ms
        float_intervall = float(intervall[start:end - 2])
        return timedelta(milliseconds=float_intervall)
    if intervall == "*":
        return None
    raise ValueError(intervall)


def experiment_time(time_):
    if type(time_) is not time:
        raise TypeError
    hour = time_.hour
    minute = time_.minute
    exp_minute = (minute // 10) * 10
    return time(hour=hour, minute=exp_minute, second=0)


def number_of_hops(traceroute_list):
    return len(traceroute_list)


def check_if_ip_is_in_network(ip, network):
    lowest = network.network_address
    biggest = network.broadcast_address
    return lowest <= ip <= biggest


def convert_traceroute(traceroute):
    port = traceroute["port"]
    trace = traceroute["traceroute"]
    new_trace = []
    try:
        for tr_ in trace:
            n, ip_, t1, t2, t3 = tr_
            if ip_ == "*":
                raise ValueError
            new_t1 = intervall_conversion(t1)
            new_t2 = intervall_conversion(t2)
            new_t3 = intervall_conversion(t3)
            new_ip = ipaddress.IPv4Address(ip_)
            new_trace.append((int(n), new_ip, new_t1, new_t2, new_t3))
    except ValueError:
        return None

    exp_time = experiment_time(time_)
    experiment_datetime = datetime(year=date_.year, month=date_.month, day=date_.day,
                                   hour=exp_time.hour, minute=exp_time.minute, second=exp_time.second)

    return {"datetime": experiment_datetime, "port": port, "traceroute": new_trace}



if __name__ == '__main__':
    starting_date_time_experiment = datetime(year=2019, month=7, day=19, hour=9, minute=0, second=0)
    ending_date_time_experiment = datetime(year=2019, month=7, day=26, hour=8, minute=50, second=0)
    timeout_experiment = timedelta(minutes=1)


    traceroutes = []

    # Filter the valid traceroute
    traceroutes = filter(
        lambda x: x and starting_date_time_experiment <= x["datetime"] <= ending_date_time_experiment,
        traceroutes
    )

    for i in traceroutes:
        print(i["datetime"], i["port"], i["traceroute"])