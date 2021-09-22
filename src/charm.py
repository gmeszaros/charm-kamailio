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
# from charmhelpers.core.templating import render
# from subprocess import check_call, CalledProcessError
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus

logger = logging.getLogger(__name__)


class KamailioCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.kamctl_action, self._on_kamctl_action)
        self._stored.set_default(
            external_url=self.app.name,
            tls_secret_name="",
            bind_address_port=self.model.config["bind-address-port"]
        )

        self.ingress = IngressRequires(self, self._ingress_config)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""

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

        plan = container.get_plan()

        if plan.services != layer["services"]:
            container.add_layer("kamailio", layer, combine=True)
            logger.info("Added updated layer 'kamailio' to Pebble plan")

            if container.get_service("kamailio").is_running():
                container.stop("kamailio")

            container.start("kamailio")
            logging.info("Restarted kamailio service")

        self.unit.status = ActiveStatus()

    def _kamailio_layer(self):

        layer = {
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
        return layer

    def _on_kamctl_action(self, event):
        """Just an example to show how to receive actions.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle actions, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the actions.py file.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        args = event.params["args"]
        if args:
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

    def _render_kamailio_config(self):
        logger.warning("in _render_kamailio_config: %s" % self.model.config["bind-address-port"])
        # vhost_file = "/etc/kamailio/kamailio-local.cfg"
        # vhost_template = 'kamailio-local.cfg.j2'
        # context = {
        #     'bind_address_port': self._stored.bind_address_port
        # }
        # render(vhost_template, vhost_file, context, perms=0o755)
        #  TODO: change config value on running container file
        #  Update port to 8888 and restart service
        container = self.unit.get_container("kamailio")
        # infos = container.list_files('/etc/kamailio/', pattern='*.cfg')
        # logger.info('config files: %s', infos)

        # config = container.pull('/etc/kamailio/kamailio.cfg').read()
        # if 'listen_port =' not in config:
        #     config += '\nlisten_port = ' + self._stored.bind_address_port + '\n'
        # else:
        config = "listen=" + self.model.config["bind-address-port"]
        container.push('/etc/kamailio/kamailio-local.cfg', config)


if __name__ == "__main__":
    main(KamailioCharm)
