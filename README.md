[![Build Status](https://travis-ci.org/Giuseppe1992/CloudMeasurement.svg?branch=master)](https://travis-ci.org/Giuseppe1992/CloudMeasurement)

# CloudMeasurement
CloudMeasurement is a CLI that create multiple experiments in different Cloud infrastructures
(for now just AWS, but Google Cloud is planned ).

# Installation

CloudMeasurement works with Mac OSX and Ubuntu (18.04, 20.04) the installation is straight forward, you have to clone 
the repository, install the requirements and then the tool.

#### Update the system and clone the repository (Ubuntu OS)
```bash
vagrant@ubuntu-bionic:~$ sudo apt update && sudo apt install awscli git python3-pip -y

vagrant@ubuntu-bionic:~$ git clone https://github.com/Giuseppe1992/CloudMeasurement.git


```

#### Install the dependencies and the software
```bash
vagrant@ubuntu-bionic:~$ cd CloudMeasurement/
vagrant@ubuntu-bionic:~/CloudMeasurement$ 

vagrant@ubuntu-bionic:~/CloudMeasurement$ pip3 install -r requirements.txt 

vagrant@ubuntu-bionic:~/CloudMeasurement$ sudo python3 setup.py install
```

#### check the installation

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm 
No operation
```

# Configure the Environment

#### Configure CloudMeasurement
In the configuration the user has to configure the AWS Access key ID and Secret Access Key, if it is using AWS for the
first time.

In the last line, the user has to specify the path of the private key that will be used to connect with the virtual
 instances in the experiments.
  
Make sure to give a correct path, by default is pointing the default key from ~/.ssh
 directory

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm --init
AWS Access Key ID [None]: ******************
AWS Secret Access Key [None]: ********************************
Default region name [None]: eu-central-1
Default output format [None]: json
Insert the default private key [default: /home/vagrant/.ssh/id_rsa] : 

```

#### View the configuration

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm --configuration
+-------------------------------------------------------+---------------------------------+---------------------------+
| DB_PATH                                               | UTILS_PATH                      | PRIVATE_KEY_PATH          |
+=======================================================+=================================+===========================+
| /home/vagrant/.CloudMeasurement/CloudMeasurementDB.db | /home/vagrant/.CloudMeasurement | /home/vagrant/.ssh/id_rsa |
+-------------------------------------------------------+---------------------------------+---------------------------+

```

#### Run the helper

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -h
Usage: cm [options]
(type cm -h for details)

The utility creates experiments  from the command line. It can create
experiments, list them, and manage.

Options:
  -h, --help            show this help message and exit
  -c CREATE_EXPERIMENT, --create_experiment=CREATE_EXPERIMENT
                        possible experiments:  multiregionalTrace
  --init                initialize the environment
  --configuration       initialize the environment
  --purge               purge all the active experiments
  -e, --ls_experiments  list the experiments
...

```

# Run Experiments

## Multiregional Traceroute

## Regional Traceroute

### Create your first experiment

#### Multiregional Trace creation

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -c multiregional --regions="eu-central-1,eu-west-2"

```

#### Regional Trace creation

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -c regional --regions="eu-central-1"

```

#### List the created Experiments

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -e

```

#### List the created Instances

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -i

```

#### Start your experiment

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -s EXPERIMENT_ID

```

#### Retrieve all the data of your experiment

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm --retrieve_data EXPERIMENT_ID

```

#### Save the data in a specified path

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm --save_data EXPERIMENT_ID,LOCAL_PATH

```

#### Delete an experiment

```bash
vagrant@ubuntu-bionic:~/CloudMeasurement$ cm -d EXPERIMENT_ID

```

