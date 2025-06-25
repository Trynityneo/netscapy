import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional
import os
import re
import time

from utils.logger import get_logger

logger = get_logger()

class NiktoScanner:
    def __init__(self, target: str, output_dir: str = "output/reports"):
        self.target = target
        self.output_dir = output_dir
        self.output_file = Path(self.output_dir) / f"nikto_scan_{self.target.replace('/', '_')}.xml"
        self.results: Dict[str, Any] = {
            'target': target,
            'scan_results': {
                'vulnerabilities': [],
                'scan_details': {}
            },
            'status': 'pending'
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_scan(self, arguments: str = "-h") -> Dict[str, Any]:
        """
        Run Nikto scan with the specified arguments
        
        Args:
            arguments (str): Nikto command line arguments
            
        Returns:
            dict: Scan results
        """
        try:
            # Build the Nikto command
            cmd = ["nikto", "-o", str(self.output_file), "-Format", "xml"]
            
            # Add the target and any additional arguments
            cmd.extend(arguments.split())
            cmd.extend(["-host", self.target])
            
            logger.info(f"Running Nikto scan: {' '.join(cmd)}")
            
            # Execute Nikto
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update status
            self.results['status'] = 'running'
            self.results['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Clean up Nikto's progress output
                    clean_output = re.sub(r'\x1b\[.*?m', '', output).strip()
                    if clean_output:
                        logger.debug(f"Nikto output: {clean_output}")
            
            # Check for errors
            stderr = process.stderr.read()
            if stderr:
                error_msg = f"Nikto error: {stderr}"
                logger.error(error_msg)
                self.results['error'] = error_msg
                self.results['status'] = 'failed'
                return self.results
            
            # Parse the XML output
            self._parse_nikto_xml()
            
            # Update status
            self.results['status'] = 'completed'
            self.results['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return self.results
            
        except Exception as e:
            error_msg = f"Error running Nikto scan: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
            self.results['status'] = 'failed'
            return self.results
    
    def _parse_nikto_xml(self) -> None:
        """Parse Nikto XML output and extract relevant information"""
        try:
            if not self.output_file.exists():
                raise FileNotFoundError(f"Nikto XML output file not found: {self.output_file}")
            
            tree = ET.parse(self.output_file)
            root = tree.getroot()
            
            # Extract scan details
            scandetails = root.find('scandetails')
            if scandetails is not None:
                self.results['scan_details'] = {
                    'target_ip': scandetails.get('targetip', ''),
                    'target_hostname': scandetails.get('targethostname', ''),
                    'target_port': scandetails.get('targetport', ''),
                    'target_banner': scandetails.get('targetbanner', ''),
                    'start_time': scandetails.get('starttime', ''),
                    'site_name': scandetails.get('sitename', ''),
                    'site_ip': scandetails.get('siteip', ''),
                    'host_header': scandetails.get('hostheader', ''),
                    'errors': []
                }
                
                # Extract any scan errors
                for error in scandetails.findall('error'):
                    self.results['scan_details']['errors'].append({
                        'message': error.text,
                        'details': error.get('details', '')
                    })
            
            # Extract vulnerabilities
            for item in root.findall('.//item'):
                vulnerability = {
                    'id': item.get('id', ''),
                    'osvdb_id': item.get('osvdbid', ''),
                    'osvdb_link': item.get('osvdblink', ''),
                    'description': item.find('description').text if item.find('description') is not None else '',
                    'uri': item.find('uri').text if item.find('uri') is not None else '',
                    'name': item.find('namelink').get('name', '') if item.find('namelink') is not None else '',
                    'method': item.find('namelink').get('method', '') if item.find('namelink') is not None else '',
                    'iplink': item.find('iplink').text if item.find('iplink') is not None else '',
                }
                
                # Extract additional details
                for elem in item:
                    if elem.tag not in ['description', 'uri', 'namelink', 'iplink'] and elem.text:
                        vulnerability[elem.tag] = elem.text
                
                self.results['scan_results']['vulnerabilities'].append(vulnerability)
            
            logger.info(f"Found {len(self.results['scan_results']['vulnerabilities'])} potential vulnerabilities")
            
        except Exception as e:
            error_msg = f"Error parsing Nikto XML: {str(e)}"
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
                output_file = Path(self.output_dir) / f"nikto_scan_{self.target.replace('/', '_')}.json"
            else:
                output_file = Path(output_file)
            
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=4)
            
            logger.info(f"Saved Nikto scan results to {output_file}")
            return str(output_file)
            
        except Exception as e:
            error_msg = f"Error saving Nikto results: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

# Example usage
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    
    scanner = NiktoScanner(target)
    results = scanner.run_scan("-h")
    output_file = scanner.save_results()
    print(f"Scan completed. Results saved to {output_file}")
