# Kamailio Operator Charm

## Description

Kamailio® (successor of former OpenSER and SER) is an Open Source SIP Server
released under GPLv2+, able to handle thousands of call setups per second.
Kamailio can be used to build large platforms for VoIP and realtime
communications – presence, WebRTC, Instant messaging and other applications.

Moreover, it can be easily used for scaling up SIP-to-PSTN gateways, PBX
systems or media servers like Asterisk™, FreeSWITCH™ or SEMS.

## Quickstart

Assuming you have Juju installed and bootstrapped on a Kubernetes cluster
(if you do not, see the next section):

```bash
# Clone the charm code
$ git clone https://github.com/gmeszaros/kamailio && cd kamailio

# Build the charm package
$ charmcraft pack

# Deploy the Kamailio charm
$ juju deploy ./kamailio_ubuntu-20.04-amd64.charm  --resource kamailio-image=kamailio/kamailio:5.3.3-stretch

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator --config ingress-class="public"

# Relate kamailio and ingress integrator
$ juju add-relation kamailio nginx-ingress-integrator

# Add an entry to /etc/hosts
$ echo "127.0.1.1 kamailio.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

The service is now available and interface binding can be adjusted by running:
```bash
juju config kamailio bind-address-port='udp:0.0.0.0:5060'
```

## Development Setup

To set up a local test environment with [MicroK8s](https://microk8s.io):

```bash
# Install MicroK8s
$ sudo snap install --classic microk8s

# Wait for MicroK8s to be ready
$ sudo microk8s status --wait-ready

# Enable features required by Juju controller & charm
$ sudo microk8s enable storage dns ingress
# (Optional) Alias kubectl bundled with MicroK8s package
$ sudo snap alias microk8s.kubectl kubectl

# (Optional) Add current user to 'microk8s' group
# This avoid needing to use 'sudo' with the 'microk8s' command
$ sudo usermod -aG microk8s $(whoami)

# Activate the new group (in the current shell only)
# Log out and log back in to make the change system-wide
$ newgrp microk8s

# Install Charmcraft
$ sudo snap install charmcraft

# Install juju
$ sudo snap install --classic juju

# Bootstrap the Juju controller on MicroK8s
$ juju bootstrap microk8s micro

# Add a new model to Juju
$ juju add-model development
```

## Build and Deploy Locally

```bash
# Clone the charm code
$ git clone https://github.com/gmeszaros/kamailio && cd kamailio

# Build the charm package
$ charmcraft pack

# Deploy the kamailio charm
$ juju deploy ./kamailio_ubuntu-20.04-amd64.charm  --resource kamailio-image=kamailio/kamailio:5.3.3-stretch

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator --config ingress-class="public"

# Relate kamailio and ingress integrator
$ juju add-relation kamailio nginx-ingress-integrator

# Add an entry to /etc/hosts
$ echo "127.0.1.1 kamailio.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

The service is now available and interface binding can be adjusted by running:
```bash
juju config kamailio bind-address-port='udp:0.0.0.0:5060'
```

## Testing

```bash
# Clone the charm code
$ git clone https://github.com/gmeszaros/kamailio && cd kamailio

# Install python3-virtualenv
$ sudo apt update && sudo apt install -y python3-virtualenv

# Create a virtualenv for the charm code
$ virtualenv venv

# Activate the venv
$ source ./venv/bin/activate

# Install dependencies
$ pip install -r requirements-dev.txt

# Run the tests
$ ./run_tests
```
