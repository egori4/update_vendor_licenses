#!/usr/bin/python

import paramiko
import time
import getpass
from scp import SCPClient
import os
import sys



lic_srv_ip = input("Enter License Server IP:\r\n")

#check if lic_srv_ip is not empty and string
if not lic_srv_ip:
    print("License Server IP is empty. Enter License Server IP and try again")
    sys.exit(1) 

user = input("Enter username:\r\n")
if not user:
    print("Username is empty. Enter username and try again")
    sys.exit(1)
password = getpass.getpass('Enter password:\n')
if not password:
    print("Password is empty. Enter password and try again")
    sys.exit(1)


vendor_name = input("Enter vendor name from the list [Synopsys, Cadence, Amiq, Ansys, Cliosoft, Mentor, Real-Intent]:\r\n")
if vendor_name == "Synopsys":
    vendor_ssh_port = 27020
elif vendor_name == "Cadence":
    vendor_ssh_port = 5280 ### this is temporary, need to change to 27003
elif vendor_name == "Amiq (DVT)": 
    vendor_ssh_port = 27005
elif vendor_name == "Ansys (totem)":
    vendor_ssh_port = 1055
elif vendor_name == "Cliosoft (sos)":
    vendor_ssh_port = 27002
elif vendor_name == "Mentor":
    vendor_ssh_port = 1717
elif vendor_name == "Real-Intent":
    vendor_ssh_port = 27001

else:
    print("Invalid vendor name. Enter vendor name from the list and try again [Synopsys, Cadence, Amiq, Ansys, Cliosoft, Mentor, Real-Intent]:\r\n")
    exit()


### temp var for testing - to be removed later ###

# lic_srv_ip = '1.1.1.1'
# vendor_ssh_port = 22
# user = 'test'
# password = 'test'
# vendor_name = 'Cadence'

##########################

######### Variables ##############
new_local_lic_path = './new_lic/' #this is a local script path where the new license file should exist (before we modify hostid and path)
new_remote_lic_path = f'/data/tools/{vendor_name}/' #'/tmp/' # this is a remote path where the new license file will be copied to on the License Server
log_path = f'/data/tools/{vendor_name}/lic_admin/log/log.log' # !!!!!!! Validate path to the log file=
debug_run = True

class LicenseServer:
    def __init__(self, lic_srv_ip, new_local_lic_path, new_remote_lic_path,log_path, vendor_name,vendor_ssh_port, user, password,debug_run):
        self.lic_srv_ip = lic_srv_ip
        self.new_local_lic_path = new_local_lic_path
        self.new_remote_lic_path = new_remote_lic_path
        self.log_path = log_path
        self.vendor_name = vendor_name
        self.vendor_ssh_port = vendor_ssh_port
        self.user = user
        self.password = password
        self.debug_run = debug_run
        

    def connect_to_license_server(self):
        #Connect to the License Server

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print('='*50)
        print(f'Connecting to the Licese Server {self.lic_srv_ip}')
        print('='*50)
        
        ssh_client.connect(hostname=self.lic_srv_ip, port=self.vendor_ssh_port, username=self.user, password=self.password,
                            look_for_keys=False, allow_agent=False)

        return ssh_client


    def get_current_license(self,shell):
        #Get current license file from the License Server

        shell.send('sudo su edatools' + '\n')
        time.sleep(1)

        shell.send(password + '\n')
        time.sleep(1)

        shell.send('cd ~' + '\n') #change to home directory
        time.sleep(1)

        shell.send(f'source ~/{vendor_name}.setup' + '\n') #!!!!!!!!! Validate path to setup file
        time.sleep(1)


        shell.send(f'lmstat -c {vendor_ssh_port}@license' + '\n') #!!!!!!!!! Validate lmstat command output
        time.sleep(1)


        lmstat_output = shell.recv(10000)

        
        # !!!!!!!!!!!!!!!!! This is temporary, remove this var "lmstat_output_from_efrat" once the lmstat output is available
#         lmstat_output_from_efrat = """
        
# [edatools@license efrats]$ lmstat -c 27001@license
# lmstat - Copyright (c) 1989-2019 Flexera. All Rights Reserved.
# Flexible License Manager status on Sun 12/11/2022 18:07

# License server status: 27001@license
#     License file(s) on license: /data/tools/Real-Intent/license/license.20231123.MCDC.lic:/data/tools/Real-Intent/license/license.24112021.MCDC.Proteantecs.lic:/data/tools/Real-Intent/license/license.15022022.MCDC.Proteantecs.lic:

# license: license server UP (MASTER) v11.16.0

# Vendor daemon status (on license):

#     vlmd: UP v11.16.0
# dconcept: UP v11.16.3

# [edatools@license efrats]$
#         """

#         lmstat_output = lmstat_output + lmstat_output_from_efrat.encode() ###### Remove this line once the lmstat output is available

        if self.debug_run:
            print('='*50)
            print(f'Printing output for "sudo su edatools", "source ~/{vendor_name}.setup", and "lmstat -c {vendor_ssh_port}@license"' + '\r\n')
            print(lmstat_output.decode())
            print('='*50)

        return lmstat_output

    def get_vendor_lic_location(self, lmstat_output):
        #get the current license file location
        if self.debug_run:
            print('='*50)
            print(f'Getting file location of the current {vendor_name} license file' + '\r\n')

        lines = lmstat_output.decode().split('\n')
        for line in lines:
            if line.startswith('    License file(s) on license'):
                vendor_lic_file = line.split(' ')[8]
                vendor_lic_file = vendor_lic_file.split(':')[0]
        
        if self.debug_run:
            print(f'Existing license file location: {vendor_lic_file}')
            print('='*50)
        return vendor_lic_file

    def get_current_vendor_lic_output(self,shell,vendor_lic_file):
        #Get current license file from the License Server
        
        shell.send(f'cat {vendor_lic_file}' + '\n')
        time.sleep(2)

        current_vendor_lic_output = shell.recv(1000000)

        if self.debug_run:
            print('='*50)
            print('Printing existing remote license file' + '\r\n')
            print(current_vendor_lic_output.decode())
            print('='*50)

        return current_vendor_lic_output

    def get_vendor_host_id(self, current_vendor_lic_output):
        #get the current hostid from the existing remote license file
        if self.debug_run:
            print('='*50)
            print(f'Getting existing vendor Host ID' + '\r\n')

        lines = current_vendor_lic_output.decode().split('\n')
        for line in lines:
            if line.startswith('SERVER'): #search for string "SERVER Cadence_SERVER to get the hostid
                vendor_hostid = line.split(' ')[2]
        
        if self.debug_run:
            print(f'Existing HostID: {vendor_hostid}')
            print('='*50)

        return vendor_hostid


    def get_vendor_path(self, current_vendor_lic_output):
        #get the current path from the existing remote license file
        if self.debug_run:
            print('='*50)
            print(f'Getting existing vendor path' + '\r\n')

        lines = current_vendor_lic_output.decode().split('\n')
        for line in lines:
            if line.startswith('DAEMON'): #search for string "DAEMON cdslmd" to get the path
                vendor_path = line.split(' ')[2]

            if line.startswith('VENDOR snpslmd'): #search for string "DAEMON cdslmd" to get the path
                vendor_path = line.split(' ')[2]
        if self.debug_run:
            print(f'Existing Vendor path: {vendor_path}')
            print('='*50)

        return vendor_path

    def set_hostid_and_path(self,new_local_lic_path,vendor_name,vendor_hostid, vendor_path):
        #set the hostid and path on the new local license file
        if self.debug_run:
            print('='*50)
            print(f'Setting vendor host ID and path on the new local license' + '\r\n')

        #if updated license file exists, delete it
        for file in os.listdir(new_local_lic_path):
            if file.endswith("_ready.lic"):
                os.remove(new_local_lic_path + file)

            if file.endswith("dummy_file.txt"): #this is a dummy file necessary to precreated the directory in the git repo
                os.remove(new_local_lic_path + file)

        for file in os.listdir(new_local_lic_path):
            fin = open(new_local_lic_path + file, "rt")
            #output file to write the result to

            if file.endswith(".lic"):
                # fout = open(new_local_lic_path + file.split('.')[0] +"_ready.lic", "wt")
                fout = open(new_local_lic_path + file.rsplit(".", 1)[0] +"_ready.lic", "wt")
                
            else:
                fout = open(new_local_lic_path + file + "_ready.lic", "wt")

            for line in fin:
                #read replace the string and write to output file
                if line.startswith('SERVER'):
                    fout.write(line.replace (line.split(' ')[2], vendor_hostid))

                elif line.startswith('DAEMON'):
                    fout.write(line.replace (line.split(' ')[2], vendor_path))
                    
                else:
                    fout.write(line)

            if self.debug_run:
                print(f'Updated new local license file content "{fout.name}" with a existing Host ID and path from the existing remote license')

        if self.debug_run:    
            print('='*50)
                
            #close input and output files
            fin.close()
            fout.close()

        return


    def prep_lmgrd_lic_string(self,new_local_lic_path,new_remote_lic_path):
        # Prepare the full license string for lmgrd
        all_lic_string = ''

        for file in os.listdir(new_local_lic_path):
            if file.endswith("_ready.lic"):
                all_lic_string += new_remote_lic_path + file + ':' #add all the new license files to the string separated by a colon
        
        all_lic_string = all_lic_string.rsplit(":", 1)[0] # remove the last colon
        
        return all_lic_string


    def upload_new_lic_file(self,ssh_client, new_local_lic_path,new_remote_lic_path):
        #Uploading new license file to the License Server

        scp = SCPClient(ssh_client.get_transport())

        for file in os.listdir(new_local_lic_path):
            if file.endswith("_ready.lic"):
                scp.put(new_local_lic_path + file, new_remote_lic_path)

                if self.debug_run:
                    print('='*50)
                    print(f'Uploaded new license file "{file}" to the License Server remote path "{new_remote_lic_path}')     
                    print('='*50)
        scp.close()

        return

    def remove_old_lic_file(self,shell, vendor_lic_file):
        #Remove old license file from the License Server
        shell.send(f'lmdown -c {vendor_lic_file}' + '\n')
        time.sleep(1)
        
        lmdown_output = shell.recv(10000)

        if self.debug_run:
            print('='*50)
            print(f'Printing output for "lmdown -c {vendor_lic_file}"' + '\r\n')
            print(lmdown_output.decode())
            print('='*50)


    def set_new_license(self,shell,lmgrd_license_string,log_path):
        #Set new license on the License Server
        shell.send(f'lmgrd -c {lmgrd_license_string} -l {log_path}' + '\n') # has not been validated, need to check the command, need to add error handling, where can we get the log file path and file name
        time.sleep(2)
        lmgrd_output = shell.recv(100000)

        if self.debug_run:
            print('='*50)
            print(f'Printing output for seting new license command - "lmgrd" command' + '\r\n')
            print(lmgrd_output.decode())
            print('='*50)

    def check_log_file(self,shell,log_path):
        #Check the log file for errors

        shell.send(f'cat {log_path}' + '\n') # !!!!!!! Validate path to the log file, add error validations
        time.sleep(1)

        log_output = shell.recv(10000)

        if self.debug_run:
            print('='*50)
            print('Printing log file output' + '\r\n')
            print(log_output.decode())



    def verify_license(self,shell,lmgrd_license_string):
        #Verify the license on the License Server

        shell.send(f'sssverify {lmgrd_license_string}' + '\n')
        time.sleep(2)

        sssverify_output = shell.recv(10000)

        print('='*50)
        print('Printing sslverify output' + '\r\n')
        print(sssverify_output.decode())
        print('='*50)

    ############################## Main script #######################################################
    def run(self):
        #Run the script

        if self.debug_run:
            print('='*50)
            print(f'!!!Running the script with DEBUG mode ON!!!')
            print('='*50)

        #################### Connect to the License Server ###########################################
        
        ssh_client = self.connect_to_license_server()
        shell = ssh_client.invoke_shell()

        #################### Get the current license file from the License Server ####################

        lmstat_output = self.get_current_license(shell)

        ################## Get the existing path to the license file #################################

        vendor_lic_file = self.get_vendor_lic_location(lmstat_output)

        # #################### Get the existing license file from the server #########################

        current_vendor_lic_output = self.get_current_vendor_lic_output(shell,vendor_lic_file)

        ################### Get existing hostid and path by opening an existing Vendor license (Using Cadence specific example) ####################

        vendor_hostid = self.get_vendor_host_id(current_vendor_lic_output)
        vendor_path = self.get_vendor_path(current_vendor_lic_output)

       #################### Open new license and replace hostid and path from the existing lic (Using Cadence specific example) ####################
        
        self.set_hostid_and_path(new_local_lic_path,vendor_name,vendor_hostid, vendor_path)

        # #################### Upload new license file to the server ####################

        self.upload_new_lic_file(ssh_client, new_local_lic_path,new_remote_lic_path)

       #################### Remove the old license file from the server ####################

        self.remove_old_lic_file(shell, vendor_lic_file)

        ###################### Get lmgrd license files string ######################

        lmgrd_license_string = self.prep_lmgrd_lic_string(new_local_lic_path,new_remote_lic_path)

        # #################### Set the new license file to the server ####################

        self.set_new_license(shell, lmgrd_license_string,log_path)
        
        # #################### Check the log file for errors  ############################### 


        self.check_log_file(shell,log_path)

        # #################### Verify license is properly installed ###############################
        
        self.verify_license(shell,lmgrd_license_string)

        # #################### Close the connection to the License Server ###############################

        if ssh_client.get_transport().is_active() == True:
            print('Closing connection')
            ssh_client.close()

if __name__ == '__main__':
    LicenseServer(lic_srv_ip, new_local_lic_path, new_remote_lic_path, log_path, vendor_name,vendor_ssh_port, user, password,debug_run).run()