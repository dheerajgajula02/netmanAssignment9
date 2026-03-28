from __future__ import print_function
import unittest
try:
    from ncclient import manager
    from ncclient.xml_ import to_ele
    from netaddr import IPAddress
    import ipaddress
    import pandas as pd
    import paramiko
except Exception:
    print('Install all the necessary modules')


# Read router connection details from info.csv (same as main code)
_READ_FILE = pd.read_csv('info.csv')
ROUTER_CREDENTIALS = {
    row['Router']: {
        'host': row['Mgmt IP'],
        'username': row['Username'],
        'password': row['Password']
    }
    for _, row in _READ_FILE.iterrows()
}

FETCH_INFO = '''
<filter>
<config-format-text-block>
<text-filter-spec> %s </text-filter-spec>
</config-format-text-block>
</filter>
'''


def get_connection(router_name):
    """Establish NETCONF connection to a router."""
    creds = ROUTER_CREDENTIALS[router_name]
    return manager.connect(
        host=creds['host'],
        port=22,
        username=creds['username'],
        password=creds['password'],
        hostkey_verify=False,
        device_params={'name': 'iosxr'},
        allow_agent=False,
        look_for_keys=True
    )


class TestNetworkConfig(unittest.TestCase):
    """Unit tests to verify network configuration via NETCONF."""

    def test_r3_loopback99_ip(self):
        """Test 1: Verify that Loopback 99 on Router 3 has IP 10.1.3.1/24."""
        conn = get_connection('R3')
        fetch_lo_info = FETCH_INFO % ('int Loopback99')
        output = conn.get_config('running', fetch_lo_info)
        split_output = str(output).split()
        lo_ip = split_output[9]
        lo_mask = str(IPAddress(split_output[10]).netmask_bits())
        lo_ip_with_prefix = lo_ip + '/' + lo_mask
        conn.close_session()
        self.assertEqual(lo_ip_with_prefix, '10.1.3.1/24',
                         f'Expected 10.1.3.1/24 but got {lo_ip_with_prefix}')

    def test_r1_single_ospf_area(self):
        """Test 2: Verify that R1 is configured for only a single OSPF area."""
        conn = get_connection('R1')
        fetch_ospf_info = FETCH_INFO % ('| s ospf')
        output = conn.get_config('running', fetch_ospf_info)
        ospf_config = str(output)
        # Count occurrences of 'area' keyword in OSPF config
        area_values = set()
        split_output = ospf_config.split()
        for idx, word in enumerate(split_output):
            if word == 'area':
                area_values.add(split_output[idx + 1])
        conn.close_session()
        self.assertEqual(len(area_values), 1,
                         f'Expected 1 OSPF area but found {len(area_values)}: {area_values}')

    def test_ping_r2_loopback_to_r5_loopback(self):
        """Test 3: Verify ping from R2 loopback to R5 loopback is successful."""
        # R2 loopback: 10.1.2.1, R5 loopback: 10.1.5.1
        # Use paramiko SSH CLI to run ping since IOS-XR NETCONF exec RPC
        # does not return a proper message-id in its reply
        creds = ROUTER_CREDENTIALS['R2']
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(creds['host'], port=22,
                    username=creds['username'], password=creds['password'])
        shell = ssh.invoke_shell()
        shell.send('ping 10.1.5.1 source 10.1.2.1 repeat 4\n')
        import time
        time.sleep(5)
        result = shell.recv(4096).decode('utf-8', errors='ignore')
        ssh.close()
        self.assertIn('!!!!', result,
                      f'Ping from R2 loopback to R5 loopback failed. Output: {result}')


if __name__ == '__main__':
    unittest.main()
