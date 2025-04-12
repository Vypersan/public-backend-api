# BACKEND API.
This is the BACKEND API used by the Golden OX bot but changed to fit public bots. This exists to make the code less nested and offload slow(er) task(s) to another thread or process. 
While not necessary, this improves response time(s) for the bot by a second or more and lowers resource usage.
This should **NOT** be used for the public unless other bots start to depend on the data this program holds.


## Requirements before running [WINDOWS]:
- python 3.12 or ^.
- cmd (Command) or powershell access.
- An unused port that is not in the "well known" class and preferably in the registered class. (1024 to 4915)
- certificate files for your domain in .pem and .cert format. Those being certfile, keyfile and origin-ca.cert.  (This must match the domain of the server this is running on. Otherwise any program that interacts with this API might return a "validation" error due to domain name mismatch.)



## Requirements before running [LINUX]:
- python 3.12 or ^.
- python3-pip.
- CLI access.
- An unused port that is not in the "well known" class and preferably in the registered class. (1024 to 4915)
- certificate files for your domain in .pem format. Those being certfile, keyfile and origin-ca-cert.  (This must match the domain of the server this is running on. Otherwise any program that interacts with this API might return a "validation" error due to domain name mismatch.)

## Set up
1. Clone this repository
2. **Recommended**: create virtual environment and activate it
    - In the root directory, run `python -m venv venv`
    - While in root directory, you can run `call venv/Scripts/activate`
3. Pip install the required pip packages, using `pip install -r requirements.txt`
4. Put `conf.json` file in `Auth` folder.
    - Contact repository owner for this file
5. Ensure the database file (`database.db`) exists in root directory
    - Contact repository owner for this file
6. Ensure the certificate files (`certfile.pem, keyfile.pem, origin-ca-cert`) exists in root directory
 - Contact repository owner for this file or provide your own.

## How to run HTTPS:
1. Open command line interface.
2. decide on a port to use (As mentioned in the requirements for your platform.)
3. enter the following command: `uvicorn api:api --port <portnumber here> --host <host.ip.here (use 0.0.0.0 for global)> --ssl-keyfile=/path/to/keyfile.pem --ssl-certfile=/path/to/certfile.pem --ssl-ca-certs=/path/to/origin-ca.cert  <optional args>`

## How to run HTTP (No SSL)
1. Open command line interface.
2. decide on a port to use (As mentioned in the requirements for your platform.)
3. enter the following command: `uvicorn api:api --port <portnumber here> --host <host.ip.here (use 0.0.0.0 for global)> <optional args>`

## Additional arguments:
`--reload` : Runs the same server but reloads when any change is made in the file(s) and then restarts the server. **SHOULD NOT BE USED IN PRODUCTION OR LIVE.**

There are other arguments but we do not use that. You can read more [HERE](https://www.uvicorn.org/settings/)



## Documentation:
the documentation of this API can be found by using `<api-ip>/docs or <api-ip>/docsv2`.