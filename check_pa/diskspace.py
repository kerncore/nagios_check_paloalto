# -*- coding: utf-8 -*-

import logging
import re

import nagiosplugin as np

from check_pa.xml_reader import XMLReader

_log = logging.getLogger('nagiosplugin')


def create_check(args):
    """

    :return:
    """
    return np.Check(
        DiskSpace(args.host, args.token),
        np.ScalarContext('diskspace', args.warn, args.crit),
        DiskSpaceSummary())


class DiskSpace(np.Resource):
    """Reads the used disk space of the Palo Alto Firewall System."""

    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.cmd = '<show><system><disk-space><%2Fdisk-space><%2Fsystem' \
                   '><%2Fshow>'
        self.xml_obj = XMLReader(self.host, self.token, self.cmd)

    def probe(self):
        """
        Querys the REST-API and create disk space metrics.

        :return: a disk space metric.
        """
        _log.info('Reading XML from: %s', self.xml_obj.build_request_url())
        soup = self.xml_obj.read()
        available_hdds = re.findall('(sda\d.*?)(?=/)', soup.result.string)
        for hdd in available_hdds:
            sda = re.findall('(sda\d)', hdd)[0]
            percent = int(re.findall('([0-9]+%)', hdd)[0].replace("%", ""))
            yield np.Metric(sda, percent, min=0, max=100,
                            context='diskspace')


class DiskSpaceSummary(np.Summary):
    """Create status line from results."""

    def ok(self, results):
        """
        Prints a more informative output, e. g. sda2: 55% free space,
        sda5: 43% free space, sda6: 30% free space, sda8: 46% free space

        :param results: Results container
        :return: status line
        """
        l = []
        for sda in results.results:
            s = '%s: %s%% used space' % (sda.metric.name, sda.metric.value)
            l.append(s)
        _log.debug('HDD count: %d' % len(l))
        output = ", ".join(l)
        return str(output)

    def problem(self, results):
        """
        Prints a more informative output

        :param results: Results container
        :return: status line
        """
        return 'Used disk space: %s' % (str(results.first_significant))
