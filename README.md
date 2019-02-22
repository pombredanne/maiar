# Maiar Packaging System

The Maiar Packaging System provides a generic framework for custom packages to be uploaded to a Google Cloud Storage
bucket (which then acts as the repository) and utilizing custom build/install scripts, can support any language or
type of install, assuming it can be started from a bash script.

### WARNING: This is alpha-quality software, and may have bugs, and should not be used for production or mission-critical workloads

NOTICE: Due to the fact that bash scripts can do anything in a system, it is strongly recommended to only use this
system for internally-created and maintained packages.

Also note that this currently only supports building on linux (generate_maiar_packages also works on Mac OSX), although
cross-platform support is planned in the future.

## Usage for Downloading/Building/Installing Packages

```
usage: maiar [-h] [--repository REPOSITORY] [--root-dir ROOT_DIR] [--dry-run]
             [--skip-gcs] [--project PROJECT] [--token TOKEN]
             {download,build,install,build_env,pip_env}
             [packages [packages ...]]

positional arguments:
  {download,build,install,build_env,pip_env}
                        Stage to process
  packages              Packages to process, or a file with a list of
                        requirements

optional arguments:
  -h, --help            show this help message and exit
  --repository REPOSITORY
                        GCS Repository to download from
  --root-dir ROOT_DIR   Root directory for packages to be downloaded to and
                        built from, default is: /opt/maiar/
  --dry-run             Show steps, but do not actually download/build/install
                        anything
  --skip-gcs            Do not access GCS, use only if package files are
                        already downloaded
  --project PROJECT     Google Cloud Storage project (only needed if
                        specifying credentials manually)
  --token TOKEN         Google Cloud Storage access token, optional if you are
                        already logged in locally (this can also be obtained
                        by running gcloud auth application-default print-access-token)
```

This command will perform the given stage (download/build/install) of the given packages, into the root dir specified
by --root-dir (default: /opt/maiar/). Optionally, specifying --dry-run will only print the steps that will be run.

Note that previous steps will be run, such that install will download, build, then install, while build will only
download and build.

In addition to specifying a list of packages, a file such as requirements.maiar can be specified, where the requirements
are as a list in this format:

```
# This file should be in the order the packages need to be installed

example-requirement==1.0.0
another-requirement==2.3.4
```

All packages on the command line or in the file should be specified as name==version, and comments starting with # are
allowed in a given requirements file.

The repository (Google Cloud Storage Bucket) that is used can be specified on the command line, or in a repository.maiar
file, where the bucket path (such as: gs://example-bucket/) is the only content in the file.

## Running in Docker Build

To use local Google Cloud credentials in a Docker build, you can add a build arg, for example:

```
docker build -t gcr.io/your-repository/container-name:tag \
    --build-arg ANY_OTHER_BUILD_ARG=value \
    --build-arg GCLOUD_TOKEN="$(gcloud auth application-default print-access-token)" \
    .
```

Then you can run maiar in the Dockerfile such as:

```
ARG GCLOUD_TOKEN
RUN maiar install requirements.maiar --token $GCLOUD_TOKEN --project $YOUR_PROJECT_NAME
```

## Creating new packages and uploading them to Google Cloud

```
usage: generate_maiar_packages [-h] [--repository REPOSITORY] [--dry-run]
                               [--project PROJECT] [--token TOKEN]
                               {build,push} package_directories
                               [package_directories ...]

positional arguments:
  {build,push}          Stage to process
  package_directories   Directory where package directories are found, or a
                        list of package directories

optional arguments:
  -h, --help            show this help message and exit
  --repository REPOSITORY
                        GCS Repository to upload to
  --dry-run             Show steps, but do not actually build/push anything
  --project PROJECT     Google Cloud Storage project (only needed if
                        specifying credentials manually)
  --token TOKEN         Google Cloud Storage access token, optional if you are
                        already logged in locally (this can also be obtained
                        by running gcloud auth application-default print-access-token)
```

This command will perform the given stage (build/push) of the given package directory (or directories), into the
repository specified by --repository or in a repository.maiar file.

Note that push does not run build, and building the necessary packages must be done first.

Each package directory should be in the format: package-name.version

And contain a script named one of: maiar.sh, maiar.bash, maiar.py or just maiar

This is the script that will be run as:
```
maiar.sh build
maiar.sh install
```
With $MAIAR_ROOT set to the root build and install directory.

This script should then run make or make install respectively, and will be run in the appropriate build subdirectory.

If the script needs to link a binary file, ${MAIAR_ROOT}/bin/ is the recommended location to do so, which should also
be added to $PATH in a Dockerfile or an install machine.

See the example_install_scripts folder for some example scripts which perform these actions.

In addition, it should have a DOWNLOADED_FROM or SOURCE_REPO documentation file indicating the package's source if it
ever needs to be rebuilt in the future.

Running the build command will automatically validate the name of each package folder, plus the existence of the
necessary install scripts and documentation files.
