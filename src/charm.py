#!/usr/bin/env python3
# Copyright 2021 Gabor Meszaros
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus
from ops.pebble import ServiceStatus

logger = logging.getLogger(__name__)


class KamailioCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.config_changed,
                               self._on_config_changed)

        # Observe action events
        action_event_observer_mapping = {
            "restart": self._on_restart_action,
            "start": self._on_start_action,
            "stop": self._on_stop_action,
            "kamctl": self._on_kamctl_action,
        }
        for event, observer in action_event_observer_mapping.items():
            logger.debug(f"event: {event}")
            self.framework.observe(self.on[event].action, observer)

        self._stored.set_default(
            external_url=self.app.name,
            tls_secret_name="",
            bind_address_port=self.model.config["bind-address-port"],
            sip_domain=self.model.config["sip-domain"]
        )

        self.ingress = IngressRequires(self, self._ingress_config)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""

        logging.debug('Handling Juju config change')

        container = self.unit.get_container("kamailio")

        layer = self._kamailio_layer()

        if "error" in layer:
            self.unit.status = BlockedStatus(layer["error"])
            logger.warning(layer["error"])
            return

        if "external-url" in self.model.config and \
                self.model.config["external-url"] != self._stored.external_url:
            self._stored.external_url = self.model.config["external-url"]
            self.ingress.update_config(self._ingress_config)

        if "tls-secret-name" in self.model.config and \
                self.model.config["tls-secret-name"] != self._stored.tls_secret_name:
            self._stored.tls_secret_name = self.model.config["tls-secret-name"]
            self.ingress.update_config(self._ingress_config)

        if "bind-address-port" in self.model.config and \
                self.model.config["bind-address-port"] != self._stored.bind_address_port:
            self._stored.bind_address_port_port = self.model.config["bind-address-port"]
            self._render_kamailio_config()

        if "sip-domain" in self.model.config and \
                self.model.config["sip-domain"] != self._stored.sip_domain:
            self._stored.bind_address_port_port = self.model.config["sip-domain"]
            self._render_kamctlrc_config()

        plan = container.get_plan()

        if plan.services != layer["services"]:
            container.add_layer("kamailio", layer, combine=True)
            logger.info("Added updated layer 'kamailio' to Pebble plan")

            if container.get_service("kamailio").is_running():
                container.stop("kamailio")

            container.start("kamailio")
            logging.info("Restarted kamailio service")

        self.unit.status = ActiveStatus(f'{"Container is running"}')

    def _kamailio_layer(self) -> dict:
        """Generate Pebble Layer for Kamailio"""

        return {
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

    def _on_restart_action(self, event):
        """Observer for restart action event"""
        try:
            self._restart_kamailio()
            event.set_results({"output": "service restarted"})
        except Exception as e:
            event.fail(f"Failed restarting kamailio: {e}")

    def _on_start_action(self, event):
        """Observer for start action event"""
        try:
            self._start_kamailio()
            event.set_results({"output": "service started"})
        except Exception as e:
            event.fail(f"Failed starting kamailio: {e}")

    def _on_stop_action(self, event):
        """Observer for stop action event"""
        try:
            self._stop_kamailio()
            event.set_results({"output": "service stopped"})
        except Exception as e:
            event.fail(f"Failed stopping kamailio: {e}")

    def _on_kamctl_action(self, event):
        """Observer for kamctl action event"""

        if event.params["args"]:
            event.set_results({"kamctl called with args": "Currently not implemented."})
            # check_call(["kamctl", args])
        else:
            event.set_results({"kamctl called": "Currently not implemented."})

    @property
    def _external_url(self):
        return self.config.get("external-url") or self.app.name

    @property
    def _ingress_config(self):
        ingress_config = {
            "service-hostname": self._external_url,
            "service-name": self.app.name,
            "service-port": 5060,
        }
        tls_secret_name = self.config.get("tls-secret-name")
        if tls_secret_name:
            ingress_config["tls-secret-name"] = tls_secret_name
        return ingress_config

    def _render_kamctlrc_config(self):
        logger.warning("in _render_kamctlrc_config: %s" % self.model.config["sip-domain"])
        container = self.unit.get_container("kamailio")
        config = container.pull('/etc/kamailio/kamctlrc').read()
        logger.warning("kamctlrc: %s" % config)
        config = "SIP-DOMAIN=" + self.model.config["sip-domain"]
        container.push('/etc/kamailio/kamctlrc.cfg', config)

    def _render_kamailio_config(self):
        logger.warning("in _render_kamailio_config: %s" % self.model.config["bind-address-port"])
        container = self.unit.get_container("kamailio")
        config = "listen=" + self.model.config["bind-address-port"]
        container.push('/etc/kamailio/kamailio-local.cfg', config)

    def _restart_kamailio(self):
        container = self.unit.get_container("kamailio")
        if container.get_service("kamailio").current == ServiceStatus.ACTIVE:
            container.stop("kamailio")
        container.start("kamailio")
        self.unit.status = ActiveStatus(f'{"Container is running"}')

    def _start_kamailio(self):
        container = self.unit.get_container("kamailio")
        if container.get_service("kamailio").current == ServiceStatus.ACTIVE:
            raise Exception("kamailio service is already active")
        container.start("kamailio")
        self.unit.status = ActiveStatus(f'{"Container is running"}')

    def _stop_kamailio(self):
        container = self.unit.get_container("kamailio")
        if container.get_service("kamailio").current != ServiceStatus.ACTIVE:
            raise Exception("kamailio service is not running")
        container.stop("kamailio")
        self.unit.status = BlockedStatus(f'{"Container Stopped"}')


if __name__ == "__main__":
    main(KamailioCharm)
