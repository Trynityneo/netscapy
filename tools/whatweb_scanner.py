import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
import time

from utils.logger import get_logger

logger = get_logger()

class WhatWebScanner:
    def __init__(self, target: str, output_dir: str = "output/reports"):
        self.target = self._normalize_target(target)
        self.output_dir = output_dir
        self.output_file = Path(self.output_dir) / f"whatweb_scan_{self.target.replace('/', '_')}.json"
        self.results = {
            'target': self.target,
            'scan_results': {},
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'error': None
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def _normalize_target(self, target: str) -> str:
        """Ensure target has http:// or https:// prefix"""
        if not (target.startswith('http://') or target.startswith('https://')):
            return f"http://{target}"
        return target

    def run_scan(self, arguments: str = "--color=never --no-errors -a 3") -> Dict[str, Any]:
        """Run WhatWeb scan with specified arguments"""
        try:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
                temp_path = tmp.name

            # Build command
            cmd = ["whatweb", "--log-json", temp_path]
            if arguments:
                cmd.extend(arguments.split())
            cmd.append(self.target)
            
            logger.info(f"Running: {' '.join(cmd)}")
            
            # Update status
            self.results['status'] = 'running'
            self.results['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Execute
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            # Handle errors
            if process.returncode != 0:
                error_msg = f"WhatWeb error: {stderr}"
                logger.error(error_msg)
                self.results['error'] = error_msg
                self.results['status'] = 'failed'
                return self.results
            
            # Parse results
            self._parse_results(temp_path)
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
            
            self.results['status'] = 'completed'
            self.results['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return self.results
            
        except Exception as e:
            error_msg = f"Error in WhatWeb scan: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
            self.results['status'] = 'failed'
            return self.results
    
    def _parse_results(self, file_path: str) -> None:
        """Parse WhatWeb JSON output"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list) or not data:
                return
                
            # Extract relevant info from first result
            result = data[0]
            self.results['scan_results'] = {
                'url': result.get('target', {}).get('url', ''),
                'ip': result.get('plugins', {}).get('IP', {}).get('string', [None])[0],
                'http_status': result.get('http_status', 0),
                'technologies': self._extract_technologies(result.get('plugins', {})),
                'headers': result.get('headers', {})
            }
            
        except Exception as e:
            error_msg = f"Error parsing WhatWeb results: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
    
    def _extract_technologies(self, plugins: Dict) -> Dict[str, List[str]]:
        """Extract technology information from plugins"""
        tech = {}
        for name, data in plugins.items():
            if name == 'HTTPServer':
                tech['web_server'] = data.get('string', [None])[0]
            elif name == 'Title':
                tech['title'] = data.get('string', [None])[0]
            elif name not in ['IP', 'HTTPServer', 'Title']:
                if name not in tech:
                    tech[name] = []
                if isinstance(data.get('string'), list):
                    tech[name].extend([s for s in data['string'] if s])
        return tech
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """Save scan results to JSON file"""
        try:
            if not output_file:
                output_file = self.output_file
            else:
                output_file = Path(output_file)
            
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"Results saved to {output_file}")
            return str(output_file)
            
        except Exception as e:
            error_msg = f"Error saving results: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

# Example usage
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    
    scanner = WhatWebScanner(target)
    results = scanner.run_scan()
    output_file = scanner.save_results()
    print(f"Scan completed. Results saved to {output_file}")
