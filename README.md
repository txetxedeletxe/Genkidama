<p align="center" style="font-size: 1.5em;"><strong>Share your energy with me!</strong></p>
<p align="center" style="font-size: 1em;"><strong>オラに元気をわけてくれ!</strong></p>

<!-- Banner image goes here -->
<p align="center">
  <img src="genkidama_blue_logo.svg" alt="Docker banner" style="max-width: 100%; width: 400px;" />
</p>

[![License: GPL v3](https://img.shields.io/github/license/txetxedeletxe/Genkidama?color=blue)](https://github.com/txetxedeletxe/Genkidama/blob/main/LICENSE)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python&logoColor=white)
[![Version](https://img.shields.io/github/v/release/txetxedeletxe/Genkidama?include_prereleases&color=orange)](https://github.com/txetxedeletxe/Genkidama/releases)
[![Deployments](https://img.shields.io/badge/deployments-view_history-success?logo=github)](https://github.com/txetxedeletxe/Genkidama/deployments)
## Genkidama
Genkidama is a pure-python library that: 
 1. Enables **developers** to write a wide variety of distributed programs (to scale compute, to manage a large fleet of computers, to troll your friends, ...) with very few extra lines of code on top of what a locally running script would require.
 2. Allows **system maintainers** to easily setup highly-heterogeneous computer clusters (comprised of any platform that can run python) in minutes.

## This README
This README gives a general description of the Genkidama library. The intent is to clarify the scope of the project and to get the end-user up and running using the library; therefore it is no in-depth tutorial or detailed API reference, for that have a look at the relevant resources (TODO write these resources).

Throughout the rest of this README some domain specific terminology is used, check out the [Glossary](#glossary) at the end of this readme for definitions of these terms.

## A Word of Caution
Genkidama allows arbitrary code execution in remote machines, as such it presents a major security pitfall if extreme caution is not exercised; in addition, at the current state Genkidama does not authenticate connections and runs all communications unencrypted, therefore this software should only ever be deployed in networks that are absolutely hermetic (such as LAN or even virtual LAN) with parties that are completely trusted.

Note that the risk is not only involved with the Donors that execute arbitrary code, but also with the Kaios that receive data produced by these Donors if they wrongly trust data and, for instance, unpickle malware infected objects or outright execute code packaged in this data.

## Quick Start
### Installation
At the time being (and as long as there is no significant architectural change) there is a single distribution of Genkidama, which is distributed as a [PyPI](https://pypi.org/project/genkidama/) source distribution (sdist) package:

`pip install genkidama`

This distribution is targeted for every usecase this library covers (and in particular for developers and system maintainers).

### Quick Setup
The first order of business is to establish a connection between a Kaio and a Donor, this can be accomplished in several ways depending on the network that connects both, but in the most simple and general case the Donor will run a server listening for a TCP connection in a given port (default port is [9000!](https://www.youtube.com/watch?v=SiMHTK15Pik)) and a Kaio client will connect to it therefore establishing a TCP connection. 

Note that the client and server roles have no fundamental relation to the Kaio and Donor roles, the first set of roles (client/server) only determines how the connection is established (who listens vs who calls), whereas the second set of roles (Kaio/Donor) determines the protocol and the dynamics of the session (who makes requests vs who executes requests); it is therefore entirely possible to have the Kaio act as the server and the Donor as the client, which in fact will be interesting in some cases where the Donor is behind a firewall.

In any case, and for the sake of brevity, in the following we stick to the standard client-Kaio and server-Donor setup.

#### Donor Server Setup
With genkidama installed, simply run in a shell:

`genkidama <bind_address>`

where `<bind_address>` is the IP address* to which you want to bind the server socket, for example `localhost` if you want to use/test the library locally (recommended), or `192.168.X.XXX` if you want to connect from a client in the same LAN. You can also supply more arguments such as `-p PORT` for the server to listen in a specific port (instead of the default). Check out all the available arguments running `genkidama -h`.

This command is simply an alias for `python -m genkidama`, which you can also use if you prefer, and starts a server listening on the given `bind_address` and `PORT` immediately. By default the logging level is `INFO`, so you will mostly only see messages when Kaios connect and disconnect; change the log level with `--log-level LEVEL`.

*So far only IPv4 is supported through this interface.
#### Kaio Client Setup
To connect to a running Donor server as a Kaio client from a `python` script or interactive terminal/notebook, run the following

```python
from genkidama import connect_to_session

session = connect_to_session(donor_IP_address)
```

where `donor_IP_address` is a string with the IP address of the donor server. If the server is reachable, it will return a `GenkidamaSession` object which can be used to interact with the Donor and make execution requests. For instance, to run a simple echo example do

```python
proc = session.execute("print(input())")
proc.stdin.write("Hello World\n".encode())

proc.wait()

proc_output = proc.stdout.read().decode()
print(proc_output)
```

which should just print `Hello World` on your Kaio, however observe that this data was produced in the Donor as a consequence of the input data that the Kaio forwarded to the Donor in the first place, which finally forwards the produced data back to the Kaio (which is the same as the input data in this echo example).

## Glossary
* **Kaio:** Term to refer to the machine/system/software sending out requests to the Donors for execution and collecting the results of the executed processes.
* **Donor:** Term to refer to the machines receiving requests from one or more Kaios and doing the actual work.
