#!/bin/bash

#install mysql as backend db for Airflow
yum install -y mysql57-server
service mysqld start

#auto configure after install
mysql -u root <<-EOF
CREATE DATABASE airflow;
UPDATE mysql.user SET authentication_string=PASSWORD('Welcome123!') WHERE User='root';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.db WHERE Db='test' OR Db='test_%';
FLUSH PRIVILEGES;
EOF

#remove default config and add required parameter explicit_defaults_for_timestamp
rm /etc/my.cnf

cat << 'EOF' >> /etc/my.cnf
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0
# Settings user and group are ignored when systemd is used.
# If you need to run mysqld under a different user or group,
# customize your systemd unit file for mysqld according to the
# instructions in http://fedoraproject.org/wiki/Systemd

explicit_defaults_for_timestamp = 1
[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
EOF

#stop and restart mysql for changes to take effect
service mysqld stop
yum install -y mysql-devel
service mysqld start

#necessary env variable before install airflow
export SLUGIFY_USES_TEXT_UNIDECODE=yes
pip3 install apache-airflow
pip3 install apache-airflow[celery]
pip3 install apache-airflow[slack]

#install impyla and other packages needed if we want to query bdp
pip3 install --no-deps impyla
pip3 install --no-deps git+https://github.com/snowch/thrift_sasl
pip3 install --no-deps pure-sasl

#pip install a number of packages from DS airflow instance
pip3 install pymysql configparser googleads pandas numpy flower bitarray thriftpy datadog mysqlclient adal alabaster alembic amqp analytics-python appdirs atlasclient attrs aws-xray-sdk awscli azure Babel bcrypt billiard 
pip3 install bleach boto boto3 botocore bz2file cached-property cachetools celery certifi cffi chardet click cloudant colorama configparser cookies croniter cryptography cx-Oracle cymem cytoolz datadog decorator defusedxml 
pip3 install dill docker docker-pycreds docopt docutils ecdsa elasticsearch elasticsearch-dsl entrypoints enum34 fastavro Flask freezegun funcsigs future futures gitdb2 GitPython google-api-core google-api-python-client
pip3 install google-auth google-auth-httplib2 google-cloud-bigquery google-cloud-bigtable google-cloud-container google-cloud-core google-cloud-spanner google-resumable-media googleads googleapis-common-protos grpc-google-iam-v1
pip3 install grpcio grpcio-gcp gunicorn hdfs hive-thrift-py hmsclient html5lib httplib2 idna ijson imagesize inflection ipaddress iso8601 isodate itsdangerous JayDeBeApi Jinja2 jira jmespath json-merge-patch jsondiff jsonpickle 
pip3 install keyring kombu kubernetes ldap3 lockfile lxml Mako Markdown MarkupSafe mock mongomock monotonic moto msgpack msgpack-numpy msrest msrestazure multi-key-dict murmurhash mysql-connector-python mysqlclient nltk nose 
pip3 install nose-ignore-docstring nose-timer ntlm-auth numpy oauth2client oauthlib ordereddict packaging pandas-gbq parameterized paramiko pathlib pathlib2 pbr pendulum pinotdb plac preshed protobuf psutil pyaml pyasn1 
pip3 install pyasn1-modules pycparser pycryptodome pycryptodomex pydata-google-auth pydruid Pygments PyHive PyJWT pykerberos pymongo pymssql PyNaCl pyOpenSSL pyparsing pysftp PySmbClient PySocks python-daemon python-http-client 
pip3 install python-jenkins python-jose python-editor 
pip3 install python-nvd3 python-openid python-slugify pytz pytzdata pywinrm PyYAML qds-sdk redis rednose regex requests requests-futures requests-kerberos requests-mock
pip3 install requests-ntlm requests-oauthlib requests-toolbelt responses rsa s3transfer sasl scandir scikit-learn SecretStorage sendgrid sentinels setproctitle setuptools simple-salesforce simplejson singledispatch 
pip3 install six sklearn slackclient smart-open smmap2 snakebite snowballstemmer 
pip3 install snowflake-connector-python snowflake-sqlalchemy spacy Sphinx 
pip3 install sphinx-argparse sphinx-PyPi-upload sphinx-rtd-theme sphinxcontrib-httpdomain 
pip3 install sphinxcontrib-websupport SQLAlchemy sshtunnel suds-jurko tabulate 
pip3 install tenacity termstyle text-unidecode thinc toolz tornado tqdm typing tzlocal 
pip3 install ujson unicodecsv Unidecode uritemplate urllib3 vertica-python vine webencodings 
pip3 install websocket-client Werkzeug wheel wrapt WTForms xmltodict zdesk zeep zope.deprecation Pillow beautifulsoup4 django boxsdk


#initialize the airflow db 
mkdir /opt/shared
chmod 777 /opt/shared
export AIRFLOW_HOME=/opt/shared/airflow
airflow initdb

#change the configuration to local executor and mysql DB
cd /opt/shared/airflow
rm ./airflow.cfg
cat << 'EOF' >> airflow.cfg
[core]
# The home folder for airflow, default is ~/airflow
airflow_home = /opt/shared/airflow

# The folder where your airflow pipelines live, most likely a
# subfolder in a code repository
# This path must be absolute
dags_folder = /opt/shared/airflow/dags

# The folder where airflow should store its log files
# This path must be absolute
base_log_folder = /opt/shared/airflow/logs

# Airflow can store logs remotely in AWS S3, Google Cloud Storage or Elastic Search.
# Users must supply an Airflow connection id that provides access to the storage
# location. If remote_logging is set to true, see UPDATING.md for additional
# configuration requirements.
remote_logging = True
remote_log_conn_id = aws_default
remote_base_log_folder = s3://roku-dea-external/ds_airflow_logs/
encrypt_s3_logs = False

# Logging level
logging_level = INFO
fab_logging_level = WARN

# Logging class
# Specify the class that will specify the logging configuration
# This class has to be on the python classpath
# logging_config_class = my.path.default_local_settings.LOGGING_CONFIG
logging_config_class =

# Log format
log_format = [%%(asctime)s] {%%(filename)s:%%(lineno)d} %%(levelname)s - %%(message)s
simple_log_format = %%(asctime)s %%(levelname)s - %%(message)s

# Log filename format
log_filename_template = {{ ti.dag_id }}/{{ ti.task_id }}/{{ ts }}/{{ try_number }}.log
log_processor_filename_template = {{ filename }}.log
dag_processor_manager_log_location = /opt/shared/airflow/logs/dag_processor_manager/dag_processor_manager.log

# Hostname by providing a path to a callable, which will resolve the hostname
hostname_callable = socket:getfqdn

# Default timezone in case supplied date times are naive
# can be utc (default), system, or any IANA timezone string (e.g. Europe/Amsterdam)
default_timezone = utc

# The executor class that airflow should use. Choices include
# SequentialExecutor, LocalExecutor, CeleryExecutor, DaskExecutor, KubernetesExecutor
executor = LocalExecutor

# The SqlAlchemy connection string to the metadata database.
# SqlAlchemy supports many different database engine, more information
# their website
sql_alchemy_conn = mysql://root:Welcome123!@localhost:3306/airflow

# The encoding for the databases
sql_engine_encoding = utf-8

# If SqlAlchemy should pool database connections.
sql_alchemy_pool_enabled = True

# The SqlAlchemy pool size is the maximum number of database connections
# in the pool. 0 indicates no limit.
sql_alchemy_pool_size = 5

# The SqlAlchemy pool recycle is the number of seconds a connection
# can be idle in the pool before it is invalidated. This config does
# not apply to sqlite. If the number of DB connections is ever exceeded,
# a lower config value will allow the system to recover faster.
sql_alchemy_pool_recycle = 1800

# How many seconds to retry re-establishing a DB connection after
# disconnects. Setting this to 0 disables retries.
sql_alchemy_reconnect_timeout = 300

# The amount of parallelism as a setting to the executor. This defines
# the max number of task instances that should run simultaneously
# on this airflow installation
parallelism = 32

# The number of task instances allowed to run concurrently by the scheduler
dag_concurrency = 16

# Are DAGs paused by default at creation
dags_are_paused_at_creation = True

# When not using pools, tasks are run in the default pool,
# whose size is guided by this config element
non_pooled_task_slot_count = 128

# The maximum number of active DAG runs per DAG
max_active_runs_per_dag = 16

# Whether to load the examples that ship with Airflow. It's good to
# get started, but you probably want to set this to False in a production
# environment
load_examples = False

# Where your Airflow plugins are stored
plugins_folder = /opt/shared/airflow/plugins

# Secret key to save connection passwords in the db
fernet_key = rWgv__REDACTED__l85zR0=    # TODO: Replace with actual Fernet key

# Whether to disable pickling dags
donot_pickle = False

# How long before timing out a python file import while filling the DagBag
dagbag_import_timeout = 30

# The class to use for running task instances in a subprocess
task_runner = BashTaskRunner

# If set, tasks without a `run_as_user` argument will be run with this user
# Can be used to de-elevate a sudo user running Airflow when executing tasks
default_impersonation =

# What security module to use (for example kerberos):
security =

# If set to False enables some unsecure features like Charts and Ad Hoc Queries.
# In 2.0 will default to True.
secure_mode = False

# Turn unit test mode on (overwrites many configuration options with test
# values at runtime)
unit_test_mode = False

# Name of handler to read task instance logs.
# Default to use task handler.
task_log_reader = task

# Whether to enable pickling for xcom (note that this is insecure and allows for
# RCE exploits). This will be deprecated in Airflow 2.0 (be forced to False).
enable_xcom_pickling = True

# When a task is killed forcefully, this is the amount of time in seconds that
# it has to cleanup after it is sent a SIGTERM, before it is SIGKILLED
killed_task_cleanup_time = 60

# Whether to override params with dag_run.conf. If you pass some key-value pairs through `airflow backfill -c` or
# `airflow trigger_dag -c`, the key-value pairs will override the existing ones in params.
dag_run_conf_overrides_params = False

# Worker initialisation check to validate Metadata Database connection
worker_precheck = False

[cli]
# In what way should the cli access the API. The LocalClient will use the
# database directly, while the json_client will use the api running on the
# webserver
api_client = airflow.api.client.local_client

# If you set web_server_url_prefix, do NOT forget to append it here, ex:
# endpoint_url = http://localhost:8080/myroot
# So api will look like: http://localhost:8080/myroot/api/experimental/...
endpoint_url = http://localhost:8080

[api]
# How to authenticate users of the API
auth_backend = airflow.api.auth.backend.default

[lineage]
# what lineage backend to use
backend =

[atlas]
sasl_enabled = False
host =
port = 21000
username =
password =

[operators]
# The default owner assigned to each new operator, unless
# provided explicitly or passed via `default_args`
default_owner = Airflow
default_cpus = 1
default_ram = 512
default_disk = 512
default_gpus = 0

[hive]
# Default mapreduce queue for HiveOperator tasks
default_hive_mapred_queue =

[webserver]
# The base url of your website as airflow cannot guess what domain or
# cname you are using. This is used in automated emails that
# airflow sends to point links to the right web server
base_url = http://localhost:8080

# The ip specified when starting the web server
web_server_host = 0.0.0.0

# The port on which to run the web server
web_server_port = 8080

# Paths to the SSL certificate and key for the web server. When both are
# provided SSL will be enabled. This does not change the web server port.
web_server_ssl_cert =
web_server_ssl_key =

# Number of seconds the webserver waits before killing gunicorn master that doesn't respond
web_server_master_timeout = 120

# Number of seconds the gunicorn webserver waits before timing out on a worker
web_server_worker_timeout = 120

# Number of workers to refresh at a time. When set to 0, worker refresh is
# disabled. When nonzero, airflow periodically refreshes webserver workers by
# bringing up new ones and killing old ones.
worker_refresh_batch_size = 1

# Number of seconds to wait before refreshing a batch of workers.
worker_refresh_interval = 30

# Secret key used to run your flask app
secret_key = temporary_key

# Number of workers to run the Gunicorn web server
workers = 4

# The worker class gunicorn should use. Choices include
# sync (default), eventlet, gevent
worker_class = sync

# Log files for the gunicorn webserver. '-' means log to stderr.
access_logfile = -
error_logfile = -

# Expose the configuration file in the web server
# This is only applicable for the flask-admin based web UI (non FAB-based).
# In the FAB-based web UI with RBAC feature,
# access to configuration is controlled by role permissions.
expose_config = False

# Set to true to turn on authentication:
# https://airflow.apache.org/security.html#web-authentication
authenticate = False

# Filter the list of dags by owner name (requires authentication to be enabled)
filter_by_owner = False

# Filtering mode. Choices include user (default) and ldapgroup.
# Ldap group filtering requires using the ldap backend
#
# Note that the ldap server needs the memberOf overlay to be set up
# in order to user the ldapgroup mode.
owner_mode = user

# Default DAG view.  Valid values are:
# tree, graph, duration, gantt, landing_times
dag_default_view = tree

# Default DAG orientation. Valid values are:
# LR (Left->Right), TB (Top->Bottom), RL (Right->Left), BT (Bottom->Top)
dag_orientation = LR

# Puts the webserver in demonstration mode; blurs the names of Operators for
# privacy.
demo_mode = False

# The amount of time (in secs) webserver will wait for initial handshake
# while fetching logs from other worker machine
log_fetch_timeout_sec = 5

# By default, the webserver shows paused DAGs. Flip this to hide paused
# DAGs by default
hide_paused_dags_by_default = False

# Consistent page size across all listing views in the UI
page_size = 100

# Use FAB-based webserver with RBAC feature
rbac = False

# Define the color of navigation bar
navbar_color = #007A87

# Default dagrun to show in UI
default_dag_run_display_number = 25

# Enable werkzeug `ProxyFix` middleware
enable_proxy_fix = False


[email]
email_backend = airflow.utils.email.send_email_smtp


[smtp]
# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an
# smtp server here
smtp_host = hq-vmonitor.corp.asnyder
smtp_starttls = False
smtp_ssl = False
# Uncomment and set the user/pass settings if you want to use SMTP AUTH
# smtp_user = USER
# smtp_password = PW
smtp_port = 25
smtp_mail_from = redacted@email.com


[celery]
# This section only applies if you are using the CeleryExecutor in
# [core] section above

# The app name that will be used by celery
celery_app_name = airflow.executors.celery_executor

# The concurrency that will be used when starting workers with the
# airflow worker command. This defines the number of task instances that
# a worker will take, so size up your workers based on the resources on
# your worker box and the nature of your tasks
worker_concurrency = 16

# When you start an airflow worker, airflow starts a tiny web server
# subprocess to serve the workers local log files to the airflow main
# web server, who then builds pages and sends them to users. This defines
# the port on which the logs are served. It needs to be unused, and open
# visible from the main web server to connect into the workers.
worker_log_server_port = 8793

# The Celery broker URL. Celery supports RabbitMQ, Redis and experimentally
# a sqlalchemy database. Refer to the Celery documentation for more
# information.
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-settings
broker_url = amqp://airflow:airflow@dsna-airflow-qts.corp.asnyder:5672/

# The Celery result_backend. When a job finishes, it needs to update the
# metadata of the job. Therefore it will post a message on a message bus,
# or insert it into a database (depending of the backend)
# This status is used by the scheduler to update the state of the task
# The use of a database is highly recommended
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-result-backend-settings
result_backend = db+mysql://airflow_worker:airflow@dsna-airflow-qts.corp.asnyder:3306/airflow

# Celery Flower is a sweet UI for Celery. Airflow has a shortcut to start
# it `airflow flower`. This defines the IP that Celery Flower runs on
flower_host = 0.0.0.0

# The root URL for Flower
# Ex: flower_url_prefix = /flower
flower_url_prefix =

# This defines the port that Celery Flower runs on
flower_port = 5555

# Securing Flower with Basic Authentication
# Accepts user:password pairs separated by a comma
# Example: flower_basic_auth = user1:password1,user2:password2
flower_basic_auth =

# Default queue that tasks get assigned to and that worker listen on.
default_queue = default

# Import path for celery configuration options
celery_config_options = airflow.config_templates.default_celery.DEFAULT_CELERY_CONFIG

# In case of using SSL
ssl_active = False
ssl_key =
ssl_cert =
ssl_cacert =

[celery_broker_transport_options]
# This section is for specifying options which can be passed to the
# underlying celery broker transport.  See:
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_transport_options

# The visibility timeout defines the number of seconds to wait for the worker
# to acknowledge the task before the message is redelivered to another worker.
# Make sure to increase the visibility timeout to match the time of the longest
# ETA you're planning to use.
#
# visibility_timeout is only supported for Redis and SQS celery brokers.
# See:
#   http://docs.celeryproject.org/en/master/userguide/configuration.html#std:setting-broker_transport_options
#
#visibility_timeout = 21600

[dask]
# This section only applies if you are using the DaskExecutor in
# [core] section above

# The IP address and port of the Dask cluster's scheduler.
cluster_address = 127.0.0.1:8786
# TLS/ SSL settings to access a secured Dask scheduler.
tls_ca =
tls_cert =
tls_key =


[scheduler]
# Task instances listen for external kill signal (when you clear tasks
# from the CLI or the UI), this defines the frequency at which they should
# listen (in seconds).
job_heartbeat_sec = 5

# The scheduler constantly tries to trigger new tasks (look at the
# scheduler section in the docs for more information). This defines
# how often the scheduler should run (in seconds).
scheduler_heartbeat_sec = 5

# after how much time should the scheduler terminate in seconds
# -1 indicates to run continuously (see also num_runs)
run_duration = -1

# after how much time (seconds) a new DAGs should be picked up from the filesystem
min_file_process_interval = 0

# How often (in seconds) to scan the DAGs directory for new files. Default to 5 minutes.
dag_dir_list_interval = 300

# How often should stats be printed to the logs
print_stats_interval = 30

# If the last scheduler heartbeat happened more than scheduler_health_check_threshold ago (in seconds),
# scheduler is considered unhealthy.
# This is used by the health check in the /health endpoint
scheduler_health_check_threshold = 30

child_process_log_directory = /opt/shared/airflow/logs/scheduler

# Local task jobs periodically heartbeat to the DB. If the job has
# not heartbeat in this many seconds, the scheduler will mark the
# associated task instance as failed and will re-schedule the task.
scheduler_zombie_task_threshold = 300

# Turn off scheduler catchup by setting this to False.
# Default behavior is unchanged and
# Command Line Backfills still work, but the scheduler
# will not do scheduler catchup if this is False,
# however it can be set on a per DAG basis in the
# DAG definition (catchup)
catchup_by_default = True

# This changes the batch size of queries in the scheduling main loop.
# If this is too high, SQL query performance may be impacted by one
# or more of the following:
#  - reversion to full table scan
#  - complexity of query predicate
#  - excessive locking
#
# Additionally, you may hit the maximum allowable query length for your db.
#
# Set this to 0 for no limit (not advised)
max_tis_per_query = 512

# Statsd (https://github.com/etsy/statsd) integration settings
statsd_on = False
statsd_host = localhost
statsd_port = 8125
statsd_prefix = airflow

# The scheduler can run multiple threads in parallel to schedule dags.
# This defines how many threads will run.
max_threads = 2

authenticate = False

# Turn off scheduler use of cron intervals by setting this to False.
# DAGs submitted manually in the web UI or with trigger_dag will still run.
use_job_schedule = True

[ldap]
# set this to ldaps://<your.ldap.server>:<port>
uri =
user_filter = objectClass=*
user_name_attr = uid
group_member_attr = memberOf
superuser_filter =
data_profiler_filter =
bind_user = cn=Manager,dc=example,dc=com
bind_password = insecure
basedn = dc=example,dc=com
cacert = /etc/ca/ldap_ca.crt
search_scope = LEVEL

[mesos]
# Mesos master address which MesosExecutor will connect to.
master = localhost:5050

# The framework name which Airflow scheduler will register itself as on mesos
framework_name = Airflow

# Number of cpu cores required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
task_cpu = 1

# Memory in MB required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
task_memory = 256

# Enable framework checkpointing for mesos
# See http://mesos.apache.org/documentation/latest/slave-recovery/
checkpoint = False

# Failover timeout in milliseconds.
# When checkpointing is enabled and this option is set, Mesos waits
# until the configured timeout for
# the MesosExecutor framework to re-register after a failover. Mesos
# shuts down running tasks if the
# MesosExecutor framework fails to re-register within this timeframe.
# failover_timeout = 604800

# Enable framework authentication for mesos
# See http://mesos.apache.org/documentation/latest/configuration/
authenticate = False

# Mesos credentials, if authentication is enabled
# default_principal = admin
# default_secret = admin

# Optional Docker Image to run on slave before running the command
# This image should be accessible from mesos slave i.e mesos slave
# should be able to pull this docker image before executing the command.
# docker_image_slave = puckel/docker-airflow

[kerberos]
ccache = /tmp/airflow_krb5_ccache
# gets augmented with fqdn
principal = airflow
reinit_frequency = 3600
kinit_path = kinit
keytab = airflow.keytab


[github_enterprise]
api_rev = v3

[admin]
# UI to hide sensitive variable fields when set to True
hide_sensitive_variable_fields = True

[elasticsearch]
elasticsearch_host =
elasticsearch_log_id_template = {dag_id}-{task_id}-{execution_date}-{try_number}
elasticsearch_end_of_log_mark = end_of_log

[kubernetes]
# The repository, tag and imagePullPolicy of the Kubernetes Image for the Worker to Run
worker_container_repository =
worker_container_tag =
worker_container_image_pull_policy = IfNotPresent

# If True (default), worker pods will be deleted upon termination
delete_worker_pods = True

# The Kubernetes namespace where airflow workers should be created. Defaults to `default`
namespace = default

# The name of the Kubernetes ConfigMap Containing the Airflow Configuration (this file)
airflow_configmap =

# For docker image already contains DAGs, this is set to `True`, and the worker will search for dags in dags_folder,
# otherwise use git sync or dags volume claim to mount DAGs
dags_in_image = False

# For either git sync or volume mounted DAGs, the worker will look in this subpath for DAGs
dags_volume_subpath =

# For DAGs mounted via a volume claim (mutually exclusive with git-sync and host path)
dags_volume_claim =

# For volume mounted logs, the worker will look in this subpath for logs
logs_volume_subpath =

# A shared volume claim for the logs
logs_volume_claim =

# For DAGs mounted via a hostPath volume (mutually exclusive with volume claim and git-sync)
# Useful in local environment, discouraged in production
dags_volume_host =

# A hostPath volume for the logs
# Useful in local environment, discouraged in production
logs_volume_host =

# Git credentials and repository for DAGs mounted via Git (mutually exclusive with volume claim)
git_repo =
git_branch =
git_user =
git_password =
git_subpath =
git_sync_root = /git
git_sync_dest = repo
# Mount point of the volume if git-sync is being used.
# i.e. /opt/shared/airflow/dags
git_dags_folder_mount_point =

# For cloning DAGs from git repositories into volumes: https://github.com/kubernetes/git-sync
git_sync_container_repository = gcr.io/google-containers/git-sync-amd64
git_sync_container_tag = v2.0.5
git_sync_init_container_name = git-sync-clone

# The name of the Kubernetes service account to be associated with airflow workers, if any.
# Service accounts are required for workers that require access to secrets or cluster resources.
# See the Kubernetes RBAC documentation for more:
#   https://kubernetes.io/docs/admin/authorization/rbac/
worker_service_account_name =

# Any image pull secrets to be given to worker pods, If more than one secret is
# required, provide a comma separated list: secret_a,secret_b
image_pull_secrets =

# GCP Service Account Keys to be provided to tasks run on Kubernetes Executors
# Should be supplied in the format: key-name-1:key-path-1,key-name-2:key-path-2
gcp_service_account_keys =

# Use the service account kubernetes gives to pods to connect to kubernetes cluster.
# It's intended for clients that expect to be running inside a pod running on kubernetes.
# It will raise an exception if called from a process not running in a kubernetes environment.
in_cluster = True

# Affinity configuration as a single line formatted JSON object.
# See the affinity model for top-level key names (e.g. `nodeAffinity`, etc.):
#   https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.12/#affinity-v1-core
affinity =

# A list of toleration objects as a single line formatted JSON array
# See:
#   https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.12/#toleration-v1-core
tolerations =

[kubernetes_node_selectors]
# The Key-value pairs to be given to worker pods.
# The worker pods will be scheduled to the nodes of the specified key-value pairs.
# Should be supplied in the format: key = value

[kubernetes_secrets]
# The scheduler mounts the following secrets into your workers as they are launched by the
# scheduler. You may define as many secrets as needed and the kubernetes launcher will parse the
# defined secrets and mount them as secret environment variables in the launched workers.
# Secrets in this section are defined as follows
#     <environment_variable_mount> = <kubernetes_secret_object>:<kubernetes_secret_key>
#
# For example if you wanted to mount a kubernetes secret key named `postgres_password` from the
# kubernetes secret object `airflow-secret` as the environment variable `POSTGRES_PASSWORD` into
# your workers you would follow the following format:
#     POSTGRES_PASSWORD = airflow-secret:postgres_credentials
#
# Additionally you may override worker airflow settings with the AIRFLOW__<SECTION>__<KEY>
# formatting as supported by airflow normally.
EOF

#reinitialize the DB
airflow initdb
#web server if there is a public facing IP we can access at port 5000
nohup airflow webserver -p 8080 & 

nohup airflow scheduler & 
