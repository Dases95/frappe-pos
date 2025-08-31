# Installing and Setting up Frappe Framework with PostgreSQL on WSL Ubuntu-20.04

In this guide, we will walk through the steps to install and set up the Frappe framework with PostgreSQL on Windows Subsystem for Linux (WSL). Frappe is a full-stack web application framework used for rapid development of web applications and ERP systems.

## Prerequisites

Before you begin, make sure you have the following prerequisites:

1. **Windows 10 or later**: Ensure that you have a Windows version that supports WSL.
2. **WSL installed**: Set up WSL on your system. You can follow the instructions [here](https://docs.microsoft.com/en-us/windows/wsl/install).
3. **Ubuntu WSL distribution**: We'll be using the Ubuntu-20.04 distribution in WSL for the installation. If you haven't installed it yet, you can get it from the Microsoft Store or follow the instructions [here](https://docs.microsoft.com/en-us/windows/wsl/install#step-6---install-your-linux-distribution-of-choice).

## Step 1: Update Ubuntu

Open a terminal in Ubuntu WSL and update the package lists to ensure you have the latest package information.

```bash
sudo apt update
sudo apt upgrade
```

## Step 2: Install Prerequisites

Frappe and Pyenv require some additional packages to be installed. Let's install them.

```bash
sudo apt install git redis-server build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```


Install Pyenv to set up required python 3.10 version

```bash
curl https://pyenv.run | bash
```

You should have an output ending like following, don't forget to follow the instructions

```bash
# Load pyenv automatically by appending
# the following to
~/.bash_profile if it exists, otherwise ~/.profile (for login shells)
and ~/.bashrc (for interactive shells) :

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Restart your shell for the changes to take effect.

# Load pyenv-virtualenv automatically by adding
# the following to ~/.bashrc:

eval "$(pyenv virtualenv-init -)"
```

After downloading and executing the bash script of the pyenv, we will add some environment variables using the command:

```bash
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init --path)" && echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
```

Restart the Shell

```bash
exec $SHELL
```

Ensure Pyenv is successfully installed 

```bash
pyenv --version
```

Install python 3.10 with Pyenv

```bash
pyenv install 3.10
```

Configure python 3.10 as the default version

```bash
pyenv global 3.10
```

Install nvm

```bash
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash
```

Export environment variables

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
```

Install Node 18

```bash
nvm install 18
```

Ensure it is correctly installed

```bash
node -v
```

Install yarn using npm

```bash
npm install -g yarn
```

Install wkhtmltopdf

```bash
sudo apt-get install xvfb libfontconfig wkhtmltopdf
```


## Step 3: Install PostgreSQL

Frappe needs a database to store its data, and we'll use PostgreSQL for this purpose.

```bash
sudo apt install postgresql postgresql-contrib
```

Ensure PostgresQL is running

```bash
sudo service postgresql start
```

During the installation, PostgreSQL will create a new system user named "postgres." To access the PostgreSQL prompt, switch to the "postgres" user.

```bash
sudo su - postgres
```

Now, enter the PostgreSQL prompt by running:

```bash
psql
```

Within the PostgreSQL prompt, set a password for the default "postgres" user, and remember it !

```sql
\password postgres
```

Exit the PostgreSQL prompt by typing:

```sql
\q
```

Switch back to your normal user:

```bash
exit
```

## Step 4: Install Bench

Bench is a command-line utility used to manage Frappe applications. We'll install it using pip.

```bash
pip install frappe-bench
```

Confirm the bench installation by checking version

```bash
bench --version
```

## Step 5: Create a Bench

Now, let's create a new bench (Frappe application workspace).

```bash
bench init frappe-bench --frappe-branch version-15
```

This will create a new bench in the "frappe-bench" directory and install the required Frappe version 14.


## Step 6: Install Frappe Site

Create a new site for your Frappe application.

Navigate to the bench directory.

```bash
cd frappe-bench
```

```bash
bench new-site test.site --db-type postgres --set-default
```
You will be asked to input the postgres user password. Then an Admin password that will allow you to login to your created site.

This will create a new site with the specified name "test.site", and by using `--set-default` will designate this site as the current one in `currentsite.txt`. this name will be used to access your site.

## Step 7: Install Inventory App

Now that you have a Frappe site set up, you can install the custom inventory app.

### Option 1: Install from Local Directory

If you have the inventory app in your local directory, you can install it directly:

```bash
bench get-app inventory
```

### Option 2: Install from Git Repository

Install the inventory app from the GitHub repository:

```bash
bench get-app https://github.com/Dases95/frappe-pos
```

### Install the App on Your Site

After getting the app, install it on your site:

```bash
bench --site test.site install-app inventory
```

Replace `test.site` with your actual site name if different.

### Migrate the Database

Run database migrations to set up the inventory app's database schema:

```bash
bench --site test.site migrate
```

### Build Assets

Build the frontend assets for the inventory app:

```bash
bench build
```

### Setup Geographic Data (Optional)

This inventory app includes enhanced geographical features for Algeria. To set up the geographic data:

```bash
# Extract geography data from source files
bench inventory extract-geography

# Install geography data into your site
bench inventory install-geography
```

The inventory app is now installed and ready to use on your Frappe site. It includes features for managing customers with geographic data, wilayas (provinces), and communes (municipalities) specific to Algeria.

## Step 8: Disable firewall (this is needed to allow websocket connections from your browser).

Run the following command to disable the firewall in WSL:
```
sudo ufw disable
```

Then follow these instructions to add the redis socketio_port (default: 9000) to the firewall inbound rules in windows:
https://www.windowscentral.com/how-open-port-windows-firewall

Then get the ip address to add it to the hosts in the next step:
```
ip addr show eth0 | awk '/inet / {split($2, a, "/"); print a[1]}'
```

## Step 9: Add the site name to hosts.

Add the name of the created site to your hosts file by adding the following two lines:
```
{wsl ip address} test.site
127.0.0.1 test.site
```

This will match the 127.0.0.1 ip and the wsl ip with the test.site domain. So that you can access your site with that domain.

You can use a service that adds automatically the wsl ip address to your hosts. Here is the link to the service repo: https://github.com/shayne/go-wsl2-host

## Step 10: Start Frappe

Start the Frappe development server.

```bash
bench start
```

You should now be able to access your Frappe application by navigating to `http://test.site:8000` in your web browser. Remember to replace test.site with your site name.

Congratulations! You have successfully installed and set up Frappe framework with PostgreSQL on WSL.

Please note that this guide covers the basic setup for development purposes. In a production environment, additional security measures and configurations may be necessary.


### Common Issues

#### 1. 404 Page Not Found Error After Fresh Installation

Unless you didn't specify `--set-default` option while creating the new site, this issue typically occurs when the `currentsite.txt ` file does not exist yet. [reference](https://www.youtube.com/watch?v=kR1mk0yBKUE)
1. Create this file inside `sites` directory:
```bash
touch sites/currentsite.txt
```
2. Insert the name of your site in the created file, e.g `test.site`.
3. Stop and Start the Server.

#### 2. `yarn install` Raises `ERROR: [Errno 2] No such file or directory: 'install'`, while `bench init`.
This issue typically occurs due to missing or misconfigured dependencies.
1. Check Node.js and Yarn Installation:
```bash
node -v
yarn -v
```
2. Use the correct node version by set the default version of node to `v18.x.x`:
```bash
nvm alias default v18.x.x
```