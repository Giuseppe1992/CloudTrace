from pathlib import Path, PosixPath
import ansible_runner


class InventoryConfiguration(object):
    def __init__(self, inventory_path):
        if not (type(inventory_path) is Path or type(inventory_path) is PosixPath):
            raise TypeError("inventory_path should be Path or PosixPath type, got: {}".format(type(inventory_path)))

        with open(inventory_path, "w") as inventory:
            inventory.write("# ANSIBLE YML FILE FOR CLOUD MEASUREMENT EXPERIMENT \n")

        self.path = inventory_path
        self.items = dict()

    def add_host(self, host_id, region, public_ip, user="ubuntu", password=None):
        if region not in self.items.keys():
            self.items[region] = [(host_id, public_ip, user, password)]
        else:
            self.items[region].append((host_id, public_ip, user, password))

    def make_inventory(self):
        if self.items is dict():
            raise ValueError("the inventory is empty")

        with open(self.path, "w") as inventory:
            for region in self.items.keys():
                inventory.write("\n[{}]\n".format(region.replace("-", "_")))
                for item in self.items[region]:
                    host_id, public_ip, user, password = item
                    comment = "# host_id={}".format(host_id)
                    ansible_user = "ansible_user={}".format(user)
                    if password is None:
                        inventory.write("{} {} {}\n".format(public_ip, ansible_user, comment))
                    else:
                        ansible_password = "ansible_password={}".format(password)
                        inventory.write("{} {} {} {}\n".format(public_ip, ansible_user, ansible_password, comment))

    @staticmethod
    def run_inventory(inventory_path, host_pattern, module, module_args, forks=10, cmdline="--become"):
        r = ansible_runner.run(host_pattern=host_pattern, module=module, module_args=module_args,
                               inventory=inventory_path, forks=forks, cmdline=cmdline)
        return r.stats


if __name__ == '__main__':
    a = InventoryConfiguration(Path("/Users/giuseppe/desktop/test.yml"))
    a.add_host("aaaa", "rrrr", "ip", "ubuntu", "pass")
    a.add_host("bbbb", "rrrr", "ip1", "ubuntu", "pass")
    a.add_host("cccc", "rrrr", "ip2", "ubuntu1", "pass1")
    a.add_host("dddd", "r2", "ip3", "ubuntu1", "pass1")
    a.make_inventory()
