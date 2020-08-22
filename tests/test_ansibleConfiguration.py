import unittest
from CloudMeasurement.experiments.ansibleConfiguration import InventoryConfiguration, Path

class MyTestCase(unittest.TestCase):

    def test_add_host_1(self):
        ic = InventoryConfiguration(inventory_path=Path("/tmp/test.cfg"))
        ic.add_host(host_id="host_id1", region="region-1", public_ip="0.0.0.0", user="user_1", password="password")
        self.assertEqual(len(ic.items), 1)

    def test_add_host_2(self):
        ic = InventoryConfiguration(inventory_path=Path("/tmp/test.cfg"))
        ic.add_host(host_id="host_id1", region="region-1", public_ip="0.0.0.0", user="user_1", password="password")
        ic.add_host(host_id="host_id2", region="region-2", public_ip="0.0.0.1")
        self.assertEqual(len(ic.items), 2)

    def test_add_host_3(self):
        ic = InventoryConfiguration(inventory_path=Path("/tmp/test.cfg"))
        ic.add_host(host_id="host_id1", region="region-1", public_ip="0.0.0.0", user="user_1", password="password")
        ic.add_host(host_id="host_id2", region="region-1", public_ip="0.0.0.1")
        self.assertEqual(len(ic.items), 1)

    def test_add_host_4(self):
        ic = InventoryConfiguration(inventory_path=Path("/tmp/test.cfg"))
        ic.add_host(host_id="host_id1", region="region-1", public_ip="0.0.0.0", user="user_1", password="password")
        ic.add_host(host_id="host_id2", region="region-1", public_ip="0.0.0.1")
        ic.add_host(host_id="host_id3", region="region-2", public_ip="0.0.0.2")
        self.assertEqual(len(ic.items), 2)

    def test_make_inventory_1(self):
        test_path = Path("/tmp/test.cfg")
        ic = InventoryConfiguration(inventory_path=test_path)
        ic.items = {"region-1": [("id_1", "ip_1", "user_1", "password_1"),
                                 ("id_2", "ip_2", "user_1", "password_1"),
                                 ("id_3", "ip_3", "user_2", None)]}
        ic.make_inventory()
        with open(test_path) as f:
            lines = f.readlines()
        text = ""
        for line in lines:
            text += str(line)
        expected_text = '\n[region_1]\n' \
                        'ip_1 ansible_user=user_1 ansible_password=password_1 # host_id=id_1\n' \
                        'ip_2 ansible_user=user_1 ansible_password=password_1 # host_id=id_2\n' \
                        'ip_3 ansible_user=user_2 # host_id=id_3\n'
        self.assertEqual(text, expected_text)

    def test_make_inventory_2(self):
        test_path = Path("/tmp/test.cfg")
        ic = InventoryConfiguration(inventory_path=test_path)
        ic.items = {"region-1": [("id_1", "ip_1", "user_1", "password_1"),
                                 ("id_2", "ip_2", "user_1", "password_1")],
                    "region-2": [("id_3", "ip_3", "user_3", "password_2")]
                    }
        ic.make_inventory()
        with open(test_path) as f:
            lines = f.readlines()
        text = ""
        for line in lines:
            text += str(line)
        expected_text = '\n[region_1]\n' \
                        'ip_1 ansible_user=user_1 ansible_password=password_1 # host_id=id_1\n' \
                        'ip_2 ansible_user=user_1 ansible_password=password_1 # host_id=id_2\n' \
                        '\n[region_2]\n' \
                        'ip_3 ansible_user=user_3 ansible_password=password_2 # host_id=id_3\n'
        self.assertEqual(text, expected_text)


if __name__ == '__main__':
    unittest.main()
