import unittest
import os

from check_util import CheckUtil
from Common import CommonVariables
from io import StringIO
from .console_logger import ConsoleLogger
from .test_utils import MockDistroPatcher
try:
    builtins_open = "builtins.open"
    import unittest.mock as mock # python3+
except ImportError:
    builtins_open = "__builtin__.open"
    import mock # python2

class TestCheckUtil(unittest.TestCase):
    """ unit tests for functions in the check_util module """

    def setUp(self):
        self.logger = ConsoleLogger()
        self.cutil = CheckUtil(self.logger)

    def get_mock_filestream(self, somestring):
        stream = StringIO()
        stream.write(somestring)
        stream.seek(0)
        return stream

    @mock.patch('os.path.isfile', return_value=False)
    @mock.patch('os.path.isdir', return_value=False)
    def test_appcompat(self, os_path_isdir, os_path_isfile):
        self.assertFalse(self.cutil.is_app_compat_issue_detected())

    @mock.patch('os.popen')
    def test_memory(self, os_popen):
        output = u'8000000'
        os_popen.return_value = self.get_mock_filestream(output)
        self.assertFalse(self.cutil.is_insufficient_memory())

    @mock.patch('os.popen')
    def test_memory_low_memory(self, os_popen):
        output = u'6000000'
        os_popen.return_value = self.get_mock_filestream(output)
        self.assertTrue(self.cutil.is_insufficient_memory())

    def test_is_kv_id(self):
        # https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules
        self.cutil.check_kv_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/adenszqtrrg/providers/Microsoft.KeyVault/vaults/adenszqtrkv", "")
        self.cutil.check_kv_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/adenszqtrrg/providers/microsoft.keyvault/vaults/adenszqtrkv", "")

        # invalid cases
        self.assertRaises(Exception, self.cutil.check_kv_id, "////", "")
        self.assertRaises(Exception, self.cutil.check_kv_id, "/subscriptions/{subid}/resourceGroups/{rgname}/providers/Microsoft.KeyVault/", "")
        self.assertRaises(Exception, self.cutil.check_kv_id, "/subscriptions/{subid}/resourceGroups/{rgname}/providers/Microsoft.KeyVault////////", "")
        self.assertRaises(Exception, self.cutil.check_kv_id, "/subscriptions/{subid}/resourceGroupssss/{rgname}/providers/Microsoft.KeyVault/vaults/{vaultname}", "")
        self.assertRaises(Exception, self.cutil.check_kv_id, "/subscriptions/{subid}/resourceGroups/{rgname}/providers/Microsoft.KeyVault/vaults/{vaultname}", "")

    def test_is_kv_url(self):
        dns_suffix_list = ["vault.azure.net", "vault.azure.cn", "vault.usgovcloudapi.net", "vault.microsoftazure.de"]

        for dns_suffix in dns_suffix_list:
            self.cutil.check_kv_url("https://testkv." + dns_suffix + "/", "")
            self.cutil.check_kv_url("https://test-kv2." + dns_suffix + "/", "")
            self.cutil.check_kv_url("https://test-kv2." + dns_suffix + ":443/", "")
            self.cutil.check_kek_url("https://test-kv2." + dns_suffix + ":443/keys/kekname/00000000000000000000000000000000", "")
            self.assertRaises(Exception, self.cutil.check_kv_url, "http://testkv." + dns_suffix + "/", "")
            # self.assertRaises(Exception, self.cutil.check_kv_url, "https://https://testkv." + dns_suffix + "/", "")
            # self.assertRaises(Exception, self.cutil.check_kv_url, "https://testkv.testkv." + dns_suffix + "/", "")
        # self.assertRaises(Exception, self.cutil.check_kv_url, "https://testkv.vault.azure.com/", "")
        self.assertRaises(Exception, self.cutil.check_kv_url, "https://", "")

    @mock.patch('MetadataUtil.MetadataUtil.is_vmss')
    def test_validate_volume_type_single_vm(self, mock_is_vmss):
        # First test for normal VMs
        mock_is_vmss.return_value = False
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "DATA"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "ALL"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "all"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "Os"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "OS"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "os"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "Data"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "data"})
        for vt in CommonVariables.SupportedVolumeTypes:
            self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: vt})

        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "NON-OS"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: ""})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "123"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {})

    @mock.patch('MetadataUtil.MetadataUtil.is_vmss')
    def test_validate_volume_type_vmss(self, mock_is_vmss):
        # Then test for VMSS
        mock_is_vmss.return_value = True
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "DATA"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "Data"})
        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "data"})
        for vt in CommonVariables.SupportedVolumeTypesVMSS:
            self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: vt})

        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "ALL"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "all"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "Os"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "OS"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "os"})
        self.assertRaises(Exception, self.cutil.validate_volume_type, {})

        distro_patcher_sup = MockDistroPatcher('redhat', '8.5', '4.4')
        distro_patcher_sup.support_online_encryption = True
        distro_patcher_not_sup = MockDistroPatcher('redhat', '7.9', '4.4')

        self.cutil.validate_volume_type({CommonVariables.VolumeTypeKey: "All"}, distro_patcher_sup)
        self.assertRaises(Exception, self.cutil.validate_volume_type, {CommonVariables.VolumeTypeKey: "OS"}, distro_patcher_not_sup)

    @mock.patch('check_util.CheckUtil.validate_memory_os_encryption')
    @mock.patch('CommandExecutor.CommandExecutor.Execute', return_value=0)
    @mock.patch('MetadataUtil.MetadataUtil.is_vmss')
    def test_fatal_checks(self, mock_is_vmss, mock_exec, mock_validate_memory):
        mock_is_vmss.return_value = False
        mock_distro_patcher = MockDistroPatcher('Ubuntu', '14.04', '4.15')
        self.cutil.precheck_for_fatal_failures({
            CommonVariables.VolumeTypeKey: "DATA",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.DisableEncryption
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)
        self.cutil.precheck_for_fatal_failures({
            CommonVariables.VolumeTypeKey: "ALL",
            CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
            CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)
        self.cutil.precheck_for_fatal_failures({
            CommonVariables.VolumeTypeKey: "ALL",
            CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
            CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
            CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormat
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)
        self.cutil.precheck_for_fatal_failures({
            CommonVariables.VolumeTypeKey: "ALL",
            CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
            CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
            CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-256',
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)
        self.assertRaises(Exception, self.cutil.precheck_for_fatal_failures, {})
        self.assertRaises(Exception, self.cutil.precheck_for_fatal_failures, {CommonVariables.VolumeTypeKey: "123"}, mock_distro_patcher, {"os": "NotEncrypted"})
        self.assertRaises(Exception, self.cutil.precheck_for_fatal_failures, {
            CommonVariables.VolumeTypeKey: "ALL",
            CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
            CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
            CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-25600',
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)
        mock_distro_patcher = MockDistroPatcher('Ubuntu', '14.04', '4.4')
        self.assertRaises(Exception, self.cutil.precheck_for_fatal_failures, {
            CommonVariables.VolumeTypeKey: "ALL"
            }, { "os": "NotEncrypted" }, mock_distro_patcher, None)

    def test_mount_scheme(self):
        proc_mounts_output = """sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
udev /dev devtmpfs rw,relatime,size=4070564k,nr_inodes=1017641,mode=755 0 0
devpts /dev/pts devpts rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000 0 0
tmpfs /run tmpfs rw,nosuid,noexec,relatime,size=815720k,mode=755 0 0
/dev/sda1 / ext4 rw,relatime,discard,data=ordered 0 0
none /sys/fs/cgroup tmpfs rw,relatime,size=4k,mode=755 0 0
none /sys/fs/fuse/connections fusectl rw,relatime 0 0
none /sys/kernel/debug debugfs rw,relatime 0 0
none /sys/kernel/security securityfs rw,relatime 0 0
none /run/lock tmpfs rw,nosuid,nodev,noexec,relatime,size=5120k 0 0
none /run/shm tmpfs rw,nosuid,nodev,relatime 0 0
none /run/user tmpfs rw,nosuid,nodev,noexec,relatime,size=102400k,mode=755 0 0
none /sys/fs/pstore pstore rw,relatime 0 0
systemd /sys/fs/cgroup/systemd cgroup rw,nosuid,nodev,noexec,relatime,name=systemd 0 0
/dev/mapper/fee16d98-9c18-4e7d-af70-afd7f3dfb2d9 /mnt/resource ext4 rw,relatime,data=ordered 0 0
/dev/mapper/vg0-lv0 /data ext4 rw,relatime,discard,data=ordered 0 0"""
        with mock.patch(builtins_open, mock.mock_open(read_data=proc_mounts_output)) as mock_open:
            self.assertFalse(self.cutil.is_unsupported_mount_scheme())
            self.assertEqual(mock_open.call_count,1)

    # Skip LVM OS validation when OS volume is not being targeted
    def test_skip_lvm_os_check_if_data_only_enable(self):
        # skip lvm detection if data only 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "DATA", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_os_check_if_data_only_ef(self):
        # skip lvm detection if data only 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "DATA", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormat}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_os_check_if_data_only_efa(self):
        # skip lvm detection if data only 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "DATA", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_os_check_if_data_only_disable(self):
        # skip lvm detection if data only 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "DATA", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.DisableEncryption}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_os_check_if_query(self):
        # skip lvm detection if query status operation is invoked without volume type
        self.cutil.validate_lvm_os({CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.QueryEncryptionStatus}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_no_encryption_operation(self):
        # skip lvm detection if no encryption operation 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "ALL"}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    def test_skip_lvm_no_volume_type(self):
        # skip lvm detection if no volume type specified
        self.cutil.validate_lvm_os({CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", return_value=-1)
    def test_no_lvm_no_config(self, os_system):
        # simulate no LVM OS, no config 
        self.cutil.validate_lvm_os({}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", return_value=0)
    def test_lvm_no_config(self, os_system):
        # simulate valid LVM OS, no config
        self.cutil.validate_lvm_os({}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", side_effect=[0, -1])
    def test_invalid_lvm_no_config(self, os_system):
        # simulate invalid LVM naming scheme, but no config setting to encrypt OS
        self.cutil.validate_lvm_os({}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", return_value=-1)
    def test_lvm_os_lvm_absent(self, os_system):
        # using patched return value of -1, simulate no LVM OS 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "ALL", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", return_value=0)
    def test_lvm_os_valid(self, os_system):
        # simulate a valid LVM OS and a valid naming scheme by always returning 0
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "ALL", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", side_effect=[0, -1])
    def test_lvm_os_lv_missing_expected_name(self, os_system):
        # using patched side effects, first simulate LVM OS present, then simulate not finding the expected LV name 
        self.assertRaises(Exception, self.cutil.validate_lvm_os, {CommonVariables.VolumeTypeKey: "ALL", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption}, MockDistroPatcher('Ubuntu', '14.04', '4.4'))

    @mock.patch("os.system", side_effect=[0, -1])
    def test_lvm_os_lv_online_encryption(self, os_system):
        mock_patcher = MockDistroPatcher('Redhat', '8.2', '4.4')
        mock_patcher.support_online_encryption = True
        # using patched side effects, first simulate LVM OS present, then simulate not finding the expected LV name. Test should pass as online encryption does not restrict LVM layout. 
        self.cutil.validate_lvm_os({CommonVariables.VolumeTypeKey: "ALL", CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption}, mock_patcher)
    
    @mock.patch("CommandExecutor.CommandExecutor.Execute", return_value=0)
    def test_vfat(self, mocked_exec):
        # simulate call to modprobe vfat that succeeds and returns cleanly from execute 
        self.cutil.validate_vfat()

    @mock.patch("CommandExecutor.CommandExecutor.Execute", side_effect=Exception())
    def test_no_vfat(self, mocked_exec):
        # simulate call to modprobe vfat that fails and raises exception from execute 
        self.assertRaises(Exception, self.cutil.validate_vfat) 
      
    @mock.patch('os.popen')
    def test_minimum_memory(self, os_popen):
        output = u'6000000'
        os_popen.return_value = self.get_mock_filestream(output)
        self.assertRaises(Exception, self.cutil.validate_memory_os_encryption, {
            CommonVariables.VolumeTypeKey: "ALL",
            CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
            CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
            CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
            CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-25600',
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
            }, { "os": "NotEncrypted" })

        self.cutil.validate_memory_os_encryption( {
        CommonVariables.VolumeTypeKey: "ALL",
        CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
        CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
        CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-25600',
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
        }, { "os": "Encrypted" })

        output = u'8000000'
        os_popen.return_value = self.get_mock_filestream(output)
        self.cutil.validate_memory_os_encryption( {
        CommonVariables.VolumeTypeKey: "ALL",
        CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
        CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
        CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-25600',
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
        }, { "os": "Encrypted" })

        output = u'8000000'
        os_popen.return_value = self.get_mock_filestream(output)
        self.cutil.validate_memory_os_encryption( {
        CommonVariables.VolumeTypeKey: "ALL",
        CommonVariables.KeyVaultURLKey: "https://vaultname.vault.azure.net/",
        CommonVariables.KeyVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionKeyURLKey: "https://vaultname.vault.azure.net/keys/keyname/ver",
        CommonVariables.KekVaultResourceIdKey: "/subscriptions/subid/resourceGroups/rgname/providers/Microsoft.KeyVault/vaults/vaultname",
        CommonVariables.KeyEncryptionAlgorithmKey: 'rsa-OAEP-25600',
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
        }, { "os": "NotEncrypted" })

    def test_supported_os(self):
        # test exception is raised for Ubuntu 14.04 kernel version
        self.assertRaises(Exception, self.cutil.is_supported_os, {
            CommonVariables.VolumeTypeKey: "ALL"
            }, MockDistroPatcher('Ubuntu', '14.04', '4.4'), {"os" : "NotEncrypted"})
        # test exception is not raised for Ubuntu 14.04 kernel version 4.15
        self.cutil.is_supported_os({
            CommonVariables.VolumeTypeKey: "ALL"
            }, MockDistroPatcher('Ubuntu', '14.04', '4.15'), {"os" : "NotEncrypted"})
        # test exception is not raised for already encrypted OS volume
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                   MockDistroPatcher('Ubuntu', '14.04', '4.4'), {"os" : "Encrypted"})
        # test exception is raised for unsupported OS
        self.assertRaises(Exception, self.cutil.is_supported_os, {CommonVariables.VolumeTypeKey: "ALL"},
                          MockDistroPatcher('Ubuntu', '12.04', ''), {"os" : "NotEncrypted"})
        self.assertRaises(Exception, self.cutil.is_supported_os, {CommonVariables.VolumeTypeKey: "ALL"},
                          MockDistroPatcher('redhat', '6.7', ''), {"os" : "NotEncrypted"})
        # test exception is not raised for supported OS
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                   MockDistroPatcher('Ubuntu', '18.04', ''), {"os" : "NotEncrypted"})
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                   MockDistroPatcher('centos', '7.2.1511', ''), {"os" : "NotEncrypted"})
        # test exception is not raised for DATA volume
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "DATA"},
                                   MockDistroPatcher('SuSE', '12.4', ''), {"os" : "NotEncrypted"})

    def test_supported_os_online_encryption(self):
        # test exception is not raised for redhat 8.5
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                    MockDistroPatcher('redhat', '8.5', '4.4'), {"os" : "NotEncrypted"})
        # test exception is not raised for redhat 8.15
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                    MockDistroPatcher('redhat', '8.15', '4.4'), {"os" : "NotEncrypted"})
        # test exception is raised for redhat 8.0
        self.assertRaises(Exception, self.cutil.is_supported_os, {
            CommonVariables.VolumeTypeKey: "ALL"
            }, MockDistroPatcher('redhat', '8.0', '4.4'), {"os" : "NotEncrypted"})
        # test exception is raised for redhat 9.0
        self.assertRaises(Exception, self.cutil.is_supported_os, {
            CommonVariables.VolumeTypeKey: "ALL"
            }, MockDistroPatcher('redhat', '9.0', '4.4'), {"os" : "NotEncrypted"})
        # test exception is not raised for oracle 8.5
        self.cutil.is_supported_os({CommonVariables.VolumeTypeKey: "ALL"},
                                    MockDistroPatcher('oracle', '8.5', '4.4'), {"os" : "NotEncrypted"})
        # test exception is raised for oracle 8.4
        self.assertRaises(Exception, self.cutil.is_supported_os, {
            CommonVariables.VolumeTypeKey: "ALL"
            }, MockDistroPatcher('oracle', '8.4', '4.4'), {"os" : "NotEncrypted"})

    def test_volume_type_enable_common(self):
        self.cutil.validate_volume_type_for_enable({
                CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.QueryEncryptionStatus
            }, "data")

        self.cutil.validate_volume_type_for_enable({
                CommonVariables.VolumeTypeKey: "All",
                CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
            }, None)

    def test_volume_type_enable_from_data(self):
        self.assertRaises(Exception, self.cutil.validate_volume_type_for_enable, {
            CommonVariables.VolumeTypeKey: "Os",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormat
            }, "Data")
        
        self.cutil.validate_volume_type_for_enable({
        CommonVariables.VolumeTypeKey: "All",
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
        }, "Data")

        self.cutil.validate_volume_type_for_enable({
        CommonVariables.VolumeTypeKey: "Data",
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
        }, "data")

    def test_volume_type_enable_from_os(self):
        self.assertRaises(Exception, self.cutil.validate_volume_type_for_enable, {
            CommonVariables.VolumeTypeKey: "DATA",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
            }, "Os")

        self.cutil.validate_volume_type_for_enable({
        CommonVariables.VolumeTypeKey: "All",
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
        }, "Os")

        self.cutil.validate_volume_type_for_enable({
        CommonVariables.VolumeTypeKey: "Os",
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
        }, "OS")
        
    def test_volume_type_enable_from_all(self):
        self.cutil.validate_volume_type_for_enable({
        CommonVariables.VolumeTypeKey: "All",
        CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
        }, "All")
        self.assertRaises(Exception, self.cutil.validate_volume_type_for_enable, {
            CommonVariables.VolumeTypeKey: "OS",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryption
            }, "ALL")

        self.assertRaises(Exception, self.cutil.validate_volume_type_for_enable, {
            CommonVariables.VolumeTypeKey: "Data",
            CommonVariables.EncryptionEncryptionOperationKey: CommonVariables.EnableEncryptionFormatAll
            }, "All")   

    def test_check_kv_url(self):
        # Expected: https://{keyvault-name}.{vault-endpoint}[:443][/]
        self.assertIsNone(self.cutil.check_kv_url("https://keyvault-name.vault-endpoint.net",""))
        self.assertIsNone(self.cutil.check_kv_url("https://keyvault-name.vault-endpoint.net/",""))
        self.assertIsNone(self.cutil.check_kv_url("https://keyvault-name.vault-endpoint.net:443",""))
        self.assertIsNone(self.cutil.check_kv_url("https://keyvault-name.vault-endpoint.net:443/",""))

        self.assertRaises(Exception, self.cutil.check_kv_url, { "https://keyvault.vault.endpoint.net////", "" })
        self.assertRaises(Exception, self.cutil.check_kv_url, { "invalidurl", ""})
        self.assertRaises(Exception, self.cutil.check_kv_url, { None, "" })
        self.assertRaises(Exception, self.cutil.check_kv_url, { "https://localhost", "" })
        self.assertRaises(Exception, self.cutil.check_kv_url, { "ftp://foo", "" })

    def test_check_kek_url(self):
        # Expected: https://{keyvault-name}.{vault-endpoint}/keys/{object-name}/{object-version}
        self.assertIsNone(self.cutil.check_kek_url("https://keyvault-name.vault-endpoint.net/keys/kekname/00000000000000000000000000000000",""))
        self.assertIsNone(self.cutil.check_kek_url("https://keyvault-name.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000",""))
        self.assertIsNone(self.cutil.check_kek_url("https://keyvault-name.vault-endpoint.net/keys/kekname/00000000000000000000000000000000/",""))
        self.assertIsNone(self.cutil.check_kek_url("https://keyvault-name.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000/",""))

        self.assertRaises(Exception, self.cutil.check_kek_url, { "https://keyvault-name.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000////", ""})
        self.assertRaises(Exception, self.cutil.check_kek_url, { "invalidurl", ""})
        self.assertRaises(Exception, self.cutil.check_kek_url, { None, "" })

    def test_check_kv_id(self):
        # Expected: "/subscriptions/{subid}/resourceGroups/{rgname}/providers/Microsoft.KeyVault/vaults/{vaultname}"
        self.assertIsNone(self.cutil.check_kv_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testrgname/providers/Microsoft.KeyVault/vaults/testkvname",""))
        self.assertIsNone(self.cutil.check_kv_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/testrgname/providers/microsoft.keyvault/vaults/testkvname",""))
        self.assertIsNone(self.cutil.check_kv_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/test.rgname/providers/microsoft.keyvault/vaults/testkvname",""))

        self.assertRaises(Exception, self.cutil.check_kv_id, { "","" })
        self.assertRaises(Exception, self.cutil.check_kv_id, { "https://not/a/resource/id","" })
        self.assertRaises(Exception, self.cutil.check_kv_id, { "https://keyvault-name.vault-endpoint.net/keys/kekname/00000000000000000000000000000000","" })
        self.assertRaises(Exception, self.cutil.check_kv_id, { "kekname","" })

    def test_get_kv_id_name(self):
        """extract key vault name from KV ID"""
        self.assertEqual(self.cutil.get_kv_id_name("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testrgname/providers/Microsoft.KeyVault/vaults/testkvname"),"testkvname")
        self.assertEqual(self.cutil.get_kv_id_name("/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/testrgname/providers/microsoft.keyvault/vaults/testkvname"),"testkvname")
        self.assertEqual(self.cutil.get_kv_id_name("/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/test.rgname/providers/microsoft.keyvault/vaults/testkvname"),"testkvname")

        self.assertRaises(Exception, self.cutil.get_kv_id_name, { "" })
        self.assertRaises(Exception, self.cutil.get_kv_id_name, { "https://not/a/resource/id","" })
        self.assertRaises(Exception, self.cutil.get_kv_id_name, { "https://keyvault-name.vault-endpoint.net/keys/kekname/00000000000000000000000000000000","" })
        self.assertRaises(Exception, self.cutil.get_kv_id_name, { "kekname","" })

    def test_get_kv_url_name(self):
        """extract key vault name from KV URL"""
        self.assertEqual(self.cutil.get_kv_url_name("https://testkvname.vault.windows.net"),"testkvname")
        self.assertEqual(self.cutil.get_kv_url_name("https://testkvname.vault.windows.net/"),"testkvname")
        self.assertEqual(self.cutil.get_kv_url_name("https://testkvname.vault.windows.net:443"),"testkvname")
        self.assertEqual(self.cutil.get_kv_url_name("https://testkvname.vault.windows.net:443/"),"testkvname")
        self.assertEqual(self.cutil.get_kv_url_name("https://TESTKVNAME.vault.windows.net:443/").lower(),"testkvname")

        self.assertIsNone(self.cutil.get_kv_url_name(None))
        self.assertIsNone(self.cutil.get_kv_url_name(""))
        self.assertIsNone(self.cutil.get_kv_url_name("https://"))

    def test_get_kek_url_name(self):
        """extract key vault name from KEK URL"""
        self.assertEqual(self.cutil.get_kek_url_name("https://testkvname.vault-endpoint.net/keys/kekname/00000000000000000000000000000000"),"testkvname")
        self.assertEqual(self.cutil.get_kek_url_name("https://tEsTkVnAmE.vault-endpoint.net/keys/kekname/00000000000000000000000000000000/").lower(),"testkvname")
        self.assertEqual(self.cutil.get_kek_url_name("https://TESTKVNAME.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000").lower(),"testkvname")
        self.assertEqual(self.cutil.get_kek_url_name("https://testKVNAME.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000/").lower(),"testkvname")

        self.assertIsNone(self.cutil.get_kek_url_name(""))
        self.assertIsNone(self.cutil.get_kek_url_name("invalid-url"))
        self.assertIsNone(self.cutil.get_kek_url_name("https://foo"))
        self.assertIsNone(self.cutil.get_kek_url_name(None))

    def test_check_kek_name(self):
        """ensure KEK KV ID vault name matches KEK URL vault name"""
        kek_kv_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testrgname/providers/Microsoft.KeyVault/vaults/testkvname"
        kek_kv_url = "https://testkvname.vault-endpoint.net/keys/kekname/00000000000000000000000000000000"
        kek_kv_url_2 = "https://testkvname2.vault-endpoint.net/keys/kekname/00000000000000000000000000000000"

        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id.upper(), kek_kv_url, ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://testkvname.vault-endpoint.net/keys/kekname/00000000000000000000000000000000", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://testkvname.vault-endpoint.net/keys/kekname/00000000000000000000000000000000/", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://testkvname.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://testkvname.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000/", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://TESTKVNAME.vault-endpoint.net/keys/kekname/00000000000000000000000000000000", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://TeStKvNaMe.vault-endpoint.net/keys/kekname/00000000000000000000000000000000/", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://TESTKVNAME.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000", ""))
        self.assertIsNone(self.cutil.check_kek_name(kek_kv_id, "https://testKVNAME.vault-endpoint.net:443/keys/kekname/00000000000000000000000000000000/", ""))

        self.assertRaises(Exception, self.cutil.check_kek_name, { kek_kv_id, kek_kv_url_2, "" })
        self.assertRaises(Exception, self.cutil.check_kek_name, { None, kek_kv_url, "" })
        self.assertRaises(Exception, self.cutil.check_kek_name, { kek_kv_id, None, "" })

    def test_check_kv_name(self):
        """ensure KV ID vault name matches KV URL vault name"""
        kv_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testrgname/providers/Microsoft.KeyVault/vaults/testkvname"
        kv_url = "https://testkvname.vault.windows.net"
        kv_url_2 = "https://testkvname2.vault.windows.net"

        self.assertIsNone(self.cutil.check_kv_name(kv_id.upper(), kv_url, ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://testkvname.vault.windows.net", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://testkvname.vault.windows.net/", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://testkvname.vault.windows.net:443", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://testkvname.vault.windows.net:443/", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://TESTKVNAME.vault.windows.net", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://TESTKVNAME.vault.windows.net/", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://TESTKVNAME.vault.windows.net:443", ""))
        self.assertIsNone(self.cutil.check_kv_name(kv_id, "https://TESTKVNAME.vault.windows.net:443/", ""))

        self.assertRaises(Exception, self.cutil.check_kv_name, { kv_id, kv_url_2, "" })
        self.assertRaises(Exception, self.cutil.check_kv_name, { None, kv_url, "" })
        self.assertRaises(Exception, self.cutil.check_kv_name, { kv_id, None, "" })