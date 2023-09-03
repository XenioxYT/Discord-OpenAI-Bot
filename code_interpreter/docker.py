import os
import subprocess
import re

import os
import re
import subprocess

def run_code_in_docker(code):
    try:
        # Search for plt.savefig in the code and extract the path
        match = re.search(r"plt\.savefig\(['\"](.*?)['\"]\)", code)
        docker_image_path = match.group(1) if match else None
        
        if docker_image_path:
            # Set where you want to save the image on the host
            host_directory = "/home/gpu/repliesbot-vin-server/code_interpreter/images"
            host_image_path = os.path.join(host_directory, os.path.basename(docker_image_path))
            
            # Create host directory if it doesn't exist
            if not os.path.exists(host_directory):
                os.makedirs(host_directory)
        
        # Your existing code to create a Docker container
        container_create_command = [
            'docker',
            'create',
            '--memory=1g',
            '--cpus=1',
            'code_interpreter',
            'python',
            '-c',
            code
        ]
        container_id = subprocess.check_output(container_create_command, stderr=subprocess.STDOUT).decode('utf-8').strip()
        
        try:
            output_run = subprocess.run(['docker', 'start', '-a', container_id], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Standard Output: ", output_run.stdout.decode('utf-8'))  # Log stdout
            
            # If an image was generated, copy it to the host
            if docker_image_path:
                subprocess.run(['docker', 'cp', f'{container_id}:{docker_image_path}', host_image_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logs = subprocess.check_output(['docker', 'logs', container_id]).decode('utf-8')
            print("Logs: ", logs)  # Log logs
            
            return logs, host_image_path if docker_image_path else None
            
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error: {e}")
            print(f"Standard Output: {e.stdout.decode('utf-8')}")
            print(f"Standard Error: {e.stderr.decode('utf-8')}")
            return f"Command failed with error: {e}"
        
        finally:
            subprocess.run(['docker', 'rm', '-f', container_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        if e.output:
            print(f"Output: {e.output.decode('utf-8')}")


# Example usage
code = '''
print("Hello world!")
'''

output = run_code_in_docker(code)
print(f"Output: {output}")
