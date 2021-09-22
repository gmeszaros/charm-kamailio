# Copyright 2021 Gabor Meszaros
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock

from charm import KamailioCharm
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(KamailioCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        self.assertEqual((self.harness.charm._stored.bind_address_port), 'udp:0.0.0.0:5060')
        self.harness.update_config({"bind-address-port": "udp:0.0.0.0:5069"})
        self.assertEqual(list(self.harness.charm._stored.bind_address_port), "udp:0.0.0.0:5069")

    def test_action(self):
        # the harness doesn't (yet!) help much with actions themselves
        action_event = Mock(params={"args": ""})
        self.harness.charm._on_kamctl_action(action_event)

        self.assertTrue(action_event.set_results.called)

    def test_action_fail(self):
        action_event = Mock(params={"args": "ps"})
        self.harness.charm._on_kamctl_action(action_event)

        self.assertEqual(action_event.fail.call_args, None)

    def test_kamailio_layer(self):
        # Test with empty config.
        expected = {
            "summary": "kamailio layer",
            "description": "pebble config layer for kamailio",
            "services": {
                "kamailio": {
                    "override": "replace",
                    "summary": "kamailio",
                    "command": "kamailio -DD -E",
                    "startup": "enabled",
                }
            },
        }
        self.assertEqual(self.harness.charm._kamailio_layer(), expected)
