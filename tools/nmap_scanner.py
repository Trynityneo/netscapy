import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import os

from utils.logger import get_logger

logger = get_logger()

class NmapScanner:
    def __init__(self, target: str, output_dir: str = "output/reports"):
        self.target = target
        self.output_dir = output_dir
        self.output_file = Path(self.output_dir) / f"nmap_scan_{self.target.replace('/', '_')}.xml"
        self.results: Dict[str, Any] = {
            'target': target,
            'scan_results': {}
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_scan(self, arguments: str = "-sV -sC -T4") -> Dict[str, Any]:
        """
        Run Nmap scan with the specified arguments
        
        Args:
            arguments (str): Nmap command line arguments
            
        Returns:
            dict: Scan results
        """
        try:
            # Build the Nmap command
            cmd = ["nmap", "-oX", str(self.output_file)] + arguments.split() + [self.target]
            logger.info(f"Running Nmap scan: {' '.join(cmd)}")
            
            # Execute Nmap
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logger.debug(f"Nmap output: {output.strip()}")
            
            # Check for errors
            stderr = process.stderr.read()
            if stderr:
                logger.error(f"Nmap error: {stderr}")
                self.results['error'] = stderr
                return self.results
            
            # Parse the XML output
            self._parse_nmap_xml()
            
            return self.results
            
        except Exception as e:
            error_msg = f"Error running Nmap scan: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
            return self.results
    
    def _parse_nmap_xml(self) -> None:
        """Parse Nmap XML output and extract relevant information"""
        try:
            if not self.output_file.exists():
                raise FileNotFoundError(f"Nmap XML output file not found: {self.output_file}")
            
            tree = ET.parse(self.output_file)
            root = tree.getroot()
            
            # Extract host information
            for host in root.findall('host'):
                host_info = {}
                
                # Get host status
                status = host.find('status')
                if status is not None:
                    host_info['status'] = status.get('state', 'unknown')
                
                # Get addresses
                addresses = []
                for addr in host.findall('address'):
                    addresses.append({
                        'type': addr.get('addrtype', ''),
                        'address': addr.get('addr', '')
                    })
                if addresses:
                    host_info['addresses'] = addresses
                
                # Get hostnames
                hostnames = []
                for hname in host.findall('hostnames/hostname'):
                    hostnames.append({
                        'name': hname.get('name', ''),
                        'type': hname.get('type', '')
                    })
                if hostnames:
                    host_info['hostnames'] = hostnames
                
                # Get ports and services
                ports = []
                for port in host.findall('ports/port'):
                    port_info = {
                        'port': port.get('portid', ''),
                        'protocol': port.get('protocol', '')
                    }
                    
                    # Get service information
                    service = port.find('service')
                    if service is not None:
                        port_info['service'] = {
                            'name': service.get('name', ''),
                            'product': service.get('product', ''),
                            'version': service.get('version', ''),
                            'extrainfo': service.get('extrainfo', '')
                        }
                    
                    # Get script output if any
                    scripts = []
                    for script in port.findall('script'):
                        scripts.append({
                            'id': script.get('id', ''),
                            'output': script.get('output', '')
                        })
                    if scripts:
                        port_info['scripts'] = scripts
                    
                    ports.append(port_info)
                
                if ports:
                    host_info['ports'] = ports
                
                # Add host info to results
                self.results['scan_results'] = host_info
            
            logger.info("Successfully parsed Nmap XML output")
            
        except Exception as e:
            error_msg = f"Error parsing Nmap XML: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """
        Save scan results to a JSON file
        
        Args:
            output_file (str, optional): Path to output file. If not provided, a default will be used.
            
        Returns:
            str: Path to the saved file
        """
        try:
            if not output_file:
                output_file = Path(self.output_dir) / f"nmap_scan_{self.target.replace('/', '_')}.json"
            else:
                output_file = Path(output_file)
            
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=4)
            
            logger.info(f"Saved Nmap scan results to {output_file}")
            return str(output_file)
            
        except Exception as e:
            error_msg = f"Error saving Nmap results: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

# Example usage
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    
    scanner = NmapScanner(target)
    results = scanner.run_scan("-sV -sC -T4")
    output_file = scanner.save_results()
    print(f"Scan completed. Results saved to {output_file}")
