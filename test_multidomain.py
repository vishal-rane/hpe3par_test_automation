import pytest
from time import sleep
import hpe_3par_kubernetes_manager as manager
import logging
from hpe3parclient.exceptions import HTTPNotFound

timeout = 900

"""logfile = "CSI_test_automation.log"
loglevel = logging.DEBUG
logging.basicConfig(filename=logfile, level=loglevel, format='%(levelname)s-%(asctime)s\n%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('=============================== Test Automation START ========================')
"""
publish_pass = True


def test_no_domain():
    hpe3par_cli = None
    objs_dict = None
    try:
        # yml = "YAML/multi-domain-no-domain.yml"
        yml = "YAML/MD-cpg-1-domain-no.yml"
        array_ip, array_uname, array_pwd, protocol = manager.read_array_prop(yml)
        hpe3par_cli = manager.get_3par_cli_client(yml)

        cpg_domain, host_domain, host, cpg_name = get_domain(yml, hpe3par_cli)
        hpe3par_version = manager.get_array_version(hpe3par_cli)
        print("\n########################### Multi-Domain::test_no_domain::%s%s::START ###########################" %
              (hpe3par_version[0:5],protocol))

        assert cpg_domain is None, "CPG %s belongs to domain %s, terminating test" % (cpg_name, cpg_domain)
        assert host_domain is None, "Host %s belongs to domain %s, terminating test" % (host, host_domain)

        # run_pod(yml, hpe3par_cli, protocol)
        print("=== Creating pod for CPG and host in no domain")
        status, kind, reason, obj, objs_dict = create_pod(yml, hpe3par_cli)
        assert status is True, "Test for CPG and HOST both in no domain is failed as % failed to %" % (kind, reason)
        verify(hpe3par_cli, protocol, objs_dict['pvc'], objs_dict['pod'], objs_dict['sc'], objs_dict['secret'])
        print("\n########################### Multi-Domain::test_no_domain::%s%s::END ###########################" %
              (hpe3par_version[0:5], protocol))
    except Exception as e:
        print("Exception in test_no_domain :: %s" % e)
    finally:
        if hpe3par_cli is not None:
            hpe3par_cli.logout()
        if objs_dict is not None:
            cleanup(objs_dict['secret'], objs_dict['sc'], objs_dict['pvc'], objs_dict['pod'])


def test_same_domain():
    hpe3par_cli = None
    objs_dict = None
    base_objs_dict = None
    try:
        yml_1 = 'YAML/MD-cpg-2-domain-x.yml'
        hpe3par_cli = manager.get_3par_cli_client(yml_1)
        array_ip, array_uname, array_pwd, protocol = manager.read_array_prop(yml_1)

        cpg_domain, host_domain, host, cpg_name = get_domain(yml_1, hpe3par_cli)
        hpe3par_version = manager.get_array_version(hpe3par_cli)
        print("\n########################### Multi-Domain::test_same_domain::%s%s::START ###########################" %
              (hpe3par_version[0:5], protocol))
        print("\n\n%s" % cpg_domain)
        print("\n\n%s" % host_domain)

        assert host is None or (host is not None and cpg_domain == host_domain), \
            "Host entry exists with domain %s whereas cpg %s belongs to %s. Terminating test for same domain." % (host_domain, cpg_name, cpg_domain)

        base_status, base_kind, base_reason, base_obj, base_objs_dict = create_pod(yml_1, hpe3par_cli)
        assert base_status is True, "Terminating test since %s failed to %s" % (base_kind, base_reason)
        print("Volume created and publishes successfully for domain %s" % cpg_domain)

        yml_2 = "YAML/MD-cpg-3-domain-x.yml"
        # array_ip, array_uname, array_pwd, protocol = manager.read_array_prop(yml_2)
        cpg_domain_2, host_domain_2, host_2, cpg_name_2 = get_domain(yml_2, hpe3par_cli)
        assert cpg_domain == cpg_domain_2, "Terminating test as %s does not belong to % domain" % (cpg_name_2,
                                                                                                   cpg_domain)
        print("Now creating and publishing another volume in same domain %s ..." % cpg_domain)

        status, kind, reason, obj, objs_dict = create_pod(yml_2, hpe3par_cli)
        assert status is True, "Failed to publish volume on existing domain %s as %s failed to %s" % (cpg_domain, kind, reason)

        print("Verifying Volume, CRD and vluns for published volume...")
        verify(hpe3par_cli, protocol, objs_dict['pvc'], objs_dict['pod'], objs_dict['sc'], objs_dict['secret'])
        print("Second volume created and publishes successfully in same domain")
        print("\n########################### Multi-Domain::test_same_domain::%s%s::END ###########################" %
          (hpe3par_version[0:5], protocol))
    except Exception as e:
        print("Exception in test_same_domain :: %s" % e)

    finally:
        if hpe3par_cli is not None:
            hpe3par_cli.logout()
        if base_objs_dict is not None:
            cleanup(base_objs_dict['secret'], base_objs_dict['sc'], base_objs_dict['pvc'], base_objs_dict['pod'])
        if objs_dict is not None:
            cleanup(objs_dict['secret'], objs_dict['sc'], objs_dict['pvc'], objs_dict['pod'])


def test_diff_domain():
    hpe3par_cli = None
    base_objs_dict = None
    objs_dict = None
    try:
        yml_1 = 'YAML/MD-cpg-2-domain-x.yml'
        hpe3par_cli = manager.get_3par_cli_client(yml_1)

        cpg_domain, host_domain, host, cpg_name = get_domain(yml_1, hpe3par_cli)
        hpe3par_version = manager.get_array_version(hpe3par_cli)
        array_ip, array_uname, array_pwd, protocol = manager.read_array_prop(yml_1)
        print("\n########################### Multi-Domain::test_diff_domain::%s%s::START ###########################" %
              (hpe3par_version[0:5], protocol))

        """print("\n\n%s" % cpg_domain)
        print("\n\n%s" % host_domain)

        assert host is None or (host is not None and cpg_domain != host_domain), \
            "Host entry exists with domain %s whereas cpg %s belongs to %s. Terminating test." % (
            host_domain, cpg_name, cpg_domain)"""

        if host is None:
            base_status, base_kind, base_reason, base_obj, base_objs_dict = create_pod(yml_1, hpe3par_cli)
            assert base_status is True, "Terminating test since %s failed to %s" % (base_kind, base_reason)
            print("Volume created and publishes successfully for domain %s" % cpg_domain)
            cpg_domain, host_domain, host, cpg_name = get_domain(yml_1, hpe3par_cli)

        yml_2 = "YAML/MD-cpg-4-domain-y.yml"
        array_ip, array_uname, array_pwd, protocol = manager.read_array_prop(yml_2)
        cpg_domain_2, host_domain_2, host_2, cpg_name_2 = get_domain(yml_2, hpe3par_cli)

        assert host_domain != cpg_domain_2, \
            "Terminating test since host %s is in domain %s and cpg %s also belongs to same domain" % (host, host_domain, cpg_name_2)
        print("Now creating and publishing volume in different domain %s ..." % cpg_domain_2)
        status, kind, reason, obj, objs_dict = create_pod(yml_2, hpe3par_cli)
        assert status is False and kind == 'POD' and reason == 'Running', \
            'multi-domain test failed as %s failed to %s while exporting volume on different domain' % (kind, obj)

        print("Verifying Volume, CRD and vluns for published volume...")
        verify(hpe3par_cli, protocol, objs_dict['pvc'], objs_dict['pod'], objs_dict['sc'], objs_dict['secret'])
        print("Second volume created and publishes successfully in same domain")
        print("\n########################### Multi-Domain::test_diff_domain::%s%s::END ###########################" %
              (hpe3par_version[0:5], protocol))
    except Exception as e:
        print("Exception in test_diff_domain :: %s" % e)

    finally:
        if hpe3par_cli is not None:
            hpe3par_cli.logout()
        if base_objs_dict is not None:
            cleanup(base_objs_dict['secret'], base_objs_dict['sc'], base_objs_dict['pvc'], base_objs_dict['pod'])
        if objs_dict is not None:
            cleanup(objs_dict['secret'], objs_dict['sc'], objs_dict['pvc'], objs_dict['pod'])


def get_domain(yml, hpe3par_cli):
    try:
        provisioning, compression, cpg_name, size = manager.get_sc_properties(yml)
        pod_node = manager.get_pod_node(yml)
        assert pod_node is not None, "Pod %s does not specify nodeName, terminating test..."

        dot_index = pod_node.find('.')
        if dot_index > 0:
            pod_node = pod_node[0:dot_index]

        # Check domain of host and cpg
        cpg = hpe3par_cli.getCPG(cpg_name)
        cpg_domain = None
        host = None
        host_domain = None
        if 'domain' in cpg:
            cpg_domain = cpg['domain']
        try:
            host = hpe3par_cli.getHost(pod_node)
            host_domain = None
            if 'domain' in host:
                host_domain = host['domain']
        except HTTPNotFound as ex:
            print("Host does not exist, continue test...")

        return cpg_domain, host_domain, host, cpg_name

    except Exception as e:
        print("Exception in get_domain :: %s" % e)


def create_pod(yml, hpe3par_cli):
    try:
        secret = manager.create_secret(yml)
        sc = manager.create_sc(yml)
        pvc = manager.create_pvc(yml)
        flag, pvc_obj = manager.check_status(timeout, pvc.metadata.name, kind='pvc', status='Bound',
                                             namespace=pvc.metadata.namespace)
        # assert flag is True, "PVC %s status check timed out, not in Bound state yet..." % pvc_obj.metadata.name
        if flag is False:
            return False, "PVC", 'Bound', pvc_obj, {'secret': secret, 'sc': sc, 'pvc': pvc_obj, 'pod': None}

        pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        # print(pvc_crd)
        volume_name = manager.get_pvc_volume(pvc_crd)
        volume = manager.get_volume_from_array(hpe3par_cli, volume_name)
        # assert volume is not None, "Volume is not created on 3PAR for pvc %s. Terminating test. " % volume_name
        if volume is None:
            return False, "3PAR_Volume", 'create', volume_name, {'secret': secret, 'sc': sc, 'pvc': pvc_obj, 'pod': None}

        pod = manager.create_pod(yml)
        flag, pod_obj = manager.check_status(timeout, pod.metadata.name, kind='pod', status='Running',
                                             namespace=pod.metadata.namespace)
        # assert flag is True, "Pod %s status check timed out, not in Running state yet. Terminating test." % pod.metadata.name
        if flag is False:
            return False, 'POD', 'Running', pod_obj, {'secret': secret, 'sc': sc, 'pvc': pvc_obj, 'pod': pod_obj}

        return True, None, None, None, {'secret': secret, 'sc': sc, 'pvc': pvc_obj, 'pod': pod_obj}
    except Exception as e:
        print("Exception in create_pod :: %s" % e)
        raise e
    """finally:
        cleanup(secret, sc, pvc, pod)"""


def verify(hpe3par_cli, protocol, pvc_obj, pod_obj, sc, secret):
    try:
        """ secret = manager.create_secret(yml)
        sc = manager.create_sc(yml)
        pvc = manager.create_pvc(yml)
        flag, pvc_obj = manager.check_status(timeout, pvc.metadata.name, kind='pvc', status='Bound',
                                             namespace=pvc.metadata.namespace)
        #assert flag is True, "PVC %s status check timed out, not in Bound state yet..." % pvc_obj.metadata.name
        if flag is False:
            return "PVC", pvc_obj,

        pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        #print(pvc_crd)
        volume_name = manager.get_pvc_volume(pvc_crd)
        volume = manager.get_volume_from_array(hpe3par_cli, volume_name)
        assert volume is not None, "Volume is not created on 3PAR for pvc %s. Terminating test. " % volume_name

        pod = manager.create_pod(yml)
        flag, pod_obj = manager.check_status(timeout, pod.metadata.name, kind='pod', status='Running',
                                             namespace=pod.metadata.namespace)
        assert flag is True, "Pod %s status check timed out, not in Running state yet. Terminating test." % pod.metadata.name
        """
        pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        # print(pvc_crd)
        volume_name = manager.get_pvc_volume(pvc_crd)

        # Verify crd fpr published status
        assert manager.verify_pvc_crd_published(pvc_obj.spec.volume_name) is True, \
            "PVC CRD %s Published is false after Pod is running" % pvc_obj.spec.volume_name

        hpe3par_vlun = manager.get_3par_vlun(hpe3par_cli,volume_name)
        assert manager.verify_pod_node(hpe3par_vlun, pod_obj) is True, \
            "Node for pod received from 3par and cluster do not match"

        if protocol == 'iscsi':
            iscsi_ips = manager.get_iscsi_ips(hpe3par_cli)

            flag, disk_partition = manager.verify_by_path(iscsi_ips, pod_obj.spec.node_name)
            assert flag is True, "partition not found"
            print("disk_partition received are %s " % disk_partition)

            flag, disk_partition_mod = manager.verify_multipath(hpe3par_vlun, disk_partition)
            assert flag is True, "multipath check failed"
            print("disk_partition after multipath check are %s " % disk_partition)
            print("disk_partition_mod after multipath check are %s " % disk_partition_mod)
            assert manager.verify_partition(disk_partition_mod), "partition mismatch"

            assert manager.verify_lsscsi(pod_obj.spec.node_name, disk_partition), "lsscsi verificatio failed"

        assert manager.delete_pod(pod_obj.metadata.name, pod_obj.metadata.namespace), "Pod %s is not deleted yet " % \
                                                                              pod.metadata.name
        assert manager.check_if_deleted(timeout, pod_obj.metadata.name, "Pod", namespace=pod_obj.metadata.namespace) is True, \
            "Pod %s is not deleted yet " % pod_obj.metadata.name

        if protocol == 'iscsi':
            flag, ip = manager.verify_deleted_partition(iscsi_ips, pod_obj.spec.node_name)
            assert flag is True, "Partition(s) not cleaned after volume deletion for iscsi-ip %s " % ip

            paths = manager.verify_deleted_multipath_entries(pod_obj.spec.node_name, hpe3par_vlun)
            assert paths is None or len(paths) == 0, "Multipath entries are not cleaned"

            # partitions = manager.verify_deleted_lsscsi_entries(pod_obj.spec.node_name, disk_partition)
            # assert len(partitions) == 0, "lsscsi verificatio failed for vlun deletion"
            flag = manager.verify_deleted_lsscsi_entries(pod_obj.spec.node_name, disk_partition)
            print("flag after deleted lsscsi verificatio is %s " % flag)
            assert flag, "lsscsi verification failed for vlun deletion"

        # Verify crd for unpublished status
        """try:
            assert manager.verify_pvc_crd_published(pvc_obj.spec.volume_name) is False, \
                "PVC CRD %s Published is true after Pod is deleted" % pvc_obj.spec.volume_name
            print("PVC CRD published is false after pod deletion.")
            #logging.warning("PVC CRD published is false after pod deletion.")
        except Exception as e:
            print("Resuming test after failure of publishes status check for pvc crd... \n%s" % e)
            #logging.error("Resuming test after failure of publishes status check for pvc crd... \n%s" % e)"""
        assert manager.delete_pvc(pvc_obj.metadata.name)

        assert manager.check_if_deleted(timeout, pvc_obj.metadata.name, "PVC", namespace=pvc_obj.metadata.namespace) is True, \
            "PVC %s is not deleted yet " % pvc_obj.metadata.name

        #pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        #print("PVC crd after PVC object deletion :: %s " % pvc_crd)
        assert manager.check_if_crd_deleted(pvc_obj.spec.volume_name, "hpevolumeinfos") is True, \
            "CRD %s of %s is not deleted yet. Taking longer..." % (pvc_obj.spec.volume_name, 'hpevolumeinfos')

        assert manager.verify_delete_volume_on_3par(hpe3par_cli, volume_name), \
            "Volume %s from 3PAR for PVC %s is not deleted" % (volume_name, pvc_obj.metadata.name)

        assert manager.delete_sc(sc.metadata.name) is True

        assert manager.check_if_deleted(timeout, sc.metadata.name, "SC") is True, "SC %s is not deleted yet " \
                                                                                  % sc.metadata.name

        assert manager.delete_secret(secret.metadata.name, secret.metadata.namespace) is True

        assert manager.check_if_deleted(timeout, secret.metadata.name, "Secret", namespace=secret.metadata.namespace) is True, \
            "Secret %s is not deleted yet " % secret.metadata.name

    except Exception as e:
        print("Exception in run_pod :: %s" % e)
        #logging.error("Exception in test_publish :: %s" % e)
        """if step == 'pvc':
            manager.delete_pvc(pvc.metadata.name)
            manager.delete_sc(sc.metadata.name)
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)
        if step == 'sc':
            manager.delete_sc(sc.metadata.name)
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)
        if step == 'secret':
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)"""
        raise e



def run_pod_bkp(yml, hpe3par_cli, protocol):
    secret = None
    sc = None
    pvc = None
    pod = None
    try:
        secret = manager.create_secret(yml)
        sc = manager.create_sc(yml)
        pvc = manager.create_pvc(yml)
        flag, pvc_obj = manager.check_status(timeout, pvc.metadata.name, kind='pvc', status='Bound',
                                             namespace=pvc.metadata.namespace)
        assert flag is True, "PVC %s status check timed out, not in Bound state yet..." % pvc_obj.metadata.name

        pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        #print(pvc_crd)
        volume_name = manager.get_pvc_volume(pvc_crd)
        volume = manager.get_volume_from_array(hpe3par_cli, volume_name)
        assert volume is not None, "Volume is not created on 3PAR for pvc %s. Terminating test. " % volume_name

        pod = manager.create_pod(yml)
        flag, pod_obj = manager.check_status(timeout, pod.metadata.name, kind='pod', status='Running',
                                             namespace=pod.metadata.namespace)
        assert flag is True, "Pod %s status check timed out, not in Running state yet. Terminating test." % pod.metadata.name

        # Verify crd fpr published status
        assert manager.verify_pvc_crd_published(pvc_obj.spec.volume_name) is True, \
            "PVC CRD %s Published is false after Pod is running" % pvc_obj.spec.volume_name

        hpe3par_vlun = manager.get_3par_vlun(hpe3par_cli,volume_name)
        assert manager.verify_pod_node(hpe3par_vlun, pod_obj) is True, \
            "Node for pod received from 3par and cluster do not match"

        if protocol == 'iscsi':
            iscsi_ips = manager.get_iscsi_ips(hpe3par_cli)

            flag, disk_partition = manager.verify_by_path(iscsi_ips, pod_obj.spec.node_name)
            assert flag is True, "partition not found"
            print("disk_partition received are %s " % disk_partition)

            flag, disk_partition_mod = manager.verify_multipath(hpe3par_vlun, disk_partition)
            assert flag is True, "multipath check failed"
            print("disk_partition after multipath check are %s " % disk_partition)
            print("disk_partition_mod after multipath check are %s " % disk_partition_mod)
            assert manager.verify_partition(disk_partition_mod), "partition mismatch"

            assert manager.verify_lsscsi(pod_obj.spec.node_name, disk_partition), "lsscsi verificatio failed"

        assert manager.delete_pod(pod.metadata.name, pod.metadata.namespace), "Pod %s is not deleted yet " % \
                                                                              pod.metadata.name
        assert manager.check_if_deleted(timeout, pod.metadata.name, "Pod", namespace=pod.metadata.namespace) is True, \
            "Pod %s is not deleted yet " % pod.metadata.name

        if protocol == 'iscsi':
            flag, ip = manager.verify_deleted_partition(iscsi_ips, pod_obj.spec.node_name)
            assert flag is True, "Partition(s) not cleaned after volume deletion for iscsi-ip %s " % ip

            paths = manager.verify_deleted_multipath_entries(pod_obj.spec.node_name, hpe3par_vlun)
            assert paths is None or len(paths) == 0, "Multipath entries are not cleaned"

            # partitions = manager.verify_deleted_lsscsi_entries(pod_obj.spec.node_name, disk_partition)
            # assert len(partitions) == 0, "lsscsi verificatio failed for vlun deletion"
            flag = manager.verify_deleted_lsscsi_entries(pod_obj.spec.node_name, disk_partition)
            print("flag after deleted lsscsi verificatio is %s " % flag)
            assert flag, "lsscsi verification failed for vlun deletion"

        # Verify crd for unpublished status
        """try:
            assert manager.verify_pvc_crd_published(pvc_obj.spec.volume_name) is False, \
                "PVC CRD %s Published is true after Pod is deleted" % pvc_obj.spec.volume_name
            print("PVC CRD published is false after pod deletion.")
            #logging.warning("PVC CRD published is false after pod deletion.")
        except Exception as e:
            print("Resuming test after failure of publishes status check for pvc crd... \n%s" % e)
            #logging.error("Resuming test after failure of publishes status check for pvc crd... \n%s" % e)"""
        assert manager.delete_pvc(pvc.metadata.name)

        assert manager.check_if_deleted(timeout, pvc.metadata.name, "PVC", namespace=pvc.metadata.namespace) is True, \
            "PVC %s is not deleted yet " % pvc.metadata.name

        #pvc_crd = manager.get_pvc_crd(pvc_obj.spec.volume_name)
        #print("PVC crd after PVC object deletion :: %s " % pvc_crd)
        assert manager.check_if_crd_deleted(pvc_obj.spec.volume_name, "hpevolumeinfos") is True, \
            "CRD %s of %s is not deleted yet. Taking longer..." % (pvc_obj.spec.volume_name, 'hpevolumeinfos')

        assert manager.verify_delete_volume_on_3par(hpe3par_cli, volume_name), \
            "Volume %s from 3PAR for PVC %s is not deleted" % (volume_name, pvc.metadata.name)

        assert manager.delete_sc(sc.metadata.name) is True

        assert manager.check_if_deleted(timeout, sc.metadata.name, "SC") is True, "SC %s is not deleted yet " \
                                                                                  % sc.metadata.name

        assert manager.delete_secret(secret.metadata.name, secret.metadata.namespace) is True

        assert manager.check_if_deleted(timeout, secret.metadata.name, "Secret", namespace=secret.metadata.namespace) is True, \
            "Secret %s is not deleted yet " % secret.metadata.name

    except Exception as e:
        print("Exception in run_pod :: %s" % e)
        #logging.error("Exception in test_publish :: %s" % e)
        """if step == 'pvc':
            manager.delete_pvc(pvc.metadata.name)
            manager.delete_sc(sc.metadata.name)
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)
        if step == 'sc':
            manager.delete_sc(sc.metadata.name)
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)
        if step == 'secret':
            manager.delete_secret(secret.metadata.name, secret.metadata.namespace)"""
        raise e
    finally:
        cleanup(secret, sc, pvc, pod)


def cleanup(secret, sc, pvc, pod):
    print("====== cleanup :START =========")
    #logging.info("====== cleanup after failure:START =========")
    if pod is not None and manager.check_if_deleted(2, pod.metadata.name, "Pod", namespace=pod.metadata.namespace) is False:
        manager.delete_pod(pod.metadata.name, pod.metadata.namespace)
    if pvc is not None and manager.check_if_deleted(2, pvc.metadata.name, "PVC", namespace=pvc.metadata.namespace) is False:
        manager.delete_pvc(pvc.metadata.name)
    if sc is not None and manager.check_if_deleted(2, sc.metadata.name, "SC") is False:
        manager.delete_sc(sc.metadata.name)
    if secret is not None and manager.check_if_deleted(2, secret.metadata.name, "Secret", namespace=secret.metadata.namespace) is False:
        manager.delete_secret(secret.metadata.name, secret.metadata.namespace)
    print("====== cleanup :END =========")
    #logging.info("====== cleanup after failure:END =========")