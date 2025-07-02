import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import os
from utils.logger import get_logger

logger = get_logger()


class NmapScanner:
    def __init__(self, target: str, output_dir: str = "output/reports"):
        self.target = target
        self.output_dir = output_dir
        self.txt_output_file = Path(
            self.output_dir) / f"nmap_scan_{self.target.replace('/', '_')}.txt"
        self.json_output_file = Path(
            self.output_dir) / f"nmap_scan_{self.target.replace('/', '_')}.json"
        self.results: Dict[str, Any] = {
            'target': target,
            'status': 'pending',
            'txt_file': str(self.txt_output_file),
            'raw_output': '',
            'error': None
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def run_scan(self, arguments: str = "-sV -sC -T4") -> Dict[str, Any]:
        """
        Run Nmap scan with the specified arguments, save as TXT and JSON only.
        """
        try:
            # Build the Nmap command
            cmd = ["nmap", "-oN", str(self.txt_output_file)] + \
                arguments.split() + [self.target]
            logger.info(f"Running Nmap scan: {' '.join(cmd)}")

            # Execute Nmap
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # Read the text output from file
            if self.txt_output_file.exists():
                with open(self.txt_output_file, 'r') as f:
                    raw_output = f.read()
            else:
                raw_output = stdout

            self.results['raw_output'] = raw_output
            self.results['status'] = 'completed' if process.returncode == 0 else 'failed'
            self.results['error'] = stderr if process.returncode != 0 else None

            # Parse ports from raw_output and add to results
            self.results['ports'] = self.parse_nmap_ports(raw_output)

            # Save JSON
            with open(self.json_output_file, 'w') as f:
                json.dump(self.results, f, indent=2)

            logger.info(
                f"Nmap scan completed. Results saved to {self.txt_output_file} and {self.json_output_file}")
            return self.results

        except Exception as e:
            error_msg = f"Error running Nmap scan: {str(e)}"
            logger.error(error_msg)
            self.results['error'] = error_msg
            self.results['status'] = 'failed'
            # Save JSON with error
            with open(self.json_output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            return self.results

    def parse_nmap_ports(self, raw_output):
        import re
        ports = []
        in_ports = False
        for line in raw_output.splitlines():
            if line.strip().startswith("PORT"):
                in_ports = True
                continue
            if in_ports:
                if not line.strip() or line.startswith("Nmap done") or line.startswith("#"):
                    break
                m = re.match(r"^(\d+)/(\w+)\s+(\w+)\s+(\S+)(\s+.+)?$", line.strip())
                if m:
                    port, proto, state, service, version = m.groups()
                    ports.append({
                        "port": port,
                        "protocol": proto,
                        "state": state,
                        "service": service,
                        "version": (version or "").strip()
                    })
        return ports

    def save_results(self, output_file: Optional[str] = None) -> str:
        """
        Save scan results to a JSON file (already handled in run_scan, but kept for compatibility)
        """
        if not output_file:
            output_file = self.json_output_file
        else:
            output_file = Path(output_file)
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Saved Nmap scan results to {output_file}")
        return str(output_file)


# Example usage
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    scanner = NmapScanner(target)
    results = scanner.run_scan("-sV -sC -T4")
    output_file = scanner.save_results()
    print(f"Scan completed. Results saved to {output_file}")
