# Requirements

* Install python3

* Install paramiko module<br>
	pip install paramiko

* Install scp module<br>
	pip install scp

# About

Script purpose is to automate the process of license renewal for the vendors from the list [Synopsys, Cadence, Amiq, Ansys, Cliosoft, Mentor, Real-Intent].

Below are the steps

1. Connect to the License Server IP through SSH (function "connect_to_license_server")
2. Run the following commands on the License Server IP to get lmstat output (function "get_current_license")<br>
sudo su edatools <br>
cd ~<br>
source ~/{vendor_name}.setup<br>
lmstat -c {vendor_ssh_port}@license<br>
3. Parse lmstat output and get the current license path (function "get_vendor_lic_location")
4. Get the current license content (function "get_current_vendor_lic_output")
5. Parse current license content and get current vendor "host ID" (function "get_vendor_host_id")
6. Parse current license content and get current vendor "path" (function "get_vendor_path")
7. Open new license file and set host ID and path from the previous step(function "set_hostid_and_path")
8. Upload new license file to the License server through SCP (function "upload_new_lic_file")
9. Detach the old license file using lmdown command (function "remove_old_lic_file")
10. Prepare the license string for uploading (function "prep_lmgrd_lic_string")
11. Set new license using lmgrd command (function "set_new_license")
12. Get the log file output (function "check_log_file")
13. Verify the new license integrity using sssverify commad (function "verify_license")

	* To print each step output, set "debug_run" variable to True
	
# How to run

1. Set variables(optional)

	Below are the preset defaults

	new_local_lic_path = './new_lic/' #this is a local script path where the new license file should exist (before we modify hostid and path)

	new_remote_lic_path = f'/data/tools/{vendor_name}/' # this is a remote path on the license server where new license will be uploaded
	
	log_path = f'/data/tools/{vendor_name}/lic_admin/log/log.log' #this is a remote path on the license server for the log

	debug_run = True # False = limited log, True = extensive logging


2. Put the new license file/s into ./new_lic inside the local directory from where the script runs
	Make sure to remove any other files from this directory (new_lic) if exists.

3. Run the script 

	From Windows: 
		Powershell, terminals
			python.exe .\<<path to main.py directory>>\main.py
		CMD
			python.exe <<path to main.py directory>>\main.py
	
	From Linux 
		python3 /mnt/c/DATA/Scripts/FIVERR/Lic_update_by_efratshp/main.py

	Script will prompt for the following input
		Enter License Server IP
		Enter username
		Enter password
		Enter vendor name from the list [Synopsys, Cadence, Amiq, Ansys, Cliosoft, Mentor, Real-Intent]
	

* !!! To be removed  !!!
	1. Temp vars for testing

		lic_srv_ip = 'x.x.x.x'
		vendor_ssh_port = 22
		user = 'test'
		password = 'test'
		vendor_name = 'Cadence'

	2. lmstat var from Efrat